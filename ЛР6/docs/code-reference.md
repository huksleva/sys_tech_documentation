# Справочник кода

## Точки входа и карта файлов

| Файл | Назначение | Документация |
|---|---|---|
| alien_invasion.py | Совместимый запуск из дерева исходников | [Launcher](api/tooling-and-tests.md) |
| src/alien_invasion/__init__.py | Экспорт AlienInvasion | [Игровой пакет](api/runtime.md) |
| src/alien_invasion/__main__.py | Запуск через python -m | [Игровой пакет](api/runtime.md) |
| src/alien_invasion/alien_invasion.py | Цикл, ввод, коллизии и переходы | [Игровой пакет](api/runtime.md) |
| src/alien_invasion/settings.py | Постоянные параметры и рост сложности | [Игровой пакет](api/runtime.md) |
| src/alien_invasion/game_stats.py | Изменяемая статистика | [Игровой пакет](api/runtime.md) |
| src/alien_invasion/ship.py, bullet.py, alien.py | Спрайты | [Игровой пакет](api/runtime.md) |
| src/alien_invasion/button.py, scoreboard.py | Кнопка Play и HUD | [Игровой пакет](api/runtime.md) |
| src/alien_invasion/assets.py, images/__init__.py | Загрузка package data | [Игровой пакет](api/runtime.md) |
| scripts/__init__.py, package_tools.py | Инструмент воспроизводимой поставки | [Инструменты](api/tooling-and-tests.md) |
| tests/__init__.py, conftest.py, test_game_rules.py | Headless-фикстура и правила | [Тесты](api/tooling-and-tests.md) |
| tests/test_documentation.py | Покрытие, ссылки, архив и конфигурация | [Тесты](api/tooling-and-tests.md) |

## Как читать API

Первая строка docstring объясняет действие. `Attributes` описывает состояние
владельца, `Args` — входные данные, `Returns` — ненулевой результат, `Raises` —
наблюдаемую ошибку. Описания написаны по-русски, названия секций оставлены
английскими для Google parser. Для фикстуры применяется `Yields`.

Внутренние методы с префиксом `_` показаны в API через `filters: []`.
Они документированы для сопровождения, но не обещают стабильного публичного API.
Инвентаризация файлов и всех именованных определений проверяется AST-тестами;
Ruff дополнительно проверяет стиль docstrings.

## Исходные ресурсы

`ship.bmp` и `alien.bmp` — BMP-изображения из выданного архива. Они входят
в wheel, sdist и ZIP. Как двоичные данные, они не требуют docstrings.
Сгенерированные `site/`, `dist/`, `.venv/`, кэши и байткод не входят в
инвентаризацию Python-исходников.
