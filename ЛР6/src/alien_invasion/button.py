"""Создаёт отображение кнопки Play; запуск сессии решает контроллер."""

import pygame


class Button:
    """Хранит геометрию и текст кнопки начала игры.

    Attributes:
        screen: Поверхность окна.
        screen_rect: Границы окна для центрирования.
        width: Ширина кнопки, 200 пикселей.
        height: Высота кнопки, 50 пикселей.
        button_color: Зелёный фон кнопки RGB.
        text_color: Белый цвет текста RGB.
        font: Системный шрифт Pygame размером 48.
        rect: Область клика и отрисовки кнопки.
        msg_image: Подготовленная поверхность надписи.
        msg_image_rect: Центрированный прямоугольник надписи.
    """

    def __init__(self, ai_game, msg):
        """Создаёт кнопку в центре экрана и подготавливает текст.

        Args:
            ai_game: Контроллер с поверхностью окна.
            msg: Надпись на кнопке, обычно Play.
        """
        self.screen = ai_game.screen
        self.screen_rect = self.screen.get_rect()
        self.width, self.height = 200, 50
        self.button_color = (0, 135, 0)
        self.text_color = (255, 255, 255)
        self.font = pygame.font.SysFont(None, 48)
        self.rect = pygame.Rect(0, 0, self.width, self.height)
        self.rect.center = self.screen_rect.center
        self._prep_msg(msg)

    def _prep_msg(self, msg):
        """Создаёт сглаженный текст и центрирует его в кнопке.

        Args:
            msg: Строка, отображаемая на кнопке.
        """
        self.msg_image = self.font.render(msg, True, self.text_color, self.button_color)
        self.msg_image_rect = self.msg_image.get_rect(center=self.rect.center)

    def draw_button(self):
        """Рисует фон кнопки и ранее подготовленную надпись."""
        self.screen.fill(self.button_color, self.rect)
        self.screen.blit(self.msg_image, self.msg_image_rect)
