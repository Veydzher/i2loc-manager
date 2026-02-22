import csv
from enum import Enum
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QUndoCommand
from PySide6.QtWidgets import (
    QFileDialog, QDialog, QLabel, QComboBox, QProgressDialog, QVBoxLayout,
    QGridLayout, QDialogButtonBox, QWidget, QScrollArea, QHBoxLayout,
    QRadioButton, QButtonGroup, QTextEdit, QGroupBox, QCheckBox, QSizePolicy, QMessageBox
)

from gui.helpers import ConfigurableCheckBox, CollapsibleSection, CustomPushButton, message_box
from utils.app_locales import ftr
from utils.enums import (
    FileExtension as Fe,
    FileSeperator as Fs,
    TermType,
    LanguageDataFlags as Ldf
)
from utils.helpers import normalise, check_language
from utils.manager import manager

REQUIRED_COLUMNS = ["Key", "Type", "Desc"]


class UpdateMode(Enum):
    REPLACE = 0
    MERGE = 1
    ADD_NEW_ONLY = 2
    UPDATE_ONLY = 3


class ImportConfig:
    def __init__(self):
        self.mode: UpdateMode = UpdateMode.MERGE
        self.language_mapping: dict = {}  # {csv_lang: lang_index or 'CREATE_NEW'}
        self.create_missing_terms: bool = True
        self.update_term_type: bool = True
        self.update_descriptions: bool = True
        self.skip_empty_cells: bool = True


class ImportCommand(QUndoCommand):
    def __init__(self, model, changes, stats):
        super().__init__()
        self.model = model
        self.changes = changes
        self.stats = stats
        self._applied = True

    def undo(self):
        for change in reversed(self.changes):
            change_type = change["type"]

            if change_type == "translation":
                row, lang_idx, old_val = change["row"], change["lang_idx"], change["old"]
                manager.set_translation(row, lang_idx, old_val)

            elif change_type == "term_field":
                row, field, old_val = change["row"], change["field"], change["old"]
                terms = manager.get_terms()
                if 0 <= row < len(terms):
                    terms[row][field] = old_val

            elif change_type == "term_added":
                terms = manager.get_terms()
                terms.pop(change["row"])

            elif change_type == "language_added":
                self.model.remove_language(change["lang_idx"])

            elif change_type == "full_replace":
                manager.get_terms().clear()
                manager.get_terms().extend(change["old_terms"])
                manager.get_languages().clear()
                manager.get_languages().extend(change["old_languages"])

        self._applied = False
        self.model.beginResetModel()
        self.model.endResetModel()

    def redo(self):
        if not self._applied:
            for change in self.changes:
                change_type = change["type"]

                if change_type == "translation":
                    manager.set_translation(change["row"], change["lang_idx"], change["new"])

                elif change_type == "term_field":
                    terms = manager.get_terms()
                    if 0 <= change["row"] < len(terms):
                        terms[change["row"]][change["field"]] = change["new"]

                elif change_type == "term_added":
                    manager.get_terms().insert(change["row"], change["term_data"])

                elif change_type == "language_added":
                    self.model.add_language(
                        change["name"], change["code"], change["flags"], None
                    )

                elif change_type == "full_replace":
                    manager.get_terms().clear()
                    manager.get_languages().clear()

            self._applied = True
            self.model.beginResetModel()
            self.model.endResetModel()


