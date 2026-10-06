# Руководство студента

## Установка и команды

1. Установите Python 3.11+ и Poetry по официальным инструкциям.
2. Перейдите в каталог проекта, содержащий `pyproject.toml`.
3. Выполните `poetry install --with docs`.
4. Запустите `poetry run poe run` и начните игру кнопкой Play.
5. Проверьте изменения через `poetry run poe check` и `poetry run poe docs-site`.

Для пользователя игры достаточно `poetry install --only main`; optional-группа
`docs` требуется для сайта, а группа `dev` — для Ruff, pytest и Poe.
После установки только main запускайте `poetry run alien-invasion`.

## Обновление документации

Сначала измените поведение и его docstring у владельца правила, затем тест
инварианта, Markdown и строку [матрицы покрытия](api/codebase-coverage.md).
API-сайт получает описание непосредственно из Python-кода.

```bash
poetry run poe docs-serve
```

Откройте `http://127.0.0.1:8000`. MkDocs автоматически пересоберёт страницы
после сохранения. Перед поставкой выполните `poetry run poe build`.

## Разбор ошибок

| Симптом | Действие |
|---|---|
| mkdocs или poe не найдены | Повторить poetry install --with docs |
| Ruff требует форматирование | Выполнить poe format и повторить poe check |
| MkDocs сообщает WARNING | Исправить nav, ссылку или имя в ::: и пересобрать |
| Изображение не найдено | Проверить BMP в src/alien_invasion/images и установленном wheel |
| ZIP требует site/index.html | Сначала выполнить poe docs-site |
| Окно не открывается при ручном запуске | Убрать SDL_VIDEODRIVER=dummy из пользовательской среды |

Не редактируйте `poetry.lock` вручную: после изменения диапазонов зависимостей
выполните `poetry lock`, затем `poetry install --with docs`.

## Первоисточники

- [Google Python Style Guide: docstrings](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings).
- [PEP 257](https://peps.python.org/pep-0257/).
- [Ruff Formatter](https://docs.astral.sh/ruff/formatter/) и [настройки Ruff](https://docs.astral.sh/ruff/settings/).
- [Poetry: группы зависимостей](https://python-poetry.org/docs/managing-dependencies/) и [include/exclude](https://python-poetry.org/docs/pyproject/#include-and-exclude).
- [Poe: последовательности задач](https://poethepoet.natn.io/tasks/task_types/sequence.html).
- [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/getting-started/).
- [mkdocstrings-python](https://mkdocstrings.github.io/python/usage/).
- [Pygame: Sprite и Group](https://www.pygame.org/docs/ref/sprite.html).
