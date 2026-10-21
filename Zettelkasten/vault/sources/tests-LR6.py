"""Acceptance-тесты ожидаемого поведения игры."""

from alien_invasion.alien import Alien
from alien_invasion.bullet import Bullet


def _start_game(game):
    """Начинает сессию кликом по центру кнопки Play.

    Args:
        game: Изолированный контроллер Pygame.
    """
    game._check_play_button(game.play_button.rect.center)


def test_game_starts_inactive_and_play_starts_a_new_session(game):
    """Проверяет неактивный старт и сброс сессии кнопкой Play.

    Args:
        game: Изолированный контроллер Pygame.
    """
    assert game.stats.game_active is False
    assert game.stats.ships_left == game.settings.ship_limit == 3
    assert game.stats.score == 0
    assert game.stats.level == 1

    _start_game(game)

    assert game.stats.game_active is True
    assert game.stats.ships_left == 3
    assert len(game.aliens) > 0


def test_ship_stays_inside_screen_bounds(game):
    """Проверяет неподвижность корабля за левой и правой границей.

    Args:
        game: Изолированный контроллер Pygame.
    """
    _start_game(game)
    ship = game.ship

    ship.rect.right = ship.screen_rect.right
    ship.x = float(ship.rect.x)
    ship.moving_right = True
    ship.update()
    assert ship.rect.right == ship.screen_rect.right

    ship.moving_right = False
    ship.rect.left = 0
    ship.x = float(ship.rect.x)
    ship.moving_left = True
    ship.update()
    assert ship.rect.left == 0


def test_no_more_than_three_bullets_can_exist(game):
    """Проверяет лимит трёх пуль при четвёртой попытке выстрела.

    Args:
        game: Изолированный контроллер Pygame.
    """
    _start_game(game)

    for _ in range(game.settings.bullets_allowed + 1):
        game._fire_bullet()

    assert len(game.bullets) == game.settings.bullets_allowed == 3


def test_fleet_is_built_and_changes_direction_at_screen_edge(game):
    """Проверяет создание флота, его опускание и разворот у края.

    Args:
        game: Изолированный контроллер Pygame.
    """
    _start_game(game)
    assert len(game.aliens) > 1

    edge_alien = next(iter(game.aliens))
    old_y = edge_alien.rect.y
    edge_alien.rect.right = game.screen.get_rect().right
    game.settings.fleet_direction = 1

    game._check_fleet_edges()

    assert edge_alien.rect.y == old_y + game.settings.fleet_drop_speed
    assert game.settings.fleet_direction == -1


def test_destroying_last_alien_adds_score_level_and_high_score(game):
    """Проверяет очки, рекорд и сложность после последней цели.

    Args:
        game: Изолированный контроллер Pygame.
    """
    _start_game(game)
    game.aliens.empty()
    game.bullets.empty()

    alien = Alien(game)
    bullet = Bullet(game)
    bullet.rect.center = alien.rect.center
    game.aliens.add(alien)
    game.bullets.add(bullet)

    game._check_bullet_alien_collisions()

    assert game.stats.score == 50
    assert game.stats.high_score == 50
    assert game.stats.level == 2
    assert game.settings.alien_points == 75
    assert len(game.aliens) > 0


def test_losing_final_ship_ends_game(monkeypatch, game):
    """Проверяет активную игру при нуле замен и завершение следующим попаданием.

    Args:
        monkeypatch: Фикстура подмены блокирующей паузы.
        game: Изолированный контроллер Pygame.
    """
    _start_game(game)
    monkeypatch.setattr("alien_invasion.alien_invasion.sleep", lambda _: None)
    game.stats.ships_left = 1

    game._ship_hit()
    assert game.stats.ships_left == 0
    assert game.stats.game_active is True

    game._ship_hit()
    assert game.stats.game_active is False


def test_fractional_speed_cannot_push_ship_outside_screen(game):
    """Проверяет ограничение координат при шаге, превышающем остаток до края.

    Args:
        game: Изолированный контроллер Pygame.
    """
    _start_game(game)
    ship = game.ship
    game.settings.ship_speed = 10.5
    ship.rect.right = ship.screen_rect.right - 1
    ship.x = float(ship.rect.x)
    ship.moving_right = True
    ship.update()
    assert ship.rect.right == ship.screen_rect.right
    ship.moving_right = False
    ship.moving_left = True
    ship.x = 0.5
    ship.update()
    assert ship.rect.left == 0
    assert ship.x == 0.0


def test_inactive_input_cannot_move_or_fire(game):
    """Проверяет игнорирование стрелок и Space вне активной сессии.

    Args:
        game: Изолированный контроллер Pygame.
    """
    import pygame

    for key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_SPACE):
        game._check_keydown_events(pygame.event.Event(pygame.KEYDOWN, key=key))
    game._fire_bullet()
    assert not game.ship.moving_left
    assert not game.ship.moving_right
    assert not game.bullets


def test_keyboard_events_set_and_clear_movement(game):
    """Проверяет маршрутизацию нажатия, отпускания и Space из очереди событий.

    Args:
        game: Изолированный контроллер Pygame.
    """
    import pygame

    _start_game(game)
    pygame.event.clear()
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RIGHT))
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE))
    game._check_events()
    assert game.ship.moving_right
    assert len(game.bullets) == 1
    pygame.event.post(pygame.event.Event(pygame.KEYUP, key=pygame.K_RIGHT))
    game._check_events()
    assert not game.ship.moving_right


