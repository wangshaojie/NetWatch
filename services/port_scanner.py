"""
Port Scanner Service
Uses psutil to scan network connections
"""
import logging
import socket
import psutil
from typing import List, Set
from models.port_model import PortConnection


# System process names that should be protected
SYSTEM_PROCESSES: Set[str] = {
    'system', 'smss.exe', 'csrss.exe', 'wininit.exe', 'services.exe',
    'lsass.exe', 'svchost.exe', 'winlogon.exe', 'explorer.exe',
    'dllhost.exe', 'rundll32.exe', 'taskmgr.exe', 'winmgmt.exe',
    'spoolsv.exe', 'fontdrvhost.exe', 'dwm.exe', 'conhost.exe',
    'ctfmon.exe', 'sihost.exe', 'logonui.exe', 'WUDFHost.exe',
    'Registry', 'smss', 'audiodg.exe', 'SearchIndexer.exe'
}


class PortScanner:
    """Scans and retrieves port information using psutil"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._process_cache = {}

    def get_all_connections(self) -> List[PortConnection]:
        """Get all TCP and UDP connections with process information"""
        connections = []
        seen = set()  # Track seen (proto, laddr, lport, raddr, rport, status, pid)

        try:
            for conn in psutil.net_connections(kind='inet'):
                try:
                    # Get protocol
                    protocol = 'TCP' if conn.type == socket.SOCK_STREAM else 'UDP'

                    # Get local address and port
                    if conn.laddr:
                        local_addr = conn.laddr.ip
                        local_port = conn.laddr.port
                    else:
                        continue

                    # Get remote address and port
                    remote_addr = ''
                    remote_port = 0
                    if conn.raddr:
                        remote_addr = conn.raddr.ip
                        remote_port = conn.raddr.port

                    # Get status
                    status = conn.status if hasattr(conn, 'status') else 'UNKNOWN'

                    # Get PID
                    pid = conn.pid
                    if not pid:
                        continue

                    # Create unique key for deduplication
                    key = (protocol, local_addr, local_port, remote_addr, remote_port, status, pid)
                    if key in seen:
                        continue
                    seen.add(key)

                    # Get process information
                    process_info = self._get_process_info(pid)

                    # Skip system processes
                    if process_info['name'].lower() in SYSTEM_PROCESSES:
                        continue

                    connection = PortConnection(
                        protocol=protocol,
                        local_address=local_addr,
                        local_port=local_port,
                        remote_address=remote_addr,
                        remote_port=remote_port,
                        status=status,
                        pid=pid,
                        process_name=process_info['name'],
                        process_path=process_info['path'],
                        cpu_percent=process_info['cpu'],
                        memory_percent=process_info['memory'],
                        memory_mb=process_info['memory_mb']
                    )
                    connections.append(connection)

                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as e:
                    self.logger.debug(f"Skipping connection due to: {e}")
                    continue
                except Exception as e:
                    self.logger.error(f"Error processing connection: {e}")
                    continue

        except Exception as e:
            self.logger.error(f"Error scanning connections: {e}")

        # Sort by port number
        connections.sort(key=lambda x: (x.local_port, x.protocol))
        return connections

    def _get_process_info(self, pid: int) -> dict:
        """Get process information by PID"""
        if pid in self._process_cache:
            return self._process_cache[pid]

        info = {
            'name': f'Unknown ({pid})',
            'path': '',
            'cpu': 0.0,
            'memory': 0.0,
            'memory_mb': 0.0
        }

        try:
            process = psutil.Process(pid)
            # Get name, path and cpu in one call batch
            info['name'] = process.name()

            try:
                info['path'] = process.exe()
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                info['path'] = ''

            # cpu_percent() with short interval (10ms) for accurate reading
            try:
                info['cpu'] = process.cpu_percent(interval=0.01)
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                info['cpu'] = 0.0

            # Get memory info in one call
            try:
                mem_info = process.memory_info()
                info['memory_mb'] = mem_info.rss / (1024 * 1024)
                info['memory'] = process.memory_percent()
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                pass

        except psutil.NoSuchProcess:
            pass
        except psutil.AccessDenied:
            pass
        except Exception as e:
            self.logger.debug(f"Error getting process info for PID {pid}: {e}")

        # Cache the result
        if len(self._process_cache) < 10000:  # Limit cache size
            self._process_cache[pid] = info

        return info

    def clear_cache(self):
        """Clear the process cache"""
        self._process_cache.clear()
