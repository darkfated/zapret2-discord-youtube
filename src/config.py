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
    DEFAULTS = {
        "game_filter": "tcp+udp",
        "ipset_mode": "loaded",
        "auto_update_check": True,
        "dns_over_https": True,
        "language": "ru",
        "wf_parts": [
            "windivert_part.discord_media.txt",
            "windivert_part.stun.txt",
            "windivert_part.wireguard.txt",
            "windivert_part.quic_initial_ietf.txt",
        ],
        "wf_tcp": "80,443,2053,2083,2087,2096,8443",
        "wf_udp": "443,19294-19344,50000-50100",
        "game_filter_tcp": "1024-65535",
        "game_filter_udp": "1024-65535",
    }

    def __init__(self):
        self._path = CONFIG_DIR / "settings.yaml"
        self._data = dict(self.DEFAULTS)
        if self._path.exists():
            loaded = load_yaml(self._path)
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
    def game_filter_tcp(self):
        mode = self._data["game_filter"]
        if mode in ("tcp+udp", "tcp"):
            return self._data["game_filter_tcp"]
        return ""

    @property
    def game_filter_udp(self):
        mode = self._data["game_filter"]
        if mode in ("tcp+udp", "udp"):
            return self._data["game_filter_udp"]
        return ""

    def wf_tcp_full(self):
        parts = [self._data["wf_tcp"]]
        gft = self.game_filter_tcp
        if gft:
            parts.append(gft)
        return ",".join(parts)

    def wf_udp_full(self):
        parts = [self._data["wf_udp"]]
        gfu = self.game_filter_udp
        if gfu:
            parts.append(gfu)
        return ",".join(parts)
