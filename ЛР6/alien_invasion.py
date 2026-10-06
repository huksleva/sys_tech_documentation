"""Запускает игру из дерева исходников, выбирая пакет в ``src`` первым."""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
SOURCE_ROOT = PROJECT_ROOT / "src"
if str(SOURCE_ROOT) in sys.path:
    sys.path.remove(str(SOURCE_ROOT))
sys.path.insert(0, str(SOURCE_ROOT))

from alien_invasion.alien_invasion import main as run_main


def main():
    """Передаёт запуск главной функции пакета Alien Invasion."""
    run_main()


if __name__ == "__main__":
    main()
