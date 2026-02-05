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
        self.has_descriptions: bool = False

    def is_modified(self):
        """Check whether the data is modified or not.

        :return: True if modified, False otherwise.
        """
        return self.content != self.backup

    def make_backup(self):
        """Make the backup of the data."""
        self.backup = deepcopy(self.content)

    def get_terms(self):
        """Get the terms' dictionaries list."""
        return self.content.get("terms", [])

    def term_count(self):
        """Get the number of terms."""
        return len(self.get_terms())

    def update_file_info(self, file_path: Path | str):
        """Update stored file path and name from the given path.

        :param file_path: path to the file.
        """
        if isinstance(file_path, str):
            file_path = Path(file_path)

        self.file_path = file_path
        self.file_name = file_path.stem

    def get_languages(self):
        """Get the languages' dictionaries list."""
        return self.content.get("languages", [])

    def get_languages_copy(self):
        """Get the copy of languages' dictionaries list."""
        return deepcopy(self.content.get("languages", []))

    def get_language_index(self, code: str):
        """Get the index of the language given its code."""
        for idx, lang in enumerate(self.get_languages()):
            if lang["code"] == code:
                return idx
        return -1

    def get_displayed_languages(self):
        """Get a list of display names of the languages. E.g. `English [en]`."""
        return [
            f"{lang['name']} [{lang['code']}]" if lang["code"] else lang["name"]
            for lang in self.get_languages()
        ]

    def move_language_entries(self, from_index: int, to_index: int):
        """Move translation and flag entries from one language to another.

        :param from_index: source language index.
        :param to_index: target language index.
        """
        terms = self.get_terms()
        languages = self.get_languages()

        for term in terms:
            translations = term["translations"]
            flags = term["flags"]

            if 0 <= from_index < len(translations):
                translation = translations.pop(from_index)
                translations.insert(to_index, translation)

            if 0 <= from_index < len(flags):
                flag = flags.pop(from_index)
                flags.insert(to_index, flag)

        if 0 <= from_index < len(languages):
            languages.insert(to_index, languages.pop(from_index))

    def add_translation(self, term_index: int, lang_index: int, translation: Any, flags: int):
        """Add the translation and its flag for a given term and language.

        :param term_index: index of the term in the `terms` list.
        :param lang_index: index of the language in the `languages` list.
        :param translation: any value to set.
        :param flags: integer value to set.
        """
        self.set_translation(term_index, lang_index, str(translation))
        self.set_translation_flag(term_index, lang_index, flags)

    def get_translation(self, term_index: int, lang_index: int | None):
        """Get the translation for a given term and language.

        :param term_index: index of the term in the `terms` list.
        :param lang_index: index of the language in the `languages` list.
        """
        terms = self.get_terms()
        if lang_index is not None and 0 <= term_index < len(terms):
            translations = terms[term_index]["translations"]
            if 0 <= lang_index < len(translations):
                return translations[lang_index]
        return ""

    def set_translation(self, term_index: int, lang_index: int, value: str):
        """Set the translation for a given term and language.

        :param term_index: index of the term in the `terms` list.
        :param lang_index: index of the language in the `languages` list.
        :param value: string value to set
        """
        terms = self.get_terms()

        if 0 <= term_index < len(terms):
            translations = terms[term_index]["translations"]
            if 0 <= lang_index < len(translations):
                translations[lang_index] = value
            else:
                while len(translations) <= lang_index:
                    translations.append("")
                translations[lang_index] = value

    def get_translation_flag(self, term_index: int, lang_index: int) -> int:
        """Get the flag for a given term and language.

        :param term_index: index of the term in the `terms` list.
        :param lang_index: index of the language in the `languages` list.
        :return: integer value of the translation flag if exists. Otherwise, -1.
        """
        terms = self.get_terms()
        if 0 <= term_index < len(terms):
            flags = terms[term_index]["flags"]
            if 0 <= lang_index < len(flags):
                return flags[lang_index]
        return -1

    def set_translation_flag(self, term_index: int, lang_index: int, value: int):
        """Set the flag for a given term and language.

        :param term_index: index of the term in the `terms` list.
        :param lang_index: index of the language in the `languages` list.
        :param value: integer value to set.
        """
        terms = self.get_terms()
        if 0 <= term_index < len(terms):
            flags = terms[term_index]["flags"]
            if 0 <= lang_index < len(flags):
                flags[lang_index] = value
            else:
                while len(flags) <= lang_index:
                    flags.append(0)
                flags[lang_index] = value

    def open_dump_file(self, path: str | Path):
        """Open and process the UABEA dump file.

        :param path: path to the file.
        :return: string value of the exception if raised, True otherwise.
        """
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

            self.content = output_content
            self.update_file_info(path)
            self.make_backup()
            return True
        except (OSError, KeyError, MemoryError, PermissionError) as e:
            return str(e)

    def save_dump_file(self, file_path: str | Path):
        """Build and save the UABEA dump file to specified path.

        :param file_path: path to the file to save.
        :return: string value of the exception if raised, True otherwise.
        """
        try:
            if isinstance(file_path, str):
                file_path = Path(file_path)

            suffix = Fe.parse(file_path.suffix)
            if suffix is Fe.TXT:
                output = self.build_txt_dump()
            elif suffix is Fe.JSON:
                output = self.build_json_dump()
            else:
                raise InvalidExtensionError

            with open(file_path, "w+", encoding="utf-8") as f:
                f.write(output)

            self.make_backup()
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
        """Convert the UABEA TXT dump into JSON one.

        :param dump_lines: list of string lines.
        :return: UABEA JSON dump content.
        """
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
        """Build the UABEA TXT dump file.

        :return: UABEA TXT dump data.
        """
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
                output.append(f"      0 int TermType = {Tt[term['type']]}")
                if self.has_descriptions:
                    output.append(f"      1 string Description = \"{term['desc']}\"")

                translations = term["translations"]
                output.append("      0 string Languages")
                output.append(f"       1 Array Array ({len(translations)} items)")
                output.append(f"        0 int size = {len(translations)}")

                for t_index, translation in enumerate(translations):
                    translation = escape(translation)
                    output.append(f"        [{t_index}]")
                    output.append(f"         1 string data = \"{translation}\"")

                flags = term["flags"]
                output.append("      0 vector Flags")
                output.append(f"       1 Array Array ({len(flags)} items)")
                output.append(f"        0 int size = {len(flags)}")

                for f_index, flag in enumerate(flags):
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
            output.append(f"  0 int OnMissingTranslation = {Mta[metadata['OnMissingTranslation']]}")
            output.append(f"  1 string mTerm_AppName = \"{metadata['mTerm_AppName']}\"")

            output.append("  0 LanguageData mLanguages")
            output.append(f"   1 Array Array ({len(languages)} items)")
            output.append(f"    0 int size = {len(languages)}")

            for l_index, lang in enumerate(languages):
                output.append(f"    [{l_index}]")
                output.append("     0 LanguageData data")
                output.append(f"      1 string Name = \"{lang['name']}\"")
                output.append(f"      1 string Code = \"{lang['code']}\"")
                output.append(f"      1 UInt8 Flags = {Ldf[lang['flags']]}")

            output.append(f"  1 UInt8 IgnoreDeviceLanguage = {int(metadata['IgnoreDeviceLanguage'])}")
            output.append(f"  0 int _AllowUnloadingLanguages = {Aul[metadata['_AllowUnloadingLanguages']]}")
            output.append(f"  1 string Google_WebServiceURL = \"{metadata['Google_WebServiceURL']}\"")
            output.append(f"  1 string Google_SpreadsheetKey = \"{metadata['Google_SpreadsheetKey']}\"")
            output.append(f"  1 string Google_SpreadsheetName = \"{metadata['Google_SpreadsheetName']}\"")
            output.append(f"  1 string Google_LastUpdatedVersion = \"{metadata['Google_LastUpdatedVersion']}\"")
            output.append(f"  0 int GoogleUpdateFrequency = {Guf[metadata['GoogleUpdateFrequency']]}")
            output.append(f"  0 int GoogleInEditorCheckFrequency = {Guf[metadata['GoogleInEditorCheckFrequency']]}")
            output.append(f"  0 int GoogleUpdateSynchronization = {Gus[metadata['GoogleUpdateSynchronization']]}")
            output.append(f"  0 float GoogleUpdateDelay = {int(metadata['GoogleUpdateDelay'])}")

            assets = metadata["Assets"]["Array"]
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

    def parse_json_dump(self, dump_content: dict):
        """Parse UABEA JSON dump content into a custom dictionary.

        :param dump_content: UABEA JSON dump content.
        :return: custom data dictionary.
        """
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

        for lang_dict in dump_content["mSource"]["mLanguages"]["Array"]:
            result["languages"].append({
                "name": lang_dict["Name"],
                "code": lang_dict["Code"],
                "flags": Ldf(lang_dict["Flags"])
            })

        self.has_descriptions = any(term.get("Description", None) for term in dump_content["mSource"]["mTerms"]["Array"])

        for term in dump_content["mSource"]["mTerms"]["Array"]:
            term_data = (
                term["Term"],
                Tt(term["TermType"]),
                term.get("Description", ""),
                term["Languages_Touch"]["Array"]
            )

            flags = []
            translations = []

            if term["Languages"] and term["Flags"]:
                t_languages = term["Languages"]["Array"]
                t_flags = term["Flags"]["Array"]

                for idx, (tr, fl) in enumerate(zip(t_languages, t_flags)):
                    if idx < len(t_languages) and idx < len(t_flags):
                        translations.append(tr)
                        flags.append(fl)

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
        """Build the UABEA JSON dump.

        Includes `insert_metadata` function to be able to put specified metadata entries easier.
        As well as `build_term` and `build_language` functions.

        :return: JSON formatted string.
        """
        output = {}
        try:
            def insert_metadata(parsing_metadata, target):
                metadata = self.content.get("metadata", [])
                for name, type_ in parsing_metadata:
                    if name in metadata:
                        if issubclass(type_, (Aul, Guf, Gus, Mta)):
                            target[name] = type_[metadata[name]]
                        else:
                            target[name] = type_(metadata[name])

            def build_term(t_dict):
                term = {
                    "Term": t_dict["name"],
                    "TermType": Tt[t_dict["type"]]
                }

                if self.has_descriptions:
                    term["Description"] = t_dict["desc"]

                term |= {
                    "Languages": {"Array": t_dict["translations"]},
                    "Flags": {"Array": t_dict["flags"]},
                    "Languages_Touch": {"Array": t_dict["languages_touch"]}
                }

                return term

            def build_language(l_dict):
                return {
                    "Name": l_dict["name"],
                    "Code": l_dict["code"],
                    "Flags": Ldf[l_dict["flags"]]
                }

            build_metadata = [
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

            insert_metadata(build_metadata[:3], m_source)

            m_source["mTerms"] = {"Array": []}
            for term_dict in self.content.get("terms", []):
                m_source["mTerms"]["Array"].append(
                    build_term(term_dict)
                )

            insert_metadata(build_metadata[3:6], m_source)

            m_source["mLanguages"] = {"Array": []}
            for lang_dict in self.content.get("languages", []):
                m_source["mLanguages"]["Array"].append(
                    build_language(lang_dict)
                )

            insert_metadata(build_metadata[6:], m_source)
        except Exception as e:
            return str(e)
        finally:
            return json.dumps(output, ensure_ascii=False, indent=2)


manager = I2Manager()
