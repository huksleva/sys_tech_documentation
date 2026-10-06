"""Определяет пришельца, движущегося с общим направлением флота."""

from pygame.sprite import Sprite

from .assets import load_image


class Alien(Sprite):
    """Представляет одну цель и её горизонтальную координату.

    Attributes:
        screen: Поверхность игрового окна.
        settings: Общие скорость и направление флота.
        image: BMP пришельца из ресурсов пакета.
        rect: Прямоугольник отрисовки и столкновений.
        x: Вещественная координата левого края.
    """

    def __init__(self, ai_game):
        """Загружает изображение и создаёт цель у начала координат.

        Args:
            ai_game: Контроллер, предоставляющий экран и правила флота.
        """
        super().__init__()
        self.screen = ai_game.screen
        self.settings = ai_game.settings
        self.image = load_image("alien.bmp")
        self.rect = self.image.get_rect()
        self.x = float(self.rect.x)

    def check_edges(self):
        """Сообщает, касается ли цель любой горизонтальной границы окна.

        Returns:
            True при ``rect.left <= 0`` либо ``rect.right >= screen.right``.
        """
        return self.rect.right >= self.screen.get_rect().right or self.rect.left <= 0

    def update(self):
        """Перемещает цель по общей скорости и направлению и обновляет ``rect.x``."""
        self.x += self.settings.alien_speed * self.settings.fleet_direction
        self.rect.x = int(self.x)
