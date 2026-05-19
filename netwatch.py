"""
NetWatch - Windows Port Manager
A visual port management tool for Windows
"""

import sys
import subprocess
import re
import os
from datetime import datetime
from typing import List, Tuple, Optional
from dataclasses import dataclass

# 检测是否打包环境
FROZEN = getattr(sys, 'frozen', False)

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QPushButton, QHeaderView,
    QDialog, QLabel, QDialogButtonBox, QMessageBox, QStatusBar,
    QToolTip, QLineEdit, QDesktopWidget
)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QPalette, QIcon


@dataclass
class PortInfo:
    protocol: str
    local_addr: str
    port: int
    pid: int
    process_name: str


# Whitelist of system processes that should never be killed
SYSTEM_PROCESSES_WHITELIST = [
    'system',
    'smss.exe',
    'csrss.exe',
    'wininit.exe',
    'services.exe',
    'lsass.exe',
    'svchost.exe',
    'winlogon.exe',
    'explorer.exe',
    'dllhost.exe',
    'rundll32.exe',
    'taskmgr.exe',
    'taskmgr',
    'registry',
    'winmgmt.exe',
    'spoolsv.exe',
    'securityhealthservice.exe',
    'msiexec.exe',
    'conhost.exe',
    'fontdrvhost.exe',
    'wmiprvse.exe',
    'searchindexer.exe',
    'searchhost.exe',
    'startmenux.exe',
    'shellexperiencehost.exe',
    'runtimebroker.exe',
    'textinputhost.exe',
    'dwm.exe',
    'win32yank.exe',
    'ctfmon.exe',
    'audiodg.exe',
    'sihost.exe',
    'logonui.exe',
    'provisionserver.exe',
    'netbios',
    'dns.exe',
    'dhcp.exe',
    'ikeext.exe',
    'iphlpsvc.exe',
    'nlaapi.dll',
    'nsi.exe',
    'tcpipprov.dll',
    'dhcpcore.dll',
    'bootimg.exe',
]


class PortScannerWorker(QThread):
    """后台线程扫描端口"""
    finished = pyqtSignal(list)

    def __init__(self, scanner):
        super().__init__()
        self.scanner = scanner

    def run(self):
        ports = self.scanner.get_all_ports()
        self.finished.emit(ports)


class PortScanner:
    """Scans and retrieves port information using netstat"""

    def __init__(self):
        self._process_cache = {}

    def _load_all_processes(self):
        """一次性加载所有进程信息到缓存"""
        self._process_cache = {}

        # 特殊 PID
        self._process_cache[0] = "System Idle Process"
        self._process_cache[4] = "System"

        try:
            # 一次性获取所有进程
            result = subprocess.run(
                'tasklist /FO CSV /NH',
                capture_output=True, text=True, timeout=10,
                shell=True,
                encoding='utf-8',
                errors='ignore'
            )
            for line in result.stdout.splitlines():
                line = line.strip()
                if not line:
                    continue
                # Parse CSV: "imagename","pid","sessionname","sessionnum","memusage"
                match = re.match(r'"([^"]+)","(\d+)"', line)
                if match:
                    name = match.group(1)
                    pid = int(match.group(2))
                    self._process_cache[pid] = name
        except Exception:
            pass

    def _get_process_name(self, pid: int) -> str:
        """Get process name from PID (从缓存)"""
        if pid in self._process_cache:
            return self._process_cache[pid]
        return f"Unknown (PID: {pid})"

    def _is_system_process(self, process_name: str) -> bool:
        """Check if process is a system critical process"""
        if not process_name:
            return False
        name_lower = process_name.lower()
        for sys_proc in SYSTEM_PROCESSES_WHITELIST:
            if sys_proc.lower() in name_lower:
                return True
        return False

    def get_all_ports(self) -> List[PortInfo]:
        """Get all TCP and UDP ports with process information"""
        ports = []

        # 先一次性加载所有进程信息
        self._load_all_processes()

        try:
            result = subprocess.run(
                'netstat -ano',
                capture_output=True, text=True, timeout=30,
                shell=True,
                encoding='utf-8',
                errors='ignore'
            )

            lines = result.stdout.splitlines()
            if not lines:
                print("DEBUG: netstat returned no output")
                return ports

            for line in lines:
                line = line.strip()
                if not line or line.startswith('Proto') or line.startswith('Active'):
                    continue

                parts = line.split()
                if len(parts) < 5:
                    continue

                protocol = parts[0].upper()
                if protocol not in ('TCP', 'UDP'):
                    continue

                local_addr = parts[1]
                # Parse address and port
                if ':' in local_addr:
                    addr_parts = local_addr.rsplit(':', 1)
                    address = addr_parts[0] if addr_parts[0] else '0.0.0.0'
                    try:
                        port = int(addr_parts[-1])
                    except ValueError:
                        continue
                else:
                    continue

                try:
                    pid = int(parts[-1])
                except ValueError:
                    continue

                process_name = self._get_process_name(pid)
                is_system = self._is_system_process(process_name)

                if not is_system:
                    ports.append(PortInfo(
                        protocol=protocol,
                        local_addr=address,
                        port=port,
                        pid=pid,
                        process_name=process_name
                    ))

        except subprocess.TimeoutExpired:
            print("Netstat command timed out")
        except Exception as e:
            print(f"Error scanning ports: {e}")

        # Sort by port number, then by protocol
        ports.sort(key=lambda x: (x.port, x.protocol))
        return ports


