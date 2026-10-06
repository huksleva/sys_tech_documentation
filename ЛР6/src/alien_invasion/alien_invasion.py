"""Содержит запускаемый каркас игры и точки будущей реализации."""

from time import sleep

import pygame

from .alien import Alien
from .bullet import Bullet
from .button import Button
from .game_stats import GameStats
from .scoreboard import Scoreboard
from .settings import Settings
from .ship import Ship


class AlienInvasion:
    """Создаёт стартовый экран и хранит интерфейс будущей игры."""

    def __init__(self):
        """Инициализирует Pygame и безопасные пустые контейнеры."""
        pygame.init()
        self.settings = Settings()
        self.screen = pygame.display.set_mode(
            (self.settings.screen_width, self.settings.screen_height)
        )
        pygame.display.set_caption("Alien Invasion — starter")
        self.stats = GameStats(self)
        self.ship = Ship(self)
        self.bullets = pygame.sprite.Group()
        self.aliens = pygame.sprite.Group()
        self.play_button = Button(self, "Play")
        self.sb = Scoreboard(self)
        self.running = True

    def run_game(self):
        """Запускает базовый цикл до закрытия окна."""
        while self.running:
            self._check_events()
            self.ship.update()
            self._update_screen()
        pygame.quit()

    def _check_events(self):
        """Обрабатывает доступные события стартового экрана."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                self._check_play_button(event.pos)

            # TODO: добавьте обработку клавиатуры.
            # Пример нажатия:
            # if event.type == pygame.KEYDOWN and event.key == pygame.K_RIGHT:
            #     self.ship.moving_right = True
            # Пример отпускания клавиши:
            # if event.type == pygame.KEYUP and event.key == pygame.K_RIGHT:
            #     self.ship.moving_right = False

    def _check_play_button(self, mouse_pos):
        """TODO: начать новую сессию по нажатию кнопки Play."""

    def _check_keydown_events(self, event):
        """TODO: обработать нажатие клавиши."""

    def _check_keyup_events(self, event):
        """TODO: обработать отпускание клавиши."""

    def _fire_bullet(self):
        """TODO: создать снаряд с соблюдением лимита."""

    def _update_bullets(self):
        """TODO: обновить и удалить снаряды."""

    def _check_bullet_alien_collisions(self):
        """TODO: обработать столкновения и переход уровня."""

    def _update_aliens(self):
        """TODO: обновить флот пришельцев."""

    def _check_aliens_bottom(self):
        """TODO: обработать достижение нижней границы."""

    def _ship_hit(self):
        """TODO: обработать потерю корабля."""

    def _create_fleet(self):
        """TODO: создать начальный флот."""

    def _create_alien(self, alien_number, row_number):
        """TODO: создать одного пришельца по координатам сетки."""

    def _check_fleet_edges(self):
        """TODO: проверить край экрана для флота."""

    def _change_fleet_direction(self):
        """TODO: опустить флот и изменить направление."""

    def _update_screen(self):
        """Отрисовывает доступные стартовые объекты."""
        self.screen.fill(self.settings.bg_color)
        self.ship.blitme()
        if not self.stats.game_active:
            self.play_button.draw_button()
        pygame.display.flip()


def main():
    """Создаёт и запускает стартовую игру."""
    AlienInvasion().run_game()
