import json
from PySide6.QtCore import (
    Qt, QAbstractListModel, QModelIndex, QPersistentModelIndex
)
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGroupBox, QComboBox, QFormLayout,
    QLineEdit, QCheckBox, QRadioButton, QDialogButtonBox, QMessageBox,
    QListView, QAbstractItemView, QLabel, QPushButton
)
from utils.enums import LanguageDataFlags as LDF
from utils.helpers import pathfind, check_language

with open(pathfind("assets\\languages.json"), "r", encoding="utf-8") as f:
    ISO_LANGUAGES = json.load(f)

class Language:
    def __init__(self, name, code, flags):
        self.name = name
        self.code = code
        self.flags = flags

    def __str__(self):
        return f"{self.name} [{self.code}]"
        # return f"{self.name} [{self.code}]" if self.code != self.name.lower() else self.name

class LanguageModel(QAbstractListModel):
    def __init__(self, mw, languages=None):
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

        if role == Qt.ItemDataRole.DisplayRole:
            return str(self._languages[index.row()])

        return None

    def add_language(self, lang, copy_from):
        self.mw.custom_table.model().add_language(lang.name, lang.code, lang.flags, copy_from)
        self.beginInsertRows(QModelIndex(), len(self._languages), len(self._languages))
        self._languages.append(lang)
        self.endInsertRows()

    def remove_language(self, index):
        if 0 <= index < len(self._languages):
            self.mw.custom_table.model().remove_language(self._languages[index].code)
            self.beginRemoveRows(QModelIndex(), index, index)
            removed = self._languages.pop(index)
            self.endRemoveRows()
            return removed
        return None

    def move_language(self, from_index, to_index):
        if 0 <= from_index < len(self._languages) and 0 <= to_index < len(self._languages):
            self.beginMoveRows(QModelIndex(), from_index, from_index,
                            QModelIndex(), to_index + (1 if to_index > from_index else 0))
            lang = self._languages.pop(from_index)
            self._languages.insert(to_index, lang)
            self.endMoveRows()
            return True
        return False

    def get_language(self, index):
        return self._languages[index] if 0 <= index < len(self._languages) else None

    def get_languages(self):
        return self._languages.copy()

    def language_exists(self, name, code):
        return any(lang.name == name or lang.code == code for lang in self._languages)

