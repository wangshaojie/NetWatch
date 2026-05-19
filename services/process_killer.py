"""
Process Killer Service
Safely terminates processes
"""
import logging
import psutil
from typing import Tuple


# Protected system processes
PROTECTED_PROCESSES = {
    'system', 'smss.exe', 'csrss.exe', 'wininit.exe', 'services.exe',
    'lsass.exe', 'svchost.exe', 'winlogon.exe', 'explorer.exe',
    'dllhost.exe', 'rundll32.exe', 'taskmgr.exe', 'winmgmt.exe',
    'spoolsv.exe', 'fontdrvhost.exe', 'dwm.exe', 'conhost.exe',
    'ctfmon.exe', 'sihost.exe', 'logonui.exe', 'wudfhost.exe'
}


class ProcessKiller:
    """Handles process termination safely"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def is_protected_process(self, process_name: str) -> bool:
        """Check if process is protected"""
        if not process_name:
            return True
        return process_name.lower() in PROTECTED_PROCESSES

    def kill_process(self, pid: int, process_name: str = '') -> Tuple[bool, str]:
        """Kill a process by PID"""
        # Validate PID
        if not isinstance(pid, int) or pid <= 0:
            return False, "Invalid PID"

        # Check if system process
        if process_name and self.is_protected_process(process_name):
            return False, "Cannot terminate system process"

        # Special PIDs that should never be killed
        if pid in (0, 4):
            return False, "Cannot terminate system idle or core process"

        try:
            process = psutil.Process(pid)
            name = process.name()

            # Double-check protection
            if self.is_protected_process(name):
                return False, "Cannot terminate protected system process"

            # Try to terminate gracefully first
            try:
                process.terminate()
                gone, alive = psutil.wait_procs([process], timeout=3)

                if process in alive:
                    # Force kill if still alive
                    process.kill()
                    return True, f"Process {pid} ({name}) terminated (forced)"
                else:
                    return True, f"Process {pid} ({name}) terminated successfully"

            except psutil.TimeoutExpired:
                # Force kill
                process.kill()
                return True, f"Process {pid} ({name}) terminated (timeout, forced)"

        except psutil.NoSuchProcess:
            return False, "Process not found. It may have already terminated."
        except psutil.AccessDenied:
            return False, "Access denied. Try running as Administrator."
        except Exception as e:
            self.logger.error(f"Error killing process {pid}: {e}")
            return False, f"Error: {str(e)}"

    def get_process_info(self, pid: int) -> dict:
        """Get information about a process"""
        try:
            process = psutil.Process(pid)
            return {
                'name': process.name(),
                'exe': process.exe(),
                'status': process.status(),
                'username': process.username(),
                'cpu_percent': process.cpu_percent(),
                'memory_percent': process.memory_percent(),
                'memory_mb': process.memory_info().rss / (1024 * 1024),
                'create_time': process.create_time(),
                'threads': process.num_threads()
            }
        except psutil.NoSuchProcess:
            return {}
        except Exception as e:
            self.logger.error(f"Error getting process info: {e}")
            return {}
