"""Настраивает SDL dummy до импорта Pygame и изолирует игровые экземпляры."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from alien_invasion.alien_invasion import AlienInvasion


@pytest.fixture
def game():
    """Создаёт новый контроллер и освобождает Pygame после сценария.

    Yields:
        Контроллер в неактивном состоянии с изолированной статистикой.
    """
    instance = AlienInvasion()
    try:
        yield instance
    finally:
        pygame.quit()
