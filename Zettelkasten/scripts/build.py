"""Validate a Markdown Zettelkasten and rebuild its derived deliverables.

The editable source of truth is vault/*.md. The builder never rewrites it.
Validation uses the standard library; full rendering needs Pillow, ReportLab,
and pypdf. No network access or application installation is required.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import math
import re
import textwrap
from collections import Counter
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parents[1]
VAULT = ROOT / 'vault'
OUTPUT = ROOT / 'output'
KINDS = ('GDD', 'SRS', 'SDD', 'DEV', 'MKT', 'SUP', 'IDEA')
COLORS = ('#2274a5', '#c76b19', '#21866b', '#7a58a5', '#b24d75', '#566576', '#b19716')
COLOR = dict(zip(KINDS, COLORS))
WIKI = re.compile(r'\[\[([^\]\n]+)\]\]')


def load_and_validate():
    notes = {}
    errors = []
    ids = set()
    for p in sorted(VAULT.glob('*.md')):
        body = p.read_text(encoding='utf-8')
        match_id = re.search(r'^id: "(\d{14})"$', body, re.M)
        match_type = re.search(r'^type: (\w+)$', body, re.M)
        title = re.search(r'^# (.+)$', body, re.M)
        if not all((match_id, match_type, title)):
            errors.append(f'{p.name}: missing ID, type or title')
            continue
        note_id = match_id[1]
        if note_id in ids:
            errors.append(f'{p.name}: duplicate ID {note_id}')
        ids.add(note_id)
        tag_line = re.search(r'^Теги: (.+)$', body, re.M)
        tags = set(re.findall(r'#([A-Za-z][A-Za-z0-9_-]*)', tag_line[1] if tag_line else ''))
        if len(tags) < 2:
            errors.append(f'{p.name}: fewer than two tags')
        notes[p.stem] = dict(path=p, id=note_id, kind=match_type[1], title=title[1], tags=tags, body=body)
    atomic = {key: n for key, n in notes.items() if n['kind'] != 'META'}
    for key, n in atomic.items():
        if key != n['id'] or n['kind'] not in KINDS:
            errors.append(f'{key}: invalid canonical filename or type')
        if n['kind'] not in n['tags']:
            errors.append(f'{key}: missing type tag')
        if len(re.findall(r'^## Идея$', n['body'], re.M)) != 1:
            errors.append(f'{key}: expected exactly one idea section')
    edges = set()
    for key, n in notes.items():
        for target in WIKI.findall(n['body']):
            dest = target.split('|', 1)[0].split('#', 1)[0]
            if dest not in notes:
                errors.append(f'{key}: unresolved wikilink {dest}')
            elif key in atomic and dest in atomic:
                if key == dest:
                    errors.append(f'{key}: self link')
                edges.add((key, dest))
        for dest in re.findall(r'\]\((sources/[^)]+)\)', n['body']):
            if not (VAULT / dest).is_file():
                errors.append(f'{key}: missing source {dest}')
    outgoing = {key: set() for key in atomic}
    incoming = {key: set() for key in atomic}
    for src, dst in edges:
        outgoing[src].add(dst)
        incoming[dst].add(src)
    for key in atomic:
        if len(outgoing[key]) < 2:
            errors.append(f'{key}: fewer than two meaningful outgoing links')
        if not incoming[key]:
            errors.append(f'{key}: no incoming links')

    def reachable(start, mapping):
        reached = {start}
        pending = [start]
        while pending:
            node = pending.pop()
            for other in mapping[node] - reached:
                reached.add(other)
                pending.append(other)
        return reached

    undirected = {k: outgoing[k] | incoming[k] for k in atomic}
    remaining = set(atomic)
    components = 0
    while remaining:
        remaining -= reachable(next(iter(remaining)), undirected)
        components += 1
    if components != 1:
        errors.append(f'Atomic graph has {components} weak components')
    strong = bool(atomic) and all(len(reachable(k, outgoing)) == len(atomic) for k in atomic)
    tags = Counter(tag for n in atomic.values() for tag in n['tags'])
    metrics = dict(atomic_notes=len(atomic), service_notes=len(notes)-len(atomic),
                   directed_links=len(edges), undirected_pairs=len({tuple(sorted(e)) for e in edges}),
                   cross_type_links=sum(atomic[a]['kind'] != atomic[b]['kind'] for a,b in edges),
                   isolated_notes=sum(not undirected[k] for k in atomic),
                   min_outgoing_links=min(map(len, outgoing.values()), default=0),
                   min_incoming_links=min(map(len, incoming.values()), default=0),
                   min_tags=min((len(n['tags']) for n in notes.values()), default=0),
                   weak_components=components, strongly_connected=strong,
                   type_counts=dict(Counter(n['kind'] for n in atomic.values())),
                   tag_counts=dict(sorted(tags.items())), broken_wikilinks=sum('unresolved wikilink' in e for e in errors),
                   errors=errors, status='PASS' if not errors else 'FAIL')
    OUTPUT.mkdir(exist_ok=True)
    (OUTPUT / 'validation.json').write_text(json.dumps(metrics, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    if errors:
        raise ValueError('\n'.join(errors))
    return notes, atomic, edges, metrics


def svg_to_png(svg_path, png_path, size, draw_function):
    """Render with Pillow using the same geometry as the SVG source."""
    from PIL import Image, ImageDraw, ImageFont
    font_dir = Path('C:/Windows/Fonts')
    if not (font_dir / 'arial.ttf').exists():
        font_dir = Path('/usr/share/fonts/truetype/dejavu')
    regular = font_dir / ('arial.ttf' if (font_dir / 'arial.ttf').exists() else 'DejaVuSans.ttf')
    bold = font_dir / ('arialbd.ttf' if (font_dir / 'arialbd.ttf').exists() else 'DejaVuSans-Bold.ttf')
    img = Image.new('RGB', size, 'white')
    draw = ImageDraw.Draw(img)
    def font(size, heavy=False):
        return ImageFont.truetype(str(bold if heavy else regular), size)
    svg = draw_function(draw, font)
    svg_path.write_text(svg, encoding='utf-8')
    img.save(png_path)


def build_graph(atomic, edges, metrics):
    from PIL import Image, ImageDraw
    folder = VAULT / 'attachments'
    folder.mkdir(exist_ok=True)
    width, height = 2100, 1740
    center = (1050, 760)
    radius = 550
    keys = sorted(atomic)
    pos = {k: (center[0]+radius*math.cos(-math.pi/2+2*math.pi*i/len(keys)),
               center[1]+radius*math.sin(-math.pi/2+2*math.pi*i/len(keys))) for i,k in enumerate(keys)}
    def draw_graph(draw, font):
        parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
                 '<rect width="100%" height="100%" fill="white"/>',
                 '<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="#aeb9c6"/></marker></defs>']
        def label(x,y,text,size=32,color='#203247',bold=False,anchor='start'):
            draw.text((x,y),text,font=font(size,bold),fill=color,anchor={'middle':'mm','start':'lm','end':'rm'}[anchor])
            parts.append(f'<text x="{x}" y="{y}" dominant-baseline="central" text-anchor="{anchor}" font-family="Arial, sans-serif" font-size="{size}" font-weight="{700 if bold else 400}" fill="{color}">{html.escape(text)}</text>')
        label(1050,65,'ALIEN INVASION / СЕТЬ КАРТОЧЕК',48,bold=True,anchor='middle')
        label(1050,122,f'35 атомарных заметок · {metrics["directed_links"]} направленных ссылок · 7 типов',29,anchor='middle')
        label(1050,165,'Номер узла = последние две цифры ID карточки',25,color='#64748b',anchor='middle')
        for a,b in sorted(edges):
            x1,y1=pos[a]; x2,y2=pos[b]
            dx,dy=x2-x1,y2-y1
            dist=math.hypot(dx,dy)
            start=(x1+dx/dist*34,y1+dy/dist*34)
            end=(x2-dx/dist*37,y2-dy/dist*37)
            draw.line([start,end],fill='#ced6df',width=2)
            angle=math.atan2(dy,dx)
            points=[end,(end[0]-13*math.cos(angle-.45),end[1]-13*math.sin(angle-.45)),
                    (end[0]-13*math.cos(angle+.45),end[1]-13*math.sin(angle+.45))]
            draw.polygon(points,fill='#aeb9c6')
            parts.append(f'<path d="M {start[0]:.1f} {start[1]:.1f} L {end[0]:.1f} {end[1]:.1f}" fill="none" stroke="#ced6df" stroke-width="2" marker-end="url(#arrow)"/>')
        for key in keys:
            n=atomic[key]; x,y=pos[key]; color=COLOR[n['kind']]
            draw.ellipse((x-35,y-35,x+35,y+35),fill=color,outline='white',width=4)
            parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="35" fill="{color}" stroke="white" stroke-width="4"/>')
            label(x,y,f'{int(key[-6:]):02d}',30,'white',True,'middle')
        y=1390
        for i,kind in enumerate(KINDS):
            x=100+i*290
            draw.rounded_rectangle((x,y,x+255,y+62),radius=12,fill=COLOR[kind])
            parts.append(f'<rect x="{x}" y="{y}" width="255" height="62" rx="12" fill="{COLOR[kind]}"/>')
            label(x+127,y+31,f'{kind} · {metrics["type_counts"][kind]}',27,'white',True,'middle')
        groups = [('01-08 GDD','Игровые решения'),('09-14 SRS','Проверяемые требования'),('15-20 SDD','Устройство программы'),('21-24 DEV','Разработка и проверки'),('25-27 MKT','Показ и распространение'),('28-30 SUP','Поддержка'),('31-35 IDEA','Новые гипотезы')]
        for i,(a,b) in enumerate(groups):
            row,col=divmod(i,4); x=75+col*515; yy=1503+row*82
            label(x,yy,a,25,bold=True)
            label(x,yy+35,b,23,color='#64748b')
        label(1050,1700,'Стрелка указывает на упомянутую карточку. Служебные заметки и источники исключены.',25,anchor='middle')
        parts.append('</svg>')
        return '\n'.join(parts)
    svg_to_png(folder/'graph.svg',folder/'graph.png',(width,height),draw_graph)

    selected = [k for k,n in atomic.items() if 'ui' in n['tags']]
    tw,th=1600,1000
    def draw_tag(draw,font):
        parts=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{tw}" height="{th}"><rect width="100%" height="100%" fill="white"/>']
        def txt(x,y,text,size=28,bold=False,color='#203247',middle=False):
            draw.text((x,y),text,font=font(size,bold),fill=color,anchor='mm' if middle else 'lm')
            parts.append(f'<text x="{x}" y="{y}" dominant-baseline="central" text-anchor="{"middle" if middle else "start"}" font-family="Arial, sans-serif" font-size="{size}" font-weight="{700 if bold else 400}" fill="{color}">{html.escape(text)}</text>')
        txt(800,65,'ГОРИЗОНТАЛЬНАЯ СВЯЗЬ ЧЕРЕЗ #ui',40,True,middle=True)
        txt(800,120,f'{len(selected)} карточек из {len({atomic[k]["kind"] for k in selected})} типов',27,middle=True)
        locations=[]
        for i,k in enumerate(selected):
            side=i%2; row=i//2
            x=40 if side==0 else 1040; y=235+row*255
            locations.append((k,x,y))
            start=(x+500,y+90) if side==0 else (x,y+90)
            draw.line([start,(800,510)],fill='#c8d3df',width=5)
            parts.append(f'<line x1="{start[0]}" y1="{start[1]}" x2="800" y2="510" stroke="#c8d3df" stroke-width="5"/>')
        for k,x,y in locations:
            note=atomic[k]; color=COLOR[note['kind']]
            draw.rounded_rectangle((x,y,x+520,y+180),radius=18,fill='#f4f7fa',outline=color,width=4)
            parts.append(f'<rect x="{x}" y="{y}" width="520" height="180" rx="18" fill="#f4f7fa" stroke="{color}" stroke-width="4"/>')
            txt(x+25,y+35,f'{note["kind"]} / {int(k[-6:]):02d}',29,True,color)
            title=note['title'].split(' - ',1)[1]
            for j,line in enumerate(textwrap.wrap(title,width=29)):
                txt(x+25,y+80+j*35,line,26)
        draw.ellipse((705,415,895,605),fill='#203247')
        parts.append('<circle cx="800" cy="510" r="95" fill="#203247"/>')
        txt(800,510,'#ui',43,True,'white',True)
        txt(800,960,'Общий тег связывает темы; смысловые ссылки остаются внутри карточек.',25,middle=True)
        parts.append('</svg>')
        return '\n'.join(parts)
    svg_to_png(folder/'tag-ui.svg',folder/'tag-ui.png',(tw,th),draw_tag)
    (OUTPUT/'graph-data.json').write_text(json.dumps({'nodes':[{'id':k,'type':n['kind'],'title':n['title']} for k,n in atomic.items()],
        'edges':[{'source':a,'target':b} for a,b in sorted(edges)],'tag_ui':selected},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


def body_section(note, name):
    return note['body'].split('## '+name+'\n\n',1)[1].split('\n## ',1)[0].strip()


def build_documents(atomic):
    descriptions={'GDD':'Игровые решения и смысл правил','SRS':'Требования и способы проверки','SDD':'Устройство фактической реализации ЛР6',
        'DEV':'Разработка, проверки и согласование источников','MKT':'Гипотезы показа и распространения','SUP':'Процедуры поддержки и инструкции',
        'IDEA':'Новые идеи, полученные из сети'}
    for kind in KINDS:
        lines=[f'# {kind}: Alien Invasion',f'\n{descriptions[kind]}. Сборка из атомарных карточек от 21.10.2026.',
               '\nДокумент сохраняет статусы карточек. Проектные требования, выводы и предложения не являются утверждением о готовой реализации. Источники и подробные связи доступны по ссылкам.']
        for k,n in atomic.items():
            if n['kind']!=kind:
                continue
            lines.extend([f'\n## {n["title"].split(" - ",1)[1]}',f'\n[Карточка {k}](../vault/{k}.md).',
                          '\n'+body_section(n,'Идея'), '\n'+body_section(n,'Обоснование и проверка')])
            relation=body_section(n,'Связи')
            relation=WIKI.sub(lambda m: f'[{m[1]}](../vault/{m[1]}.md)',relation)
            lines.append('\n'+relation)
        (ROOT/'docs'/f'{kind}.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    with (OUTPUT/'cards.csv').open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.writer(f)
        writer.writerow(['ID','Тип','Заголовок','Теги'])
        writer.writerows((k,n['kind'],n['title'],' '.join('#'+t for t in sorted(n['tags']))) for k,n in atomic.items())


def report_text(m):
    return f'''# Практическая работа: основы Zettelkasten

## Сеть знаний о разработке Alien Invasion

Тоц Леонид Александрович · группа ИВТ-2

Системы и технологии подготовки технической и издательской документации

РГПУ им. А. И. Герцена · Санкт-Петербург · 21 октября 2026 г.

### Цель работы

Организовать знания о разработке игры в виде небольших атомарных карточек, связать их по смыслу, выделить новые идеи и собрать из сети материалы технической документации.

### Исходные данные и выбор темы

Использовано задание Дмитрия Власова «Практическая работа #2 - Основы Zettelkasten» и уточнение преподавателя о сети небольших карточек. Тема выбрана по существующим материалам проекта Alien Invasion: GDD/SRS/SDD ЛР5 и реализация Python/Pygame ЛР6. Номер новой папки не назначался, поскольку в репозитории уже есть ЛР2 с другой темой.

### Полученный результат

Подготовлены {m['atomic_notes']} предметных карточек семи типов, {m['service_notes']} служебные заметки, пять карточек новых идей, два графа, семь отдельных документов Markdown, этот отчёт и архив для передачи. Хранилище не требует облачного сервиса или сторонних плагинов.

### Статусы утверждений

«Подтверждено кодом» означает чтение реализации ЛР6. «Проектное требование» относится к документам ЛР5. «Гипотеза» обозначает ещё не реализованное и не проверенное с игроками предложение. Новые замеры производительности и прогон игры в этой работе не выполнялись.

---PAGE---

## 1. Организация хранилища

Все предметные карточки лежат плоско в vault. Иерархическое оглавление находится в заметке «Старт», а типы GDD/SRS/SDD/DEV/MKT/SUP/IDEA задают точки зрения на предмет. Папки sources и attachments содержат основания и изображения, а не иерархию карточек.

| Тип | Карточек | Содержание |
| --- | --- | --- |
| GDD | 8 | Цель, цикл, движение, залп, флот, уровни, рекорд, HUD |
| SRS | 6 | Лимит пуль, состояние, повтор, офлайн, читаемость, FPS |
| SDD | 6 | Контроллер, ввод, координаты, коллизии, ресурсы, кадр |
| DEV | 4 | Проверки, расхождения, поставка, порядок разработки |
| MKT | 3 | Показ, распространение, получение отзывов |
| SUP | 3 | Дефекты, руководство, выпуск исправления |
| IDEA | 5 | Новые предложения и критерии проверки |

### Пример атомарной карточки

ID: 20261021000009. SRS - Четвёртая активная пуля не создаётся.

Одна мысль: в активной партии существует не более трёх пуль, а удаление пули освобождает слот. Теги: #SRS #requirements #mechanics. Основания: SRS ЛР5, обработчик выстрела и тесты ЛР6.

Ссылки связывают требование с игровой причиной ограничения (04), обработкой попаданий (18), проверкой правила (21) и идеей индикатора (31). Каждая ссылка сопровождается пояснением, зачем переходить к другой карточке.

### Идентификаторы и редактирование

14 цифр состоят из даты 20261021 и порядкового номера. Это постоянный адрес, а не журнал фактического времени создания. Изменение формулировки не требует нового ID; независимая мысль получает отдельную карточку. Числовые имена и ссылки вида [[20261021000009]] подходят для открытия в Obsidian и настройки ID в Zettlr.

---PAGE---

## 2. Граф смысловых связей

![Граф предметных карточек](vault/attachments/graph.png)

Каждый номер на графе соответствует последним двум цифрам ID карточки. Цвет задаёт её тип. Рёбра построены автоматически из реальных ссылок, стрелка направлена к упомянутой карточке. Служебные заметки и снимки исходных материалов исключены.

Граф содержит {m['directed_links']} направленных ссылок между {m['undirected_pairs']} парами карточек; {m['cross_type_links']} ссылок проходят между разными типами. Изолированных предметных заметок нет. Сеть имеет одну компоненту связности. Полноразмерные PNG и SVG находятся в vault/attachments; подписи всех узлов доступны в «Старт» и output/cards.csv.

---PAGE---

## 3. Теги и пересмотр

![Карточки с общим тегом ui](vault/attachments/tag-ui.png)

Тег #ui объединяет {m['tag_counts']['ui']} карточек из GDD, SRS, SUP и IDEA. Это горизонтальная подборка интерфейса: HUD, доступность показателей, первое знакомство, индикатор залпа и предупреждение. Она дополняет объяснённые ссылки внутри карточек.

### Проверка подборок

Автоматически сопоставлены списки файлов для #ui ({m['tag_counts']['ui']}), #mechanics ({m['tag_counts']['mechanics']}), #performance ({m['tag_counts']['performance']}) и #idea ({m['tag_counts']['idea']}). В «Теги-проекта» сохранены явные списки результатов, с которыми можно сравнить поиск редактора.

### Выполненный пересмотр

Сверка ЛР5 и ЛР6 выявила разный смысл запаса кораблей: три жизни в проекте и три замены сверх текущего корабля в коде. В карточке 22 различие выделено явно. Карточка 18 отдельно описывает уничтожение нескольких перекрывающихся целей одной пулей. В карточке 29 указана фактическая клавиша выхода Q вместо проектного Esc. Эти выводы не меняют исходные ЛР.

---PAGE---

## 4. Новые идеи из связей

Ниже приведены гипотезы, полученные при сопоставлении уже существующих карточек. Они не объявляются реализованными функциями.

### 31. Индикатор залпа

Связка 09 -> 08 -> 13: ограниченные пули, постоянный HUD и представление помимо цвета. Предложение: три сегмента и число свободных слотов. Проверка: сегменты соответствуют числу активных пуль; игрок понимает причину отказа в выстреле.

### 32. Предупреждение о низком флоте

Связка 05 -> 08 -> 13: приближение угрозы, обратная связь и читаемость. Предложение: значок и текст при пересечении согласованной опасной высоты. Проверка: правильное включение и сброс предупреждения, затем оценка полезности порога с игроками.

### 33. Неблокирующее восстановление

Связка 20 -> 10 -> 22: обработка кадра, запрет действий и расхождение проекта с кодом. Предложение: RECOVERING с таймером вместо sleep(0.5). Проверка: выход во время восстановления работает, запас повторно не списывается, управление возвращается один раз.

### 34. Временной шаг движения

Связка 14 -> 17 -> 20: нестабильный FPS, дробная позиция и цикл. Предложение: скорости в пикселях за секунду, умноженные на dt. Проверка: одинаковое перемещение за секунду при шагах 1/30 и 1/60 в заданной погрешности; большой dt требует отдельной защиты коллизий.

### 35. Сохранение рекорда

Связка 07 -> 11 -> 12: рекорд процесса, повторная партия и офлайн-режим. Предложение: локальный JSON. Проверка: сохранение после перезапуска, отсутствие сброса при Play и безопасный старт с повреждённым файлом.

### Интеграция в документы

В docs созданы отдельные GDD.md, SRS.md, SDD.md, DEV.md, MKT.md, SUP.md и IDEA.md. Каждый документ собран из соответствующих карточек с обычными Markdown-ссылками. Так сеть используется для подготовки связного материала и сохраняет адреса исходных мыслей.

---PAGE---

## 5. Проверка и воспроизведение

Скрипт scripts/build.py проверил фактические файлы хранилища. Машиночитаемый результат сохранён в output/validation.json, список рёбер - в output/edges.csv. Граф и документы строятся из того же набора карточек.

| Проверка | Результат |
| --- | --- |
| Предметные карточки / минимум задания | {m['atomic_notes']} / 15 |
| Уникальность ID и соответствие имён | Выполнено |
| Минимальное число тегов на заметку | {m['min_tags']} |
| Минимум исходящих / входящих связей | {m['min_outgoing_links']} / {m['min_incoming_links']} |
| Неразрешённые внутренние ссылки | {m['broken_wikilinks']} |
| Изолированные предметные карточки | {m['isolated_notes']} |
| Компоненты связности | {m['weak_components']} |
| Новые идеи / документы Markdown | 5 / 7 |

### Открытие и проверка в редакторе

В Obsidian открыть vault как хранилище, затем «Старт». Для графа выбрать Graph view, фильтр -path:sources исключит исходники; Tags покажет общие теги. В Zettlr добавить vault как рабочую папку и настроить распознавание ID из 14 цифр. Проверить переход из карточки 09 к 31 и подборку #ui. Дополнительные плагины не нужны.

Для повторной проверки из папки Zettelkasten: python scripts/build.py --validate-only. Полная сборка: python scripts/build.py; для неё нужны Pillow, ReportLab и pypdf. Сборка не меняет карточки. Архив содержит всё необходимое для чтения и проверки файлов на другом компьютере.

### Границы выполненной работы

Подготовка файлов, графов и автоматическая проверка выполнены. Установка и открытие Obsidian/Zettlr, проверка поиска в их интерфейсе и снимок живого графа не выполнялись. Готовый статический граф является собственным представлением реальных ссылок и не выдаётся за снимок приложения.

По выбору пользователя результат оставлен локально в папке и полном ZIP-архиве. Пункт PDF о коммите в новом удалённом репозитории не выполнялся: удалённый репозиторий не создавался, коммит и push не выполнялись.

### Вывод

Плоское хранение атомарных мыслей и объяснённые перекрёстные ссылки позволили связать игровой дизайн, требования, код и поддержку. Практический результат работы с сетью - пять проверяемых предложений и явное обнаружение расхождений между проектом и реализацией.

---PAGE---

## 6. Использованные материалы

### Задание и метод

1. Дмитрий Власов. Практическая работа #2 - Основы Zettelkasten. 2024. 11 с. PDF, переданный пользователем. Требования к атомарности, связям, тегам, графу и итоговым документам использованы при подготовке результата.

2. Zettelkasten: как один немецкий учёный стал невероятно продуктивным. Хабр, 29.06.2020. Перевод статьи David B. Clear. Дополнительный материал преподавателя: https://habr.com/ru/articles/508672/

3. Официальный сайт Zettlr. Поддержка ID, внутренних ссылок, тегов и графа: https://www.zettlr.com/

4. Obsidian Help. Internal links: https://help.obsidian.md/Linking+notes+and+files/Internal+links

5. Obsidian Help. Graph view: https://help.obsidian.md/Plugins/Graph+view

Онлайн-источники просмотрены 21.10.2026. Объяснения приведены своими словами; исходный учебный PDF не переиздаётся в составе результата.

### Материалы проекта

6. ЛР5/GDD.md, ЛР5/SRS.md, ЛР5/SDD.md - проектная документация игры.

7. ЛР6/README.md и docs/architecture.md - описание фактического учебного проекта и его архитектуры.

8. ЛР6/src/alien_invasion: alien_invasion.py, settings.py, ship.py, game_stats.py, assets.py - источники фактов о поведении, вводе, координатах, рекорде и ресурсах.

9. ЛР6/tests/test_game_rules.py и pyproject.toml - определения проверок и состав зависимостей/поставки. Тесты изучены, повторный запуск в рамках этой работы не выполнялся.

Снимки перечисленных материалов сохранены в vault/sources. Их происхождение указано в служебной заметке «Источники». Исходные папки ЛР5 и ЛР6 не менялись.
'''


def render_pdf(markdown):
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, Image, KeepTogether
    from pypdf import PdfReader
    folder=Path('C:/Windows/Fonts')
    regular=folder/'arial.ttf'; bold=folder/'arialbd.ttf'; italic=folder/'ariali.ttf'
    if not regular.exists():
        folder=Path('/usr/share/fonts/truetype/dejavu')
        regular=folder/'DejaVuSans.ttf'; bold=folder/'DejaVuSans-Bold.ttf'; italic=folder/'DejaVuSans-Oblique.ttf'
    for name,file in [('Body',regular),('Body-Bold',bold),('Body-Italic',italic)]:
        pdfmetrics.registerFont(TTFont(name,str(file)))
    pdfmetrics.registerFontFamily('Body',normal='Body',bold='Body-Bold',italic='Body-Italic',boldItalic='Body-Bold')
    styles=getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Main',fontName='Body',fontSize=10.4,leading=15.5,spaceAfter=9,textColor=colors.HexColor('#203247')))
    styles.add(ParagraphStyle(name='Big',parent=styles['Main'],fontName='Body-Bold',fontSize=25,leading=31,spaceAfter=24))
    styles.add(ParagraphStyle(name='Section',parent=styles['Main'],fontName='Body-Bold',fontSize=17,leading=22,spaceAfter=15,spaceBefore=2,keepWithNext=True))
    styles.add(ParagraphStyle(name='Sub',parent=styles['Main'],fontName='Body-Bold',fontSize=11.5,leading=16,spaceBefore=10,spaceAfter=7,keepWithNext=True))
    styles.add(ParagraphStyle(name='Cell',parent=styles['Main'],fontSize=9,leading=12,spaceAfter=0))
    styles.add(ParagraphStyle(name='Small',parent=styles['Main'],fontSize=8.2,leading=11.5,spaceAfter=6))
    story=[]
    lines=markdown.strip().splitlines()
    i=0
    def para(text,style='Main'):
        text=html.escape(text)
        text=re.sub(r'https://[^\s<]+',lambda m:f'<link href="{m[0]}" color="#2274a5">{m[0]}</link>',text)
        return Paragraph(text,styles[style])
    while i<len(lines):
        line=lines[i].strip()
        if not line:
            i+=1; continue
        if line=='---PAGE---':
            story.append(PageBreak()); i+=1; continue
        if line.startswith('!['):
            path=re.search(r'\]\(([^)]+)\)',line)[1]
            image_path=ROOT/path
            from PIL import Image as PILImage
            with PILImage.open(image_path) as img:
                w,h=img.size
            max_w=174*mm; max_h=155*mm if 'graph.png' in path else 106*mm
            scale=min(max_w/w,max_h/h)
            story.extend([Image(str(image_path),width=w*scale,height=h*scale),Spacer(1,5*mm)])
            i+=1; continue
        if line.startswith('|'):
            rows=[]
            while i<len(lines) and lines[i].strip().startswith('|'):
                cells=[x.strip() for x in lines[i].strip().strip('|').split('|')]
                if not all(re.fullmatch('[-: ]+',x) for x in cells):
                    rows.append([para(x,'Cell') for x in cells])
                i+=1
            widths=([37*mm,20*mm,117*mm] if len(rows[0])==3 else [112*mm,62*mm])
            table=Table(rows,colWidths=widths,repeatRows=1,hAlign='LEFT')
            table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e9f0f6')),('VALIGN',(0,0),(-1,-1),'TOP'),
                ('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),
                ('LINEBELOW',(0,0),(-1,0),.7,colors.HexColor('#b8c8d8')),('LINEBELOW',(0,1),(-1,-1),.35,colors.HexColor('#e0e7ee'))]))
            story.extend([table,Spacer(1,4*mm)])
            continue
        if line.startswith('# '):
            story.append(Spacer(1,13*mm))
            story.append(para(line[2:],'Big'))
        elif line.startswith('## '):
            story.append(para(line[3:],'Section'))
        elif line.startswith('### '):
            story.append(para(line[4:],'Sub'))
        else:
            story.append(para(line,'Small' if line.startswith('https://') else 'Main'))
        i+=1
    pdf_path=OUTPUT/'pdf'/'Zettelkasten-report.pdf'
    pdf_path.parent.mkdir(exist_ok=True)
    def footer(canvas,doc):
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor('#cbd5e1'))
        canvas.line(18*mm,18*mm,192*mm,18*mm)
        canvas.setFont('Body',8)
        canvas.setFillColor(colors.HexColor('#64748b'))
        canvas.drawString(18*mm,12*mm,'Alien Invasion · Zettelkasten · Тоц Л. А. · 21.10.2026')
        canvas.drawRightString(192*mm,12*mm,str(doc.page))
        canvas.restoreState()
    doc=SimpleDocTemplate(str(pdf_path),pagesize=(210*mm,297*mm),rightMargin=18*mm,leftMargin=18*mm,topMargin=19*mm,bottomMargin=23*mm,
        title='Основы Zettelkasten: Alien Invasion',author='Тоц Леонид Александрович')
    doc.build(story,onFirstPage=footer,onLaterPages=footer)
    reader=PdfReader(pdf_path)
    if len(reader.pages)!=7:
        raise ValueError(f'Expected 7 deliberate report pages, got {len(reader.pages)}; review layout')
    for page in reader.pages:
        if not page.extract_text().strip():
            raise ValueError('Empty report page')
    return len(reader.pages)


def archive():
    archive_path=OUTPUT/'Alien-Invasion-Zettelkasten.zip'
    manifest=OUTPUT/'manifest.sha256'
    files=[p for p in ROOT.rglob('*') if p.is_file() and p not in (archive_path,manifest)
        and '__pycache__' not in p.parts and not p.name.startswith('workspace')]
    files.sort()
    manifest.write_text('\n'.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.relative_to(ROOT).as_posix() for p in files)+'\n',encoding='utf-8')
    with ZipFile(archive_path,'w',ZIP_DEFLATED) as z:
        for p in files+[manifest]:
            z.write(p,Path('Alien-Invasion-Zettelkasten')/p.relative_to(ROOT))
    with ZipFile(archive_path) as z:
        bad=z.testzip()
        if bad:
            raise ValueError('Invalid ZIP entry '+bad)
        expected={('Alien-Invasion-Zettelkasten/'+p.relative_to(ROOT).as_posix()) for p in files+[manifest]}
        if set(z.namelist())!=expected:
            raise ValueError('ZIP contents do not match deliverables')
    return archive_path


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--validate-only',action='store_true')
    args=parser.parse_args()
    notes,atomic,edges,metrics=load_and_validate()
    print(json.dumps(metrics,ensure_ascii=False,indent=2))
    if args.validate_only:
        return
    with (OUTPUT/'edges.csv').open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.writer(f); writer.writerow(['Источник','Цель','Тип источника','Тип цели'])
        writer.writerows((a,b,atomic[a]['kind'],atomic[b]['kind']) for a,b in sorted(edges))
    build_graph(atomic,edges,metrics)
    build_documents(atomic)
    text=report_text(metrics)
    (ROOT/'report.md').write_text(text,encoding='utf-8')
    pages=render_pdf(text)
    for note in notes.values():
        for path in re.findall(r'!\[[^\]]*\]\(([^)]+)\)',note['body']):
            if not (VAULT/path).is_file():
                raise ValueError(f'Missing image {path}')
    graph=json.loads((OUTPUT/'graph-data.json').read_text(encoding='utf-8'))
    if {(e['source'],e['target']) for e in graph['edges']}!=edges:
        raise ValueError('Rendered graph edge data mismatch')
    zip_path=archive()
    print(f'Built {pages}-page PDF, 7 documents, 2 graphs and verified archive: {zip_path}')


if __name__=='__main__':
    main()
