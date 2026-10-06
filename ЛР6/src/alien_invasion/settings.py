"""Определяет постоянные правила и динамическую сложность игры."""


class Settings:
    """Хранит правила экрана, спрайтов и роста сложности.

    Attributes:
        screen_width: Ширина окна, 640 пикселей.
        screen_height: Высота окна, 480 пикселей.
        bg_color: Цвет фона RGB.
        ship_limit: Начальный запас замен корабля, 3; текущий корабль отдельно.
        bullets_allowed: Максимум одновременно активных пуль, 3.
        bullet_width: Ширина прямоугольной пули в пикселях.
        bullet_height: Высота прямоугольной пули в пикселях.
        bullet_color: Цвет пули RGB.
        fleet_drop_speed: Вертикальный шаг флота при развороте, 10 пикселей.
        speedup_scale: Множитель скоростей после уровня, 1,1.
        score_scale: Множитель стоимости пришельца после уровня, 1,5.
        fps: Верхний предел частоты кадров, 60.
        ship_speed: Скорость корабля в пикселях за кадр; стартовое значение 1,5.
        bullet_speed: Скорость пули вверх; стартовое значение 1,0.
        alien_speed: Горизонтальная скорость пришельца; стартовое значение 1,0.
        fleet_direction: 1 для движения вправо, -1 для движения влево.
        alien_points: Очки за цель; стартовое значение 50.
    """

    def __init__(self):
        """Создаёт постоянные параметры и начальную динамическую сложность."""
        self.screen_width = 640
        self.screen_height = 480
        self.bg_color = (230, 230, 230)
        self.ship_limit = 3
        self.bullets_allowed = 3
        self.bullet_width = 3
        self.bullet_height = 15
        self.bullet_color = (60, 60, 60)
        self.fleet_drop_speed = 10
        self.speedup_scale = 1.1
        self.score_scale = 1.5
        self.fps = 60
        self.initialize_dynamic_settings()

    def initialize_dynamic_settings(self):
        """Сбрасывает скорости, направление и цену цели при начале сессии."""
        self.ship_speed = 1.5
        self.bullet_speed = 1.0
        self.alien_speed = 1.0
        self.fleet_direction = 1
        self.alien_points = 50

    def increase_speed(self):
        """Умножает скорости на 1,1, а цену цели на 1,5 с округлением вниз."""
        self.ship_speed *= self.speedup_scale
        self.bullet_speed *= self.speedup_scale
        self.alien_speed *= self.speedup_scale
        self.alien_points = int(self.alien_points * self.score_scale)
