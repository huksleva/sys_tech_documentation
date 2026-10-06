"""Headless-настройка Pygame для acceptance-тестов."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from alien_invasion.alien_invasion import AlienInvasion


@pytest.fixture
def game():
    """Создаёт отдельный экземпляр игры."""
    instance = AlienInvasion()
    yield instance
    pygame.quit()
