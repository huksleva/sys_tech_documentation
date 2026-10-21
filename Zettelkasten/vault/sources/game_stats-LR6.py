"""Отделяет изменяемую статистику сессии от игровых настроек."""


class GameStats:
    """Хранит активность, запас кораблей, счёт, рекорд и уровень.

    Attributes:
        settings: Настройки, задающие исходный запас замен.
        high_score: Лучший счёт за время жизни процесса; не сохраняется на диск.
        game_active: Разрешены ли обновление игровой механики и ввод.
        ships_left: Число доступных замен после попадания; 0 допускает игру.
        score: Сумма очков текущей сессии.
        level: Уровень текущей сессии, начиная с 1.
    """

    def __init__(self, ai_game):
        """Создаёт неактивную сессию с нулевым рекордом.

        Args:
            ai_game: Контроллер, предоставляющий настройки правил.
        """
        self.settings = ai_game.settings
        self.high_score = 0
        self.reset_stats()
        self.game_active = False

    def reset_stats(self):
        """Сбрасывает запас, счёт и уровень, сохраняя рекорд и активность."""
        self.ships_left = self.settings.ship_limit
        self.score = 0
        self.level = 1
