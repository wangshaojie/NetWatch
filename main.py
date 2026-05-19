"""
NetWatch - Professional Windows Port Manager
main.py - Entry point
"""
import sys
import os
import logging
from logging.handlers import RotatingFileHandler

# High DPI support - MUST be before any Qt imports
os.environ['QT_ENABLE_HIGHDPI_SCALING'] = '1'
os.environ['QT_SCALE_FACTOR_ROUNDING_POLICY'] = 'PassThrough'

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QIcon

from core.single_instance import SingleInstance
from core.theme_manager import ThemeManager
from ui.main_window import MainWindow


def setup_logging():
    """Setup logging system with rotation"""
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
    os.makedirs(log_dir, exist_ok=True)

    log_file = os.path.join(log_dir, 'netwatch.log')

    handler = RotatingFileHandler(
        log_file,
        maxBytes=5 * 1024 * 1024,  # 5MB
        backupCount=5,
        encoding='utf-8'
    )

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)

    # Also log to console in debug mode
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(formatter)
    logger.addHandler(console)

    return logger


def main():
    logger = setup_logging()
    logger.info("NetWatch starting...")

    # Single instance check
    instance = SingleInstance()
    if not instance.is_unique:
        logger.warning("Another instance is running, activating existing window")
        instance.activate_existing()
        sys.exit(0)

    app = QApplication(sys.argv)
    app.setApplicationName("NetWatch")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("NetWatch")

    # Windows App User Model ID for taskbar grouping
    try:
        from ctypes import windll
        windll.shell32.SetCurrentProcessExplicitAppUserModelID("NetWatch.PortManager.1.0")
    except Exception:
        pass

    # Setup theme
    theme_manager = ThemeManager()
    theme_manager.apply_theme(theme_manager.DARK_THEME)

    # Load stylesheet
    app.setStyle('Fusion')

    # Set default font
    font = QFont("Segoe UI", 9)
    app.setFont(font)

    # Create and show main window
    window = MainWindow(theme_manager)

    # Set window icon
    icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'icon.ico')
    if os.path.exists(icon_path):
        window.setWindowIcon(QIcon(icon_path))

    window.show()

    logger.info("NetWatch started successfully")

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
