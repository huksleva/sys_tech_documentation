"""Определяет корабль игрока и ограниченное горизонтальное движение."""

from pygame.sprite import Sprite

from .assets import load_image


class Ship(Sprite):
    """Представляет корабль, его положение и флаги удержания стрелок.

    Attributes:
        screen: Поверхность окна, на которой рисуется корабль.
        screen_rect: Прямоугольник границ экрана.
        settings: Настройки скорости перемещения.
        image: BMP корабля из package data.
        rect: Прямоугольник отображения и столкновений.
        x: Вещественная горизонтальная координата левого края.
        moving_right: Удерживается ли стрелка вправо.
        moving_left: Удерживается ли стрелка влево.
    """

    def __init__(self, ai_game):
        """Создаёт неподвижный корабль у нижнего центра экрана.

        Args:
            ai_game: Контроллер с экраном и настройками скорости.
        """
        super().__init__()
        self.screen = ai_game.screen
        self.screen_rect = self.screen.get_rect()
        self.settings = ai_game.settings
        self.image = load_image("ship.bmp")
        self.rect = self.image.get_rect()
        self.moving_right = False
        self.moving_left = False
        self.center_ship()

    def update(self):
        """Двигает корабль и ограничивает координату даже при дробной скорости.

        Одновременное удержание обеих стрелок даёт нулевое смещение.
        Float-координата ограничивается до синхронизации с целым ``rect.x``.
        """
        direction = int(self.moving_right) - int(self.moving_left)
        self.x += direction * self.settings.ship_speed
        self.x = max(0.0, min(self.x, float(self.screen_rect.width - self.rect.width)))
        self.rect.x = int(self.x)

    def blitme(self):
        """Рисует корабль в текущем прямоугольнике без обновления экрана."""
        self.screen.blit(self.image, self.rect)

    def center_ship(self):
        """Центрирует корабль у нижней границы и снимает оба флага движения."""
        self.rect.midbottom = self.screen_rect.midbottom
        self.x = float(self.rect.x)
        self.moving_right = False
        self.moving_left = False
