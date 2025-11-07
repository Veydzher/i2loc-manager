import os
import re
import json
from copy import deepcopy
from utils.exceptions import ParsingTxtError
from utils.enums import (
    FileExts as FE,
    TermType as TT,
    LanguageDataFlags as LDF,
    GoogleUpdateFrequency as GUF,
    GoogleUpdateSynchronization as GUS,
    MissingTranslationAction as MTA,
    AllowUnloadLanguages as AUL
)

class I2Manager:
    def __init__(self, main_window):
        self.mw = main_window

        self.backup = {}
        self.content = {}
        self.filename = ""
        self.filepath = ""

    def term_count(self):
        return len(self.content.get("terms", []))

    def get_terms(self):
        return self.content.get("terms", [])

    def get_language(self, code:str):
        return next(
            (lang for lang in self.get_languages() if lang["code"] == code),
            None
        )

    def get_language_from_text(self, text: str):
        if "[" in text and "]" in text:
            name, code = text.split("[", 1)
            return code.strip("]"), name.strip()

        return text.lower().strip(), text.strip()

    def get_languages(self, option=""):
        content_langs = self.content.get("languages", [])
        languages = []

        match option:
            case "names":
                for lang in content_langs:
                    languages.append(lang["name"])

            case "codes":
                for lang in content_langs:
                    languages.append(lang["code"])

            case "displayed":
                for lang in content_langs:
                    if lang["code"] != lang["name"].lower():
                        item = f"{lang["name"]} [{lang["code"]}]"
                    else:
                        item = lang["name"]

                    languages.append(item)

            case _:
                languages = deepcopy(content_langs)

        return languages

    def escape(self, s: str):
        replacements = {
            "\\": "\\\\",   # backslash
            "\n": "\\n",    # new line
            "\r": "\\r",    # carriage return
        }

        for actual, escaped in replacements.items():
            s = s.replace(actual, escaped)

        return s

    def unescape(self, s: str):
        replacements = {
            "\\r": "\r",    # carriage return
            "\\n": "\n",    # new line
            "\\\\": "\\"    # backslash
        }

        for escaped, actual in replacements.items():
            s = s.replace(escaped, actual)

        return s

    def process_dump_file(self, path: str):
        # Add a structure check rather than terms/languages arrays one
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
                name = os.path.splitext(os.path.basename(path))[0]
                extension = os.path.splitext(path)[1].lower()

            if extension == FE.TXT.value:
                term_pattern = r"\[\d+\]\s+.*TermData\s+data"
                lang_pattern = r"\[\d+\]\s+.*LanguageData\s+data"
                terms = len(re.findall(term_pattern, content))
                langs = len(re.findall(lang_pattern, content))

                if not terms or not langs:
                    return "error-no-terms-language"

                output_content = self.parse_txt_dump(content)

            elif extension == FE.JSON.value:
                content = json.loads(content)
                terms = content.get("mSource", {}).get("mTerms", {}).get("Array", [])
                langs = content.get("mSource", {}).get("mLanguages", {}).get("Array", [])

                if not terms or not langs:
                    return "error-no-terms-language"

                output_content = self.parse_json_dump(content)

            else:
                return "error-invalid-extension"

            self.filename = name
            self.filepath = path
            self.content = output_content
            self.backup = deepcopy(self.content)
            return True
        except (OSError, KeyError, MemoryError, PermissionError) as e:
            return str(e)
        except ParsingTxtError as e:
            return ("error-parsing-txt", {"error": e.args[0]})

    def parse_txt_dump(self, dump_content):
        result = {
            "structure": {"import": FE.TXT.name},
            "languages": [],
            "metadata": {},
            "terms": []
        }

        structure_patterns = {
            "m_GameObject": (int, None, r"PPtr<GameObject>\s+m_GameObject\s+.*int m_FileID\s*=\s*(\d+)\s+.*SInt64\s+m_PathID\s*=\s*(\d+)"),
            "m_Enabled": (int, bool, r"UInt8\s+m_Enabled\s*=\s*(\d+)"),
            "m_Script": (int, None, r"PPtr<MonoScript>\s+m_Script\s+.*int\s+m_FileID\s*=\s*(\d+)\s+.*SInt64\s+m_PathID\s*=\s*(\d+)"),
            "m_Name": (str, None, r"string\s+m_Name\s*=\s*\"(.*)\"")
        }

        patterns = {
            "languages": r"string\s+Name\s*=\s*\"(.*?)\"\s+.*string\s+Code\s*=\s*\"(.*?)\"\s+.*UInt8\s+Flags\s*=\s*(\d+)",

            "term_name": r"Term\s*=\s*\"(.*)\"",
            "term_type": r"TermType\s*=\s*(\d+)",
            "term_desc": r"Description\s*=\s*\"(.*)\"",
            "langs_section": r"Languages.*?size\s*=\s*(\d+)(.*?)0\s+string\s+Languages_Touch",
            "langs_touch": r"string\s+Languages_Touch\s+.*Array\s+Array\s+\((\d+)\s+items\)\s+.*int\s+size\s*=\s*(\d+)",

            "translation": r"string\s+data\s*=\s*\"(.*)\"",
            "flag": r"UInt8\s+data\s*=\s*(\d+)",

            "assets_block": r"vector\s+Assets\s*.*Array\s+Array\s+\((\d+)\s*items\)\s*.*size\s*=\s*\d+([\s\S]*?)(?=\n\d*\n|\Z)",
            "assets_item": r"\[\d+\][\s\S]*?m_FileID\s*=\s*(\d+)[\s\S]*?m_PathID\s*=\s*(\d+)"
        }

        metadata_patterns = {
            "UserAgreesToHaveItOnTheScene": (int, bool),
            "UserAgreesToHaveItInsideThePluginsFolder": (int, bool),
            "GoogleLiveSyncIsUptoDate": (int, bool),

            "CaseInsensitiveTerms": (int, bool),
            "OnMissingTranslation": (int, MTA),
            "mTerm_AppName": (str, None),

            "IgnoreDeviceLanguage": (int, bool),
            "_AllowUnloadingLanguages": (int, AUL),
            "Google_WebServiceURL": (str, None),
            "Google_SpreadsheetKey": (str, None),
            "Google_SpreadsheetName": (str, None),
            "Google_LastUpdatedVersion": (str, None),
            "GoogleUpdateFrequency": (int, GUF),
            "GoogleInEditorCheckFrequency": (int, GUF),
            "GoogleUpdateSynchronization": (int, GUS),
            "GoogleUpdateDelay": (float, None)
        }

        for key, (key_type, value_type, pattern) in structure_patterns.items():
            fs_match = re.search(pattern, dump_content)
            if fs_match:
                if len(fs_match.groups()) == 1:
                    fs_result = value_type(key_type(fs_match.group(1))) if value_type else key_type(fs_match.group(1))
                else:
                    fs_result = {
                        "m_FileID": key_type(fs_match.group(1)),
                        "m_PathID": key_type(fs_match.group(2))
                    }

                result["structure"][key] = fs_result
            else:
                raise ParsingTxtError(key)

        language_codes = []
        for name, code, flags in re.findall(patterns["languages"], dump_content):
            code = code or name.lower()
            language_codes.append(code)
            result["languages"].append({
                "name": name,
                "code": code,
                "flags": LDF(int(flags))
            })


        # Capture of Language_Touch and plural forms: [i2p_Plural],
        # [i2p_Zero], [i2p_One], [i2p_Two] or [i2p_Few], [i2p_Many]
        term_blocks = re.split(r"(?=TermData data)", dump_content)
        if not term_blocks[0].startswith("TermData data"):
            term_blocks = term_blocks[1:]

        is_checked = False
        for block in term_blocks:
            name_match = re.search(patterns["term_name"], block)
            if not name_match:
                continue

            type_match = re.search(patterns["term_type"], block)
            type_match = int(type_match.group(1)) if type_match else 0
            desc_match = re.search(patterns["term_desc"], block)

            term_name = name_match.group(1)
            term_type = TT(type_match)
            term_desc = desc_match.group(1) if desc_match else ""

            languages_touch = re.search(patterns["langs_touch"], block)
            if (
                languages_touch and not is_checked and
                int(languages_touch.group(1)) > 0 and
                int(languages_touch.group(2)) > 0
            ):
                is_checked = True
                self.mw.report(
                    "Extraction of Languages_Touch Array is not implemented because its structure and usage are not fully specified. "
                    "As a result, if the file is imported back to UABEA, errors may occur due to missing or incomplete Languages_Touch data."
                )

            translations, t_flags = {}, {}
            section_match = re.search(patterns["langs_section"], block, re.DOTALL)
            if section_match:
                section = section_match.group(2)
                tr_matches = re.findall(patterns["translation"], section)
                fl_matches = re.findall(patterns["flag"], section)

                for idx, (tr, fl) in enumerate(zip(tr_matches, fl_matches)):
                    if idx < len(language_codes):
                        code = language_codes[idx]
                        translations[code] = self.unescape(tr)
                        t_flags[code] = int(fl)

            result["terms"].append({
                "name": term_name,
                "type": term_type,
                "desc": term_desc,
                "translations": translations,
                "flags": t_flags
            })


        for key, (key_type, value_type) in metadata_patterns.items():
            if key_type is int:
                value = r"(\d+)"
            elif key_type is float:
                value = r"(\d+)"
            else:
                value = r"\"(.*)\""

            pattern = fr"{key}\s*=\s*{value}"
            match = re.search(pattern, dump_content)
            if match:
                parsed_value = key_type(match.group(1))
                result["metadata"][key] = value_type(parsed_value) if value_type else parsed_value
            else:
                raise ParsingTxtError(key)


        assets_match = re.search(patterns["assets_block"], dump_content, re.DOTALL)
        if assets_match:
            asset_refs = {"Array": []}
            assets_section = assets_match.group(2)
            assets_items = re.findall(patterns["assets_item"], assets_section)
            if assets_items:
                for file_id, path_id in assets_items:
                    asset_refs["Array"].append({
                        "m_FileID": int(file_id),
                        "m_PathID": int(path_id)
                    })
            result["metadata"]["Assets"] = asset_refs

        return result

    def build_txt_dump(self):
        try:
            output = []
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
                output.append(f"      0 int TermType = {TT._value(term['type'])}")
                if term["desc"]:
                    output.append(f"      1 string Description = \"{term['desc']}\"")

                translations = term["translations"]
                output.append("      0 string Languages")
                output.append(f"       1 Array Array ({len(translations)} items)")
                output.append(f"        0 int size = {len(translations)}")

                for t_index, lang in enumerate(languages):
                    lang_code = lang["code"]
                    translation = self.escape(translations[lang_code])
                    output.append(f"        [{t_index}]")
                    output.append(f"         1 string data = \"{translation}\"")

                flags = term["flags"]
                output.append("      0 vector Flags")
                output.append(f"       1 Array Array ({len(translations)} items)")
                output.append(f"        0 int size = {len(translations)}")

                for f_index, flag in enumerate(flags.values()):
                    output.append(f"        [{f_index}]")
                    output.append(f"         0 UInt8 data = {flag}")

                # Implementation: Dynamic output of Languages_Touch
                output.append("      0 string Languages_Touch")
                output.append("       1 Array Array (0 items)")
                output.append("        0 int size = 0")

            output.append(f"  1 UInt8 CaseInsensitiveTerms = {int(metadata['CaseInsensitiveTerms'])}")
            output.append(f"  0 int OnMissingTranslation = {MTA._value(metadata['OnMissingTranslation'])}")
            output.append(f"  1 string mTerm_AppName = \"{metadata['mTerm_AppName']}\"")

            output.append("  0 LanguageData mLanguages")
            output.append(f"   1 Array Array ({len(languages)} items)")
            output.append(f"    0 int size = {len(languages)}")

            for l_index, lang in enumerate(languages):
                output.append(f"    [{l_index}]")
                output.append("     0 LanguageData data")
                output.append(f"      1 string Name = \"{lang['name']}\"")
                output.append(f"      1 string Code = \"{lang['code']}\"")
                output.append(f"      1 UInt8 Flags = {LDF._value(lang['flags'])}")

            output.append(f"  1 UInt8 IgnoreDeviceLanguage = {int(metadata['IgnoreDeviceLanguage'])}")
            output.append(f"  0 int _AllowUnloadingLanguages = {AUL._value(metadata['_AllowUnloadingLanguages'])}")
            output.append(f"  1 string Google_WebServiceURL = \"{metadata['Google_WebServiceURL']}\"")
            output.append(f"  1 string Google_SpreadsheetKey = \"{metadata['Google_SpreadsheetKey']}\"")
            output.append(f"  1 string Google_SpreadsheetName = \"{metadata['Google_SpreadsheetName']}\"")
            output.append(f"  1 string Google_LastUpdatedVersion = \"{metadata['Google_LastUpdatedVersion']}\"")
            output.append(f"  0 int GoogleUpdateFrequency = {GUF._value(metadata['GoogleUpdateFrequency'])}")
            output.append(f"  0 int GoogleInEditorCheckFrequency = {GUF._value(metadata['GoogleInEditorCheckFrequency'])}")
            output.append(f"  0 int GoogleUpdateSynchronization = {GUS._value(metadata['GoogleUpdateSynchronization'])}")
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

            self.backup = deepcopy(self.content)
            return "\n".join(output) + "\n"
        except Exception as e:
            raise e from e

    def parse_json_dump(self, dump_content):
        result = {
            "structure": {"import": FE.JSON.name},
            "languages": [],
            "metadata": {},
            "terms": []
        }

        parse_metadata = {
            "UserAgreesToHaveItOnTheScene": bool,
            "UserAgreesToHaveItInsideThePluginsFolder": bool,
            "GoogleLiveSyncIsUptoDate": bool,

            "CaseInsensitiveTerms": bool,
            "OnMissingTranslation": MTA,
            "mTerm_AppName": str,

            "IgnoreDeviceLanguage": bool,
            "_AllowUnloadingLanguages": AUL,
            "Google_WebServiceURL": str,
            "Google_SpreadsheetKey": str,
            "Google_SpreadsheetName": str,
            "Google_LastUpdatedVersion": str,
            "GoogleUpdateFrequency": GUF,
            "GoogleInEditorCheckFrequency": GUF,
            "GoogleUpdateSynchronization": GUS,
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
                LDF(lang_dict["Flags"])
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
                TT(term["TermType"]),
                term.get("Description", "")
            )

            translations, flags = {}, {}
            if term["Languages"] and term["Flags"]:
                trs = term["Languages"]["Array"]
                fls = term["Flags"]["Array"]
                for idx, (tr, fl) in enumerate(zip(trs, fls)):
                    if idx < len(language_codes):
                        translations[language_codes[idx]] = tr
                        flags[language_codes[idx]] = fl

            languages_touch_check = term["Languages_Touch"]["Array"]
            if languages_touch_check:
                self.mw.report(
                    "Found items in Languages_Touch Array that is not implemented to be extracted. "
                    "You will proceed, but if the file gets imported back to UABEA, errors may appear."
                )

            result["terms"].append({
                "name": term_data[0],
                "type": term_data[1],
                "desc": term_data[2],
                "translations": translations,
                "flags": flags
            })

        return result

    def build_json_dump(self):
        try:
            def insert_metadata(metadata, parse_metadata, target):
                for key, type_ in parse_metadata:
                    if key in metadata:
                        if issubclass(type_, (GUF, GUS, MTA, AUL)):
                            target[key] = type_._value(metadata[key])
                        else:
                            target[key] = type_(metadata[key])

            def build_term(t_dict):
                term = {
                    "Term": t_dict["name"],
                    "TermType": TT._value(t_dict["type"]),
                    "Languages": {"Array": []},
                    "Flags": {"Array": list(t_dict["flags"].values())},
                    "Languages_Touch": {"Array": []}
                }
                if desc := t_dict.get("desc"):
                    term["Description"] = desc

                for code in self.get_languages("codes"):
                    term["Languages"]["Array"].append(t_dict["translations"][code])
                return term

            def build_language(l_dict):
                return {
                    "Name": l_dict["name"],
                    "Code": l_dict["code"] if l_dict["code"] != l_dict["name"].lower() else "",
                    "Flags": LDF._value(l_dict["flags"])
                }

            output = {}
            parse_metadata = list({
                "UserAgreesToHaveItOnTheScene": int,
                "UserAgreesToHaveItInsideThePluginsFolder": int,
                "GoogleLiveSyncIsUptoDate": int,

                "CaseInsensitiveTerms": int,
                "OnMissingTranslation": MTA,
                "mTerm_AppName": str,

                "IgnoreDeviceLanguage": int,
                "_AllowUnloadingLanguages": AUL,
                "Google_WebServiceURL": str,
                "Google_SpreadsheetKey": str,
                "Google_SpreadsheetName": str,
                "Google_LastUpdatedVersion": str,
                "GoogleUpdateFrequency": GUF,
                "GoogleInEditorCheckFrequency": GUF,
                "GoogleUpdateSynchronization": GUS,
                "GoogleUpdateDelay": float,
                "Assets": dict
            }.items())

            for key, value in self.content.get("structure", {}).items():
                if key != "import":
                    output[key] = value

            m_source = output.setdefault("mSource", {})
            metadata = self.content.get("metadata", [])

            insert_metadata(metadata, parse_metadata[:3], m_source)

            m_source["mTerms"] = {"Array": []}
            for t_dict in self.content.get("terms", []):
                m_source["mTerms"]["Array"].append(
                    build_term(t_dict)
                )

            insert_metadata(metadata, parse_metadata[3:6], m_source)

            m_source["mLanguages"] = {"Array": []}
            for lang_dict in self.content.get("languages", []):
                m_source["mLanguages"]["Array"].append(
                    build_language(lang_dict)
                )

            insert_metadata(metadata, parse_metadata[6:], m_source)

            self.backup = deepcopy(self.content)
            return json.dumps(output, ensure_ascii=False, indent=2)
        except Exception as e:
            return str(e)
