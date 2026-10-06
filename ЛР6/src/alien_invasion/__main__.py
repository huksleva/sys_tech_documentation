"""Предоставляет запуск установленного пакета через ``python -m alien_invasion``."""

from .alien_invasion import main as run_main


def main():
    """Запускает общий игровой цикл через точку входа контроллера."""
    run_main()


if __name__ == "__main__":
    main()
