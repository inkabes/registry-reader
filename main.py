import logging
import sys
from typing import NoReturn

from PyQt6.QtWidgets import QApplication

from src.ui.window import MainWindow


logger = logging.getLogger(__name__)


def main() -> NoReturn:
    """
    Точка входа в графическое приложение.
    """
    logger.info("Запуск приложения Registry Reader.")

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    window = MainWindow()
    window.show()

    exit_code = app.exec()
    logger.info("Приложение завершено с кодом: %s", exit_code)

    sys.exit(exit_code)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    main()