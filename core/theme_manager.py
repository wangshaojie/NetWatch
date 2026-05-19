"""
Theme Manager for NetWatch
Supports Light and Dark themes with Windows 11 / Fluent Design style
"""
from PyQt5.QtCore import QObject, pyqtSignal


class ThemeManager(QObject):
    """Manages application themes"""

    LIGHT_THEME = "light"
    DARK_THEME = "dark"

    theme_changed = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self._current_theme = self.DARK_THEME
        self._stylesheets = {
            self.LIGHT_THEME: self._get_light_stylesheet(),
            self.DARK_THEME: self._get_dark_stylesheet()
        }

    @property
    def current_theme(self):
        return self._current_theme

    def apply_theme(self, theme_name: str):
        """Apply the specified theme"""
        if theme_name in self._stylesheets:
            self._current_theme = theme_name
            self.theme_changed.emit(theme_name)
            return self._stylesheets[theme_name]
        return ""

    def get_stylesheet(self):
        """Get current stylesheet"""
        return self._stylesheets.get(self._current_theme, "")

    def toggle_theme(self):
        """Toggle between light and dark themes"""
        new_theme = self.LIGHT_THEME if self._current_theme == self.DARK_THEME else self.DARK_THEME
        return self.apply_theme(new_theme)

    def _get_light_stylesheet(self):
        return """
        QMainWindow {
            background-color: #F3F3F3;
            color: #1A1A1A;
        }
        QWidget {
            background-color: transparent;
            color: #1A1A1A;
        }
        QLabel {
            color: #1A1A1A;
            background-color: transparent;
        }
        QPushButton {
            background-color: #0078D4;
            color: white;
            border: none;
            border-radius: 4px;
            padding: 8px 16px;
            font-weight: 500;
        }
        QPushButton:hover {
            background-color: #106EBE;
        }
        QPushButton:pressed {
            background-color: #005A9E;
        }
        QLineEdit {
            background-color: white;
            border: 1px solid #D1D1D1;
            border-radius: 4px;
            padding: 8px 12px;
            color: #1A1A1A;
        }
        QLineEdit:focus {
            border: 2px solid #0078D4;
        }
        QTableWidget {
            background-color: white;
            border: 1px solid #E5E5E5;
            border-radius: 4px;
            gridline-color: #F0F0F0;
            color: #1A1A1A;
        }
        QTableWidget::item {
            padding: 6px;
            border: none;
            color: #1A1A1A;
        }
        QTableWidget::item:alternate {
            background-color: #FAFAFA;
        }
        QTableWidget::item:selected {
            background-color: #0078D4;
            color: #FFFFFF;
        }
        QHeaderView::section {
            background-color: #F0F0F0;
            color: #1A1A1A;
            padding: 8px 12px;
            border: none;
            border-bottom: 2px solid #D1D1D1;
            font-weight: 600;
        }
        QStatusBar {
            background-color: #F0F0F0;
            color: #666666;
            border-top: 1px solid #E5E5E5;
        }
        QToolTip {
            background-color: #1A1A1A;
            color: white;
            border: none;
            border-radius: 4px;
            padding: 6px 10px;
        }
        """

    def _get_dark_stylesheet(self):
        return """
        QMainWindow {
            background-color: #1E1E1E;
            color: #CCCCCC;
        }
        QWidget {
            background-color: transparent;
            color: #CCCCCC;
        }
        QLabel {
            color: #CCCCCC;
            background-color: transparent;
        }
        QPushButton {
            background-color: #0078D4;
            color: white;
            border: none;
            border-radius: 4px;
            padding: 8px 16px;
            font-weight: 500;
        }
        QPushButton:hover {
            background-color: #1E90FF;
        }
        QPushButton:pressed {
            background-color: #0066CC;
        }
        QLineEdit {
            background-color: #2D2D2D;
            border: 1px solid #3D3D3D;
            border-radius: 4px;
            padding: 8px 12px;
            color: #CCCCCC;
        }
        QLineEdit:focus {
            border: 2px solid #0078D4;
        }
        QLineEdit:placeholder {
            color: #888888;
        }
        QTableWidget {
            background-color: #1E1E1E;
            border: 1px solid #3D3D3D;
            border-radius: 4px;
            gridline-color: #3D3D3D;
            color: #CCCCCC;
        }
        QTableWidget::item {
            padding: 6px;
            border: none;
            color: #CCCCCC;
        }
        QTableWidget::item:alternate {
            background-color: #2D2D2D;
        }
        QTableWidget::item:selected {
            background-color: #094771;
            color: #FFFFFF;
        }
        QTableWidget::item:hover {
            background-color: #2A3A4A;
        }
        QHeaderView::section {
            background-color: #2D2D2D;
            color: #CCCCCC;
            padding: 8px 12px;
            border: none;
            border-bottom: 2px solid #0078D4;
            font-weight: 600;
        }
        QStatusBar {
            background-color: #007ACC;
            color: white;
            border-top: 1px solid #3D3D3D;
        }
        QToolTip {
            background-color: #2D2D2D;
            color: #CCCCCC;
            border: 1px solid #3D3D3D;
            border-radius: 4px;
            padding: 6px 10px;
        }
        QScrollBar:vertical {
            background-color: #1E1E1E;
            width: 12px;
            border-radius: 6px;
        }
        QScrollBar::handle:vertical {
            background-color: #424242;
            border-radius: 6px;
            min-height: 20px;
        }
        QScrollBar::handle:vertical:hover {
            background-color: #555555;
        }
        QScrollBar:horizontal {
            background-color: #1E1E1E;
            height: 12px;
            border-radius: 6px;
        }
        QScrollBar::handle:horizontal {
            background-color: #424242;
            border-radius: 6px;
            min-width: 20px;
        }
        """
