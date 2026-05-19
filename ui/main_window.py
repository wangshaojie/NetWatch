"""
Main Window
Main application window with QTableWidget for Kill button support
"""
import logging
import os
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QLineEdit, QPushButton, QStatusBar, QLabel,
    QApplication, QMessageBox, QAbstractItemView
)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QFont, QColor

from services.port_scanner import PortScanner
from services.process_killer import ProcessKiller
from models.port_model import PortConnection
from core.theme_manager import ThemeManager


class MainWindow(QMainWindow):
    """Main application window"""

    def __init__(self, theme_manager: ThemeManager):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.theme_manager = theme_manager
        self.scanner = PortScanner()
        self.killer = ProcessKiller()
        self._scan_thread = None

        self._setup_ui()
        self._setup_timer()
        self._apply_styles()

        # Initial load
        QTimer.singleShot(100, self._start_scan)

    def _setup_ui(self):
        """Setup the user interface"""
        self.setWindowTitle("NetWatch - Port Manager")
        self.setGeometry(0, 0, 1200, 700)
        self.setMinimumSize(900, 500)

        # Center window on screen
        self._center_on_screen()

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(15, 15, 15, 10)
        layout.setSpacing(10)

        # Header
        header_layout = QHBoxLayout()

        self.title = QLabel("NetWatch 🌐")
        self.title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        header_layout.addWidget(self.title)
        header_layout.addStretch()

        # Search box
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search by port (e.g. 80, 443, 8080)...")
        self.search_box.setFixedWidth(300)
        self.search_box.setFont(QFont("Segoe UI", 10))
        self.search_box.textChanged.connect(self._on_search_changed)
        header_layout.addWidget(self.search_box)

        # Refresh button
        self.refresh_btn = QPushButton("↻ Refresh")
        self.refresh_btn.setFont(QFont("Segoe UI", 10))
        self.refresh_btn.setCursor(Qt.PointingHandCursor)
        self.refresh_btn.clicked.connect(self._start_scan)
        header_layout.addWidget(self.refresh_btn)

        # Theme toggle
        self.theme_btn = QPushButton("🌓")
        self.theme_btn.setFont(QFont("Segoe UI", 12))
        self.theme_btn.setFixedWidth(40)
        self.theme_btn.setCursor(Qt.PointingHandCursor)
        self.theme_btn.clicked.connect(self._toggle_theme)
        header_layout.addWidget(self.theme_btn)

        layout.addLayout(header_layout)

        # Table widget (always visible)
        self.table = QTableWidget()
        self.table.setColumnCount(10)
        self.table.setHorizontalHeaderLabels(
            ['Protocol', 'Local Address', 'Port', 'Remote', 'Status', 'PID', 'Process', 'CPU%', 'Memory', 'Action']
        )
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.verticalHeader().setVisible(False)
        self.table.setFocusPolicy(Qt.StrongFocus)
        self.table.setContextMenuPolicy(Qt.NoContextMenu)

        # Header setup
        header = self.table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(QHeaderView.Interactive)

        self.table.verticalHeader().setDefaultSectionSize(35)

        layout.addWidget(self.table, 1)

        # Loading label overlay
        self.loading_label = QLabel("正在获取端口...", self.table)
        self.loading_label.setFont(QFont("Segoe UI", 14))
        self.loading_label.setAlignment(Qt.AlignCenter)
        self.loading_label.hide()

        # Status bar
        self.status_bar = QStatusBar()
        self.status_bar.setFont(QFont("Segoe UI", 9))
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

    def resizeEvent(self, event):
        """Reposition loading label on resize"""
        super().resizeEvent(event)
        self._position_loading_label()

    def _position_loading_label(self):
        """Position loading label in center of table"""
        table_geo = self.table.geometry()
        self.loading_label.setGeometry(table_geo)
        if self.theme_manager.current_theme == self.theme_manager.DARK_THEME:
            self.loading_label.setStyleSheet("background-color: rgba(30, 30, 30, 200); color: #CCCCCC; border-radius: 8px; padding: 20px;")
        else:
            self.loading_label.setStyleSheet("background-color: rgba(240, 240, 240, 230); color: #1A1A1A; border-radius: 8px; padding: 20px;")

    def _setup_timer(self):
        """Setup auto-refresh timer"""
        self._refresh_timer = QTimer()
        self._refresh_timer.timeout.connect(self._start_scan)
        # self._refresh_timer.setInterval(2000)  # Auto-refresh disabled by default
        # self._refresh_timer.start()

    def _center_on_screen(self):
        """Center window on screen"""
        screen = QApplication.primaryScreen()
        if screen:
            screen_geometry = screen.geometry()
            window_geometry = self.frameGeometry()
            x = (screen_geometry.width() - window_geometry.width()) // 2
            y = (screen_geometry.height() - window_geometry.height()) // 2
            self.move(x, y)

    def _apply_styles(self):
        """Apply current theme"""
        stylesheet = self.theme_manager.get_stylesheet()
        self.setStyleSheet(stylesheet)
        # Force title color for visibility in both themes
        if self.theme_manager.current_theme == self.theme_manager.DARK_THEME:
            self.title.setStyleSheet("color: #FFFFFF; background-color: transparent;")
        else:
            self.title.setStyleSheet("color: #0078D4; background-color: transparent;")

    def _toggle_theme(self):
        """Toggle between light and dark themes"""
        self.theme_manager.toggle_theme()
        self._apply_styles()

    @pyqtSlot()
    def _start_scan(self):
        """Start scanning for ports in background"""
        if self._scan_thread and self._scan_thread.isRunning():
            return

        self.status_bar.showMessage("正在获取端口...")
        self._position_loading_label()
        self.loading_label.show()

        self._scan_thread = ScanThread(self.scanner)
        self._scan_thread.finished.connect(self._on_scan_complete)
        self._scan_thread.start()

    @pyqtSlot(list)
    def _on_scan_complete(self, connections):
        """Handle scan completion"""
        self.loading_label.hide()
        self._all_connections = connections  # Store for re-filtering
        self._display_connections(connections)

        total = len(connections)
        if self.search_box.text():
            self.status_bar.showMessage(f"Showing {self.table.rowCount()} of {total} connections")
        else:
            self.status_bar.showMessage(f"Total: {total} connections")

    def _display_connections(self, connections):
        """Display connections in table"""
        self.table.setSortingEnabled(False)

        search_text = self.search_box.text().lower()
        self._row_connections = {}  # Map row to connection

        # Filter connections first
        filtered = [c for c in connections if not search_text or c.matches_search(search_text)]

        self.table.setRowCount(len(filtered))

        for display_row, conn in enumerate(filtered):
            self._row_connections[display_row] = conn

            # Protocol
            item = QTableWidgetItem(conn.protocol)
            item.setTextAlignment(Qt.AlignCenter)
            item.setFont(QFont("Segoe UI", 9))
            self.table.setItem(display_row, 0, item)

            # Local Address
            item = QTableWidgetItem(conn.local_address)
            item.setFont(QFont("Segoe UI", 9))
            self.table.setItem(display_row, 1, item)

            # Port (highlighted in green when search matches)
            item = QTableWidgetItem(str(conn.local_port))
            item.setTextAlignment(Qt.AlignCenter)
            item.setFont(QFont("Segoe UI", 9, QFont.Bold))
            item.setForeground(QColor(0, 200, 0) if search_text else QColor(0, 120, 212))
            self.table.setItem(display_row, 2, item)

            # Remote
            remote = f"{conn.remote_address}:{conn.remote_port}" if conn.remote_address else "-"
            item = QTableWidgetItem(remote)
            item.setFont(QFont("Segoe UI", 9))
            self.table.setItem(display_row, 3, item)

            # Status
            item = QTableWidgetItem(conn.status)
            item.setTextAlignment(Qt.AlignCenter)
            item.setFont(QFont("Segoe UI", 9))
            self.table.setItem(display_row, 4, item)

            # PID
            item = QTableWidgetItem(str(conn.pid))
            item.setTextAlignment(Qt.AlignCenter)
            item.setFont(QFont("Segoe UI", 9))
            self.table.setItem(display_row, 5, item)

            # Process Name
            item = QTableWidgetItem(conn.process_name)
            item.setFont(QFont("Segoe UI", 9))
            self.table.setItem(display_row, 6, item)

            # CPU
            item = QTableWidgetItem(f"{conn.cpu_percent:.1f}")
            item.setTextAlignment(Qt.AlignCenter)
            item.setFont(QFont("Segoe UI", 9))
            item.setForeground(QColor(0, 180, 80))
            self.table.setItem(display_row, 7, item)

            # Memory
            item = QTableWidgetItem(f"{conn.memory_mb:.1f} MB")
            item.setTextAlignment(Qt.AlignCenter)
            item.setFont(QFont("Segoe UI", 9))
            item.setForeground(QColor(180, 130, 0))
            self.table.setItem(display_row, 8, item)

            # Kill Button
            kill_btn = QPushButton("Kill")
            kill_btn.setFont(QFont("Segoe UI", 9, QFont.Bold))
            kill_btn.setStyleSheet("color: #DC2626; background-color: transparent; border: none; padding: 4px 8px;")
            kill_btn.setCursor(Qt.PointingHandCursor)
            kill_btn.clicked.connect(lambda checked, r=display_row: self._on_kill_clicked(r))
            self.table.setCellWidget(display_row, 9, kill_btn)

        self.table.setSortingEnabled(True)
        self.table.resizeColumnsToContents()
        if self.table.columnWidth(0) < 60:
            self.table.setColumnWidth(0, 60)
        if self.table.columnWidth(2) < 60:
            self.table.setColumnWidth(2, 60)
        self.table.setColumnWidth(9, 70)
        # Scroll to top after filtering
        self.table.verticalScrollBar().setValue(0)

    def _on_kill_clicked(self, row: int):
        """Handle kill button click"""
        conn = self._row_connections.get(row)
        if conn:
            self._show_kill_confirmation(conn)

    def _on_search_changed(self, text: str):
        """Handle search text change"""
        if self.table.isHidden():
            return

        # Re-filter current connections
        connections = getattr(self, '_all_connections', [])
        if connections:
            self._display_connections(connections)

    def _show_kill_confirmation(self, conn: PortConnection):
        """Show confirmation dialog for killing a process"""
        reply = QMessageBox.question(
            self,
            'Confirm Kill',
            f"Are you sure you want to end this process?\n\n"
            f"Port: {conn.local_port}\n"
            f"PID: {conn.pid}\n"
            f"Process: {conn.process_name}\n"
            f"Path: {conn.process_path or 'N/A'}\n\n"
            f"This action cannot be undone.",
            QMessageBox.Yes | QMessageBox.Cancel,
            QMessageBox.Cancel
        )

        if reply == QMessageBox.Yes:
            success, message = self.killer.kill_process(conn.pid, conn.process_name)

            if success:
                QMessageBox.information(self, "Success", f"✓ {message}")
                self._start_scan()
            else:
                QMessageBox.warning(self, "Error", f"✗ {message}")

    def closeEvent(self, event):
        """Handle window close"""
        self._refresh_timer.stop()
        if self._scan_thread:
            self._scan_thread.quit()
            self._scan_thread.wait(1000)
        event.accept()


class ScanThread(QThread):
    """Background thread for scanning ports"""

    finished = pyqtSignal(list)

    def __init__(self, scanner: PortScanner):
        super().__init__()
        self.scanner = scanner

    def run(self):
        connections = self.scanner.get_all_connections()
        self.finished.emit(connections)
