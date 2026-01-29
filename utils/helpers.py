import string
import sys
from pathlib import Path

from utils.enums import LanguageDataFlags as Ldf


class InvalidExtensionError(Exception): ...


def pathfind(relative: str):
    if getattr(sys, "frozen", False):
        base = Path(sys.executable).parent
    else:
        base = Path(__file__).parent.parent

    return str(base / relative)


def check_language(name: str, code: str, flags: Ldf, langs: dict | list):
    restricted_fields = ["key", "type", "desc"]

    if not name or not code or not flags:
        return "warning", "warning-invalid-language"

    if name.lower() in restricted_fields or code.lower() in restricted_fields:
        return "warning", "warning-reserved-names"

    if name in langs or code in langs:
        return "warning", ("warning-language-exists", {"language": f"{name} [{code}]"})

    return None, None


def validate_lang_code(code: str):
    valid_code = "".join(char for char in code if char in string.ascii_letters or char == "-")

    if valid_code.count("-") > 1:
        parts = valid_code.split("-", 1)
        valid_code = parts[0] + "-" + parts[1].replace("-", "")

    return valid_code


def normalise(value: str | None):
    if not value:
        return ""

    value = value.replace("\r\n", "\n").replace("\r", "\n")
    return value


def escape(s: str):
    if not s:
        return ""

    replacements = {
        "\\": "\\\\",  # backslash
        "\n": "\\n",  # new line
        "\r": "\\r",  # carriage return
    }

    for actual, escaped in replacements.items():
        s = s.replace(actual, escaped)

    return s


def unescape(s: str):
    if not s:
        return ""

    replacements = {
        "\\r": "\r",  # carriage return
        "\\n": "\n",  # new line
        "\\\\": "\\"  # backslash
    }

    for escaped, actual in replacements.items():
        s = s.replace(escaped, actual)

    return s


def parse_raw_value(value: str):
    value = value.strip()

    if value.lower() == "true":
        return True

    elif value.lower() == "false":
        return False

    elif value.startswith('"') and value.endswith('"'):
        return unescape(value[1:-1])

    elif value.isdigit() or (value.startswith('-') and value[1:].isdigit()):
        return int(value)

    try:
        return float(value)
    except (ValueError, TypeError):
        return value
