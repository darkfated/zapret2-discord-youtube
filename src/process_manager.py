import subprocess


class ProcessManager:
    def __init__(self):
        self._process = None
        self._strategy_name = None

    @property
    def is_running(self):
        if self._process is None:
            return False
        return self._process.poll() is None

    @property
    def current_strategy(self):
        return self._strategy_name if self.is_running else None

    def start(self, cmd, strategy_name="unknown"):
        if self.is_running:
            self.stop()

        cmd_str = " ".join(f'"{c}"' if " " in c else c for c in cmd)

        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        si.wShowWindow = 0

        self._process = subprocess.Popen(
            cmd_str,
            shell=True,
            startupinfo=si,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        self._strategy_name = strategy_name
        return True

    def stop(self):
        if self._process and self.is_running:
            try:
                self._process.terminate()
                try:
                    self._process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self._process.kill()
                    self._process.wait(timeout=3)
            except Exception:
                pass
        self._process = None
        self._strategy_name = None

    def get_pid(self):
        if self.is_running and self._process:
            return self._process.pid
        return None

    def get_status_text(self):
        if self.is_running:
            pid = self.get_pid()
            return f"\u0420\u0430\u0431\u043e\u0442\u0430\u0435\u0442: {self._strategy_name} (PID: {pid})"
        return "\u041e\u0441\u0442\u0430\u043d\u043e\u0432\u043b\u0435\u043d"


_process_manager = ProcessManager()


def get_process_manager():
    return _process_manager
