import json
import string

from PySide6.QtCore import (
    Qt, QAbstractListModel, QModelIndex, QPersistentModelIndex
)
from PySide6.QtGui import QColor, QBrush
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGroupBox, QComboBox, QFormLayout,
    QLineEdit, QCheckBox, QRadioButton, QDialogButtonBox, QMessageBox,
    QListView, QAbstractItemView, QLabel, QPushButton
)

from gui.helpers import message_box, localize_buttons
from utils.app_locales import ftr
from utils.enums import LanguageDataFlags as Ldf
from utils.helpers import pathfind, check_language, validate_lang_code
from utils.manager import manager

with open(pathfind("assets\\languages.json"), "r", encoding="utf-8") as f:
    ISO_LANGUAGES = json.load(f)


class Language:
    def __init__(self, name: str, code: str, flags: Ldf):
        self.name = name
        self.code = code
        self.flags = flags
        self.prev_code = code
        self.is_modified = False

    def __str__(self):
        return f"{self.name} [{self.code}]" if not self.is_modified else f"{self.name} [{self.code}] *"
        # return f"{self.name} [{self.code}]" if self.code != self.name.lower() else self.name


class LanguageListWidget(QListView):
    def __init__(self):
        super().__init__()
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setAlternatingRowColors(True)


class LanguageModel(QAbstractListModel):
    def __init__(self, mw, languages):
        super().__init__()
        self.mw = mw
        if languages:
            self._languages = [
                Language(**lang) if isinstance(lang, dict) else lang
                for lang in languages
            ]

    def rowCount(self, parent: QModelIndex | QPersistentModelIndex = QModelIndex()):
        if parent.isValid():
            return 0
        return len(self._languages)

    def data(self, index: QModelIndex | QPersistentModelIndex, role: int = Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or index.row() >= len(self._languages):
            return None

        lang = self._languages[index.row()]

        if role == Qt.ItemDataRole.DisplayRole:
            return str(lang)

        elif role == Qt.ItemDataRole.ForegroundRole:
            if lang.flags == Ldf.DISABLED:
                return QBrush(QColor(128, 128, 128))

        return None

    def add_language(self, lang: Language, copy_from: int | None):
        self.mw.custom_table.model().add_language(lang.name, lang.code, lang.flags, copy_from)
        self.beginInsertRows(QModelIndex(), len(self._languages), len(self._languages))
        self._languages.append(lang)
        self.endInsertRows()

    def remove_language(self, index: int):
        if 0 <= index < len(self._languages):
            self.mw.custom_table.model().remove_language(self._languages[index].code)
            self.beginRemoveRows(QModelIndex(), index, index)
            removed = self._languages.pop(index)
            self.endRemoveRows()
            return removed
        return None

    def move_language(self, from_index: int, to_index: int):
        if 0 <= from_index < len(self._languages) and 0 <= to_index < len(self._languages):
            self.beginMoveRows(
                QModelIndex(), from_index, from_index,
                QModelIndex(), to_index + (1 if to_index > from_index else 0)
            )
            lang = self._languages.pop(from_index)
            self._languages.insert(to_index, lang)
            self.endMoveRows()
            return True
        return False

    def get_language(self, index: int):
        return self._languages[index] if 0 <= index < len(self._languages) else None

    def get_languages(self):
        return self._languages.copy()

    def language_exists(self, name: str, code: str):
        return any(lang.name == name or lang.code == code for lang in self._languages)


class LanguageManager(QDialog):
    def __init__(self, main_window):
        super().__init__(main_window)
        self.mw = main_window
        self.model = LanguageModel(self.mw, manager.get_languages())

        self.setup_ui()
        self.connect_signals()

        if self.model.rowCount() > 0:
            self.language_list.setCurrentIndex(self.model.index(0))

        self.exec()

    def setup_ui(self):
        self.setWindowTitle(ftr("ml-title"))
        self.setMinimumSize(600, 450)
        self.setMaximumSize(700, 500)

        # --- Layouts ---
        layout = QVBoxLayout(self)
        content_layout = QHBoxLayout()
        left_layout = QVBoxLayout()
        controls_layout = QVBoxLayout()

        # --- List Label ---
        list_label = QLabel(ftr("ml-languages-label"))
        list_label.setStyleSheet("font-weight: bold;")
        left_layout.addWidget(list_label)

        # --- Language List ---
        self.language_list = LanguageListWidget()
        self.language_list.setModel(self.model)
        left_layout.addWidget(self.language_list)

        content_layout.addLayout(left_layout, 2)

        # --- Reorder ---
        move_group = QGroupBox(ftr("ml-reorder-label"))
        move_layout = QVBoxLayout(move_group)

        self.up_btn = QPushButton(ftr("ml-move-up-button"))
        self.down_btn = QPushButton(ftr("ml-move-down-button"))

        move_layout.addWidget(self.up_btn)
        move_layout.addWidget(self.down_btn)
        controls_layout.addWidget(move_group)

        # --- Language Details ---
        details_group = QGroupBox(ftr("ml-details-label"))
        details_layout = QFormLayout(details_group)

        self.edit_name = QLineEdit()
        self.edit_code = QLineEdit()
        self.edit_flag = QComboBox()
        self.edit_native_checkbox = QCheckBox(ftr("add-language-native-name"))

        # self.edit_code.setMaxLength(5)
        self.edit_flag.setMaxVisibleItems(2)
        self.edit_flag.addItems([ftr(f"lang-flag-{flag.lower()}") for flag in Ldf.titles()])

        details_layout.addRow(ftr("add-language-name"), self.edit_name)
        details_layout.addRow(ftr("add-language-code"), self.edit_code)
        details_layout.addRow(ftr("add-language-flag"), self.edit_flag)
        details_layout.addWidget(self.edit_native_checkbox)

        controls_layout.addWidget(details_group)

        # --- Manage ---
        manage_group = QGroupBox(ftr("ml-manage-label"))
        manage_layout = QVBoxLayout(manage_group)

        self.add_btn = QPushButton(ftr("ml-add-language"))
        self.remove_btn = QPushButton(ftr("ml-remove-language"))

        manage_layout.addWidget(self.add_btn)
        manage_layout.addWidget(self.remove_btn)
        controls_layout.addWidget(manage_group)

        content_layout.addLayout(controls_layout, 1)
        layout.addLayout(content_layout)

        # --- Language Count ---
        self.status_label = QLabel(ftr("ml-languages-count", {"count": self.model.rowCount()}))
        self.status_label.setStyleSheet("color: #666; font-size: 11px;")
        layout.addWidget(self.status_label)

        # --- Dialog Buttons ---
        note_label = QLabel(ftr("ml-warning-desc"))
        note_label.setStyleSheet("color: #f00; font-size: 11px;")
        layout.addWidget(note_label, alignment=Qt.AlignmentFlag.AlignLeft)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        localize_buttons(button_box)
        layout.addWidget(button_box)

    def connect_signals(self):
        self.add_btn.clicked.connect(self.add_language)
        self.remove_btn.clicked.connect(self.remove_language)
        self.up_btn.clicked.connect(self.move_up)
        self.down_btn.clicked.connect(self.move_down)

        self.model.rowsInserted.connect(self.update_status)
        self.model.rowsRemoved.connect(self.update_status)

        self.language_list.selectionModel().currentChanged.connect(self.load_language_details)
        self.language_list.selectionModel().currentChanged.connect(self.update_button_states)
        self.language_list.model().rowsMoved.connect(self.update_button_states)

        self.edit_name.textEdited.connect(self.update_selected_language)
        self.edit_code.textEdited.connect(self.update_selected_language)
        self.edit_flag.textActivated.connect(self.update_selected_language)
        self.edit_native_checkbox.released.connect(self.update_selected_language)

    def update_status(self):
        self.status_label.setText(ftr("ml-languages-count", {"count": self.model.rowCount()}))

    def update_button_states(self):
        current_index = self.language_list.currentIndex()
        has_selection = current_index.isValid()
        row = current_index.row() if has_selection else -1
        item = self.model.get_language(row) if has_selection else None

        self.remove_btn.setEnabled(has_selection)
        self.up_btn.setEnabled(has_selection and row > 0)
        self.down_btn.setEnabled(has_selection and row < self.model.rowCount() - 1)

        if item:
            self.edit_name.setEnabled(True)
            self.edit_code.setEnabled(True)
            self.edit_flag.setEnabled(True)
            self.edit_native_checkbox.setEnabled(item.code in ISO_LANGUAGES)

    def add_language(self):
        dialog = AddLanguageDialog(self, self.model.get_languages())

        if dialog.exec():
            data = dialog.get_language_data()

            if not data:
                return

            new_lang = Language(data["name"], data["code"], data["flags"])
            new_lang.is_modified = True

            copy_from = None
            if data["copy_from"] is not None:
                copy_from = self.get_languages()[data["copy_from"]].code

            self.model.add_language(new_lang, copy_from)

            last_index = self.model.index(self.model.rowCount() - 1)
            self.language_list.setCurrentIndex(last_index)

    def remove_language(self):
        current_index = self.language_list.currentIndex()
        if not current_index.isValid():
            return

        lang = self.model.get_language(current_index.row())
        if not lang:
            return

        reply = message_box(
            self.mw, "question", ("confirm-language-removal", {"language": f"{lang.name} [{lang.code}]"}),
            standard_buttons=(
                QMessageBox.StandardButton.Yes
                | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.model.remove_language(current_index.row())

    def update_languages(self):
        if manager.content:
            manager.content["languages"] = [
                {"name": lang.name, "code": lang.code, "flags": lang.flags}
                for lang in self.model.get_languages()
            ]
            self.mw.update_lang_selector()

    def move_up(self):
        current_index = self.language_list.currentIndex()
        if current_index.isValid() and current_index.row() > 0:
            row = current_index.row()
            if self.model.move_language(row, row - 1):
                new_index = self.model.index(row - 1)
                self.language_list.setCurrentIndex(new_index)
                self.update_languages()

    def move_down(self):
        current_index = self.language_list.currentIndex()
        if current_index.isValid() and current_index.row() < self.model.rowCount() - 1:
            row = current_index.row()
            if self.model.move_language(row, row + 1):
                new_index = self.model.index(row + 1)
                self.language_list.setCurrentIndex(new_index)
                self.update_languages()

    def load_language_details(self, current: QModelIndex):
        lang = self.model.get_language(current.row())
        if not lang:
            self.edit_name.clear()
            self.edit_code.clear()
            self.edit_flag.setEnabled(False)
            self.edit_native_checkbox.setEnabled(False)
            self.edit_native_checkbox.setChecked(False)
            return

        self.edit_name.setText(lang.name)
        self.edit_code.setText(lang.code)
        self.edit_flag.setCurrentIndex(Ldf[lang.flags])

        english_name = ISO_LANGUAGES.get(lang.code, {}).get("name")
        native_name = ISO_LANGUAGES.get(lang.code, {}).get("native")
        enabled = bool(native_name) and english_name != native_name
        checked = enabled and lang.name == native_name

        self.edit_native_checkbox.setEnabled(enabled)
        self.edit_native_checkbox.setChecked(checked)

    def update_selected_language(self):
        current_index = self.language_list.currentIndex()
        lang = self.model.get_language(current_index.row())
        if not lang:
            return

        original_lang = lang

        name = self.edit_name.text().strip()
        code = self.edit_code.text().strip()

        valid_code = validate_lang_code(code)
        if valid_code != code:
            self.edit_code.setText(valid_code)
            return

        code = valid_code
        flag = Ldf(self.edit_flag.currentIndex())

        for other in self.model.get_languages():
            if other is not lang and other.code.lower() == code.lower():
                message_box(self.mw, "warning", ("warning-duplicate-code", {"code": code}))
                self.edit_code.setText(lang.prev_code)
                return

        if code in ISO_LANGUAGES:
            english_name, native_name = ISO_LANGUAGES[code].values()
            if self.edit_native_checkbox.isChecked():
                if name in (english_name, ""):
                    name = native_name
            else:
                if name in (native_name, ""):
                    name = english_name

        self.edit_name.setText(name)
        self.edit_code.setText(code)

        has_changed = (
            name != original_lang.name or
            code != original_lang.code or
            flag != original_lang.flags
        )

        lang.name = name
        lang.code = code
        lang.flags = flag

        if has_changed:
            lang.is_modified = True

        idx = self.model.index(current_index.row())
        self.model.dataChanged.emit(idx, idx)

        if len(code) >= 2:
            self.update_languages()
            manager.update_code_entries(lang.prev_code, code)
            lang.prev_code = code

    def get_languages(self):
        return self.model.get_languages()


class AddLanguageDialog(QDialog):
    def __init__(self, parent, existing_languages):
        super().__init__(parent)
        self.existing_languages = existing_languages or []
        self.mw = parent.mw
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle(ftr("add-language-title"))
        self.setFixedSize(400, 350)

        layout = QVBoxLayout(self)

        self.lang_combo = QComboBox()
        self.lang_combo.setMaxVisibleItems(8)
        self.lang_combo.addItem(ftr("add-language-manually"))

        for code, data in sorted(ISO_LANGUAGES.items(), key=lambda x: x[1]["name"]):
            name = data["name"]
            native = data["native"]
            display_text = f"{name} | {native} [{code}]" if name != native else f"{name} [{code}]"
            self.lang_combo.addItem(display_text, code)

        layout.addWidget(self.lang_combo)

        # --- Manual Entry ---
        manual_group = QGroupBox(ftr("add-language-details"))
        manual_layout = QFormLayout(manual_group)

        self.name_edit = QLineEdit()
        self.code_edit = QLineEdit()
        self.flag_edit = QComboBox()
        self.native_checkbox = QCheckBox(ftr("add-language-native-name"))

        # self.code_edit.setMaxLength(5)
        self.native_checkbox.setEnabled(False)
        self.flag_edit.setMaxVisibleItems(2)
        self.flag_edit.addItems(Ldf.titles())

        manual_layout.addRow(ftr("add-language-name"), self.name_edit)
        manual_layout.addRow(ftr("add-language-code"), self.code_edit)
        manual_layout.addRow(ftr("add-language-flag"), self.flag_edit)
        manual_layout.addWidget(self.native_checkbox)
        layout.addWidget(manual_group)

        layout.addStretch()

        # --- Copy Options ---
        copy_group = QGroupBox(ftr("add-language-initialize"))
        copy_layout = QVBoxLayout(copy_group)

        self.empty_radio = QRadioButton(ftr("add-language-initialize-option-1"))
        self.empty_radio.setChecked(True)
        self.copy_radio = QRadioButton(ftr("add-language-initialize-option-2"))

        copy_layout.addWidget(self.empty_radio)
        copy_layout.addWidget(self.copy_radio)

        self.copy_combo = QComboBox()
        self.copy_combo.setEnabled(False)
        self.populate_copy_combo()

        copy_layout.addWidget(self.copy_combo)
        layout.addWidget(copy_group)

        # --- Dialog Buttons ---
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.validate_before_accept)
        button_box.rejected.connect(self.reject)
        localize_buttons(button_box)
        layout.addWidget(button_box)

        # --- Connect Signals ---
        self.lang_combo.currentIndexChanged.connect(self.on_language_selected)
        self.copy_radio.toggled.connect(self.copy_combo.setEnabled)
        self.native_checkbox.toggled.connect(self.on_native_checkbox_toggled)
        self.code_edit.textChanged.connect(self.on_code_changed)

    def on_native_checkbox_toggled(self, checked: bool):
        code = self.code_edit.text()
        if code in ISO_LANGUAGES:
            eng_name, native = ISO_LANGUAGES[code].values()
            self.name_edit.setText(native if checked else eng_name)

    def on_code_changed(self, code: str):
        valid_code = validate_lang_code(code)
        if valid_code != code:
            self.code_edit.setText(valid_code)

        self.native_checkbox.setEnabled(valid_code in ISO_LANGUAGES)
        if valid_code in ISO_LANGUAGES:
            eng_name, native = ISO_LANGUAGES[valid_code].values()
            self.name_edit.setText(native if self.native_checkbox.isChecked() else eng_name)

    def populate_copy_combo(self):
        self.copy_combo.clear()
        for lang in self.existing_languages:
            self.copy_combo.addItem(str(lang))

    def on_language_selected(self, index: int):
        if index == 0:  # Manual entry
            self.name_edit.clear()
            self.code_edit.clear()
        else:
            code = self.lang_combo.itemData(index)
            if code and code in ISO_LANGUAGES:
                eng_name, native_name = ISO_LANGUAGES[code].values()
                if self.native_checkbox.isChecked():
                    name = native_name
                else:
                    name = eng_name
                self.name_edit.setText(name)
                self.native_checkbox.setEnabled(True)
                self.code_edit.setText(code)

    def validate_before_accept(self):
        name = self.name_edit.text().strip()
        code = self.code_edit.text().strip()
        flags = Ldf(self.flag_edit.currentIndex())

        if code not in string.ascii_letters and code in string.digits:
            message_box(self.mw, "warning", "warning-invalid-code-letters")
            return

        for lang in self.existing_languages:
            if lang.code.lower() == code.lower():
                message_box(self.mw, "warning", ("warning-duplicate-code", {"code": code}))
                return

        title, msg = check_language(name, code, flags, self.existing_languages)
        if title and msg:
            message_box(self.mw, title, msg)
            return

        self.accept()

    def get_language_data(self):
        name = self.name_edit.text().strip()
        code = self.code_edit.text().strip()
        flags = Ldf(self.flag_edit.currentIndex())
        copy_from = None

        if self.copy_radio.isChecked() and self.copy_combo.currentIndex() >= 0:
            copy_from = self.copy_combo.currentIndex()

        return {
            "name": name,
            "code": code,
            "flags": flags,
            "copy_from": copy_from
        }