class AddLanguageDialog(QDialog):
    def __init__(self, parent, existing_languages=None):
        super().__init__(parent)
        self.existing_languages = existing_languages or []
        self.mw = parent.mw
        self.fluent = parent.fluent
        self.ftr = self.fluent.tr
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle(self.ftr("add-language-title"))
        self.setFixedSize(400, 350)

        layout = QVBoxLayout(self)

        self.lang_combo = QComboBox()
        self.lang_combo.setMaxVisibleItems(8)
        self.lang_combo.addItem(self.ftr("add-language-manually"))

        for code, data in sorted(ISO_LANGUAGES.items(), key=lambda x: x[1]["name"]):
            name = data["name"]
            native = data["native"]
            self.lang_combo.addItem(f"{name} / {native} [{code}]", code)

        layout.addWidget(self.lang_combo)

        # --- Manual Entry ---
        manual_group = QGroupBox(self.ftr("add-language-details"))
        manual_layout = QFormLayout(manual_group)

        self.name_edit = QLineEdit()
        self.code_edit = QLineEdit()
        self.flag_edit = QComboBox()
        self.native_checkbox = QCheckBox(self.ftr("add-language-native-name"))

        # self.code_edit.setMaxLength(5)
        self.native_checkbox.setEnabled(False)
        self.flag_edit.setMaxVisibleItems(2)
        self.flag_edit.addItems(LDF.titles())

        manual_layout.addRow(self.ftr("add-language-name"), self.name_edit)
        manual_layout.addRow(self.ftr("add-language-code"), self.code_edit)
        manual_layout.addRow(self.ftr("add-language-flag"), self.flag_edit)
        manual_layout.addWidget(self.native_checkbox)
        layout.addWidget(manual_group)

        layout.addStretch()

        # --- Copy Options ---
        copy_group = QGroupBox(self.ftr("add-language-initialize"))
        copy_layout = QVBoxLayout(copy_group)

        self.empty_radio = QRadioButton(self.ftr("add-language-initialize-option-1"))
        self.empty_radio.setChecked(True)
        self.copy_radio = QRadioButton(self.ftr("add-language-initialize-option-2"))

        copy_layout.addWidget(self.empty_radio)
        copy_layout.addWidget(self.copy_radio)

        self.copy_combo = QComboBox()
        self.copy_combo.setEnabled(False)
        self.populate_copy_combo()

        copy_layout.addWidget(self.copy_combo)
        layout.addWidget(copy_group)

        # --- Dialog Buttons ---
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok |
                                 QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.validate_before_accept)
        button_box.rejected.connect(self.reject)
        self.mw.localise_buttons(button_box)
        layout.addWidget(button_box)

        # --- Connect Signals ---
        self.lang_combo.currentIndexChanged.connect(self.on_language_selected)
        self.copy_radio.toggled.connect(self.copy_combo.setEnabled)
        self.native_checkbox.toggled.connect(self.on_native_checkbox_toggled)
        self.code_edit.textChanged.connect(self.on_code_changed)

    def on_native_checkbox_toggled(self, checked):
        code = self.code_edit.text()
        if code in ISO_LANGUAGES:
            eng_name, native = ISO_LANGUAGES[code].values()
            self.name_edit.setText(native if checked else eng_name)

    def on_code_changed(self, code):
        self.native_checkbox.setEnabled(code in ISO_LANGUAGES)
        if code in ISO_LANGUAGES:
            eng_name, native = ISO_LANGUAGES[code].values()
            self.name_edit.setText(native if self.native_checkbox.isChecked() else eng_name)

    def populate_copy_combo(self):
        self.copy_combo.clear()
        for lang in self.existing_languages:
            self.copy_combo.addItem(str(lang))

    def on_language_selected(self, index):
        if index == 0: # Manual entry
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
        flags = LDF(self.flag_edit.currentIndex())

        for lang in self.existing_languages:
            if lang.name.lower() == name.lower():
                self.mw.message_box("warning", ("warning-duplicate-language", {"name": name}))
                return
            if lang.code.lower() == code.lower():
                self.mw.message_box("warning", ("warning-duplicate-code", {"code": code}))
                return

        title, msg = check_language(name, code, flags, self.existing_languages)
        if title and msg:
            self.mw.message_box(title, msg)
            return

        self.accept()

    def get_language_data(self):
        name = self.name_edit.text().strip()
        code = self.code_edit.text().strip()
        flags = LDF(self.flag_edit.currentIndex())
        copy_from = None

        if self.copy_radio.isChecked() and self.copy_combo.currentIndex() >= 0:
            copy_from = self.copy_combo.currentIndex()

        return {
            "name": name,
            "code": code,
            "flags": flags,
            "copy_from": copy_from
        }

class LanguageListWidget(QListView):
    def __init__(self):
        super().__init__()
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setAlternatingRowColors(True)

