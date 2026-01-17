import csv
from pathlib import Path
from typing import Any

from PySide6.QtGui import Qt
from PySide6.QtWidgets import (
    QFileDialog, QVBoxLayout, QDialog, QWidget, QHBoxLayout, QScrollArea, QCheckBox,
    QLabel, QSpacerItem, QSizePolicy, QPushButton, QDialogButtonBox, QComboBox
)

from gui.helpers import message_box
from utils.app_locales import fluent, ftr
from utils.enums import (
    FileExtension as Fe,
    FileSeperator as Fs,
    LanguageDataFlags as Ldf
)
from utils.manager import manager


class ExportModule:
    def __init__(self, main_window):
        self.mw = main_window
        self.lang_selector = self.mw.lang_selector
        self.ts = fluent.tr_batch([
            "save-title", "csv-file", "tsv-file",
            "export-translations-title",
            "export-languages-label",
            "select-all-button",
            "deselect-all-button",
            "export-button", "export-button-disabled",
            "cancel-button"
        ])

        selected_languages = self._select_languages_to_export()
        if not selected_languages:
            return

        path = QFileDialog.getSaveFileName(
            self.mw, self.ts["save-title"],
            f"{manager.file_name}-exported",
            f"{self.ts['csv-file']} (*{Fe.CSV.value});;"
            f"{self.ts['tsv-file']} (*{Fe.TSV.value})"
        )[0]

        if not path:
            return

        try:
            path = Path(path)
            file_name = path.stem
            delimiter = Fs[Fe(path.suffix).name].value
            terms = manager.get_terms()
            if not terms:
                message_box(self.mw, "warning", "warning-no-terms-found")
                return

            self.mw.status_bar_message(("exporting-file-data", {"file_name": file_name}))
            self.export_selected_languages(path, delimiter, terms, selected_languages)
        except Exception as e:
            message_box(self.mw, "error", ("error-export-file", {"error": str(e)}))

    def _select_languages_to_export(self):
        languages = manager.get_languages()

        if not languages:
            message_box(self.mw, "warning", "warning-no-available-languages")
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
            LanguageCheckBox(lang["name"], lang["code"], lang["flags"], self.lang_selector)
            for lang in languages
        ]
        checkbox_layout = QVBoxLayout(scroll_area.widget())

        for w in widgets:
            w.checkbox.stateChanged.connect(lambda _: update_dialog_buttons())
            checkbox_layout.addWidget(w)
        checkbox_layout.addItem(QSpacerItem(1, 1, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        def set_all(state):
            for widget in widgets:
                if widget.isVisible():
                    widget.SetChecked(state)

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
            any_checked = any(widget.IsChecked() for widget in widgets)
            all_checked = all(widget.IsChecked() for widget in widgets)

            select_all_button.setDisabled(all_checked)
            deselect_all_button.setDisabled(not any_checked)

            ok_button = button_box.button(QDialogButtonBox.StandardButton.Ok)
            ok_button.setEnabled(any_checked)
            ok_button.setToolTip(self.ts["export-button-disabled"] if not any_checked else "")

        update_dialog_buttons()

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return {}

        selected_languages = {w.code: w.name for w in widgets if w.IsChecked()}
        if not selected_languages:
            message_box(self.mw, "warning", "warning-no-languages-selected")
            return {}

        return selected_languages

    def export_selected_languages(self, file_path: Path, delimiter: str, terms: list[dict[str, Any]], selected_languages: dict[str, str]):
        try:
            with open(file_path, "w+", encoding="utf-8", newline="") as f:
                langs = [
                    f"{name} [{code}]" if code != name.lower() else name
                    for code, name in selected_languages.items()
                ]
                fields = ["Key", "Type", "Desc"] + langs
                writer = csv.DictWriter(f, fields, delimiter=delimiter)
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
                        message_box(self.mw, "error", ("error-processing-term", {"num": index+1, "term_name": term["name"], "error": str(e)}))
                        return

            output_langs = (
                ftr("and-text", {"langs": ", ".join(list(selected_languages.values())[:-1]), "last_lang": list(selected_languages.values())[-1]})
                if len(list(selected_languages.values())) > 1 else list(selected_languages.values())[0]
            )

            self.mw.status_bar_message(("saved-file", {"file_path": str(file_path)}), 15000)
            message_box(self.mw, "information", ("info-success-export", {
                "translation_num": exported_translations, "language_num": len(selected_languages),
                "file_name": file_path.name, "languages": output_langs
            }))
        except Exception as e:
            message_box(self.mw, "error", ("error-export-languages", {"error": str(e)}))


class LanguageCheckBox(QWidget):
    def __init__(self, name: str, code: str, flags: Ldf, lang_selector: QComboBox):
        super().__init__()
        self.name = name
        self.code = code
        self.flags = flags

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        lang_name = f"{name} [{code}]" if code != name.lower() else name
        self.checkbox = QCheckBox(lang_name)

        if flags == Ldf.DISABLED:
            self.checkbox.setStyleSheet("QCheckBox { color: #808080; }")  # Gray color

        if lang_selector.currentIndex() == 0:
            self.checkbox.setChecked(True)
        elif lang_selector.currentIndex() != 0 and lang_name == lang_selector.currentText():
            self.checkbox.setChecked(True)
        else:
            self.checkbox.setChecked(False)

        layout.addWidget(self.checkbox)

    def IsChecked(self):
        return self.checkbox.isChecked()

    def SetChecked(self, arg__1):
        self.checkbox.setChecked(arg__1)

