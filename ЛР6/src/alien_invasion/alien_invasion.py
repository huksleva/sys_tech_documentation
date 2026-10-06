"""Координирует ввод, игровой кадр, столкновения и переходы сессии."""

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
    """Управляет учебной игрой и жизненным циклом её объектов.

    Attributes:
        settings: Владелец правил и динамической сложности.
        screen: Поверхность окна Pygame.
        stats: Статистика сессии и рекорд процесса.
        ship: Текущий корабль игрока.
        bullets: Группа не более трёх активных снарядов.
        aliens: Группа целей текущего флота.
        play_button: Кнопка старта и повторного запуска.
        sb: HUD, отображающий статистику.
        running: Продолжает ли работать приложение независимо от сессии.
        clock: Ограничитель частоты кадров.
    """

    def __init__(self):
        """Инициализирует Pygame, неактивную сессию, HUD и стартовый флот."""
        pygame.init()
        self.settings = Settings()
        self.screen = pygame.display.set_mode(
            (self.settings.screen_width, self.settings.screen_height)
        )
        pygame.display.set_caption("Alien Invasion")
        self.stats = GameStats(self)
        self.ship = Ship(self)
        self.bullets = pygame.sprite.Group()
        self.aliens = pygame.sprite.Group()
        self.play_button = Button(self, "Play")
        self.sb = Scoreboard(self)
        self.running = True
        self.clock = pygame.time.Clock()
        self._create_fleet()
        pygame.mouse.set_visible(True)

    def run_game(self):
        """Выполняет кадры до выхода и освобождает Pygame даже при исключении.

        Кадр: ввод, корабль, пули и коллизии, флот, отрисовка, ограничение FPS.
        Механика обновляется только при активной сессии.
        """
        try:
            while self.running:
                self._check_events()
                if not self.running:
                    break
                if self.stats.game_active:
                    self.ship.update()
                    self._update_bullets()
                    self._update_aliens()
                self._update_screen()
                self.clock.tick(self.settings.fps)
        finally:
            pygame.quit()

    def _check_events(self):
        """Обрабатывает очередь выхода, мыши и клавиатуры.

        Только левая кнопка мыши запускает Play. После запроса выхода
        оставшиеся события очереди не запускают новую сессию.
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self._check_play_button(event.pos)
            elif event.type == pygame.KEYDOWN:
                self._check_keydown_events(event)
            elif event.type == pygame.KEYUP:
                self._check_keyup_events(event)
            if not self.running:
                break

    def _check_play_button(self, mouse_pos):
        """Начинает сессию только по клику внутри Play при неактивной игре.

        Сбрасывает статистику, сложности, пули и флот, центрирует корабль,
        обновляет HUD и скрывает курсор. Рекорд текущего процесса сохраняется.

        Args:
            mouse_pos: Пара координат клика в пикселях экрана.
        """
        if not self.play_button.rect.collidepoint(mouse_pos) or self.stats.game_active:
            return
        self.settings.initialize_dynamic_settings()
        self.stats.reset_stats()
        self.stats.game_active = True
        self.bullets.empty()
        self.aliens.empty()
        self._create_fleet()
        self.ship.center_ship()
        self.sb.prep_score()
        self.sb.prep_high_score()
        self.sb.prep_level()
        self.sb.prep_ships()
        pygame.mouse.set_visible(False)

    def _check_keydown_events(self, event):
        """Включает движение, стреляет в активной игре или завершает по Q.

        Args:
            event: Событие KEYDOWN Pygame с атрибутом key.
        """
        if event.key == pygame.K_q:
            self.running = False
        elif self.stats.game_active:
            if event.key == pygame.K_RIGHT:
                self.ship.moving_right = True
            elif event.key == pygame.K_LEFT:
                self.ship.moving_left = True
            elif event.key == pygame.K_SPACE:
                self._fire_bullet()

    def _check_keyup_events(self, event):
        """Снимает соответствующий флаг движения при отпускании стрелки.

        Args:
            event: Событие KEYUP Pygame с атрибутом key.
        """
        if event.key == pygame.K_RIGHT:
            self.ship.moving_right = False
        elif event.key == pygame.K_LEFT:
            self.ship.moving_left = False

    def _fire_bullet(self):
        """Добавляет пулю в активной игре, если лимит ещё не исчерпан.

        Лимит проверяется до создания спрайта; после удаления вылетевшей
        или попавшей пули место освобождается.
        """
        if self.stats.game_active and len(self.bullets) < self.settings.bullets_allowed:
            self.bullets.add(Bullet(self))

    def _update_bullets(self):
        """Двигает пули, удаляет вышедшие целиком вверх и проверяет попадания."""
        self.bullets.update()
        for bullet in self.bullets.copy():
            if bullet.rect.bottom <= 0:
                self.bullets.remove(bullet)
        self._check_bullet_alien_collisions()

    def _check_bullet_alien_collisions(self):
        """Удаляет пересекающиеся пули и цели, начисляет очки и меняет уровень.

        Каждая удалённая цель приносит текущую цену, включая несколько целей
        одной пули. После обновления счёта и рекорда пустой флот вызывает
        очистку пуль, рост сложности и уровня, подготовку HUD и новый флот.
        """
        collisions = pygame.sprite.groupcollide(self.bullets, self.aliens, True, True)
        if collisions:
            destroyed = sum(len(aliens) for aliens in collisions.values())
            self.stats.score += self.settings.alien_points * destroyed
            self.sb.prep_score()
            self.sb.check_high_score()
        if not self.aliens and self.stats.game_active:
            self.bullets.empty()
            self.settings.increase_speed()
            self.stats.level += 1
            self.sb.prep_level()
            self._create_fleet()

    def _update_aliens(self):
        """Разворачивает и двигает флот, затем проверяет корабль и низ экрана.

        После столкновения с кораблём проверка нижней границы пропускается,
        чтобы одно обновление не вызвало две потери запаса.
        """
        if not self.stats.game_active:
            return
        self._check_fleet_edges()
        self.aliens.update()
        if pygame.sprite.spritecollideany(self.ship, self.aliens):
            self._ship_hit()
            return
        self._check_aliens_bottom()

    def _check_aliens_bottom(self):
        """Вызывает одну потерю корабля при достижении любой целью низа экрана."""
        for alien in self.aliens:
            if alien.rect.bottom >= self.screen.get_rect().bottom:
                self._ship_hit()
                break

    def _ship_hit(self):
        """Расходует замену либо завершает сессию, если запас уже был нулевым.

        При положительном запасе уменьшает его, очищает группы, создаёт флот,
        центрирует корабль, обновляет значки HUD и ждёт 0,5 секунды. Значение 0
        после уменьшения оставляет сессию активной: Game Over наступает при
        следующем попадании. Неактивная сессия не меняется повторным вызовом.
        """
        if not self.stats.game_active:
            return
        if self.stats.ships_left > 0:
            self.stats.ships_left -= 1
            self.sb.prep_ships()
            self.bullets.empty()
            self.aliens.empty()
            self._create_fleet()
            self.ship.center_ship()
            sleep(0.5)
        else:
            self.stats.game_active = False
            self.ship.moving_left = False
            self.ship.moving_right = False
            pygame.mouse.set_visible(True)

    def _create_fleet(self):
        """Заполняет группу сеткой целей с интервалом в одну ширину и высоту.

        Слева/справа оставляет по ширине цели, сверху одну высоту, снизу
        резервирует высоту корабля и три высоты цели. Вызывается после
        очистки группы; при слишком маленьком экране сетка остаётся пустой.
        """
        alien = Alien(self)
        alien_width, alien_height = alien.rect.size
        available_width = self.settings.screen_width - 2 * alien_width
        available_height = (
            self.settings.screen_height - 3 * alien_height - self.ship.rect.height
        )
        columns = max(0, available_width // (2 * alien_width))
        rows = max(0, available_height // (2 * alien_height))
        for row_number in range(rows):
            for alien_number in range(columns):
                self._create_alien(alien_number, row_number)

    def _create_alien(self, alien_number, row_number):
        """Добавляет цель в заданную ячейку сетки флота.

        Args:
            alien_number: Индекс столбца, начиная с 0.
            row_number: Индекс строки, начиная с 0.
        """
        alien = Alien(self)
        alien.x = float(alien.rect.width * (1 + 2 * alien_number))
        alien.rect.x = int(alien.x)
        alien.rect.y = alien.rect.height * (1 + 2 * row_number)
        self.aliens.add(alien)

    def _check_fleet_edges(self):
        """Разворачивает весь флот один раз, если хотя бы одна цель у края."""
        for alien in self.aliens:
            if alien.check_edges():
                self._change_fleet_direction()
                break

    def _change_fleet_direction(self):
        """Опускает все цели на общий шаг и меняет знак направления флота."""
        for alien in self.aliens:
            alien.rect.y += self.settings.fleet_drop_speed
        self.settings.fleet_direction *= -1

    def _update_screen(self):
        """Рисует фон, спрайты, HUD и Play при неактивной сессии, затем кадр."""
        self.screen.fill(self.settings.bg_color)
        self.ship.blitme()
        for bullet in self.bullets:
            bullet.draw_bullet()
        self.aliens.draw(self.screen)
        self.sb.show_score()
        if not self.stats.game_active:
            self.play_button.draw_button()
        pygame.display.flip()


def main():
    """Создаёт контроллер и запускает цикл до Q либо закрытия окна."""
    AlienInvasion().run_game()
