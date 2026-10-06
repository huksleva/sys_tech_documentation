"""Подготавливает и рисует HUD из статистики текущей сессии."""

import pygame
from pygame.sprite import Group

from .ship import Ship


class Scoreboard:
    """Отображает счёт, рекорд, уровень и запас замен корабля.

    Attributes:
        ai_game: Контроллер для создания значков кораблей.
        screen: Поверхность окна.
        screen_rect: Границы размещения HUD.
        settings: Настройки фонового цвета.
        stats: Статистика, из которой подготавливается HUD.
        text_color: Тёмно-серый цвет текста RGB.
        font: Системный шрифт размером 32.
        score_image: Подготовленная поверхность текущего счёта.
        score_rect: Положение счёта справа вверху.
        high_score_image: Подготовленная поверхность рекорда.
        high_score_rect: Положение рекорда по центру вверху.
        level_image: Подготовленная поверхность номера уровня.
        level_rect: Положение уровня под текущим счётом.
        ships: Группа значков запаса замен слева вверху.
    """

    def __init__(self, ai_game):
        """Подготавливает все элементы HUD из исходной статистики.

        Args:
            ai_game: Контроллер с экраном, настройками и статистикой.
        """
        self.ai_game = ai_game
        self.screen = ai_game.screen
        self.screen_rect = self.screen.get_rect()
        self.settings = ai_game.settings
        self.stats = ai_game.stats
        self.text_color = (30, 30, 30)
        self.font = pygame.font.SysFont(None, 32)
        self.prep_score()
        self.prep_high_score()
        self.prep_level()
        self.prep_ships()

    def prep_score(self):
        """Форматирует точный целый счёт с разделителями тысяч справа вверху."""
        self.score_image = self.font.render(
            f"{self.stats.score:,}", True, self.text_color, self.settings.bg_color
        )
        self.score_rect = self.score_image.get_rect()
        self.score_rect.right = self.screen_rect.right - 20
        self.score_rect.top = 20

    def prep_high_score(self):
        """Подготавливает изображение рекорда по центру верхней границы."""
        self.high_score_image = self.font.render(
            f"{self.stats.high_score:,}", True, self.text_color, self.settings.bg_color
        )
        self.high_score_rect = self.high_score_image.get_rect()
        self.high_score_rect.centerx = self.screen_rect.centerx
        self.high_score_rect.top = self.score_rect.top

    def prep_level(self):
        """Подготавливает номер уровня под изображением текущего счёта."""
        self.level_image = self.font.render(
            str(self.stats.level), True, self.text_color, self.settings.bg_color
        )
        self.level_rect = self.level_image.get_rect()
        self.level_rect.right = self.score_rect.right
        self.level_rect.top = self.score_rect.bottom + 10

    def prep_ships(self):
        """Создаёт по значку на каждую доступную замену корабля.

        При нулевом запасе группа пуста, хотя текущий корабль ещё может играть.
        """
        self.ships = Group()
        for ship_number in range(self.stats.ships_left):
            ship = Ship(self.ai_game)
            ship.rect.x = 10 + ship_number * ship.rect.width
            ship.rect.y = 10
            self.ships.add(ship)

    def check_high_score(self):
        """Повышает рекорд и обновляет его изображение, если счёт больше."""
        if self.stats.score > self.stats.high_score:
            self.stats.high_score = self.stats.score
            self.prep_high_score()

    def show_score(self):
        """Рисует ранее подготовленные поверхности и значки без изменения счёта."""
        self.screen.blit(self.score_image, self.score_rect)
        self.screen.blit(self.high_score_image, self.high_score_rect)
        self.screen.blit(self.level_image, self.level_rect)
        self.ships.draw(self.screen)
