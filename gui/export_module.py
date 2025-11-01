import os
import csv
from PySide6.QtGui import Qt
from PySide6.QtWidgets import (
    QFileDialog, QVBoxLayout, QDialog, QWidget, QHBoxLayout, QScrollArea, QCheckBox,
    QLabel, QSpacerItem, QSizePolicy, QPushButton, QDialogButtonBox, QComboBox
)
from utils.enums import (
    FileExts as FE,
    FileSeps as FS
)

class ExportModule:
    def __init__(self, main_window):
        self.mw = main_window
        self.ftr = self.mw.fluent.tr
        self.manager = self.mw.manager
        self.lang_selector = self.mw.lang_selector

        self.ts = self.mw.fluent.tr_batch([
            "save-title",
            "csv-file",
            "tsv-file",
            "export-translations-title",
            "export-languages-label",
            "select-all-button",
            "deselect-all-button",
            "export-button",
            "export-button-disabled",
            "cancel-button"
        ])

        selected_languages = self._select_languages_to_export()
        if not selected_languages:
            return

        filepath, _ = QFileDialog.getSaveFileName(
            self.mw, self.ts["save-title"],
            f"{self.manager.filename}_exported",
            f"{self.ts['csv-file']} (*{FE.CSV.value});;{self.ts['tsv-file']} (*{FE.TSV.value})"
        )

        if not filepath:
            return

        try:
            delimiter = FS[FE(os.path.splitext(filepath)[1]).name].value
            terms = self.manager.content["terms"]
            if not terms:
                self.mw.message_box("warning", "warning-no-terms-found")
                return

            self.mw.status_bar_message("exporting-language-data")
            self.export_selected_languages(filepath, delimiter, terms, selected_languages)
            self.mw.status_bar_message(("saved-file", {"file_path": filepath}), 15000)
        except Exception as e:
            self.mw.message_box("error", ("error-export-file", {"error": str(e)}))

    def _select_languages_to_export(self):
        lang_names = self.manager.get_languages("names")
        lang_codes = self.manager.get_languages("codes")

        if not lang_names and lang_codes:
            self.mw.message_box("warning", "warning-no-available-languages")
            return {}

        dialog = QDialog(self.mw)
        dialog.setWindowTitle(self.ts["export-translations-title"])
        dialog.setFixedSize(500, 400)

        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel(self.ts["export-languages-label"]))

        scroll_area = QScrollArea()
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)

        scroll_area.setWidget(QWidget())

        widgets = [
            LanguageCheckBox(name, code, self.lang_selector)
            for name, code in zip(lang_names, lang_codes)
        ]
        checkbox_layout = QVBoxLayout(scroll_area.widget())

        for w in widgets:
            w.checkbox.stateChanged.connect(lambda _: update_dialog_buttons())
            checkbox_layout.addWidget(w)
        checkbox_layout.addItem(QSpacerItem(1, 1, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        def set_all(state):
            for widget in widgets:
                if widget.isVisible():
                    widget.setChecked(state)

        button_layout = QHBoxLayout()
        select_all_button = QPushButton(self.ts["select-all-button"])
        deselect_all_button = QPushButton(self.ts["deselect-all-button"])

        for button, state in [(select_all_button, True), (deselect_all_button, False)]:
            button.clicked.connect(lambda _, s=state: set_all(s))
            button_layout.addWidget(button)
        button_layout.addStretch()
        layout.addLayout(button_layout)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.button(QDialogButtonBox.StandardButton.Ok).setText(self.ts["export-button"])
        button_box.button(QDialogButtonBox.StandardButton.Cancel).setText(self.ts["cancel-button"])
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)

        def update_dialog_buttons():
            any_checked = any(w.isChecked() for w in widgets)
            all_checked = all(w.isChecked() for w in widgets)

            select_all_button.setDisabled(all_checked)
            deselect_all_button.setDisabled(not any_checked)

            ok_button = button_box.button(QDialogButtonBox.StandardButton.Ok)
            ok_button.setEnabled(any_checked)
            ok_button.setToolTip(self.ts["export-button-disabled"] if not any_checked else "")

        update_dialog_buttons()

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return {}

        selected_languages = {w.code: w.name for w in widgets if w.isChecked()}
        if not selected_languages:
            self.mw.message_box("warning", "warning-no-languages-selected")
            return {}

        return selected_languages

    def export_selected_languages(self, filepath, delimiter, terms, selected_languages):
        try:
            with open(filepath, "w+", newline="", encoding="utf-8") as f:
                langs = [f"{name} [{code}]" if code != name.lower() else name for code, name in selected_languages.items()]
                fields = ["Key", "Type", "Desc"] + langs
                writer = csv.DictWriter(f, fieldnames=fields, delimiter=delimiter)
                writer.writeheader()

                exported_translations = 0
                for index, term in enumerate(terms):
                    try:
                        writer.writerow({
                            "Key": term["name"],
                            "Type": term["type"].displayed,
                            "Desc": term["desc"],
                            **{
                                f"{name} [{code}]" if code != name.lower() else name:
                                term["translations"][code] for code, name in selected_languages.items()
                            }
                        })
                        exported_translations += 1
                    except Exception as e:
                        self.mw.message_box("error", ("error-processing-term", {"num": index+1, "term_name": term["name"], "error": str(e)}))
                        return

            output_langs = (
                self.ftr("and-text", {"langs": ", ".join(list(selected_languages.values())[:-1]), "last_lang": list(selected_languages.values())[-1]})
                if len(list(selected_languages.values())) > 1 else list(selected_languages.values())[0]
            )

            self.mw.message_box("information", ("info-success-export", {
                "translation_num": exported_translations, "language_num": len(selected_languages),
                "filename": os.path.basename(filepath), "languages": output_langs
            }))

        except Exception as e:
            self.mw.message_box("error", ("error-export-languages", {"error": str(e)}))

class LanguageCheckBox(QWidget):
    def __init__(self, name: str, code: str, lang_selector: QComboBox):
        super().__init__()
        self.name = name
        self.code = code

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        lang_name = f"{name} [{code}]" if code != name.lower() else name
        self.checkbox = QCheckBox(lang_name)
        if lang_selector.currentIndex() == 0:
            self.checkbox.setChecked(True)
        elif lang_selector.currentIndex() != 0 and lang_name == lang_selector.currentText():
            self.checkbox.setChecked(True)
        else:
            self.checkbox.setChecked(False)

        layout.addWidget(self.checkbox)

    def isChecked(self):
        return self.checkbox.isChecked()

    def setChecked(self, arg__1):
        self.checkbox.setChecked(arg__1)
