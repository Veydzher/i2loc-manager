from typing import Any, Sequence

from PySide6.QtCore import (
    Qt, QTimer, QAbstractTableModel, QModelIndex, QPersistentModelIndex
)
from PySide6.QtGui import QFontMetrics, QUndoStack, QUndoCommand
from PySide6.QtWidgets import (
    QTableView, QSizePolicy, QAbstractScrollArea, QHeaderView, QAbstractButton,
    QLabel, QApplication, QStyledItemDelegate, QTextEdit
)

from gui.helpers import message_box
from utils.enums import TermType, LanguageDataFlags as Ldf
from utils.helpers import check_language
from utils.manager import manager


class CustomTableModel(QAbstractTableModel):
    def __init__(self, mw, terms, langs):
        super().__init__()
        self.columns = None
        self.langs = None
        self.lang_columns = None
        self.terms = None

        self.mw = mw
        self.base_fields = [
            ("Key", "name"),
            ("Type", "type"),
            ("Desc", "desc")
        ]

        self.undo_stack = QUndoStack()
        self.undo_stack.canUndoChanged.connect(self._enable_undo)
        self.undo_stack.canRedoChanged.connect(self._enable_redo)

        self.update_data(terms, langs)

    def rowCount(self, parent: QModelIndex = QModelIndex()):
        if self.terms:
            return len(self.terms)

        return 0

    def columnCount(self, parent: QModelIndex = QModelIndex()):
        if self.columns:
            return len(self.columns)

        return 0

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None

        if role == Qt.ItemDataRole.TextAlignmentRole:
            return Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignLeft

        row, column = index.row(), index.column()
        if row >= len(self.terms) or column >= len(self.columns):
            return None

        term = self.terms[row]
        _, key = self.columns[column]

        if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
            if key in (column[1] for column in self.base_fields):
                text = term.get(key, "")
                if isinstance(text, TermType):
                    text = text.displayed
                return text

            return manager.get_translation(row, key)

        return None

    def setData(self, index: QModelIndex, value: Any, role: int = Qt.ItemDataRole.EditRole):
        if not index.isValid() or role != Qt.ItemDataRole.EditRole:
            return False

        row, column = index.row(), index.column()
        if row >= len(self.terms) or column >= len(self.columns):
            return False

        term = self.terms[row]
        _, key = self.columns[column]

        if key in (c[1] for c in self.base_fields):
            old_value = term.get(key, "")
        else:
            old_value = manager.get_translation(row, key)

        if old_value == value:
            return False

        ecmd = EditCommand(self, row, column, (old_value, value))
        self.undo_stack.push(ecmd)
        return True

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole):
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        if orientation == Qt.Orientation.Horizontal:
            return self.columns[section][0]

        return section + 1

    def flags(self, index: QModelIndex | QPersistentModelIndex):
        if not index.isValid():
            return Qt.ItemFlag.ItemIsEnabled

        _, key = self.columns[index.column()]
        if key in (f[1] for f in self.base_fields):
            return Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled

        return Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsEditable

    def apply_cell(self, row, column, value):
        term = self.terms[row]
        _, key = self.columns[column]

        if key in (c[1] for c in self.base_fields):
            term[key] = value
        else:
            manager.set_translation(row, key, value)

        index = self.index(row, column)
        self.dataChanged.emit(index, index, [Qt.ItemDataRole.DisplayRole])

    def update_data(self, terms, langs):
        self.beginResetModel()
        self.terms = terms
        self.langs = langs

        all_languages = manager.get_languages_copy()

        self.lang_columns = []
        for lang in self.langs:
            name = lang["name"]
            code = lang["code"]
            display_name = f"{name} [{code}]" if code else name
            self.lang_columns.append((display_name, all_languages.index(lang)))

        self.columns = self.base_fields + self.lang_columns
        self.endResetModel()

    def add_language(self, name: str, code: str, flags: Ldf, copy_lang_index: int | None = None):
        title, msg = check_language(name, code, flags, manager.get_languages())
        if title and msg:
            message_box(self.mw, title, msg)
            return None, None

        lang_idx, lang_data = manager.add_language(name, code, flags, copy_lang_index)
        self.mw.update_lang_selector()
        return lang_idx, lang_data

    def remove_language(self, lang_index: int):
        manager.remove_language(lang_index)
        self.mw.update_lang_selector()

    def add_term(
            self,
            term_name: str = "",
            term_type: TermType = TermType.TEXT,
            term_desc: str = "",
            translations: list[str] | None = None,
            flags: list[int] | None = None
    ):
        if translations is None:
            translations = []

        self.beginInsertRows(QModelIndex(), self.rowCount(), self.rowCount())
        term_idx, term_data = manager.add_term(term_name, term_type, term_desc, translations, flags)
        self.endInsertRows()
        return term_idx, term_data

    def _enable_undo(self, value):
        try:
            self.mw.config_actions[4].setEnabled(value)
        except (IndexError, RuntimeError):
            pass

    def _enable_redo(self, value):
        try:
            self.mw.config_actions[5].setEnabled(value)
        except (IndexError, RuntimeError):
            pass