class ProcessKiller:
    """Handles process termination"""

    @staticmethod
    def kill_process(pid: int) -> Tuple[bool, str]:
        """Kill a process by PID. Returns (success, message)"""
        if pid == 0 or pid == 4:
            return False, "Cannot kill System Idle Process or System process"

        try:
            result = subprocess.run(
                f'taskkill /PID {pid} /F',
                capture_output=True, text=True, timeout=10,
                shell=True
            )

            if result.returncode == 0:
                return True, f"Process {pid} terminated successfully"
            else:
                error_msg = result.stderr.strip() if result.stderr else "Unknown error"
                if "Access is denied" in error_msg:
                    return False, "Access denied. Try running as Administrator."
                elif "not found" in error_msg.lower():
                    return False, "Process not found. It may have already terminated."
                else:
                    return False, error_msg

        except subprocess.TimeoutExpired:
            return False, "Kill command timed out"
        except Exception as e:
            return False, f"Error: {str(e)}"


class ConfirmDialog(QDialog):
    """Confirmation dialog before killing a process"""

    def __init__(self, pid: int, process_name: str, port: int, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Confirm Kill")
        self.setModal(True)
        self.setMinimumWidth(400)
        self._setup_ui(pid, process_name, port)

    def _setup_ui(self, pid: int, process_name: str, port: int):
        layout = QVBoxLayout(self)

        # Icon and message
        msg_layout = QHBoxLayout()
        icon_label = QLabel("⚠️")
        icon_label.setFont(QFont("Segoe UI", 24))

        msg_label = QLabel(
            f"Are you sure you want to end process<br><br>"
            f"<b>Port:</b> {port}<br>"
            f"<b>PID:</b> {pid}<br>"
            f"<b>Name:</b> {process_name}"
        )
        msg_label.setFont(QFont("Segoe UI", 11))

        msg_layout.addWidget(icon_label)
        msg_layout.addWidget(msg_label, 1)
        layout.addLayout(msg_layout)

        # Warning
        warning = QLabel("This action cannot be undone.")
        warning.setFont(QFont("Segoe UI", 10))
        warning.setStyleSheet("color: #718096;")
        layout.addWidget(warning)

        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Cancel | QDialogButtonBox.Ok
        )
        button_box.setCenterButtons(True)

        # Customize buttons
        cancel_btn = button_box.button(QDialogButtonBox.Cancel)
        cancel_btn.setText("Cancel")
        cancel_btn.setFont(QFont("Segoe UI", 11))
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #718096;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 20px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #4A5568;
            }
        """)

        ok_btn = button_box.button(QDialogButtonBox.Ok)
        ok_btn.setText("Kill")
        ok_btn.setFont(QFont("Segoe UI", 11))
        ok_btn.setStyleSheet("""
            QPushButton {
                background-color: #E53E3E;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 20px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #C53030;
            }
        """)

        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)


class MainWindow(QMainWindow):
    """Main application window"""

    def __init__(self):
        super().__init__()
        self.scanner = PortScanner()
        self.last_refresh = None
        self._all_ports = []  # 存储所有端口数据用于搜索
        self.worker = None
        self.setWindowTitle("NetWatch - Port Manager")
        self.setGeometry(100, 100, 1100, 650)
        self.setMinimumSize(700, 500)

        # 设置窗口图标
        if FROZEN:
            icon_path = os.path.join(sys._MEIPASS, 'logo.ico')
        else:
            icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logo.ico')
        self.setWindowIcon(QIcon(icon_path))

        self._setup_ui()
        self._apply_styles()

        # 先显示窗口，再后台加载端口数据
        self.show()
        self.status_bar.showMessage("Loading ports...")
        self._start_loading()

    def _start_loading(self):
        """后台线程加载端口数据"""
        self.loading_label.show()
        self.table.hide()
        self.worker = PortScannerWorker(self.scanner)
        self.worker.finished.connect(self._on_ports_loaded)
        self.worker.start()

    def _on_ports_loaded(self, ports: List[PortInfo]):
        """端口数据加载完成"""
        self._all_ports = ports
        self._display_ports(ports)
        self.loading_label.hide()
        self.table.show()

    def _setup_ui(self):
        """Setup the user interface"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 10)
        main_layout.setSpacing(15)

        # Header
        header_layout = QHBoxLayout()

        title = QLabel("NetWatch 🌐")
        title.setFont(QFont("Segoe UI", 20, QFont.Bold))
        title.setStyleSheet("color: #2D3748;")
        header_layout.addWidget(title)

        # Search box
        search_layout = QHBoxLayout()
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search port, PID, or process name...")
        self.search_box.setFont(QFont("Segoe UI", 11))
        self.search_box.setFixedWidth(250)
        self.search_box.setStyleSheet("""
            QLineEdit {
                border: 1px solid #E2E8F0;
                border-radius: 6px;
                padding: 6px 12px;
                background-color: white;
            }
            QLineEdit:focus {
                border: 1px solid #3182CE;
            }
        """)
        self.search_box.textChanged.connect(self._on_search_changed)
        search_layout.addWidget(self.search_box)

        header_layout.addLayout(search_layout)
        header_layout.addStretch()

        self.refresh_btn = QPushButton("↻ Refresh")
        self.refresh_btn.setFont(QFont("Segoe UI", 11))
        self.refresh_btn.setCursor(Qt.PointingHandCursor)
        self.refresh_btn.clicked.connect(self.load_ports)
        header_layout.addWidget(self.refresh_btn)

        main_layout.addLayout(header_layout)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(
            ["Protocol", "Local Address", "Port", "PID", "Process Name", "Action"]
        )

        # Table styling
        header = self.table.horizontalHeader()
        header.setFont(QFont("Segoe UI", 11, QFont.Bold))
        header.setStyleSheet("""
            QHeaderView::section {
                background-color: #EDF2F7;
                color: #2D3748;
                padding: 10px 12px;
                border: none;
                border-bottom: 2px solid #CBD5E0;
                font-weight: bold;
            }
        """)
        header.setSectionResizeMode(4, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)

        self.table.setFont(QFont("Segoe UI", 12))
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setContextMenuPolicy(Qt.NoContextMenu)  # 禁用右键菜单
        self.table.setFocusPolicy(Qt.NoFocus)  # 去掉选中虚线框

        # 表格容器（用于放置加载提示）
        self.table_container = QWidget()
        table_layout = QVBoxLayout(self.table_container)
        table_layout.setContentsMargins(0, 0, 0, 0)
        table_layout.addWidget(self.table)

        # 加载提示标签（居中显示）
        self.loading_label = QLabel("Loading ports...")
        self.loading_label.setFont(QFont("Segoe UI", 14))
        self.loading_label.setAlignment(Qt.AlignCenter)
        self.loading_label.setStyleSheet("color: #718096; background-color: transparent;")
        self.loading_label.setFixedHeight(300)
        table_layout.addWidget(self.loading_label, 1)  # stretch factor 1

        main_layout.addWidget(self.table_container, 1)

        # Status bar
        self.status_bar = QStatusBar()
        self.status_bar.setFont(QFont("Segoe UI", 11))
        self.status_bar.setStyleSheet("""
            QStatusBar {
                background-color: #EDF2F7;
                color: #718096;
                border-top: 1px solid #E2E8F0;
            }
        """)
        self.setStatusBar(self.status_bar)

    def _apply_styles(self):
        """Apply global styles"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #F5F7FA;
            }
            QTableWidget {
                background-color: white;
                border: 1px solid #E2E8F0;
                border-radius: 8px;
                gridline-color: #E2E8F0;
                selection-background-color: #90CDF4;
                selection-color: #1A202C;
            }
            QTableWidget::item {
                padding: 10px 12px;
                border-bottom: 1px solid #F0F4F8;
            }
            QTableWidget::item:alternate {
                background-color: #FAFBFC;
            }
            QTableWidget::item:selected {
                color: #1A202C;
            }
            QPushButton {
                font-family: "Segoe UI";
                border-radius: 6px;
            }
        """)

    def _is_system_process(self, process_name: str) -> bool:
        """Check if process is whitelisted"""
        if not process_name:
            return False
        name_lower = process_name.lower()
        for sys_proc in SYSTEM_PROCESSES_WHITELIST:
            if sys_proc.lower() in name_lower:
                return True
        return False

    def _on_search_changed(self, text: str):
        """Filter ports based on search text"""
        if not text:
            self._display_ports(self._all_ports)
            return

        search_text = text.lower()
        filtered = []
        for port_info in self._all_ports:
            # 搜索端口号、PID、进程名、协议、地址（支持模糊匹配）
            if (search_text in str(port_info.port) or
                search_text in str(port_info.pid) or
                search_text in str(port_info.process_name).lower() or
                search_text in port_info.protocol.lower() or
                search_text in port_info.local_addr.lower()):
                filtered.append(port_info)

        self._display_ports(filtered)

    def _display_ports(self, ports: List[PortInfo]):
        """Display ports in the table"""
        self.table.setRowCount(0)
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(ports))

        for row, port_info in enumerate(ports):
            # Protocol
            proto_item = QTableWidgetItem(port_info.protocol)
            proto_item.setTextAlignment(Qt.AlignCenter)
            proto_item.setFont(QFont("Segoe UI", 11))
            self.table.setItem(row, 0, proto_item)

            # Local Address
            addr_item = QTableWidgetItem(port_info.local_addr)
            addr_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            addr_item.setFont(QFont("Segoe UI", 11, QFont.Normal))
            self.table.setItem(row, 1, addr_item)

            # Port
            port_item = QTableWidgetItem(str(port_info.port))
            port_item.setTextAlignment(Qt.AlignCenter)
            port_item.setFont(QFont("Segoe UI", 11, QFont.Bold))
            port_item.setForeground(QColor("#3182CE"))
            self.table.setItem(row, 2, port_item)

            # PID
            pid_item = QTableWidgetItem(str(port_info.pid))
            pid_item.setTextAlignment(Qt.AlignCenter)
            pid_item.setFont(QFont("Segoe UI", 11))
            self.table.setItem(row, 3, pid_item)

            # Process Name
            name_item = QTableWidgetItem(port_info.process_name)
            name_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            name_item.setFont(QFont("Segoe UI", 11))
            self.table.setItem(row, 4, name_item)

            # Kill Button
            kill_btn = QPushButton("Kill")
            kill_btn.setFont(QFont("Segoe UI", 11, QFont.Bold))
            kill_btn.setCursor(Qt.PointingHandCursor)

            is_system = self._is_system_process(port_info.process_name)

            if is_system:
                kill_btn.setEnabled(False)
                kill_btn.setToolTip("System process - cannot be terminated")
                kill_btn.setStyleSheet("color: #A0AEC0;")
            else:
                kill_btn.setStyleSheet("color: #DC2626;")
                kill_btn.clicked.connect(
                    lambda checked, p=port_info.pid, n=port_info.process_name, pt=port_info.port:
                    self._on_kill_clicked(p, n, pt)
                )

            # 用容器居中按钮
            container = QWidget()
            container_layout = QHBoxLayout(container)
            container_layout.setContentsMargins(0, 0, 0, 0)
            container_layout.setAlignment(Qt.AlignCenter)
            container_layout.addWidget(kill_btn)
            self.table.setCellWidget(row, 5, container)

        self.table.setSortingEnabled(True)
        self.table.sortByColumn(2, Qt.AscendingOrder)

        # Update status
        self.last_refresh = datetime.now().strftime("%H:%M:%S")
        search_text = self.search_box.text()
        if search_text:
            self.status_bar.showMessage(
                f"Showing {len(ports)} of {len(self._all_ports)} ports | Last refreshed: {self.last_refresh}"
            )
        else:
            self.status_bar.showMessage(
                f"Total: {len(ports)} ports | Last refreshed: {self.last_refresh}"
            )

    def load_ports(self):
        """Load and display all ports (后台线程)"""
        self.status_bar.showMessage("Loading ports...")
        self._start_loading()

    def _on_kill_clicked(self, pid: int, process_name: str, port: int):
        """Handle kill button click"""
        dialog = ConfirmDialog(pid, process_name, port, self)
        if dialog.exec_() == QDialog.Accepted:
            success, message = ProcessKiller.kill_process(pid)

            if success:
                QMessageBox.information(
                    self, "Success", f"✓ {message}",
                    QMessageBox.Ok
                )
                # Refresh after successful kill
                QTimer.singleShot(300, self.load_ports)
            else:
                QMessageBox.warning(
                    self, "Error", f"✗ {message}",
                    QMessageBox.Ok
                )
                # Still refresh to update the list
                QTimer.singleShot(300, self.load_ports)


def main():
    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 10))

    # Set application-wide stylesheet
    app.setStyleSheet("""
        QToolTip {
            background-color: #2D3748;
            color: white;
            border: none;
            border-radius: 4px;
            padding: 6px 10px;
            font-family: "Segoe UI";
            font-size: 11px;
        }
    """)

    window = MainWindow()
    window.show()

    # 窗口居中显示
    screen = QDesktopWidget().screenGeometry()
    window_geom = window.geometry()
    x = (screen.width() - window_geom.width()) // 2
    y = (screen.height() - window_geom.height()) // 2
    window.move(x, y)

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
