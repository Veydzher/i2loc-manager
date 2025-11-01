import os
import csv
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFileDialog, QDialog, QLabel, QComboBox, QProgressDialog, QVBoxLayout,
    QGridLayout, QDialogButtonBox, QWidget, QScrollArea
)
from utils.enums import (
    FileExts as FE,
    FileSeps as FS
)

class ImportModule:
    def __init__(self, main_window):
        self.mw = main_window
        self.manager = self.mw.manager
        self.ts = self.mw.fluent.tr_batch([
            "open-title",
            "all-files",
            "csv-file",
            "tsv-file",
            "importing-progress-label",
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
        file_path, _ = QFileDialog.getOpenFileName(
            self.mw, self.ts["open-title"], "",
            f"{self.ts['all-files']} (*.*);;"
            f"{self.ts['csv-file']} (*{FE.CSV.value});;"
            f"{self.ts['tsv-file']} (*{FE.TSV.value})"
        )

        if not os.path.isfile(file_path):
            return

        file_ext = os.path.splitext(file_path)[1].lower()
        if file_ext not in [FE.CSV.value, FE.TSV.value]:
            self.mw.message_box("error", "error-invalid-file")
            return

        try:
            delimiter = FS[FE(file_ext).name].value
            with open(file_path, "r", encoding="utf-8") as f:
                reader = csv.reader(f, delimiter=delimiter)
                headers = next(reader, [])

                if not headers:
                    self.mw.message_box("error", "error-no-headers")
                    return

                required_columns = ["Key", "Type", "Desc"]
                missing_columns = [col for col in required_columns if col not in headers]
                if missing_columns:
                    self.mw.message_box("error", ("error-missing-headers", {"headers": ", ".join(missing_columns)}))
                    return

                csv_languages = [col for col in headers if col not in required_columns]
                if not csv_languages:
                    self.mw.message_box("error", "error-no-languages-columns")
                    return

                lang_mapping = self._get_import_languages(csv_languages)
                if not lang_mapping:
                    return

                csv_data = []
                with open(file_path, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        new_row = dict(row.items())
                        csv_data.append(new_row)

                model = self.mw.custom_table.table_model
                if not model:
                    self.mw.message_box("error", "error-no-available-model")
                    return

                term_to_row = {
                    term["name"]: index
                    for index, term in enumerate(model.terms)
                }

                progress = QProgressDialog(self.ts["importing-progress-label"], self.ts["cancel-button"], 0, len(csv_data), self.mw)
                progress.setWindowModality(Qt.WindowModality.WindowModal)
                progress.setValue(0)

                updated_count = 0

                for i, data in enumerate(csv_data):
                    progress.setValue(i)
                    if progress.wasCanceled():
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
                                if col_value.strip() and model.data(index, Qt.ItemDataRole.DisplayRole) != col_value:
                                    model.setData(index, col_value, Qt.ItemDataRole.EditRole)
                                    updated_count += 1
                        elif col_header in lang_mapping:
                            lang_code = lang_mapping[col_header]
                            col_index = next((i for i, (_, key) in enumerate(model.columns) if key == lang_code), -1)
                            if col_index != -1:
                                index = model.index(row_index, col_index)
                                model_data = model.data(index, Qt.ItemDataRole.DisplayRole)
                                if col_value.strip() and model_data != col_value:
                                    model.setData(index, col_value, Qt.ItemDataRole.EditRole)
                                    updated_count += 1

                progress.setValue(len(csv_data))

                self.mw.message_box("information", ("info-success-import", {"count": updated_count}))
        except Exception as e:
            self.mw.message_box("error", ("error-import-file", {"error": str(e)}))
            return

    def _get_import_languages(self, table_langs):
        langs = self.manager.get_languages("displayed")

        if not table_langs and langs:
            self.mw.message_box("warning", "warning-no-available-languages")
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

            auto_index = 0
            # for i, lang in enumerate(langs):
            #     if csv_lang.lower() == lang.lower() or lang.lower() in csv_lang.lower():
            #         auto_index = i + 1
            #         break

            combo.setCurrentIndex(auto_index)
            grid.addWidget(combo, row, 1)
            mappings[csv_lang] = combo
            row += 1

        scroll_layout.addLayout(grid)
        scroll_widget.setLayout(scroll_layout)
        scroll_area.setWidget(scroll_widget)

        layout.addLayout(grid_title)
        layout.addWidget(scroll_area)
        layout.addWidget(button_box)

        lang_mapping = {}
        result = dialog.exec()
        if result == QDialog.DialogCode.Accepted:
            for csv_lang, combo in mappings.items():
                selected_index = combo.currentIndex() - 1
                selected_text = combo.currentText()
                if selected_index >= 0:
                    code, _ = self.manager.get_language_from_text(selected_text)
                    if code:
                        lang_mapping[csv_lang] = code

        return lang_mapping
