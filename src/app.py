import functools
import json
import re
import sys
import threading
import time
import tkinter as tk
import urllib.request
import webbrowser
import winreg
from tkinter import messagebox

import customtkinter as ctk

from .config import Settings
from .strategy_builder import get_all_strategies, build_command
from .process_manager import get_process_manager
from .version import VERSION

BG = "#1e1e2e"
PANEL = "#181825"
CARD = "#313244"
HOVER = "#45475a"
TEXT = "#cdd6f4"
MUTED = "#a6adc8"
ACCENT = "#89b4fa"
GREEN = "#a6e3a1"
RED = "#f38ba8"
WARN = "#f9e2af"

RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
RUN_VALUE = "zapret2-discord-youtube"
GITHUB_URL = "https://github.com/darkfated/zapret2-discord-youtube"
GITHUB_RELEASES_URL = GITHUB_URL + "/releases/latest"
GITHUB_API_LATEST = "https://api.github.com/repos/darkfated/zapret2-discord-youtube/releases/latest"

_VERSION_RE = re.compile(r"(\d+)\.(\d+)\.(\d+)")


def parse_version(text):
    match = _VERSION_RE.search(text or "")
    return tuple(int(part) for part in match.groups()) if match else None


def is_autostart_enabled():
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as key:
            value, _ = winreg.QueryValueEx(key, RUN_VALUE)
        return value.strip('"') == sys.executable
    except (FileNotFoundError, OSError):
        return False