class ImportModule:
    def __init__(self, main_window):
        self.mw = main_window
        self.import_languages()

    def import_languages(self):
        path = Path(QFileDialog.getOpenFileName(
            self.mw, ftr("open-title"), "",
            f"{ftr('all-files')} (*.*);;"
            f"{ftr('csv-file')} (*{Fe.CSV.value});;"
            f"{ftr('tsv-file')} (*{Fe.TSV.value})"
        )[0])

        if not path.is_file():
            return

        if path.suffix not in [Fe.CSV.value, Fe.TSV.value]:
            message_box(self.mw, "error", "error-invalid-file")
            return

        self.mw.status_bar_message(("importing-file-data", {"file_name": path.name}))

        try:
            csv_data, headers = self._read_csv_file(path)
            if not csv_data:
                return

            csv_languages = self._validate_and_parse_headers(headers)
            if csv_languages is None:
                return

            config = self._get_import_configuration(csv_languages)
            if not config:
                return

            model = self.mw.custom_table.table_model
            if not model:
                message_box(self.mw, "error", "error-no-available-model")
                return

            stats = self._import_data(csv_data, config, path)
            self._show_import_results(stats, path.name)

        except Exception as e:
            message_box(self.mw, "error", ("error-import-file", {"error": str(e)}))

    @staticmethod
    def _read_csv_file(path: str | Path):
        csv_data = []
        headers = []

        with open(path, "r", encoding="utf-8-sig", newline="") as file:
            sample = file.read(8192)
            file.seek(0)

            try:
                dialect = csv.Sniffer().sniff(sample)
                delimiter = dialect.delimiter
            except csv.Error:
                delimiter = Fs[Fe.CSV.name].value

            reader = csv.DictReader(file, delimiter=delimiter)
            headers = list(reader.fieldnames) if reader.fieldnames else []

            for row in reader:
                new_row = {
                    k: normalise(v) if v else ""
                    for k, v in row.items()
                }
                csv_data.append(new_row)

        return csv_data, headers

    def _validate_and_parse_headers(self, headers: list[str]):
        if not headers:
            message_box(self.mw, "error", "error-no-headers")
            return None

        missing_columns = [col for col in REQUIRED_COLUMNS if col not in headers]
        if missing_columns:
            message_box(
                self.mw, "error", (
                    "error-missing-headers",
                    {"headers": ", ".join(missing_columns)})
            )
            return None

        csv_languages = []
        for col in headers:
            if col not in REQUIRED_COLUMNS:
                lang_info = self._parse_language_header(col)
                csv_languages.append(lang_info)

        return csv_languages

    @staticmethod
    def _parse_language_header(header: str):
        enabled = not header.startswith("$")
        header = header.lstrip("$").strip()

        name = header
        code = None

        if "[" in header and "]" in header:
            try:
                bracket_start = header.index("[")
                bracket_end = header.index("]")
                name = header[:bracket_start].strip()
                code = header[bracket_start + 1:bracket_end].strip()
            except ValueError:
                pass

        return {
            "original": header,
            "name": name,
            "code": code,
            "enabled": enabled
        }

    def _get_import_configuration(self, csv_languages: list[dict]):
        existing_langs = manager.get_displayed_languages()

        if not csv_languages:
            message_box(self.mw, "warning", "warning-no-available-languages")
            return None

        dialog = QDialog(self.mw)
        dialog.setWindowTitle(ftr("import-translations-title"))
        dialog.setWindowModality(Qt.WindowModality.ApplicationModal)
        dialog.setMinimumSize(600, 300)
        dialog.setMaximumSize(650, 700)

        outer_layout = QVBoxLayout(dialog)
        outer_layout.setSpacing(8)

        # === Top Panel ===
        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(10, 10, 10, 0)
        top_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # === Modes ===
        mode_group = QGroupBox(ftr("import-mode-title"))
        mode_group.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        mode_outer = QVBoxLayout(mode_group)

        mode_buttons = QButtonGroup(dialog)

        merge_radio = QRadioButton(ftr("import-mode-merge"))
        replace_radio = QRadioButton(ftr("import-mode-replace"))
        add_new_radio = QRadioButton(ftr("import-mode-add-new"))
        update_only_radio = QRadioButton(ftr("import-mode-update-only"))

        merge_radio.setChecked(True)

        mode_buttons.addButton(merge_radio, UpdateMode.MERGE.value)
        mode_buttons.addButton(replace_radio, UpdateMode.REPLACE.value)
        mode_buttons.addButton(add_new_radio, UpdateMode.ADD_NEW_ONLY.value)
        mode_buttons.addButton(update_only_radio, UpdateMode.UPDATE_ONLY.value)

        mode_descriptions = {
            UpdateMode.MERGE.value: ftr("import-mode-merge-desc"),
            UpdateMode.REPLACE.value: ftr("import-mode-replace-desc"),
            UpdateMode.ADD_NEW_ONLY.value: ftr("import-mode-add-new-desc"),
            UpdateMode.UPDATE_ONLY.value: ftr("import-mode-update-only-desc"),
        }

        mode_desc_label = QLabel(mode_descriptions[UpdateMode.MERGE.value])
        mode_desc_label.setWordWrap(True)
        mode_desc_label.setStyleSheet("QLabel { color: #888888; font-size: 11px; }")

        for radio in [merge_radio, replace_radio, add_new_radio, update_only_radio]:
            mode_outer.addWidget(radio)

        mode_outer.addSpacing(4)
        mode_outer.addWidget(mode_desc_label)

        # === Options ===
        options_group = QGroupBox(ftr("import-options-title"))
        options_group.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        options_layout = QVBoxLayout(options_group)

        create_terms_check = ConfigurableCheckBox("import-create-terms", "import.create_terms")
        update_types_check = ConfigurableCheckBox("import-update-types", "import.update_types")
        update_desc_check = ConfigurableCheckBox("import-update-descriptions", "import.update_descriptions")
        skip_empty_check = ConfigurableCheckBox("import-skip-empty", "import.skip_empty")

        create_terms_check.setToolTip(ftr("import-create-terms-tooltip"))
        update_types_check.setToolTip(ftr("import-update-types-tooltip"))
        update_desc_check.setToolTip(ftr("import-update-descriptions-tooltip"))
        skip_empty_check.setToolTip(ftr("import-skip-empty-tooltip"))

        options_layout.addWidget(create_terms_check)
        options_layout.addWidget(update_types_check)
        options_layout.addWidget(update_desc_check)
        options_layout.addWidget(skip_empty_check)

        top_layout.addWidget(mode_group, 0, Qt.AlignmentFlag.AlignTop)
        top_layout.addSpacing(8)
        top_layout.addWidget(options_group, 0, Qt.AlignmentFlag.AlignTop)

        outer_layout.addLayout(top_layout)

        # === Advanced Language Mapping ===
        advanced_section = CollapsibleSection(ftr("advanced-title"))

        auto_map_check = QCheckBox(ftr("import-auto-map-toggle"))
        auto_map_check.setChecked(True)
        advanced_section.add_widget(auto_map_check)

        mapping_label = QLabel(ftr("import-select-languages"))
        advanced_section.add_widget(mapping_label)

        scroll_area = QScrollArea()
        scroll_area.setMinimumHeight(150)
        scroll_area.setMaximumHeight(200)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setWidgetResizable(True)

        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)

        grid_title = QGridLayout()
        grid_title.addWidget(QLabel(ftr("imported-language-label")), 0, 0)
        grid_title.addWidget(QLabel(ftr("import-to-language-label")), 0, 1)
        scroll_layout.addLayout(grid_title)

        grid = QGridLayout()
        grid.setAlignment(Qt.AlignmentFlag.AlignTop)

        mappings = {}
        row = 1

        current_languages = manager.get_languages_copy()

        for csv_lang in csv_languages:
            display_name = csv_lang["original"]
            grid.addWidget(QLabel(display_name), row, 0)

            combo = QComboBox()
            combo.addItem(ftr("do-not-import-option"))
            combo.addItem(ftr("create-new-lang-option"))

            for lang in existing_langs:
                combo.addItem(lang)

            already_exists = check_language(csv_lang["name"], csv_lang["code"], Ldf.ENABLED, current_languages)
            if already_exists != (None, None):
                item = combo.model().item(1)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEnabled)

            combo.setCurrentIndex(0)
            grid.addWidget(combo, row, 1)
            mappings[csv_lang["original"]] = combo
            row += 1

        scroll_layout.addLayout(grid)
        scroll_widget.setLayout(scroll_layout)
        scroll_area.setWidget(scroll_widget)
        advanced_section.add_widget(scroll_area)

        mapping_button_layout = QHBoxLayout()
        manual_map_button = CustomPushButton("import-auto-map-button", 60, 30, 160, 35)
        clear_button = CustomPushButton("import-clear-mappings-button", 60, 30, 160, 35)

        mapping_button_layout.addWidget(manual_map_button)
        mapping_button_layout.addWidget(clear_button)
        mapping_button_layout.addStretch()
        advanced_section.add_layout(mapping_button_layout)

        advanced_section.set_expanded(True)

        outer_layout.addWidget(advanced_section)

        # === Dialog Buttons ===
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )

        import_button = button_box.button(QDialogButtonBox.StandardButton.Ok)
        import_button.setMinimumSize(60, 30)
        import_button.setMaximumSize(160, 35)
        import_button.setText(ftr("import-button"))

        cancel_button = button_box.button(QDialogButtonBox.StandardButton.Cancel)
        cancel_button.setMinimumSize(60, 30)
        cancel_button.setMaximumSize(160, 35)
        cancel_button.setText(ftr("cancel-button"))

        outer_layout.addWidget(button_box)

        # === Misc. Functions ===
        def on_mode_changed(button_id: int):
            mode_desc_label.setText(mode_descriptions.get(button_id, ""))

        mode_buttons.idToggled.connect(lambda btn_id, checked: on_mode_changed(btn_id) if checked else None)

        def accept_dialog():
            if mode_buttons.checkedId() == UpdateMode.REPLACE.value:
                confirm = message_box(
                    self.mw,
                    "question",
                    "import-replace-confirm-message",
                    standard_buttons=(
                        QMessageBox.StandardButton.Yes
                        | QMessageBox.StandardButton.Cancel,
                        QMessageBox.StandardButton.Cancel
                    )
                )

                if confirm == QMessageBox.StandardButton.Yes:
                    dialog.accept()
            else:
                dialog.accept()

        button_box.accepted.connect(accept_dialog)
        button_box.rejected.connect(dialog.reject)

        def set_manual_mapping_enabled(enabled: bool):
            scroll_area.setEnabled(enabled)
            manual_map_button.setEnabled(not enabled)
            clear_button.setEnabled(enabled)
            mapping_label.setEnabled(enabled)

        def auto_map_languages():
            manual_map_button.setEnabled(False)
            langs = manager.get_languages()

            for csv_lang_header, combo in mappings.items():
                csv_lang = next(
                    (l for l in csv_languages if l["original"] == csv_lang_header),
                    None
                )
                if not csv_lang:
                    continue

                csv_name_lower = csv_lang["name"].lower()
                csv_code = csv_lang["code"].lower() if csv_lang["code"] else None
                best_match_index = 0

                for idx, lang in enumerate(langs):
                    lang_name = lang["name"].lower()
                    lang_code = lang["code"].lower() if lang["code"] else None

                    if csv_code and lang_code and csv_code == lang_code:
                        best_match_index = idx + 2
                        break

                    if csv_name_lower == lang_name:
                        best_match_index = idx + 2
                        break

                combo.setCurrentIndex(best_match_index)

        def update_mapping_button():
            any_mapped = any(combo.currentIndex() != 0 for combo in mappings.values())
            clear_button.setEnabled(any_mapped and not auto_map_check.isChecked())
            manual_map_button.setEnabled(not auto_map_check.isChecked() and not any_mapped)
            import_button.setEnabled(any_mapped)
            import_button.setToolTip(ftr("import-button-disabled") if not any_mapped else "")

        def clear_all_mappings():
            for combo in mappings.values():
                combo.setCurrentIndex(0)

        def on_auto_map_toggled(checked: bool):
            set_manual_mapping_enabled(not checked)
            if checked:
                auto_map_languages()
            update_mapping_button()

        for combo in mappings.values():
            combo.currentIndexChanged.connect(lambda _: update_mapping_button())

        auto_map_check.toggled.connect(on_auto_map_toggled)
        manual_map_button.clicked.connect(auto_map_languages)
        clear_button.clicked.connect(clear_all_mappings)

        set_manual_mapping_enabled(not auto_map_check.isChecked())
        if auto_map_check.isChecked():
            auto_map_languages()

        update_mapping_button()

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return None

        config = ImportConfig()
        config.mode = UpdateMode(mode_buttons.checkedId())
        config.create_missing_terms = create_terms_check.isChecked()
        config.update_term_type = update_types_check.isChecked()
        config.update_descriptions = update_desc_check.isChecked()
        config.skip_empty_cells = skip_empty_check.isChecked()

        for csv_lang_header, combo in mappings.items():
            selected_index = combo.currentIndex()

            if selected_index == 0:
                continue
            elif selected_index == 1:
                config.language_mapping[csv_lang_header] = "CREATE_NEW"
            else:
                config.language_mapping[csv_lang_header] = selected_index - 2

        return config

    def _import_data(self, csv_data: list[dict], config: ImportConfig, file_path: Path):
        model = self.mw.custom_table.table_model
        terms = manager.get_terms()
        languages = manager.get_languages()

        stats = {
            "terms_created": 0,
            "terms_updated": 0,
            "languages_created": 0,
            "translations_added": 0,
            "translations_updated": 0,
            "types_updated": 0,
            "descriptions_updated": 0,
            "total_changes": 0,
            "skipped_empty": 0,
            "errors": []
        }

        changes = []

        if config.mode == UpdateMode.REPLACE:
            old_terms = [t.copy() for t in terms]
            old_languages = [l.copy() for l in languages]

            changes.append({
                "type": "full_replace",
                "old_terms": old_terms,
                "old_languages": old_languages
            })

            terms.clear()
            languages.clear()
            stats["total_changes"] += 1

        lang_index_map = {}

        for csv_lang_header, mapping in config.language_mapping.items():
            if mapping == "CREATE_NEW":
                if csv_lang_header in csv_data[0]:
                    lang_info = self._parse_language_header(csv_lang_header)
                    lang_idx, lang_data = model.add_language(
                        lang_info["name"],
                        lang_info["code"] or "",
                        Ldf.ENABLED if lang_info["enabled"] else Ldf.DISABLED,
                        None
                    )

                    lang_index_map[csv_lang_header] = lang_idx
                    stats["languages_created"] += 1

                    changes.append({
                        "type": "language_added",
                        "lang_idx": lang_idx,
                        "name": lang_data["name"],
                        "code": lang_data["code"],
                        "flags": lang_data["flags"]
                    })
            else:
                lang_index_map[csv_lang_header] = mapping

        term_to_row = {
            term["name"]: index
            for index, term in enumerate(terms)
        }

        progress = QProgressDialog(
            ftr("import-progress-label"),
            ftr("cancel-button"),
            0, len(csv_data),
            self.mw
        )
        progress.setWindowTitle(ftr("import-progress-title"))
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setValue(0)

        canceled = False

        for idx, row_data in enumerate(csv_data):
            progress.setValue(idx)

            if progress.wasCanceled():
                canceled = True
                self.mw.status_bar_message(("importing-file-canceled", {"file_name": file_path.name}))
                break

            try:
                term_key = row_data.get("Key", "").strip()
                if not term_key:
                    continue

                if term_key in term_to_row:
                    if config.mode == UpdateMode.ADD_NEW_ONLY:
                        continue

                    row_index = term_to_row[term_key]
                    term = terms[row_index]

                    if config.update_term_type and "Type" in row_data:
                        new_type = row_data["Type"]
                        old_type = term["type"]

                        if new_type and str(old_type) != new_type:
                            try:
                                if hasattr(TermType, new_type.upper()):
                                    term_type_obj = getattr(TermType, new_type.upper())
                                else:
                                    term_type_obj = TermType.TEXT

                                changes.append({
                                    "type": "term_field",
                                    "row": row_index,
                                    "field": "type",
                                    "old": old_type,
                                    "new": term_type_obj
                                })
                                term["type"] = term_type_obj
                                stats["types_updated"] += 1
                                stats["total_changes"] += 1
                            except (ValueError, AttributeError, TypeError, KeyError):
                                stats["errors"].append(f"Row {idx}: Invalid type '{new_type}'")

                    if config.update_descriptions and "Desc" in row_data:
                        new_desc = row_data["Desc"]
                        old_desc = term["desc"]

                        if new_desc and old_desc != new_desc:
                            changes.append({
                                "type": "term_field",
                                "row": row_index,
                                "field": "desc",
                                "old": old_desc,
                                "new": new_desc
                            })
                            term["desc"] = new_desc
                            stats["descriptions_updated"] += 1
                            stats["total_changes"] += 1

                    stats["terms_updated"] += 1

                else:
                    if config.mode == UpdateMode.UPDATE_ONLY:
                        continue

                    if not config.create_missing_terms and config.mode != UpdateMode.REPLACE:
                        stats["errors"].append(ftr("import-term-not-found", {"idx": idx, "term_key": term_key}))
                        continue

                    term_type_str = row_data.get("Type", "Text")
                    try:
                        if hasattr(TermType, term_type_str.upper()):
                            term_type = getattr(TermType, term_type_str.upper())
                        else:
                            term_type = TermType.TEXT
                    except (ValueError, AttributeError, TypeError, KeyError):
                        term_type = TermType.TEXT
                        stats["errors"].append(
                            ftr("import-invalid-term-type", {"idx": idx, "term_type": term_type_str}))

                    row_index, term_data = model.add_term(
                        term_key,
                        term_type,
                        row_data.get("Desc", ""),
                        [""] * len(languages),
                        [0] * len(languages),
                        []
                    )

                    term_to_row[term_key] = row_index

                    changes.append({
                        "type": "term_added",
                        "row": row_index,
                        "term_data": term_data.copy()
                    })

                    stats["terms_created"] += 1
                    stats["total_changes"] += 1

                for csv_lang_header, lang_idx in lang_index_map.items():
                    if csv_lang_header not in row_data:
                        continue

                    new_translation = row_data[csv_lang_header]

                    if config.skip_empty_cells and not new_translation:
                        stats["skipped_empty"] += 1
                        continue

                    old_translation = manager.get_translation(row_index, lang_idx)

                    old_normalised = normalise(old_translation)
                    new_normalised = normalise(new_translation)

                    if old_normalised != new_normalised:
                        changes.append({
                            "type": "translation",
                            "row": row_index,
                            "lang_idx": lang_idx,
                            "old": old_translation,
                            "new": new_translation
                        })

                        manager.set_translation(row_index, lang_idx, new_translation)

                        if old_translation:
                            stats["translations_updated"] += 1
                        else:
                            stats["translations_added"] += 1

                        stats["total_changes"] += 1

            except Exception as e:
                stats["errors"].append(ftr("import-general-error", {"idx": idx, "error": str(e)}))

        if not canceled:
            progress.setValue(len(csv_data))

        if changes and stats["total_changes"] > 0:
            import_cmd = ImportCommand(model, changes, stats)
            model.undo_stack.push(import_cmd)
        else:
            model.beginResetModel()
            model.endResetModel()

        return stats

    def _show_import_results(self, stats: dict, file_name: str):
        summary_parts = [ftr("import-from-file-title", {"file_name": file_name}), ""]

        if stats["total_changes"] > 0:
            summary_parts.append(ftr("import-total-changes", {"count": stats["total_changes"]}))
            summary_parts.append("")

            if stats["terms_created"]:
                summary_parts.append(ftr("import-terms-created", {"count": stats["terms_created"]}))
            if stats["terms_updated"]:
                summary_parts.append(ftr("import-terms-updated", {"count": stats["terms_updated"]}))
            if stats["languages_created"]:
                summary_parts.append(ftr("import-languages-created", {"count": stats["languages_created"]}))
            if stats["translations_added"]:
                summary_parts.append(ftr("import-translations-added", {"count": stats["translations_added"]}))
            if stats["translations_updated"]:
                summary_parts.append(ftr("import-translations-updated", {"count": stats["translations_updated"]}))
            if stats["types_updated"]:
                summary_parts.append(ftr("import-term-types-updated", {"count": stats["types_updated"]}))
            if stats["descriptions_updated"]:
                summary_parts.append(ftr("import-term-descs-updated", {"count": stats["descriptions_updated"]}))
            if stats["skipped_empty"]:
                summary_parts.append(ftr("import-skipped-empty", {"count": stats["skipped_empty"]}))
        else:
            summary_parts.append(ftr("import-no-changes-made"))

        if stats["errors"]:
            summary_parts.append("")
            summary_parts.append(ftr("import-errors-title", {"count": len(stats["errors"])}))
            summary_parts.append("")

            for error in stats["errors"]:
                summary_parts.append(f"  • {error}")

        summary_text = "\n".join(summary_parts)

        dialog = QDialog(self.mw)
        dialog.setWindowTitle(ftr("import-summary-title"))
        dialog.setWindowModality(Qt.WindowModality.ApplicationModal)
        dialog.setMinimumSize(500, 400)
        dialog.setMaximumSize(600, 500)

        layout = QVBoxLayout(dialog)

        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setPlainText(summary_text)
        layout.addWidget(text_edit)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        button_box.accepted.connect(dialog.accept)
        layout.addWidget(button_box)

        dialog.exec()

        if stats["total_changes"] > 0:
            self.mw.status_bar_message(("imported-data-success", {"file_name": file_name}))
        else:
            self.mw.status_bar_message(("info-no-imported", {"file_name": file_name}))