class EditCommand(QUndoCommand):
    def __init__(self, model, row, column, values):
        super().__init__()
        self.row = row
        self.model = model
        self.column = column
        self.old_value, self.new_value = values

    def undo(self):
        self.model.apply_cell(self.row, self.column, self.old_value)

    def redo(self):
        self.model.apply_cell(self.row, self.column, self.new_value)


class MultiLineDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        value = index.model().data(index, Qt.ItemDataRole.EditRole)

        if isinstance(value, str):
            editor = QTextEdit(parent)
            editor.setAcceptRichText(False)
            editor.setTabChangesFocus(True)
            editor.setFrameStyle(0)
            editor.setContentsMargins(0, 0, 0, 0)
            editor.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
            editor.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            editor.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            editor.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
            return editor

        return super().createEditor(parent, option, index)

    def setEditorData(self, editor, index):
        if isinstance(editor, QTextEdit):
            editor.setPlainText(index.data(Qt.ItemDataRole.EditRole) or "")
        else:
            super().setEditorData(editor, index)

    def setModelData(self, editor, model, index):
        if isinstance(editor, QTextEdit):
            model.setData(index, editor.toPlainText(), Qt.ItemDataRole.EditRole)
        else:
            super().setModelData(editor, model, index)


class CustomTable(QTableView):
    def __init__(self):
        super().__init__()
        self.table_model = None

        self.default_row_height = 40
        self._rows_to_resize = []
        self._rows_to_resize_set = set()
        self._resize_timer = QTimer()
        self._resize_timer.timeout.connect(self._resize_next_batch)

        self.setEditTriggers(QTableView.EditTrigger.DoubleClicked | QTableView.EditTrigger.SelectedClicked)
        self.setHorizontalScrollMode(QTableView.ScrollMode.ScrollPerPixel)
        self.setItemDelegate(MultiLineDelegate(self))
        self.setSortingEnabled(False)
        self.setSelectionBehavior(QTableView.SelectionBehavior.SelectItems)
        self.setSelectionMode(QTableView.SelectionMode.ExtendedSelection)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setSizeAdjustPolicy(QAbstractScrollArea.SizeAdjustPolicy.AdjustIgnored)

        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        self.horizontalHeader().setSectionsMovable(True)
        self.horizontalHeader().setMinimumSectionSize(50)
        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)

        self.verticalHeader().setDefaultSectionSize(self.default_row_height)
        self.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        self.verticalScrollBar().valueChanged.connect(self._queue_visible_rows)

        self.setWordWrap(False)

    def load_table(self, parent, terms, langs):
        self.table_model = CustomTableModel(parent, terms, langs)
        self.table_model.dataChanged.connect(self._on_data_changed)
        self.setModel(self.table_model)

        corner_button = self.findChild(QAbstractButton)
        if corner_button and not corner_button.text():
            corner_button.setText("#")
            label = QLabel("#", self)
            label.setStyleSheet("font-weight: bold;")
            label.setGeometry(corner_button.geometry())
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.show()

        QTimer.singleShot(50, self._queue_visible_rows)
        self.adjust_column_widths()
        self.viewport().update()

    def update_table(self, terms, langs):
        self.table_model.update_data(terms, langs)

        QTimer.singleShot(50, self._queue_visible_rows)
        self.adjust_column_widths()
        self.viewport().update()

    def adjust_column_widths(self):
        model = self.model()
        advanced_column_width = 150
        header = self.horizontalHeader()
        font_metrics = QFontMetrics(self.font())

        header.blockSignals(True)
        for column in range(model.columnCount()):
            header_text = model.headerData(column, Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole)

            if not header_text:
                continue

            text_width = font_metrics.horizontalAdvance(str(header_text)) + advanced_column_width
            min_width = max(100, text_width)
            header.setSectionResizeMode(column, QHeaderView.ResizeMode.Interactive)
            self.setColumnWidth(column, min_width)
        header.blockSignals(False)

    def _queue_rows(self, rows):
        for row in rows:
            if row not in self._rows_to_resize_set:
                self._rows_to_resize.append(row)
                self._rows_to_resize_set.add(row)

        if not self._resize_timer.isActive():
            self._resize_timer.start(10)

    def _queue_visible_rows(self):
        rect = self.viewport().rect()
        first = self.rowAt(rect.top())
        last = self.rowAt(rect.bottom())
        if first != -1 and last != -1:
            self._queue_rows(range(first, last + 1))

    def _is_row_visible(self, row):
        rect = self.viewport().rect()
        first = self.rowAt(rect.top())
        last = self.rowAt(rect.bottom())
        if first == -1 or last == -1:
            return False
        return first <= row <= last

    def _is_row_range_visible(self, first, last):
        rect = self.viewport().rect()
        first_visible = self.rowAt(rect.top())
        last_visible = self.rowAt(rect.bottom())
        if first_visible == -1 or last_visible == -1:
            return False
        return not (last < first_visible or first > last_visible)

    def _resize_next_batch(self, rows_per_tick = 25):
        for _ in range(min(rows_per_tick, len(self._rows_to_resize))):
            if not self._rows_to_resize:
                break

            row = self._rows_to_resize.pop(0)
            self._rows_to_resize_set.discard(row)

            if self._is_row_visible(row):
                self.resizeRowToContents(row)
                if self.rowHeight(row) < self.default_row_height:
                    self.setRowHeight(row, self.default_row_height)

        if not self._rows_to_resize:
            self._resize_timer.stop()

    def _on_data_changed(self, top_left: QModelIndex, bottom_right: QModelIndex, _roles: Sequence[int]):
        if top_left and bottom_right:
            if self._is_row_range_visible(top_left.row(), bottom_right.row()):
                self._queue_rows(range(top_left.row(), bottom_right.row() + 1))

    def undo_edit(self):
        if not self.table_model:
            return

        self.table_model.undo_stack.undo()

    def redo_edit(self):
        if not self.table_model:
            return

        self.table_model.undo_stack.redo()

    def cut_selection(self):
        if not self.table_model:
            return

        selection = self.selectionModel().selectedIndexes()
        if not selection:
            return

        selection = sorted(selection, key=lambda x: (x.row(), x.column()))

        rows = {}
        for index in selection:
            rows.setdefault(index.row(), {})[index.column()] = index.data()

        cut_text = ""
        for row in sorted(rows):
            line = "\t".join(rows[row].get(column, "") for column in sorted(rows[row]))
            cut_text += line + "\n"

        QApplication.clipboard().setText(cut_text.strip())

        undo_stack = self.table_model.undo_stack

        editable_changes = []
        for index in selection:
            if index.flags() & Qt.ItemFlag.ItemIsEditable:
                old_value = index.data()
                if old_value:
                    editable_changes.append((index, old_value))

        if not editable_changes:
            return

        if undo_stack:
            undo_stack.beginMacro("Cut")

        try:
            for index, old_value in editable_changes:
                if undo_stack:
                    undo_stack.push(
                        EditCommand(
                            self.table_model,
                            index.row(),
                            index.column(),
                            (old_value, "")
                        )
                    )
                else:
                    self.table_model.setData(index, "", Qt.ItemDataRole.EditRole)
        finally:
            if undo_stack:
                undo_stack.endMacro()

    def copy_selection(self):
        if not self.table_model:
            return

        selection = self.selectionModel().selectedIndexes()
        if not selection:
            return

        selection = sorted(selection, key=lambda x: (x.row(), x.column()))

        rows = {}
        for index in selection:
            rows.setdefault(index.row(), {})[index.column()] = index.data()

        copied_text = ""
        for row in sorted(rows):
            line = "\t".join(rows[row].get(column, "") for column in sorted(rows[row]))
            copied_text += line + "\n"

        QApplication.clipboard().setText(copied_text.strip())

    def paste_selection(self):
        if not self.table_model:
            return

        clipboard = QApplication.clipboard().text()
        if not clipboard:
            return

        selected = self.selectedIndexes()
        if not selected:
            return

        lines = clipboard.splitlines()
        start_row = min(index.row() for index in selected)
        start_column = min(index.column() for index in selected)

        undo_stack = self.table_model.undo_stack

        editable_changes = []

        if len(lines) == 1:
            cells = lines[0].split("\t")
            for i, index in enumerate(sorted(selected, key=lambda x: (x.row(), x.column()))):
                cell_value = cells[i % len(cells)]
                old_value = index.data()

                if old_value != cell_value:
                    if index.flags() & Qt.ItemFlag.ItemIsEditable:
                        editable_changes.append((index, old_value, cell_value))
        else:
            for row_offset, line in enumerate(lines):
                cells = line.split("\t")
                for column_offset, cell_value in enumerate(cells):
                    row = start_row + row_offset
                    column = start_column + column_offset

                    if row >= self.table_model.rowCount() or column >= self.table_model.columnCount():
                        continue

                    index = self.table_model.index(row, column)
                    old_value = index.data()

                    if old_value != cell_value:
                        if index.flags() & Qt.ItemFlag.ItemIsEditable:
                            editable_changes.append((index, old_value, cell_value))

        if not editable_changes:
            return

        if undo_stack:
            undo_stack.beginMacro("Paste")

        try:
            for index, old_value, cell_value in editable_changes:
                if undo_stack:
                    undo_stack.push(
                        EditCommand(
                            self.table_model,
                            index.row(),
                            index.column(),
                            (old_value, cell_value)
                        )
                    )
                else:
                    self.table_model.setData(index, cell_value)
        finally:
            if undo_stack:
                undo_stack.endMacro()

    def delete_selection(self):
        if not self.table_model:
            return

        selection = self.selectionModel().selectedIndexes()
        if not selection:
            return

        selection = sorted(selection, key=lambda x: (x.row(), x.column()))

        editable_changes = []
        for index in selection:
            if index.flags() & Qt.ItemFlag.ItemIsEditable:
                old_value = index.data()
                if old_value:
                    editable_changes.append((index, old_value))

        if not editable_changes:
            return

        undo_stack = self.table_model.undo_stack
        if undo_stack:
            undo_stack.beginMacro("Delete")

        try:
            for index, old_value in editable_changes:
                if undo_stack:
                    undo_stack.push(
                        EditCommand(
                            self.table_model,
                            index.row(),
                            index.column(),
                            (old_value, "")
                        )
                    )
                else:
                    self.table_model.setData(index, "", Qt.ItemDataRole.EditRole)
        finally:
            if undo_stack:
                undo_stack.endMacro()