def set_autostart(enabled):
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as key:
        if enabled:
            winreg.SetValueEx(key, RUN_VALUE, 0, winreg.REG_SZ, f'"{sys.executable}"')
        else:
            try:
                winreg.DeleteValue(key, RUN_VALUE)
            except FileNotFoundError:
                pass


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("zapret2-discord-youtube")
        self.geometry("760x520")
        self.resizable(False, False)

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        self.configure(fg_color=BG)

        self.settings = Settings()
        self.pm = get_process_manager()
        self.strategies = get_all_strategies()

        self._name_to_key = {}
        self._row_widgets = {}
        self._selected_key = None

        self._build_ui()
        if self._name_to_key:
            self._on_pick(next(iter(self.strategies)))
        self._refresh_status()

        self._update_checked = False
        self._latest_version = None
        self._poll_status()
        self._check_updates()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self):
        sidebar = ctk.CTkFrame(self, width=210, fg_color=PANEL, corner_radius=0)
        sidebar.pack(side=tk.LEFT, fill=tk.Y)
        sidebar.pack_propagate(False)

        ctk.CTkLabel(
            sidebar, text="Режим:", font=ctk.CTkFont("Segoe UI", 13, weight="bold"), text_color=ACCENT
        ).pack(anchor=tk.W, padx=16, pady=(18, 10))

        list_frame = ctk.CTkScrollableFrame(sidebar, fg_color=PANEL, scrollbar_button_color=CARD, scrollbar_button_hover_color=HOVER)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=(8, 4), pady=(0, 14))

        for key, s in self.strategies.items():
            name = s.get("name", key)
            self._name_to_key[name] = key
            row = ctk.CTkButton(
                list_frame,
                text=name,
                font=ctk.CTkFont("Segoe UI", 12),
                anchor="w",
                height=34,
                corner_radius=6,
                fg_color="transparent",
                hover_color=HOVER,
                text_color=TEXT,
                command=functools.partial(self._on_pick, key),
            )
            row.pack(fill=tk.X, pady=1)
            self._row_widgets[key] = row

        main = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        main.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=28, pady=24)

        ctk.CTkLabel(
            main, text="zapret2-discord-youtube",
            font=ctk.CTkFont("Segoe UI", 18, weight="bold"), text_color=ACCENT,
        ).pack(anchor=tk.W)
        ctk.CTkLabel(
            main, text="Выберите режим и нажмите Старт",
            font=ctk.CTkFont("Segoe UI", 11), text_color=MUTED,
        ).pack(anchor=tk.W, pady=(2, 18))

        self.desc_label = ctk.CTkLabel(
            main, text="", wraplength=440, justify=tk.LEFT,
            font=ctk.CTkFont("Segoe UI", 11), text_color=MUTED,
        )
        self.desc_label.pack(anchor=tk.W, fill=tk.X, pady=(0, 16))

        self.auto_var = tk.BooleanVar(value=is_autostart_enabled())
        self.auto_check = ctk.CTkCheckBox(
            main, text="Запуск при старте Windows", variable=self.auto_var,
            font=ctk.CTkFont("Segoe UI", 12), fg_color=ACCENT, hover_color=ACCENT,
            checkbox_width=20, checkbox_height=20, command=self._on_toggle_autostart,
        )
        self.auto_check.pack(anchor=tk.W, pady=(0, 16))

        btns = ctk.CTkFrame(main, fg_color="transparent")
        btns.pack(fill=tk.X, pady=(0, 14))
        self.start_btn = ctk.CTkButton(
            btns, text="Старт", fg_color=GREEN, hover_color="#94e2d5", text_color="#1e1e2e",
            font=ctk.CTkFont("Segoe UI", 13, weight="bold"), height=42, corner_radius=8,
            command=self._on_start,
        )
        self.start_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))
        self.stop_btn = ctk.CTkButton(
            btns, text="Стоп", fg_color=RED, hover_color="#eba0ac", text_color="#1e1e2e",
            font=ctk.CTkFont("Segoe UI", 13, weight="bold"), height=42, corner_radius=8,
            command=self._on_stop,
        )
        self.stop_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(6, 0))

        self.status_label = ctk.CTkLabel(
            main, text="", font=ctk.CTkFont("Segoe UI", 12, weight="bold"), text_color=TEXT,
        )
        self.status_label.pack(anchor=tk.W, pady=(0, 4))
        self.info_label = ctk.CTkLabel(
            main, text="", font=ctk.CTkFont("Segoe UI", 10), text_color=MUTED,
        )
        self.info_label.pack(anchor=tk.W, pady=(0, 4))

        self.update_label = ctk.CTkLabel(
            main, text="", font=ctk.CTkFont("Segoe UI", 10, weight="bold"),
            text_color=GREEN, cursor="hand2", height=18,
        )
        self.update_label.pack(anchor=tk.W, pady=(0, 4))
        self.update_label.bind("<Button-1>", lambda e: webbrowser.open(GITHUB_RELEASES_URL))

        footer = ctk.CTkFrame(main, fg_color="transparent")
        footer.pack(side=tk.BOTTOM, fill=tk.X, pady=(20, 0))
        ctk.CTkLabel(
            footer, text=f"Полная настройка - в папке config •  v{VERSION}",
            font=ctk.CTkFont("Segoe UI", 11), text_color="#6c7086",
        ).pack(side=tk.LEFT)
        github_link = ctk.CTkLabel(
            footer, text="darkfated/zapret2-discord-youtube",
            font=ctk.CTkFont("Segoe UI", 11), text_color=ACCENT, cursor="hand2",
        )
        github_link.pack(side=tk.RIGHT)
        github_link.bind("<Button-1>", lambda e: webbrowser.open(GITHUB_URL))

    def _display_name(self, key):
        return self.strategies[key].get("name", key)

    def _on_pick(self, key):
        if self.pm.is_running and self.pm.current_strategy != self._display_name(key):
            self.pm.stop()
            time.sleep(0.5)
            self._start(key)
            self.info_label.configure(text=f"Переключён на {self._display_name(key)}. Работает")
        self._select(key)

    def _select(self, key):
        desc = self.strategies[key].get("description", "")
        color = MUTED
        if self.strategies[key].get("warning"):
            desc = f"Внимание! {self.strategies[key]['warning']}\n\n{desc}"
            color = WARN
        self.desc_label.configure(text=desc, text_color=color)
        self._selected_key = key
        self._paint_rows()
        self._refresh_status()

    def _start(self, key):
        try:
            cmd = build_command(key, self.strategies[key], self.settings)
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))
            return
        self.pm.start(cmd, self.strategies[key].get("name", key))
        self._paint_rows()
        self._refresh_status()

    def _on_start(self):
        if not self._selected_key:
            messagebox.showwarning("Внимание", "Сначала выберите режим")
            return
        self.info_label.configure(text="")
        self._start(self._selected_key)

    def _on_stop(self):
        if self.pm.is_running:
            self.pm.stop()
            self.info_label.configure(text="")
            self._paint_rows()
            self._refresh_status()

    def _on_toggle_autostart(self):
        set_autostart(self.auto_var.get())

    def _paint_rows(self):
        running = self.pm.current_strategy
        for key, row in self._row_widgets.items():
            if running == self._display_name(key):
                row.configure(fg_color=GREEN, text_color="#1e1e2e", hover_color=GREEN)
            elif self._selected_key == key:
                row.configure(fg_color=CARD, text_color=TEXT, hover_color=HOVER)
            else:
                row.configure(fg_color="transparent", text_color=TEXT, hover_color=HOVER)

    def _refresh_status(self):
        running = self.pm.is_running
        self.status_label.configure(text=self.pm.get_status_text())
        if running:
            self.start_btn.configure(state="disabled", fg_color="#45475a", text_color="#7f849c")
            self.stop_btn.configure(state="normal", fg_color=RED, hover_color="#eba0ac", text_color="#1e1e2e")
        else:
            self.start_btn.configure(state="normal", fg_color=GREEN, hover_color="#94e2d5", text_color="#1e1e2e")
            self.stop_btn.configure(state="disabled", fg_color="#45475a", text_color="#7f849c")

    def _poll_status(self):
        self._refresh_status()
        if self._update_checked:
            self._update_checked = False
            self._apply_update_check()
        running = self.pm.current_strategy
        if running and self._name_to_key.get(running) != self._selected_key:
            self._selected_key = self._name_to_key.get(running, self._selected_key)
            self._paint_rows()
        self.after(1000, self._poll_status)

    def _check_updates(self):
        def _worker():
            latest = None
            try:
                req = urllib.request.Request(
                    GITHUB_API_LATEST, headers={"User-Agent": "zapret2-discord-youtube"}
                )
                with urllib.request.urlopen(req, timeout=8) as response:
                    data = json.load(response)
                version = parse_version(data.get("tag_name") or data.get("name"))
                if version:
                    latest = version
            except Exception:
                latest = None
            self._latest_version = latest
            self._update_checked = True

        threading.Thread(target=_worker, daemon=True).start()

    def _apply_update_check(self):
        current = parse_version(VERSION)
        latest = self._latest_version
        if current and latest and latest > current:
            text = "Доступна новая версия {0} - нажмите, чтобы скачать".format(
                ".".join(str(part) for part in latest)
            )
            self.update_label.configure(text=text)

    def _on_close(self):
        if self.pm.is_running:
            if messagebox.askyesno("Выход", "Обход работает. Остановить и выйти?"):
                self.pm.stop()
        self.destroy()


def main():
    app = App()
    app.mainloop()
