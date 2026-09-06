import os
import shutil
import subprocess
import sys

NAME = "zapret2-discord-youtube"
VENV = ".venv"
PYTHON = os.path.join(VENV, "Scripts", "python.exe")
PIP = os.path.join(VENV, "Scripts", "pip.exe")

# 1. venv
if not os.path.exists(VENV):
    subprocess.run([sys.executable, "-m", "venv", VENV], check=True)

# 2. Зависимости
subprocess.run([PIP, "install", "-r", "requirements.txt"], check=True)

# 3. Сборка
subprocess.run([
    PYTHON, "-m", "PyInstaller",
    "--noconfirm", "--onefile", "--windowed", "--uac-admin",
    "--name", NAME,
    "--collect-all", "customtkinter",
    "--clean", "run.py"
], check=True)

# 4. Результат
APP = os.path.join("dist", NAME)
shutil.rmtree(APP, ignore_errors=True)
os.makedirs(APP)

shutil.copy2(os.path.join("dist", NAME + ".exe"), APP)
shutil.copytree("config", os.path.join(APP, "config"), dirs_exist_ok=True)
shutil.copytree("lists", os.path.join(APP, "lists"), dirs_exist_ok=True)
shutil.copytree("blobs", os.path.join(APP, "blobs"), dirs_exist_ok=True)
shutil.copytree("zapret2", os.path.join(APP, "zapret2"), dirs_exist_ok=True)
shutil.copy2("README.md", APP)
shutil.copy2("LICENSE", APP)

# 5. Очистка
os.remove(os.path.join("dist", NAME + ".exe"))
if os.path.exists(NAME + ".spec"):
    os.remove(NAME + ".spec")
shutil.rmtree("build", ignore_errors=True)

print("Готово.")
