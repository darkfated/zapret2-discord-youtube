from pathlib import Path
from .config import LISTS_DIR


class ListManager:
    def __init__(self):
        self._ensure_user_files()

    def _ensure_user_files(self):
        for name in ["domains-general-user.txt", "domains-exclude-user.txt", "ipset-exclude-user.txt"]:
            p = LISTS_DIR / name
            if not p.exists():
                p.touch()

    def read_domains(self, list_type):
        mapping = {
            "general": "domains-general.txt",
            "general-user": "domains-general-user.txt",
            "google": "domains-google.txt",
            "exclude": "domains-exclude.txt",
            "exclude-user": "domains-exclude-user.txt",
        }
        fname = mapping.get(list_type, list_type)
        p = LISTS_DIR / fname
        if p.exists():
            return p.read_text(encoding="utf-8").strip().splitlines()
        return []

    def write_domains(self, list_type, domains):
        mapping = {
            "general": "domains-general.txt",
            "general-user": "domains-general-user.txt",
            "google": "domains-google.txt",
            "exclude": "domains-exclude.txt",
            "exclude-user": "domains-exclude-user.txt",
        }
        fname = mapping.get(list_type, list_type)
        p = LISTS_DIR / fname
        p.write_text("\n".join(domains) + "\n", encoding="utf-8")

    def read_ipset(self, list_type):
        mapping = {
            "all": "ipset-all.txt",
            "exclude": "ipset-exclude.txt",
            "exclude-user": "ipset-exclude-user.txt",
        }
        fname = mapping.get(list_type, list_type)
        p = LISTS_DIR / fname
        if p.exists():
            return p.read_text(encoding="utf-8").strip().splitlines()
        return []

    def write_ipset(self, list_type, entries):
        mapping = {
            "all": "ipset-all.txt",
            "exclude": "ipset-exclude.txt",
            "exclude-user": "ipset-exclude-user.txt",
        }
        fname = mapping.get(list_type, list_type)
        p = LISTS_DIR / fname
        p.write_text("\n".join(entries) + "\n", encoding="utf-8")

    def add_domain(self, list_type, domain):
        domains = self.read_domains(list_type)
        if domain not in domains:
            domains.append(domain)
            self.write_domains(list_type, domains)
            return True
        return False

    def remove_domain(self, list_type, domain):
        domains = self.read_domains(list_type)
        if domain in domains:
            domains.remove(domain)
            self.write_domains(list_type, domains)
            return True
        return False

    def add_ipset(self, list_type, entry):
        entries = self.read_ipset(list_type)
        if entry not in entries:
            entries.append(entry)
            self.write_ipset(list_type, entries)
            return True
        return False

    def remove_ipset(self, list_type, entry):
        entries = self.read_ipset(list_type)
        if entry in entries:
            entries.remove(entry)
            self.write_ipset(list_type, entries)
            return True
        return False
