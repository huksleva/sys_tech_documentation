"""Определяет снаряд с дробным вертикальным перемещением вверх."""

import pygame
from pygame.sprite import Sprite


class Bullet(Sprite):
    """Представляет один прямоугольный снаряд.

    Attributes:
        screen: Поверхность окна для отрисовки.
        settings: Настройки размера и скорости пули.
        color: Цвет прямоугольника RGB.
        rect: Прямоугольник отрисовки и коллизий.
        y: Вещественная вертикальная координата верхнего края.
    """

    def __init__(self, ai_game):
        """Создаёт снаряд у верхнего центра корабля.

        Args:
            ai_game: Контроллер, предоставляющий экран, настройки и корабль.
        """
        super().__init__()
        self.screen = ai_game.screen
        self.settings = ai_game.settings
        self.color = self.settings.bullet_color
        self.rect = pygame.Rect(
            0, 0, self.settings.bullet_width, self.settings.bullet_height
        )
        self.rect.midtop = ai_game.ship.rect.midtop
        self.y = float(self.rect.y)

    def update(self):
        """Сдвигает снаряд вверх и синхронизирует ``rect.y`` с float-координатой."""
        self.y -= self.settings.bullet_speed
        self.rect.y = int(self.y)

    def draw_bullet(self):
        """Рисует прямоугольник пули на экране без изменения её состояния."""
        pygame.draw.rect(self.screen, self.color, self.rect)