class LanguageManager(QDialog):
    def __init__(self, main_window):
        super().__init__(main_window)
        self.mw = main_window
        self.fluent = self.mw.fluent
        self.ftr = self.fluent.tr
        self.manager = self.mw.manager

        self.model = LanguageModel(self.mw, self.manager.get_languages())

        self.setup_ui()
        self.connect_signals()

        if self.model.rowCount() > 0:
            self.language_list.setCurrentIndex(self.model.index(0))

        self.exec()

    def setup_ui(self):
        self.setWindowTitle(self.ftr("ml-title"))
        self.setMinimumSize(600, 400)
        self.setMaximumSize(700, 500)
        self.setSizeGripEnabled(False)

        # --- Layouts ---
        layout = QVBoxLayout(self)
        content_layout = QHBoxLayout()
        left_layout = QVBoxLayout()
        controls_layout = QVBoxLayout()

        # --- List Label ---
        list_label = QLabel(self.ftr("ml-languages-label"))
        list_label.setStyleSheet("font-weight: bold;")
        left_layout.addWidget(list_label)

        # --- Language List ---
        self.language_list = LanguageListWidget()
        self.language_list.setModel(self.model)
        left_layout.addWidget(self.language_list)

        content_layout.addLayout(left_layout, 2)

        # --- Reorder ---
        move_group = QGroupBox(self.ftr("ml-reorder-label"))
        move_layout = QVBoxLayout(move_group)

        self.up_btn = QPushButton(self.ftr("ml-move-up-button"))
        self.down_btn = QPushButton(self.ftr("ml-move-down-button"))

        move_layout.addWidget(self.up_btn)
        move_layout.addWidget(self.down_btn)
        controls_layout.addWidget(move_group)

        # --- Language Details ---
        details_group = QGroupBox(self.ftr("ml-details-label"))
        details_layout = QFormLayout(details_group)

        self.edit_name = QLineEdit()
        self.edit_code = QLineEdit()
        self.edit_flag = QComboBox()
        self.edit_native_checkbox = QCheckBox(self.ftr("add-language-native-name"))

        # self.edit_code.setMaxLength(5)
        self.edit_flag.setMaxVisibleItems(2)
        self.edit_flag.addItems(LDF.titles())

        details_layout.addRow(self.ftr("add-language-name"), self.edit_name)
        details_layout.addRow(self.ftr("add-language-code"), self.edit_code)
        details_layout.addRow(self.ftr("add-language-flag"), self.edit_flag)
        details_layout.addWidget(self.edit_native_checkbox)

        controls_layout.addWidget(details_group)

        # --- Manage ---
        manage_group = QGroupBox(self.ftr("ml-manage-label"))
        manage_layout = QVBoxLayout(manage_group)

        self.add_btn = QPushButton(self.ftr("ml-add-language"))
        self.remove_btn = QPushButton(self.ftr("ml-remove-language"))

        manage_layout.addWidget(self.add_btn)
        manage_layout.addWidget(self.remove_btn)
        controls_layout.addWidget(manage_group)

        content_layout.addLayout(controls_layout, 1)
        layout.addLayout(content_layout)

        # --- Language Count ---
        self.status_label = QLabel(self.ftr("ml-languages-count", {"count": self.model.rowCount()}))
        self.status_label.setStyleSheet("color: #666; font-size: 11px;")
        layout.addWidget(self.status_label)

        # --- Dialog Buttons ---
        note_label = QLabel(self.ftr("ml-warning-desc"))
        note_label.setStyleSheet("color: #f00; font-size: 11px;")
        layout.addWidget(note_label, alignment=Qt.AlignmentFlag.AlignLeft)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        self.mw.localise_buttons(button_box)
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
        self.edit_native_checkbox.released.connect(self.update_selected_language)

    def update_status(self):
        self.status_label.setText(self.ftr("ml-languages-count", {"count": self.model.rowCount()}))

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

        reply = self.mw.message_box(
            "question", ("confirm-language-removal", {"language": f"{lang.name} [{lang.code}]"}),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.model.remove_language(current_index.row())

    def update_languages(self):
        if self.mw.manager.content:
            self.mw.manager.content["languages"] = [
                {"name": lang.name, "code": lang.code, "flags": lang.flags}
                for lang in self.model.get_languages()
            ]
            self.mw.update_lang_selector()
            self.mw.update_table()

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
        if (current_index.isValid() and
            current_index.row() < self.model.rowCount() - 1):
            row = current_index.row()
            if self.model.move_language(row, row + 1):
                new_index = self.model.index(row + 1)
                self.language_list.setCurrentIndex(new_index)
                self.update_languages()

    def load_language_details(self, current):
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
        self.edit_flag.setCurrentIndex(LDF._value(lang.flags))

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

        name = self.edit_name.text().strip()
        code = self.edit_code.text().strip()
        flag = LDF(self.edit_flag.currentIndex())

        if code in ISO_LANGUAGES:
            english_name, native_name = ISO_LANGUAGES[code].values()
            if self.edit_native_checkbox.isChecked():
                if name in (english_name, ""):
                    name  = native_name
            else:
                if name in (native_name, ""):
                    name  = english_name

        self.edit_name.setText(name)
        # if code == name.lower():
        #     self.edit_code.clear()

        lang.name = name
        lang.code = code
        lang.flags = flag

        idx = self.model.index(current_index.row())
        self.model.dataChanged.emit(idx, idx)
        self.update_languages()

    def get_languages(self):
        return self.model.get_languages()
