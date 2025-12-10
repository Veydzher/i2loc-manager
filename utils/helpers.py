import sys
from pathlib import Path
from utils.enums import LanguageDataFlags as LDF

def pathfind(relative: str):
    if getattr(sys, "frozen", False):
        base = Path(sys.executable).parent
        data_folder = base / "data"
        if data_folder.exists() and data_folder.is_dir():
            base = data_folder
    else:
        base = Path(__file__).parent.parent

    return str(base / relative)

def check_language(name: str, code: str, flags: LDF, langs: dict | list):
    restricted_fields = ["key", "type", "desc"]

    if not name or not code or not flags:
        return "warning", "warning-invalid-language"

    if name.lower() in restricted_fields or code.lower() in restricted_fields:
        return "warning", "warning-reserved-names"

    if name in langs or code in langs:
        return "warning", ("warning-language-exists", {"language": f"{name} [{code}]"})

    return None, None

def normalise(value: str | None):
    if value is None:
        return ""

    value = value.replace("\r\n", "\n").replace("\r", "\n")
    return value

def escape(s: str):
    replacements = {
        "\\": "\\\\",   # backslash
        "\n": "\\n",    # new line
        "\r": "\\r",    # carriage return
    }

    for actual, escaped in replacements.items():
        s = s.replace(actual, escaped)

    return s

def unescape(s: str):
    replacements = {
        "\\r": "\r",    # carriage return
        "\\n": "\n",    # new line
        "\\\\": "\\"    # backslash
    }

    for escaped, actual in replacements.items():
        s = s.replace(escaped, actual)

    return s
