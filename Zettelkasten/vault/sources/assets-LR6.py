"""Загружает BMP из package data без зависимости от текущего каталога."""

from importlib.resources import as_file, files

import pygame


def load_image(name: str) -> pygame.Surface:
    """Загружает изображение из ресурсов пакета ``alien_invasion.images``.

    Args:
        name: Имя BMP внутри подпакета ресурсов.

    Returns:
        Поверхность Pygame с загруженным изображением.

    Raises:
        FileNotFoundError: Если именованный ресурс отсутствует в пакете.
        pygame.error: Если существующий файл не распознаётся как изображение.
    """
    resource = files("alien_invasion.images").joinpath(name)
    if not resource.is_file():
        raise FileNotFoundError(f"Ресурс изображения не найден: {name}")
    with as_file(resource) as path:
        return pygame.image.load(str(path))
