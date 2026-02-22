import csv
from pathlib import Path
from typing import Any

from PySide6.QtGui import Qt
from PySide6.QtWidgets import (
    QFileDialog, QVBoxLayout, QDialog, QWidget, QHBoxLayout, QScrollArea, QCheckBox, QLabel,
    QSpacerItem, QSizePolicy, QDialogButtonBox, QComboBox, QGroupBox, QGridLayout, )

from gui.helpers import ConfigurableComboBox, message_box, push_button, ConfigurableLineEdit
from utils.app_locales import ftr
from utils.enums import (
    FileExtension as Fe,
    FileSeperator as Fs,
    LanguageDataFlags as Ldf,
)
from utils.manager import manager


class CsvOptions:
    def __init__(
            self,
            quoting: int = csv.QUOTE_MINIMAL,
            quote_char: str = "\"",
            line_terminator: str = "\r\n",
            escape_char: str | None = None
    ):
        self.quoting = quoting
        self.quote_char = quote_char
        self.line_terminator = line_terminator
        self.escape_char = escape_char


class ExportModule:
    def __init__(self, main_window):
        self.mw = main_window
        self.lang_selector = self.mw.lang_selector

        result = self._select_languages_to_export()
        if not result:
            return

        selected_languages, csv_options = result

        path = QFileDialog.getSaveFileName(
            self.mw, ftr("save-title"),
            f"{manager.file_name}-EXPORT",
            f"{ftr('csv-file')} (*{Fe.CSV.value});;"
            f"{ftr('tsv-file')} (*{Fe.TSV.value})"
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
            self.export_selected_languages(path, delimiter, terms, selected_languages, csv_options)
        except Exception as e:
            message_box(self.mw, "error", ("error-export-file", {"error": str(e)}))

    def _select_languages_to_export(self):
        languages = manager.get_languages()

        if not languages:
            message_box(self.mw, "warning", "warning-no-available-languages")
            return None

        dialog = QDialog(self.mw)
        dialog.setMinimumSize(750, 400)
        dialog.setMaximumSize(800, 450)
        dialog.setContentsMargins(5, 5, 5, 5)
        dialog.setWindowTitle(ftr("export-translations-title"))

        main_layout = QVBoxLayout(dialog)
        sub_layout = QHBoxLayout()

        # === Languages List ===
        left_layout = QVBoxLayout()
        left_layout.addWidget(QLabel(ftr("export-languages-label")))

        scroll_area = QScrollArea()
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setWidgetResizable(True)
        left_layout.addWidget(scroll_area)

        scroll_area.setWidget(QWidget())

        widgets = [
            LanguageCheckBox(idx, lang["name"], lang["code"], lang["flags"], self.lang_selector)
            for idx, lang in enumerate(languages)
        ]
        checkbox_layout = QVBoxLayout(scroll_area.widget())

        for w in widgets:
            w.checkbox.stateChanged.connect(lambda _: update_dialog_buttons())
            checkbox_layout.addWidget(w)
        checkbox_layout.addItem(QSpacerItem(1, 1, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        def set_all(state):
            for widget in widgets:
                if widget.isVisible():
                    widget.set_checked(state)

        button_layout = QHBoxLayout()
        select_all_button = push_button(ftr("select-all-button"), 60, 30, 160, 35)
        deselect_all_button = push_button(ftr("deselect-all-button"), 60, 30, 160, 35)

        for button, state in [(select_all_button, True), (deselect_all_button, False)]:
            button.clicked.connect(lambda _, s=state: set_all(s))
            button_layout.addWidget(button)
        button_layout.addStretch()
        left_layout.addLayout(button_layout)

        # === Advanced CSV Options ===
        right_layout = QVBoxLayout()
        right_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        csv_group = QGroupBox(ftr("export-advanced-options-title"))
        csv_grid = QGridLayout(csv_group)
        csv_grid.setColumnMinimumWidth(0, 120)

        csv_grid.addWidget(QLabel(ftr("export-quoting-label")), 0, 0)
        quoting_combo = ConfigurableComboBox(
            [(f"{ftr('export-quoting-minimal')} {ftr('default-label')}", csv.QUOTE_MINIMAL),
             (ftr("export-quoting-all-fields"), csv.QUOTE_ALL),
             (ftr("export-quoting-non-numeric"), csv.QUOTE_NONNUMERIC),
             (ftr("export-quoting-none"), csv.QUOTE_NONE)],
            "export.quoting",
            maxVisibleItems=3
        )
        csv_grid.addWidget(quoting_combo, 0, 1)

        csv_grid.addWidget(QLabel(ftr("export-quote-character-label")), 1, 0)
        quote_char_combo = ConfigurableComboBox(
            [(f"\" {ftr('default-label')}", "\""), ("'", "'")],
            "export.quote_character"
        )
        csv_grid.addWidget(quote_char_combo, 1, 1)

        csv_grid.addWidget(QLabel(ftr("export-escape-character-label")), 2, 0)
        escape_char_edit = ConfigurableLineEdit(
            "export.escape_character",
            placeholderText=ftr("export-escape-character-optional"),
            maxLength=1
        )
        escape_char_edit.setMaximumWidth(200)
        csv_grid.addWidget(escape_char_edit, 2, 1)

        csv_grid.addWidget(QLabel(ftr("export-line-ending-label")), 3, 0)
        line_terminator_combo = ConfigurableComboBox(
            [("CRLF - Windows (\\r\\n)", "\r\n"),
             ("LF - Unix & macOS (\\n)", "\n"),
             ("CR - Classic Mac OS (\\r)", "\r")],
            "export.line_terminator"
        )
        csv_grid.addWidget(line_terminator_combo, 3, 1)

        def on_quoting_changed():
            if quoting_combo.currentData() == csv.QUOTE_NONE:
                text = ftr("export-escape-character-required")
            else:
                text = ftr("export-escape-character-optional")

            escape_char_edit.setPlaceholderText(text)

        quoting_combo.currentIndexChanged.connect(on_quoting_changed)

        right_layout.addWidget(csv_group)
        sub_layout.addLayout(left_layout)
        sub_layout.addLayout(right_layout)
        main_layout.addLayout(sub_layout)

        # === Dialog Buttons ===
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )

        export_button = button_box.button(QDialogButtonBox.StandardButton.Ok)
        export_button.setMinimumSize(60, 30)
        export_button.setMaximumSize(160, 35)
        export_button.setText(ftr("export-button"))

        cancel_button = button_box.button(QDialogButtonBox.StandardButton.Cancel)
        cancel_button.setMinimumSize(60, 30)
        cancel_button.setMaximumSize(160, 35)
        cancel_button.setText(ftr("cancel-button"))

        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)

        main_layout.addWidget(button_box)

        def update_dialog_buttons():
            any_checked = any(widget.is_checked() for widget in widgets)
            all_checked = all(widget.is_checked() for widget in widgets)

            select_all_button.setDisabled(all_checked)
            deselect_all_button.setDisabled(not any_checked)

            ok_button = button_box.button(QDialogButtonBox.StandardButton.Ok)
            ok_button.setEnabled(any_checked)
            ok_button.setToolTip(ftr("export-button-disabled") if not any_checked else "")

        update_dialog_buttons()

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return None

        selected_languages = [
            (w.index, w.name, w.code)
            for w in widgets if w.is_checked()
        ]

        if not selected_languages:
            message_box(self.mw, "warning", "warning-no-languages-selected")
            return None

        escape_char_value = escape_char_edit.text().strip()
        csv_options = CsvOptions(
            quoting_combo.currentData(),
            quote_char_combo.currentData(),
            line_terminator_combo.currentData(),
            escape_char_value
        )

        return selected_languages, csv_options

    def export_selected_languages(
            self,
            file_path: Path,
            delimiter: str,
            terms: list[dict[str, Any]],
            selected_languages: list,
            csv_options: CsvOptions | None = None
    ):
        if csv_options is None:
            csv_options = CsvOptions()

        writer_kwargs = dict(
            delimiter=delimiter,
            quoting=csv_options.quoting,
            quotechar=csv_options.quote_char,
            lineterminator=csv_options.line_terminator,
        )
        if csv_options.escape_char:
            writer_kwargs["escapechar"] = csv_options.escape_char

        try:
            with open(file_path, "w+", encoding="utf-8", newline="") as f:
                fields = ["Key", "Type", "Desc"]
                fields.extend([
                    f"{name} [{code}]" if code else name
                    for _, name, code in selected_languages
                ])
                writer = csv.DictWriter(f, fields, **writer_kwargs)
                writer.writeheader()

                exported_translations = 0
                for term_idx, term in enumerate(terms):
                    try:
                        row_data = {
                            "Key": term["name"],
                            "Type": term["type"].displayed,
                            "Desc": term["desc"]
                        }

                        for lang_idx, name, code in selected_languages:
                            display_text = f"{name} [{code}]" if code else name
                            row_data[display_text] = manager.get_translation(term_idx, lang_idx)

                        writer.writerow(row_data)
                        exported_translations += 1
                    except Exception as e:
                        message_box(
                            self.mw, "error", ("error-processing-term", {
                                "num": term_idx + 1,
                                "term_name": term["name"],
                                "error": str(e)
                            }))
                        return

            lang_displays = [f"{name} [{code}]" if code else name for _, name, code in selected_languages]
            output_langs = (
                ftr("and-text", {
                    "langs": ", ".join(lang_displays[:-1]),
                    "last_lang": lang_displays[-1]})
                if len(lang_displays) > 1 else lang_displays[0]
            )

            self.mw.status_bar_message(("saved-file", {"file_path": str(file_path)}), 15000)
            message_box(self.mw, "information", ("info-success-export", {
                "translation_num": exported_translations,
                "language_num": len(selected_languages),
                "file_name": file_path.name,
                "languages": output_langs
            }))
        except Exception as e:
            message_box(self.mw, "error", ("error-export-languages", {"error": str(e)}))


class LanguageCheckBox(QWidget):
    def __init__(self, index: int, name: str, code: str, flags: Ldf, lang_selector: QComboBox):
        super().__init__()
        self.index = index
        self.name = name
        self.code = code
        self.flags = flags

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        lang_name = f"{name} [{code}]" if code else name
        self.checkbox = QCheckBox(lang_name)

        if flags == Ldf.DISABLED:
            self.checkbox.setStyleSheet("QCheckBox { color: #808080; }")

        if lang_selector.currentIndex() == 0:
            self.checkbox.setChecked(True)
        elif lang_name == lang_selector.currentText():
            self.checkbox.setChecked(True)
        else:
            self.checkbox.setChecked(False)

        layout.addWidget(self.checkbox)

    def is_checked(self):
        return self.checkbox.isChecked()

    def set_checked(self, state: bool):
        self.checkbox.setChecked(state)
