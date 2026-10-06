"""Содержит каркас HUD."""


class Scoreboard:
    """Сохраняет публичные точки будущего отображения счёта."""

    def __init__(self, ai_game):
        """Запоминает игру без подготовки графики HUD."""
        self.ai_game = ai_game

    def prep_score(self):
        """TODO: подготовить изображение счёта."""

    def prep_high_score(self):
        """TODO: подготовить изображение рекорда."""

    def prep_level(self):
        """TODO: подготовить изображение уровня."""

    def prep_ships(self):
        """TODO: подготовить индикатор оставшихся кораблей."""

    def check_high_score(self):
        """TODO: обновить рекорд сессии."""

    def show_score(self):
        """TODO: вывести HUD на экран."""
