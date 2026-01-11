import json
import re
from copy import deepcopy
from pathlib import Path
from typing import Any

from utils.enums import (
    FileExtension as Fe,
    TermType as Tt,
    LanguageDataFlags as Ldf,
    GoogleUpdateFrequency as Guf,
    GoogleUpdateSynchronization as Gus,
    MissingTranslationAction as Mta,
    AllowUnloadLanguages as Aul
)
from utils.helpers import (
    escape,
    parse_raw_value,
    InvalidExtensionError
)


class I2Manager:
    def __init__(self):
        self.file_name: str = ""
        self.file_path: Path = Path()
        self.backup: dict[str, Any] = {}
        self.content: dict[str, Any] = {}

    def term_count(self):
        return len(self.content.get("terms", []))

    def get_terms(self):
        return self.content.get("terms", [])

    def is_modified(self):
        return self.content != self.backup

    def make_backup(self):
        self.backup = deepcopy(self.content)

    def get_languages(self):
        return deepcopy(self.content.get("languages", []))

    def get_language(self, code: str):
        return next(
            (lang for lang in self.get_languages() if lang["code"] == code),
            None
        )

    def get_language_by_index(self, index: int):
        lang = self.get_languages()[index]
        return lang["code"], lang["name"]

    def get_displayed_languages(self):
        return [
            f"{lang['name']} [{lang['code']}]" if lang["code"] != lang["name"].lower() else lang["name"]
            for lang in self.get_languages()
        ]

    def get_language_names(self):
        return [
            lang["name"]
            for lang in self.get_languages()
        ]

    def get_language_codes(self):
        return [
            lang["code"]
            for lang in self.get_languages()
        ]

    def update_code_entries(self, lang_code: str, new_code: str):
        if lang_code == new_code:
            return

        for term in self.get_terms():
            translations = term["translations"]
            translations[new_code] = translations.pop(lang_code)
            flags = term["flags"]
            flags[new_code] = flags.pop(lang_code)

    def open_dump_file(self, path: str | Path):
        try:
            if isinstance(path, str):
                path = Path(path)

            with open(path, "r", encoding="utf-8") as f:
                suffix = Fe.parse(path.suffix)
                if suffix is Fe.TXT:
                    content = self.convert_txt_dump(f.readlines())
                elif suffix is Fe.JSON:
                    content = json.loads(f.read())
                else:
                    return "error-invalid-extension"

            terms = content.get("mSource", {}).get("mTerms", {}).get("Array", [])
            langs = content.get("mSource", {}).get("mLanguages", {}).get("Array", [])

            if not terms or not langs:
                return "error-no-terms-language"

            output_content = self.parse_json_dump(content)

            self.file_path = path
            self.file_name = path.stem
            self.content = output_content
            self.make_backup()
            return True
        except (OSError, KeyError, MemoryError, PermissionError) as e:
            return str(e)

    def save_dump_file(self, file_path: str):
        try:
            if isinstance(file_path, str):
                file_path = Path(file_path)

            with open(file_path, "w+", encoding="utf-8") as f:
                suffix = Fe.parse(file_path.suffix)
                if suffix is Fe.TXT:
                    output = self.build_txt_dump()
                elif suffix is Fe.JSON:
                    output = self.build_json_dump()
                else:
                    raise InvalidExtensionError

                self.make_backup()
                f.write(output)
                return True
        except (FileNotFoundError, PermissionError) as e:
            return "error-file-access", {"error": str(e)}
        except TypeError as e:
            return "error-invalid-data", {"error": str(e)}
        except OSError as e:
            return "error-save-failed", {"error": str(e)}
        except InvalidExtensionError:
            return "error-invalid-extension"

    @staticmethod
    def convert_txt_dump(dump_lines: list[str]):
        """Converts UABEA txt dump into JSON one."""
        root = {}
        stack = [(-1, root)]

        i = 0
        while i < len(dump_lines):
            raw = dump_lines[i].rstrip()
            i += 1

            if not raw.strip() or raw.startswith("0 MonoBehaviour Base"):
                continue

            indent = len(raw) - len(raw.lstrip(' '))
            line = raw.strip()

            # find parent by indentation
            while stack and stack[-1][0] >= indent:
                stack.pop()

            parent = stack[-1][1]

            # skip array indices and size lines
            if re.match(r'\[\d+]', line):
                continue
            if "int size" in line:
                continue

            # array container
            if "Array Array" in line:
                arr = []
                if isinstance(parent, dict):
                    parent["Array"] = arr
                stack.append((indent, arr))
                continue

            # parse value
            if "=" in line:
                left, right = line.split("=", 1)
                right = right.strip()
                left = left.strip()

                name = left.split()[-1]
                value = parse_raw_value(right)

                if isinstance(parent, list):
                    parent.append(value)
                else:
                    parent[name] = value
                continue

            # object start (vector, PPtr etc)
            parts = line.split()
            name = parts[-1]

            obj = {}

            if isinstance(parent, list):
                parent.append(obj)
            else:
                parent[name] = obj

            stack.append((indent, obj))

        return root

    def build_txt_dump(self):
        output = []
        try:
            content = self.content

            structure = content["structure"]
            output.append("0 MonoBehaviour Base")

            game_object = structure["m_GameObject"]
            output.append(" 0 PPtr<GameObject> m_GameObject")
            output.append(f"  0 int m_FileID = {game_object['m_FileID']}")
            output.append(f"  0 SInt64 m_PathID = {game_object['m_PathID']}")

            output.append(f" 1 UInt8 m_Enabled = {int(structure['m_Enabled'])}")

            script = structure["m_Script"]
            output.append(" 0 PPtr<MonoScript> m_Script")
            output.append(f"  0 int m_FileID = {script['m_FileID']}")
            output.append(f"  0 SInt64 m_PathID = {script['m_PathID']}")

            output.append(f" 1 string m_Name = \"{structure['m_Name']}\"")

            metadata = content["metadata"]
            output.append(" 0 LanguageSourceData mSource")
            output.append(f"  1 UInt8 UserAgreesToHaveItOnTheScene = {int(metadata['UserAgreesToHaveItOnTheScene'])}")
            output.append(f"  1 UInt8 UserAgreesToHaveItInsideThePluginsFolder = {int(metadata['UserAgreesToHaveItInsideThePluginsFolder'])}")
            output.append(f"  1 UInt8 GoogleLiveSyncIsUptoDate = {int(metadata['GoogleLiveSyncIsUptoDate'])}")

            output.append("  0 TermData mTerms")

            terms = content["terms"]
            languages = content["languages"]

            output.append(f"   1 Array Array ({len(terms)} items)")
            output.append(f"    0 int size = {len(terms)}")

            for i, term in enumerate(terms):
                output.append(f"    [{i}]")
                output.append("     0 TermData data")
                output.append(f"      1 string Term = \"{term['name']}\"")
                output.append(f"      0 int TermType = {Tt.get_value(term['type'])}")
                if term["desc"]:
                    output.append(f"      1 string Description = \"{term['desc']}\"")

                translations = term["translations"]
                output.append("      0 string Languages")
                output.append(f"       1 Array Array ({len(translations)} items)")
                output.append(f"        0 int size = {len(translations)}")

                for t_index, lang in enumerate(languages):
                    translation = escape(translations[lang["code"]])
                    output.append(f"        [{t_index}]")
                    output.append(f"         1 string data = \"{translation}\"")

                flags = term["flags"]
                output.append("      0 vector Flags")
                output.append(f"       1 Array Array ({len(translations)} items)")
                output.append(f"        0 int size = {len(translations)}")

                for f_index, flag in enumerate(flags.values()):
                    output.append(f"        [{f_index}]")
                    output.append(f"         0 UInt8 data = {flag}")

                languages_touch = term["languages_touch"]
                output.append("      0 string Languages_Touch")
                output.append(f"       1 Array Array ({len(languages_touch)} items)")
                output.append(f"        0 int size = {len(languages_touch)}")

                for touch_idx, touch in enumerate(languages_touch):
                    output.append(f"        [{touch_idx}]")
                    output.append(f"         1 string data = \"{touch}\"")

            output.append(f"  1 UInt8 CaseInsensitiveTerms = {int(metadata['CaseInsensitiveTerms'])}")
            output.append(f"  0 int OnMissingTranslation = {Mta.get_value(metadata['OnMissingTranslation'])}")
            output.append(f"  1 string mTerm_AppName = \"{metadata['mTerm_AppName']}\"")

            output.append("  0 LanguageData mLanguages")
            output.append(f"   1 Array Array ({len(languages)} items)")
            output.append(f"    0 int size = {len(languages)}")

            for l_index, lang in enumerate(languages):
                output.append(f"    [{l_index}]")
                output.append("     0 LanguageData data")
                output.append(f"      1 string Name = \"{lang['name']}\"")
                output.append(f"      1 string Code = \"{lang['code']}\"")
                output.append(f"      1 UInt8 Flags = {Ldf.get_value(lang['flags'])}")

            output.append(f"  1 UInt8 IgnoreDeviceLanguage = {int(metadata['IgnoreDeviceLanguage'])}")
            output.append(f"  0 int _AllowUnloadingLanguages = {Aul.get_value(metadata['_AllowUnloadingLanguages'])}")
            output.append(f"  1 string Google_WebServiceURL = \"{metadata['Google_WebServiceURL']}\"")
            output.append(f"  1 string Google_SpreadsheetKey = \"{metadata['Google_SpreadsheetKey']}\"")
            output.append(f"  1 string Google_SpreadsheetName = \"{metadata['Google_SpreadsheetName']}\"")
            output.append(f"  1 string Google_LastUpdatedVersion = \"{metadata['Google_LastUpdatedVersion']}\"")
            output.append(f"  0 int GoogleUpdateFrequency = {Guf.get_value(metadata['GoogleUpdateFrequency'])}")
            output.append(f"  0 int GoogleInEditorCheckFrequency = {Guf.get_value(metadata['GoogleInEditorCheckFrequency'])}")
            output.append(f"  0 int GoogleUpdateSynchronization = {Gus.get_value(metadata['GoogleUpdateSynchronization'])}")
            output.append(f"  0 float GoogleUpdateDelay = {int(metadata['GoogleUpdateDelay'])}")

            assets = metadata.get("Assets", {})["Array"]
            output.append("  0 vector Assets")
            output.append(f"   1 Array Array ({len(assets)} items)")
            output.append(f"    0 int size = {len(assets)}")

            if assets:
                for a_index, asset in enumerate(assets):
                    output.append(f"    [{a_index}]")
                    output.append("     0 PPtr<$Object> data")
                    output.append(f"      0 int m_FileID = {asset['m_FileID']}")
                    output.append(f"      0 SInt64 m_PathID = {asset['m_PathID']}")

        except Exception as e:
            raise e from e
        finally:
            return str("\n".join(output) + "\n")

    @staticmethod
    def parse_json_dump(dump_content: dict):
        result = {
            "structure": {},
            "metadata": {},
            "terms": [],
            "languages": []
        }

        parse_metadata = {
            "UserAgreesToHaveItOnTheScene": bool,
            "UserAgreesToHaveItInsideThePluginsFolder": bool,
            "GoogleLiveSyncIsUptoDate": bool,

            "CaseInsensitiveTerms": bool,
            "OnMissingTranslation": Mta,
            "mTerm_AppName": str,

            "IgnoreDeviceLanguage": bool,
            "_AllowUnloadingLanguages": Aul,
            "Google_WebServiceURL": str,
            "Google_SpreadsheetKey": str,
            "Google_SpreadsheetName": str,
            "Google_LastUpdatedVersion": str,
            "GoogleUpdateFrequency": Guf,
            "GoogleInEditorCheckFrequency": Guf,
            "GoogleUpdateSynchronization": Gus,
            "GoogleUpdateDelay": float,
            "Assets": dict
        }

        for name, items in dump_content.items():
            if name != "mSource":
                result["structure"][name] = items

        for name, items in dump_content["mSource"].items():
            if name in parse_metadata:
                result["metadata"][name] = parse_metadata[name](items)

        language_codes = []
        for lang_dict in dump_content["mSource"]["mLanguages"]["Array"]:
            lang_data = (
                lang_dict["Name"],
                lang_dict["Code"] or lang_dict["Name"].lower(),
                Ldf(lang_dict["Flags"])
            )
            language_codes.append(lang_data[1])
            result["languages"].append({
                "name": lang_data[0],
                "code": lang_data[1],
                "flags": lang_data[2]
            })

        for term in dump_content["mSource"]["mTerms"]["Array"]:
            term_data = (
                term["Term"],
                Tt(term["TermType"]),
                term.get("Description", ""),
                term["Languages_Touch"]["Array"]
            )

            flags = {}
            translations = {}
            if term["Languages"] and term["Flags"]:
                trs = term["Languages"]["Array"]
                fls = term["Flags"]["Array"]
                for idx, (tr, fl) in enumerate(zip(trs, fls)):
                    if idx < len(language_codes):
                        translations[language_codes[idx]] = tr
                        flags[language_codes[idx]] = fl

            result["terms"].append({
                "name": term_data[0],
                "type": term_data[1],
                "desc": term_data[2],
                "translations": translations,
                "flags": flags,
                "languages_touch": term_data[3]
            })

        return result

    def build_json_dump(self):
        output = {}
        try:
            def insert_metadata(parsing_metadata, target):
                metadata = self.content.get("metadata", [])
                for name, type_ in parsing_metadata:
                    if name in metadata:
                        if issubclass(type_, (Aul, Guf, Gus, Mta)):
                            target[name] = type_.get_value(metadata[name])
                        else:
                            target[name] = type_(metadata[name])

            def build_term(t_dict):
                term = {
                    "Term": t_dict["name"],
                    "TermType": Tt.get_value(t_dict["type"]),
                    "Languages": {"Array": []},
                    "Flags": {"Array": list(t_dict["flags"].values())},
                    "Languages_Touch": {"Array": t_dict["languages_touch"]}
                }
                if desc := t_dict.get("desc"):
                    term["Description"] = desc

                for code in self.get_language_codes():
                    term["Languages"]["Array"].append(t_dict["translations"][code])
                return term

            def build_language(l_dict):
                return {
                    "Name": l_dict["name"],
                    "Code": l_dict["code"] if l_dict["code"] != l_dict["name"].lower() else "",
                    "Flags": Ldf.get_value(l_dict["flags"])
                }

            parse_metadata = [
                ("UserAgreesToHaveItOnTheScene", int),
                ("UserAgreesToHaveItInsideThePluginsFolder", int),
                ("GoogleLiveSyncIsUptoDate", int),

                ("CaseInsensitiveTerms", int),
                ("OnMissingTranslation", Mta),
                ("mTerm_AppName", str),

                ("IgnoreDeviceLanguage", int),
                ("_AllowUnloadingLanguages", Aul),
                ("Google_WebServiceURL", str),
                ("Google_SpreadsheetKey", str),
                ("Google_SpreadsheetName", str),
                ("Google_LastUpdatedVersion", str),
                ("GoogleUpdateFrequency", Guf),
                ("GoogleInEditorCheckFrequency", Guf),
                ("GoogleUpdateSynchronization", Gus),
                ("GoogleUpdateDelay", float),
                ("Assets", dict)
            ]

            for key, value in self.content.get("structure", {}).items():
                output[key] = value

            m_source = output.setdefault("mSource", {})

            insert_metadata(parse_metadata[:3], m_source)

            m_source["mTerms"] = {"Array": []}
            for term_dict in self.content.get("terms", []):
                m_source["mTerms"]["Array"].append(
                    build_term(term_dict)
                )

            insert_metadata(parse_metadata[3:6], m_source)

            m_source["mLanguages"] = {"Array": []}
            for lang_dict in self.content.get("languages", []):
                m_source["mLanguages"]["Array"].append(
                    build_language(lang_dict)
                )

            insert_metadata(parse_metadata[6:], m_source)
        except Exception as e:
            return str(e)
        finally:
            return json.dumps(output, ensure_ascii=False, indent=2)

manager = I2Manager()
