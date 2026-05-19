"""
Single Instance Manager
Ensures only one instance of NetWatch is running
"""
import os


class SingleInstance:
    """Simple single instance manager"""

    def __init__(self):
        self._is_unique = True
        self.lock_path = ".netwatch.lock"

        # Try to create lock file
        try:
            if os.path.exists(self.lock_path):
                # Another instance might be running
                # Check if process is actually alive
                with open(self.lock_path, 'r') as f:
                    pid = f.read().strip()
                    if pid and pid.isdigit():
                        import psutil
                        if psutil.pid_exists(int(pid)):
                            self._is_unique = False
                            return

            # Write our PID
            with open(self.lock_path, 'w') as f:
                f.write(str(os.getpid()))
            self._is_unique = True
        except Exception:
            self._is_unique = True

    @property
    def is_unique(self):
        return self._is_unique

    def activate_existing(self):
        pass

    def __del__(self):
        try:
            if self._is_unique and os.path.exists(self.lock_path):
                os.remove(self.lock_path)
        except Exception:
            pass