def test_expired_bullet_frees_a_firing_slot(game):
    """Проверяет движение вверх, удаление вышедшей пули и новый выстрел.

    Args:
        game: Изолированный контроллер Pygame.
    """
    _start_game(game)
    for _ in range(3):
        game._fire_bullet()
    expired = next(iter(game.bullets))
    old_y = expired.y
    expired.update()
    assert expired.y < old_y
    expired.y = -expired.rect.height
    expired.rect.y = int(expired.y)
    game._update_bullets()
    assert expired not in game.bullets
    assert len(game.bullets) == 2
    game._fire_bullet()
    assert len(game.bullets) == 3


def test_one_bullet_scores_every_overlapping_target(game):
    """Проверяет начисление за две цели одной пули и удаление обеих сторон.

    Args:
        game: Изолированный контроллер Pygame.
    """
    _start_game(game)
    game.aliens.empty()
    targets = [Alien(game), Alien(game)]
    bullet = Bullet(game)
    bullet.rect.center = targets[0].rect.center
    game.aliens.add(*targets)
    game.bullets.add(bullet)
    game._check_bullet_alien_collisions()
    assert game.stats.score == game.stats.high_score == 100
    assert all(target not in game.aliens for target in targets)
    assert bullet not in game.bullets
    assert game.stats.level == 2


def test_restart_resets_session_but_preserves_high_score(game):
    """Проверяет полный сброс повторного запуска при сохранении рекорда.

    Args:
        game: Изолированный контроллер Pygame.
    """
    _start_game(game)
    game.stats.score = 500
    game.sb.check_high_score()
    game.stats.level = 4
    game.stats.ships_left = 0
    game.settings.increase_speed()
    game.settings.fleet_direction = -1
    game.ship.moving_left = True
    game._fire_bullet()
    game.stats.game_active = False
    _start_game(game)
    assert game.stats.high_score == 500
    assert (game.stats.score, game.stats.level, game.stats.ships_left) == (0, 1, 3)
    assert game.settings.alien_points == 50
    assert game.settings.ship_speed == 1.5
    assert game.settings.fleet_direction == 1
    assert not game.bullets
    assert not game.ship.moving_left
    assert game.ship.rect.midbottom == game.screen.get_rect().midbottom
    assert len(game.sb.ships) == 3


def test_play_does_not_reset_an_active_session(game):
    """Проверяет отсутствие сброса при клике вне кнопки или активной игре.

    Args:
        game: Изолированный контроллер Pygame.
    """
    game._check_play_button((0, 0))
    assert not game.stats.game_active
    _start_game(game)
    game.stats.score = 150
    _start_game(game)
    assert game.stats.score == 150


def test_bottom_and_ship_collision_cost_one_replacement(monkeypatch, game):
    """Проверяет потерю одного запаса при одновременном низе и коллизии.

    Args:
        monkeypatch: Фикстура подмены блокирующей паузы.
        game: Изолированный контроллер Pygame.
    """
    _start_game(game)
    monkeypatch.setattr("alien_invasion.alien_invasion.sleep", lambda _: None)
    game.aliens.empty()
    alien = Alien(game)
    alien.rect.center = game.ship.rect.center
    alien.x = float(alien.rect.x)
    game.aliens.add(alien)
    game._update_aliens()
    assert game.stats.ships_left == 2
    assert game.stats.game_active


def test_bottom_alone_costs_one_replacement(monkeypatch, game):
    """Проверяет потерю запаса при нижней границе без столкновения с кораблём.

    Args:
        monkeypatch: Фикстура подмены блокирующей паузы.
        game: Изолированный контроллер Pygame.
    """
    _start_game(game)
    monkeypatch.setattr("alien_invasion.alien_invasion.sleep", lambda _: None)
    game.aliens.empty()
    alien = Alien(game)
    alien.rect.left = 60
    alien.rect.bottom = game.screen.get_rect().bottom
    game.aliens.add(alien)
    game._check_aliens_bottom()
    assert game.stats.ships_left == 2


def test_game_over_does_not_consume_more_replacements(monkeypatch, game):
    """Проверяет отсутствие повторных изменений статистики после Game Over.

    Args:
        monkeypatch: Фикстура подмены блокирующей паузы.
        game: Изолированный контроллер Pygame.
    """
    _start_game(game)
    monkeypatch.setattr("alien_invasion.alien_invasion.sleep", lambda _: None)
    game.stats.ships_left = 0
    game._ship_hit()
    game._ship_hit()
    assert not game.stats.game_active
    assert game.stats.ships_left == 0


def test_quit_event_ends_loop_and_releases_pygame(game):
    """Проверяет безопасное завершение цикла по системному событию QUIT.

    Args:
        game: Изолированный контроллер Pygame.
    """
    import pygame

    pygame.event.clear()
    pygame.event.post(pygame.event.Event(pygame.QUIT))
    game.run_game()
    assert not game.running
    assert not pygame.get_init()


def test_q_key_ends_loop_and_releases_pygame(game):
    """Проверяет завершение через Q даже на стартовом экране.

    Args:
        game: Изолированный контроллер Pygame.
    """
    import pygame

    pygame.event.clear()
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_q))
    game.run_game()
    assert not game.running
    assert not pygame.get_init()


def test_packaged_images_load_from_another_directory(monkeypatch, tmp_path):
    """Проверяет независимость package data от текущего рабочего каталога.

    Args:
        monkeypatch: Фикстура временной смены текущего каталога.
        tmp_path: Изолированный пустой каталог.
    """
    from alien_invasion.assets import load_image

    monkeypatch.chdir(tmp_path)
    assert load_image("ship.bmp").get_width() > 0
    assert load_image("alien.bmp").get_height() > 0


def test_missing_image_has_a_file_not_found_contract():
    """Проверяет FileNotFoundError для отсутствующего BMP-ресурса."""
    import pytest

    from alien_invasion.assets import load_image

    with pytest.raises(FileNotFoundError, match="absent.bmp"):
        load_image("absent.bmp")
