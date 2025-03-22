from datetime import datetime
import os
import chardet

def detect_encoding(filename):
    with open(filename, 'rb') as file:
        raw_data = file.read()
    result = chardet.detect(raw_data)
    print(f"[ENCODING '{result['encoding']}' DETECTED] Confidence: {result['confidence']*100:.1f}%")
    return result['encoding']

def write_to_file(filename, text):
    with open(filename, 'w', encoding="utf-8") as file:
        file.write(text)

def load_from_file(filename, encoding="utf-8"):
    with open(filename, 'r', encoding=encoding, errors='ignore') as file:
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