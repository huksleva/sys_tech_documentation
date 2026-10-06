# Тестирование и поставка

## Проверка качества

```bash
poetry run poe format
poetry run poe check
poetry run poe docs-site
poetry run poe archive
poetry run poe build
```

| Задача | Проверка | Меняет исходники |
|---|---|---|
| format | Ruff Formatter | Да, Python-файлы |
| format-check | ruff format --check | Нет |
| docs-check | Ruff: ошибки, импорты, Google-style docstrings | Нет |
| compile | compileall для launcher, scripts, src и tests | Нет; создаёт байткод |
| test | pytest в режиме SDL dummy | Нет |
| docs-site | MkDocs --strict --clean | Пересоздаёт site/ |
| archive | Белый список, стабильные метаданные ZIP | Создаёт ZIP в dist/ |
| build | format → check → docs-site → archive → poetry build | Да, форматирование и артефакты |

Исходные шесть acceptance-тестов сохранены; добавлены проверки ввода,
повторного запуска, дробных границ движения, освобождения пуль, многократных
коллизий, достижения низа, загрузки ресурсов и завершения цикла.
`tests/conftest.py` задаёт `SDL_VIDEODRIVER=dummy` и `SDL_AUDIODRIVER=dummy`.
Это позволяет проверять правила без настоящего окна и аудиоустройства.

Метапроверки рекурсивно обходят Markdown, проверяют относительные ссылки,
существование страниц API, совпадение матрицы с Python-файлами, docstrings у
модулей/классов/функций, навигацию MkDocs и включение всех модулей в API.
Проверки архиватора сравнивают два архива побайтно и ищут запрещённые файлы.
Строгая сборка сайта отдельно проверяет разрешение директив mkdocstrings.

## Состав поставки

`scripts/package_tools.py` разрешает только корневые `.gitignore`, `README.md`,
`alien_invasion.py`, `mkdocs.yml`, `poetry.lock`, `poetry.toml`, `pyproject.toml`
и деревья `docs`, `scripts`, `site`, `src`, `tests`. Внутри деревьев исключаются
кэши, окружения, байткод и символьные ссылки. `dist` не включается в себя.

ZIP называется `dist/alien-invasion-0.1.0-source.zip`. Файлы сортируются,
временные отметки закреплены на 1 января 1980 г., права нормализованы.
При одинаковых исходных байтах в одном окружении архивы идентичны.
Полный `build` предварительно пересобирает сайт; timestamp sitemap может
меняться между сборками сайта, поэтому сравнение ZIP относится к одному снимку.

`poetry build` создаёт wheel с игровым пакетом и BMP и sdist с исходниками,
тестами, документацией и сайтом. Документация и сайт не входят в wheel.

## Самостоятельная проверка распакованного ZIP

```bash
poetry install --with docs
poetry run poe check
poetry run poe docs-site
poetry run poe archive
python -m http.server --directory site 8000
```

Для просмотра готового сайта достаточно Python HTTP-сервера: генератор
документации не нужен. Сайт с directory URLs следует открывать по HTTP.
Результаты выполненной проверки записаны в корневом README проекта.
