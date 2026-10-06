"""Acceptance-тесты ожидаемого поведения игры."""

from alien_invasion.alien import Alien
from alien_invasion.bullet import Bullet


def _start_game(game):
    game._check_play_button(game.play_button.rect.center)


def test_game_starts_inactive_and_play_starts_a_new_session(game):
    assert game.stats.game_active is False
    assert game.stats.ships_left == game.settings.ship_limit == 3
    assert game.stats.score == 0
    assert game.stats.level == 1

    _start_game(game)

    assert game.stats.game_active is True
    assert game.stats.ships_left == 3
    assert len(game.aliens) > 0


def test_ship_stays_inside_screen_bounds(game):
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
    _start_game(game)

    for _ in range(game.settings.bullets_allowed + 1):
        game._fire_bullet()

    assert len(game.bullets) == game.settings.bullets_allowed == 3


def test_fleet_is_built_and_changes_direction_at_screen_edge(game):
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
    _start_game(game)
    monkeypatch.setattr("alien_invasion.alien_invasion.sleep", lambda _: None)
    game.stats.ships_left = 1

    game._ship_hit()
    assert game.stats.ships_left == 0
    assert game.stats.game_active is True

    game._ship_hit()
    assert game.stats.game_active is False
