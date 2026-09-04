import tkinter as tk
from tkinter import ttk, messagebox

from .config import Settings
from .strategy_builder import get_all_strategies, build_command
from .process_manager import get_process_manager


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("zapret2-discord-youtube")
        self.geometry("560x480")
        self.resizable(False, False)

        self.settings = Settings()
        self.pm = get_process_manager()
        self.strategies = get_all_strategies()

        self._apply_theme()
        self._build_ui()
        self._refresh_status()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _apply_theme(self):
        self.configure(bg="#1e1e2e")
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(".", background="#1e1e2e", foreground="#cdd6f4", font=("Segoe UI", 11))
        style.configure("TFrame", background="#1e1e2e")
        style.configure("TLabel", background="#1e1e2e", foreground="#cdd6f4")
        style.configure("TButton", background="#313244", foreground="#cdd6f4", padding=(14, 8))
        style.map("TButton", background=[("active", "#45475a")])
        style.configure("Start.TButton", background="#a6e3a1", foreground="#1e1e2e", font=("Segoe UI", 13, "bold"), padding=(20, 12))
        style.map("Start.TButton", background=[("active", "#94e2d5")])
        style.configure("Stop.TButton", background="#f38ba8", foreground="#1e1e2e", font=("Segoe UI", 13, "bold"), padding=(20, 12))
        style.map("Stop.TButton", background=[("active", "#eba0ac")])
        style.configure("TCheckbutton", background="#1e1e2e", foreground="#cdd6f4", indicatorbackground="#313244", indicatorsize=18)
        style.map("TCheckbutton", background=[("active", "#1e1e2e")], foreground=[("selected", "#a6e3a1")])
        self.option_add("*TCombobox*Listbox.background", "#313244")
        self.option_add("*TCombobox*Listbox.foreground", "#cdd6f4")
        self.option_add("*TCombobox*Listbox.selectBackground", "#45475a")

    def _build_ui(self):
        container = ttk.Frame(self)
        container.pack(fill=tk.BOTH, expand=True, padx=24, pady=24)

        ttk.Label(container, text="zapret2-discord-youtube", font=("Segoe UI", 18, "bold"), foreground="#89b4fa").pack(pady=(0, 4))
        ttk.Label(container, text="Выберите режим и нажмите Старт", font=("Segoe UI", 11)).pack(pady=(0, 20))

        picker = ttk.Frame(container)
        picker.pack(fill=tk.X, pady=(0, 8))
        ttk.Label(picker, text="Режим:", font=("Segoe UI", 12)).pack(side=tk.LEFT)

        self.combo_var = tk.StringVar()
        self.combo = ttk.Combobox(picker, textvariable=self.combo_var, state="readonly", width=38, font=("Segoe UI", 11))
        self.combo.pack(side=tk.LEFT, padx=(10, 0))
        self.combo.bind("<<ComboboxSelected>>", self._on_select)

        self._prepare_strategies()

        self.desc_var = tk.StringVar(value="")
        self.desc_label = ttk.Label(container, textvariable=self.desc_var, wraplength=480, justify=tk.LEFT, foreground="#a6adc8", font=("Segoe UI", 10))
        self.desc_label.pack(fill=tk.X, pady=(4, 14))
        self._show_desc(self.combo_var.get())

        self.auto_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(container, text="Запуск при старте Windows", variable=self.auto_var).pack(anchor=tk.W, pady=(0, 16))

        btns = ttk.Frame(container)
        btns.pack(fill=tk.X, pady=(0, 14))
        self.start_btn = ttk.Button(btns, text="Старт", style="Start.TButton", command=self._on_start)
        self.start_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))
        self.stop_btn = ttk.Button(btns, text="Стоп", style="Stop.TButton", command=self._on_stop)
        self.stop_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(6, 0))

        self.status_var = tk.StringVar(value="Остановлен")
        ttk.Label(container, textvariable=self.status_var, font=("Segoe UI", 12, "bold")).pack(pady=(0, 4))
        self.log_var = tk.StringVar(value="")
        ttk.Label(container, textvariable=self.log_var, foreground="#a6adc8", font=("Segoe UI", 10), wraplength=480, justify=tk.LEFT).pack(fill=tk.X)

        ttk.Label(container, text="Точная настройка - в файлах config/", foreground="#6c7086", font=("Segoe UI", 9)).pack(side=tk.BOTTOM, pady=(20, 0))

    def _prepare_strategies(self):
        self._name_to_key = {}
        for k, s in self.strategies.items():
            self._name_to_key[s.get("name", k)] = k
        names = list(self._name_to_key.keys())
        self.combo["values"] = names
        if names:
            self.combo_var.set(names[0])

    def _current_key(self):
        return self._name_to_key.get(self.combo_var.get())

    def _show_desc(self, name):
        key = self._name_to_key.get(name)
        if not key:
            return
        s = self.strategies[key]
        text = s.get("description", "")
        color = "#a6adc8"
        if s.get("warning"):
            text = f"Внимание! {s['warning']}\n\n{text}"
            color = "#f9e2af"
        self.desc_var.set(text)
        self.desc_label.configure(foreground=color)

    def _on_select(self, event):
        self._show_desc(self.combo_var.get())

    def _on_start(self):
        key = self._current_key()
        if not key or key not in self.strategies:
            messagebox.showwarning("Внимание", "Сначала выберите режим")
            return
        try:
            cmd = build_command(key, self.strategies[key], self.settings)
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))
            return
        if self.pm.start(cmd, self.strategies[key].get("name", key)):
            self.log_var.set("Обход включен, применяются правила")
        else:
            self.log_var.set("Не удалось запустить")
        self._refresh_status()

    def _on_stop(self):
        if self.pm.is_running:
            self.pm.stop()
            self.log_var.set("Обход выключен")
        self._refresh_status()

    def _refresh_status(self):
        self.status_var.set(self.pm.get_status_text())

    def _on_close(self):
        if self.pm.is_running:
            if messagebox.askyesno("Выход", "Обход работает. Остановить и выйти?"):
                self.pm.stop()
        self.destroy()


def main():
    app = App()
    app.mainloop()
