import csv
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFileDialog, QDialog, QLabel, QComboBox, QProgressDialog, QVBoxLayout,
    QGridLayout, QDialogButtonBox, QWidget, QScrollArea, QHBoxLayout, QPushButton
)

from gui.helpers import message_box
from utils.app_locales import fluent
from utils.enums import (
    FileExtension as Fe,
    FileSeperator as Fs
)
from utils.helpers import normalise
from utils.manager import manager


class ImportModule:
    def __init__(self, main_window):
        self.mw = main_window
        self.ts = fluent.tr_batch([
            "open-title", "all-files", "csv-file", "tsv-file",
            "importing-progress-label",
            "importing-progress-title",
            "import-translations-title",
            "import-select-languages",
            "imported-language-label",
            "import-to-language-label",
            "do-not-import-option",
            "import-button",
            "import-button-disabled",
            "cancel-button"
        ])
        self.import_languages()

    def import_languages(self):
        path = Path(QFileDialog.getOpenFileName(
            self.mw, self.ts["open-title"], "",
            f"{self.ts['all-files']} (*.*);;"
            f"{self.ts['csv-file']} (*{Fe.CSV.value});;"
            f"{self.ts['tsv-file']} (*{Fe.TSV.value})"
        )[0])

        if not path.is_file():
            return

        file_name = path.name
        file_suffix = path.suffix
        if file_suffix not in [Fe.CSV.value, Fe.TSV.value]:
            message_box(self.mw, "error", "error-invalid-file")
            return

        self.mw.status_bar_message(("importing-file-data", {"file_name": file_name}))

        try:
            delimiter = Fs[Fe(file_suffix).name].value
            with open(path, "r", encoding="utf-8", newline="") as f1:
                reader = csv.reader(f1, delimiter=delimiter)
                headers = next(reader, [])

                if not headers:
                    message_box(self.mw, "error", "error-no-headers")
                    return

                required_columns = ["Key", "Type", "Desc"]
                missing_columns = [col for col in required_columns if col not in headers]
                if missing_columns:
                    message_box(self.mw, "error", ("error-missing-headers", {"headers": ", ".join(missing_columns)}))
                    return

                csv_languages = [col for col in headers if col not in required_columns]
                if not csv_languages:
                    message_box(self.mw, "error", "error-no-languages-columns")
                    return

                lang_mapping = self._get_import_languages(csv_languages)
                if not lang_mapping:
                    return

                csv_data = []
                with open(path, "r", encoding="utf-8", newline="") as f2:
                    reader = csv.DictReader(f2, delimiter=delimiter)
                    for row in reader:
                        new_row = {
                            k: normalise(v)
                            for k, v in row.items()
                        }
                        csv_data.append(new_row)

                model = self.mw.custom_table.table_model
                if not model:
                    message_box(self.mw, "error", "error-no-available-model")
                    return

                term_to_row = {
                    term["name"]: index
                    for index, term in enumerate(model.terms)
                }

                progress = QProgressDialog(self.ts["importing-progress-label"], self.ts["cancel-button"], 0, len(csv_data), self.mw)
                progress.setWindowTitle(self.ts["importing-progress-title"])
                progress.setWindowModality(Qt.WindowModality.WindowModal)
                progress.setValue(0)

                updated_count = 0
                for i, data in enumerate(csv_data):
                    progress.setValue(i)
                    if progress.wasCanceled():
                        self.mw.status_bar_message(("importing-file-canceled", {"file_name": file_name}))
                        break

                    term_key = data.get("Key", "")
                    if not term_key or term_key not in term_to_row:
                        continue

                    row_index = term_to_row[term_key]

                    for col_header, col_value in data.items():
                        if col_header in required_columns:
                            col_key = {
                                "Key": "name",
                                "Type": "type",
                                "Desc": "desc"
                            }.get(col_header)

                            col_index = next((i for i, (_, key) in enumerate(model.columns) if key == col_key), -1)
                            if col_index != -1:
                                index = model.index(row_index, col_index)
                                model_data = model.data(index, Qt.ItemDataRole.DisplayRole)
                                normalised_data_value = normalise(model_data)

                                if col_value and normalised_data_value != col_value:
                                    model.setData(index, col_value, Qt.ItemDataRole.EditRole)
                                    updated_count += 1

                        elif col_header in lang_mapping:
                            lang_code = lang_mapping[col_header]
                            col_index = next((i for i, (_, key) in enumerate(model.columns) if key == lang_code), -1)
                            if col_index != -1:
                                index = model.index(row_index, col_index)
                                model_data = model.data(index, Qt.ItemDataRole.DisplayRole)
                                normalised_data_value = normalise(model_data)

                                if col_value and normalised_data_value != col_value:
                                    model.setData(index, col_value, Qt.ItemDataRole.EditRole)
                                    updated_count += 1

                progress.setValue(len(csv_data))

                if updated_count:
                    self.mw.status_bar_message(("imported-data-success", {"file_name": file_name}))
                    message_box(self.mw, "information", ("info-success-import", {"count": updated_count}))
                else:
                    message_box(self.mw, "information", "info-no-imported")
        except Exception as e:
            message_box(self.mw, "error", ("error-import-file", {"error": str(e)}))
            return

    def _get_import_languages(self, table_langs: list):
        langs = manager.get_displayed_languages()

        if not table_langs and langs:
            message_box(self.mw, "warning", "warning-no-available-languages")
            return {}

        dialog = QDialog(self.mw)
        dialog.setWindowTitle(self.ts["import-translations-title"])
        dialog.setFixedSize(500, 400)

        layout = QVBoxLayout(dialog)

        info_label = QLabel(self.ts["import-select-languages"])
        layout.addWidget(info_label)

        scroll_area = QScrollArea()
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setWidgetResizable(True)

        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.button(QDialogButtonBox.StandardButton.Ok).setText(self.ts["import-button"])
        button_box.button(QDialogButtonBox.StandardButton.Cancel).setText(self.ts["cancel-button"])
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)

        def update_dialog_button():
            any_selected = any(combo.currentIndex() != 0 for combo in mappings.values())
            ok_button = button_box.button(QDialogButtonBox.StandardButton.Ok)
            ok_button.setEnabled(any_selected)
            ok_button.setToolTip(self.ts["import-button-disabled"] if not any_selected else "")

        def auto_map_languages():
            for csv_lang, combo in mappings.items():
                csv_lang_lower = csv_lang.lower()
                csv_code = None

                if "[" in csv_lang and "]" in csv_lang:
                    csv_code = csv_lang.split("[")[1].split("]")[0].strip().lower()

                best_match_index = 0
                for i, lang in enumerate(langs):
                    lang_lower = lang.lower()

                    lang_code = None
                    if "[" in lang and "]" in lang:
                        lang_code = lang.split("[")[1].split("]")[0].strip().lower()

                    if csv_code and lang_code and csv_code == lang_code:
                        best_match_index = i + 1
                        break

                    lang_name = lang.split("[")[0].strip().lower() if "[" in lang else lang_lower
                    csv_name = csv_lang.split("[")[0].strip().lower() if "[" in csv_lang else csv_lang_lower

                    if csv_name == lang_name or csv_name in lang_name or lang_name in csv_name:
                        best_match_index = i + 1
                        break

                combo.setCurrentIndex(best_match_index)

        def clear_all_mappings():
            for combo in mappings.values():
                combo.setCurrentIndex(0)

        grid = QGridLayout()
        grid.setAlignment(Qt.AlignmentFlag.AlignTop)
        grid_title = QGridLayout()
        grid_title.addWidget(QLabel(self.ts["imported-language-label"]), 0, 0)
        grid_title.addWidget(QLabel(self.ts["import-to-language-label"]), 0, 1)

        row = 1
        mappings = {}

        for csv_lang in table_langs:
            grid.addWidget(QLabel(csv_lang), row, 0)

            combo = QComboBox()
            combo.currentIndexChanged.connect(lambda _: update_dialog_button())
            combo.addItem(self.ts["do-not-import-option"])
            for lang in langs:
                combo.addItem(lang)

            combo.setCurrentIndex(0)
            grid.addWidget(combo, row, 1)
            mappings[csv_lang] = combo
            row += 1

        scroll_layout.addLayout(grid)
        scroll_widget.setLayout(scroll_layout)
        scroll_area.setWidget(scroll_widget)

        mapping_button_layout = QHBoxLayout()
        auto_map_button = QPushButton(self.ts.get("auto-map-button", "Auto-Map"))
        clear_button = QPushButton(self.ts.get("clear-mappings-button", "Clear All"))

        auto_map_button.clicked.connect(auto_map_languages)
        clear_button.clicked.connect(clear_all_mappings)

        mapping_button_layout.addWidget(auto_map_button)
        mapping_button_layout.addWidget(clear_button)
        mapping_button_layout.addStretch()

        layout.addLayout(grid_title)
        layout.addWidget(scroll_area)
        layout.addLayout(mapping_button_layout)
        layout.addWidget(button_box)

        auto_map_languages()
        update_dialog_button()

        lang_mapping = {}
        result = dialog.exec()
        if result == QDialog.DialogCode.Accepted:
            for csv_lang, combo in mappings.items():
                selected_index = combo.currentIndex() - 1
                if selected_index >= 0:
                    code, _ = manager.get_language_by_index(selected_index)
                    if code:
                        lang_mapping[csv_lang] = code

        return lang_mapping

