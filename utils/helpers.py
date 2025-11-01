from pathlib import Path
from utils.enums import LanguageDataFlags as LDF

def pathfind(relative:str):
    try:
        base = Path(__file__).parent.parent
    except Exception:
        base = Path.cwd()

    final = str(base / relative)
    return final

def check_language(name:str, code:str,flags:LDF, langs:dict|list):
    restricted_fields = ["key", "type", "desc"]

    if not name or not code or not flags:
        return ("warning", "warning-invalid-language")

    if name.lower() in restricted_fields or code.lower() in restricted_fields:
        return ("warning", "warning-reserved-names")

    if name in langs or code in langs:
        return ("warning", ("warning-language-exists", {"language": f"{name} [{code}]"}))

    return (None, None)