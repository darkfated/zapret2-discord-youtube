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

        cmdline = subprocess.list2cmdline(cmd)

        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        si.wShowWindow = 0

        self._process = subprocess.Popen(
            cmdline,
            shell=False,
            startupinfo=si,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        self._strategy_name = strategy_name
        return True

    def stop(self):
        if self._process and self.is_running:
            self._kill(self._process)
        self._process = None
        self._strategy_name = None

    def _kill(self, proc):
        try:
            taskkill = subprocess.Popen(
                ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            try:
                taskkill.wait(timeout=5)
            except subprocess.TimeoutExpired:
                try:
                    taskkill.kill()
                except Exception:
                    pass
            try:
                proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                proc.kill()
                try:
                    proc.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    pass
        except Exception:
            pass

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
