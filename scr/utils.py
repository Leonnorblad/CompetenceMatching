from datetime import datetime
import os

def write_to_file(filename, text):
    with open(filename, 'w') as file:
        file.write(text)

def load_from_file(filename):
    with open(filename, 'r', encoding='utf-8') as file:
        return file.read()

def YYYYMMDD_to_unix(date: str) -> int:
    try:
        dt = datetime.strptime(date, "%Y-%m-%d")
        return int(dt.timestamp())
    except:
        return date


def paste_line():
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

def paste_double_line():
    print("═══════════════════════════════════════════════════════════════════════════════")

def clear_console():
    # for Windows
    if os.name == 'nt':
        os.system('cls')
    # for macOS and Linux
    else:
        os.system('clear')