import os
import subprocess
from pathlib import Path
from parent_login import ParentLogin

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)
ID_FILE = DATA_DIR / "parent_id.txt"


def get_saved_parent_id():
    if ID_FILE.exists():
        return ID_FILE.read_text().strip()
    return None


def save_parent_id(parent_id):
    ID_FILE.write_text(parent_id)


if __name__ == "__main__":
    parent_id = get_saved_parent_id()

    if parent_id:
        print(f"Login previo detectado: {parent_id}")
    else:
        login = ParentLogin()
        parent_id = login.run()
        if parent_id:
            save_parent_id(parent_id)
            print(f"Login exitoso para: {parent_id}")
        else:
            print("Login no realizado. Cerrando programa.")
            exit()

    # Lanzar keylogger en proceso separado
    subprocess.Popen(["python3", "keylogger.py"])
