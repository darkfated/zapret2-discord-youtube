import os
import sys
import yaml
from pathlib import Path


def _runtime_dir():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


BASE_DIR = _runtime_dir()
CONFIG_DIR = BASE_DIR / "config"
LISTS_DIR = BASE_DIR / "lists"
BLOBS_DIR = BASE_DIR / "blobs"
ZAPRET_DIR = BASE_DIR / "zapret2"


def load_yaml(path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def save_yaml(path, data):
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True)


class BlobMap:
    def __init__(self):
        self._map = load_yaml(CONFIG_DIR / "blobs.yaml")["blobs"]

    def resolve(self, name):
        return self._map.get(name, name)

    def path(self, name):
        fname = self.resolve(name)
        p = BLOBS_DIR / fname
        return str(p) if p.exists() else fname

    def all_names(self):
        return list(self._map.keys())


class Settings:
    def __init__(self):
        self._path = CONFIG_DIR / "settings.yaml"
        self._data = {}
        loaded = load_yaml(self._path) if self._path.exists() else {}
        if loaded:
            self._data.update(loaded)

    def get(self, key, default=None):
        return self._data.get(key, default)

    def set(self, key, value):
        self._data[key] = value
        self._save()

    def _save(self):
        save_yaml(self._path, self._data)

    @property
    def game_filter_mode(self):
        return self._data.get("game_filter", "off")

    @property
    def game_filter_tcp(self):
        mode = self.game_filter_mode
        if mode in ("tcp+udp", "tcp"):
            return self._data.get("game_filter_tcp", "12")
        return "12"

    @property
    def game_filter_udp(self):
        mode = self.game_filter_mode
        if mode in ("tcp+udp", "udp"):
            return self._data.get("game_filter_udp", "12")
        return "12"

    def wf_tcp_full(self):
        parts = [self._data["wf_tcp"]]
        mode = self.game_filter_mode
        if mode in ("tcp+udp", "tcp") and self._data.get("game_filter_tcp"):
            parts.append(self._data["game_filter_tcp"])
        return ",".join(parts)

    def wf_udp_full(self):
        parts = [self._data["wf_udp"]]
        mode = self.game_filter_mode
        if mode in ("tcp+udp", "udp") and self._data.get("game_filter_udp"):
            parts.append(self._data["game_filter_udp"])
        return ",".join(parts)
