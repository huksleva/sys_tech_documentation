# Матрица покрытия кодовой базы

Матрица охватывает launcher, src, scripts и tests. Проверка AST требует docstring
у каждого модуля, класса и именованной функции, включая внутренние методы.
BMP, окружения, кэши, site и dist не являются Python-исходниками.

| Файл | Документированные единицы | Страница сайта | Проверки | Статус |
|---|---|---|---|---|
| `alien_invasion.py` | Модуль, 0 классов, 1 функций/методов | [API](tooling-and-tests.md) | format-check, docs-check, test, docs-site | Готово |
| `scripts/__init__.py` | Модуль, 0 классов, 0 функций/методов | [API](tooling-and-tests.md) | format-check, docs-check, test, docs-site | Готово |
| `scripts/package_tools.py` | Модуль, 0 классов, 3 функций/методов | [API](tooling-and-tests.md) | format-check, docs-check, test, docs-site | Готово |
| `src/alien_invasion/__init__.py` | Модуль, 0 классов, 0 функций/методов | [API](runtime.md) | format-check, docs-check, test, docs-site | Готово |
| `src/alien_invasion/__main__.py` | Модуль, 0 классов, 1 функций/методов | [API](runtime.md) | format-check, docs-check, test, docs-site | Готово |
| `src/alien_invasion/alien.py` | Модуль, 1 классов, 3 функций/методов | [API](runtime.md) | format-check, docs-check, test, docs-site | Готово |
| `src/alien_invasion/alien_invasion.py` | Модуль, 1 классов, 18 функций/методов | [API](runtime.md) | format-check, docs-check, test, docs-site | Готово |
| `src/alien_invasion/assets.py` | Модуль, 0 классов, 1 функций/методов | [API](runtime.md) | format-check, docs-check, test, docs-site | Готово |
| `src/alien_invasion/bullet.py` | Модуль, 1 классов, 3 функций/методов | [API](runtime.md) | format-check, docs-check, test, docs-site | Готово |
| `src/alien_invasion/button.py` | Модуль, 1 классов, 3 функций/методов | [API](runtime.md) | format-check, docs-check, test, docs-site | Готово |
| `src/alien_invasion/game_stats.py` | Модуль, 1 классов, 2 функций/методов | [API](runtime.md) | format-check, docs-check, test, docs-site | Готово |
| `src/alien_invasion/images/__init__.py` | Модуль, 0 классов, 0 функций/методов | [API](runtime.md) | format-check, docs-check, test, docs-site | Готово |
| `src/alien_invasion/scoreboard.py` | Модуль, 1 классов, 7 функций/методов | [API](runtime.md) | format-check, docs-check, test, docs-site | Готово |
| `src/alien_invasion/settings.py` | Модуль, 1 классов, 3 функций/методов | [API](runtime.md) | format-check, docs-check, test, docs-site | Готово |
| `src/alien_invasion/ship.py` | Модуль, 1 классов, 4 функций/методов | [API](runtime.md) | format-check, docs-check, test, docs-site | Готово |
| `tests/__init__.py` | Модуль, 0 классов, 0 функций/методов | [API](tooling-and-tests.md) | format-check, docs-check, test, docs-site | Готово |
| `tests/conftest.py` | Модуль, 0 классов, 1 функций/методов | [API](tooling-and-tests.md) | format-check, docs-check, test, docs-site | Готово |
| `tests/test_documentation.py` | Модуль, 0 классов, 11 функций/методов | [API](tooling-and-tests.md) | format-check, docs-check, test, docs-site | Готово |
| `tests/test_game_rules.py` | Модуль, 0 классов, 21 функций/методов | [API](tooling-and-tests.md) | format-check, docs-check, test, docs-site | Готово |
