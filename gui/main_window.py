from pathlib import Path
from typing import Any

from PySide6.QtCore import QThread
from PySide6.QtGui import QIcon, QAction, QCloseEvent, QKeySequence, QDropEvent, QDragEnterEvent
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QComboBox, QMenu, QMessageBox, QVBoxLayout,
    QFileDialog, QLabel, QHBoxLayout, QWidget, QStyleFactory
)

from gui.about_dialog import About
from gui.custom_table import CustomTable
from gui.export_module import ExportModule
from gui.helpers import (
    FileWorker,
    message_box,
    set_window_size
)
from gui.import_module import ImportModule
from gui.langs_manage import LanguageManager
from gui.updater import UpdateManager
from utils.app_config import app_cfg
from utils.app_locales import fluent, ftr
from utils.enums import FileExtension as Fe
from utils.helpers import pathfind
from utils.manager import manager

class I2ManagerUI(QMainWindow):
    TITLE = "I2 Localization Manager"
    VERSION = "1.1.5"

    def __init__(self):
        super().__init__()
        self.config_actions = None
        self.lang_selector = None
        self.custom_table = None
        self.term_count = None
        self.temp_thread = None
        self.worker = None

        self.setAcceptDrops(True)
        self.setMinimumSize(900, 600)
        self.setWindowTitle(self.TITLE)
        self.setWindowIcon(QIcon(pathfind("assets\\icon.ico")))
        set_window_size(self)

        self.central_widget = QWidget()
        self.main_layout = QVBoxLayout()
        self.setCentralWidget(self.central_widget)
        self.central_widget.setLayout(self.main_layout)

        self.update_manager = UpdateManager(self, self.VERSION)

        self._refresh_ui()

        self.update_manager.check_for_pending_update()
        if app_cfg.get_config("check_updates_on_startup", True):
            self.update_manager.check_for_updates(True)

    def setup_menu_bar(self):
        menu_bar = self.menuBar()

        # ====== File Menu ====== #
        file_menu = menu_bar.addMenu(ftr("file-menu-title"))

        open_file = QAction(ftr("open-button"), self)
        open_file.setIcon(QIcon.fromTheme("document-open"))
        open_file.setStatusTip(ftr("open-tooltip"))
        open_file.triggered.connect(self._open_file_dialog)
        open_file.setShortcut(QKeySequence.StandardKey.Open)

        save_file = QAction(ftr("save-button"), self)
        save_file.setIcon(QIcon.fromTheme("document-save"))
        save_file.setStatusTip(ftr("save-tooltip"))
        save_file.triggered.connect(self._save_file)
        save_file.setShortcut(QKeySequence.StandardKey.Save)

        save_file_as = QAction(ftr("save-as-button"), self)
        save_file_as.setIcon(QIcon.fromTheme("document-save-as"))
        save_file_as.setStatusTip(ftr("save-as-tooltip"))
        save_file_as.triggered.connect(self._save_file_as)
        save_file_as.setShortcut(QKeySequence.StandardKey.SaveAs)

        recent_menu = self.setup_recent_menu()

        exit_app = QAction(ftr("exit-app-button"), self)
        exit_app.setIcon(QIcon.fromTheme("application-exit"))
        exit_app.setStatusTip(ftr("exit-app-tooltip"))
        exit_app.triggered.connect(self.close)
        exit_app.setShortcut(QKeySequence("Alt+F4"))

        file_menu.addActions([
            open_file,
            save_file,
            save_file_as
        ])
        file_menu.addMenu(recent_menu)
        file_menu.addSeparator()
        file_menu.addAction(exit_app)

        # ====== Edit Menu ====== #
        edit_menu = menu_bar.addMenu(ftr("edit-menu-title"))

        undo_action = QAction(ftr("undo-button"), self)
        undo_action.setIcon(QIcon.fromTheme("edit-undo"))
        undo_action.setStatusTip(ftr("undo-tooltip"))
        undo_action.triggered.connect(self._undo_edit)
        undo_action.setShortcut(QKeySequence.StandardKey.Undo)

        redo_action = QAction(ftr("redo-button"), self)
        redo_action.setIcon(QIcon.fromTheme("edit-redo"))
        redo_action.setStatusTip(ftr("redo-tooltip"))
        redo_action.triggered.connect(self._redo_edit)
        redo_action.setShortcut(QKeySequence.StandardKey.Redo)

        cut_action = QAction(ftr("cut-button"), self)
        cut_action.setIcon(QIcon.fromTheme("edit-cut"))
        cut_action.setStatusTip(ftr("cut-tooltip"))
        cut_action.triggered.connect(self._cut_selection)
        cut_action.setShortcut(QKeySequence.StandardKey.Cut)

        copy_action = QAction(ftr("copy-button"), self)
        copy_action.setIcon(QIcon.fromTheme("edit-copy"))
        copy_action.setStatusTip(ftr("copy-tooltip"))
        copy_action.triggered.connect(self._copy_selection)
        copy_action.setShortcut(QKeySequence.StandardKey.Copy)

        paste_action = QAction(ftr("paste-button"), self)
        paste_action.setIcon(QIcon.fromTheme("edit-paste"))
        paste_action.setStatusTip(ftr("paste-tooltip"))
        paste_action.triggered.connect(self._paste_selection)
        paste_action.setShortcut(QKeySequence.StandardKey.Paste)

        delete_action = QAction(ftr("delete-button"), self)
        delete_action.setIcon(QIcon.fromTheme("edit-delete"))
        delete_action.setStatusTip(ftr("delete-tooltip"))
        delete_action.triggered.connect(self._delete_selection)
        delete_action.setShortcut(QKeySequence.StandardKey.Delete)

        edit_menu.addActions([
            undo_action,
            redo_action,
            cut_action,
            copy_action,
            paste_action,
            delete_action
        ])

        # ====== View Menu ====== #
        view_menu = menu_bar.addMenu(ftr("view-menu-title"))

        refresh_table = QAction(ftr("refresh-table-button"), self)
        refresh_table.setIcon(QIcon.fromTheme("view-refresh"))
        refresh_table.setStatusTip(ftr("refresh-table-tooltip"))
        refresh_table.triggered.connect(self._update_table)
        refresh_table.setShortcut(QKeySequence.StandardKey.Refresh)

        check_updates_now = QAction(ftr("check-updates-now-button"), self)
        check_updates_now.setIcon(QIcon.fromTheme("system-software-update"))
        check_updates_now.setStatusTip(ftr("check-updates-now-tooltip"))
        check_updates_now.triggered.connect(self.update_manager.check_for_updates)

        check_updates_startup = QAction(ftr("check-updates-startup-button"), self)
        check_updates_startup.setCheckable(True)
        check_updates_startup.setChecked(app_cfg.get_config("check_updates_on_startup", True))
        check_updates_startup.setStatusTip(ftr("check-updates-startup-tooltip"))
        check_updates_startup.triggered.connect(self._toggle_startup_updates)

        view_menu.addAction(refresh_table)
        view_menu.addSeparator()
        view_menu.addMenu(self.setup_theme_menu())
        view_menu.addMenu(self.setup_language_menu())
        view_menu.addSeparator()
        view_menu.addAction(check_updates_now)
        view_menu.addAction(check_updates_startup)

        # ====== Tool Menu ====== #
        tool_menu = menu_bar.addMenu(ftr("tools-menu-title"))

        export_translations = QAction(ftr("export-translations-button"), self)
        export_translations.setStatusTip(ftr("export-translations-tooltip"))
        export_translations.triggered.connect(lambda: ExportModule(self))
        export_translations.setShortcut(QKeySequence("Ctrl+Shift+Q"))

        import_translations = QAction(ftr("import-translations-button"), self)
        import_translations.setStatusTip(ftr("import-translations-tooltip"))
        import_translations.triggered.connect(lambda: ImportModule(self))
        import_translations.setShortcut(QKeySequence("Ctrl+Shift+W"))

        manage_langs = QAction(ftr("manage-languages-button"), self)
        manage_langs.setStatusTip(ftr("manage-languages-tooltip"))
        manage_langs.triggered.connect(lambda: LanguageManager(self))
        manage_langs.setShortcut(QKeySequence("Ctrl+Shift+E"))

        tool_menu.addActions([
            export_translations,
            import_translations,
            manage_langs
        ])

        # ====== About Action ====== #
        about_action = QAction(ftr("about-app"), self)
        about_action.setStatusTip(ftr("about-app-tooltip"))
        about_action.triggered.connect(self._open_about_dialog)
        menu_bar.addAction(about_action)

        self.config_actions = [
            open_file,
            recent_menu,
            save_file,
            save_file_as,
            undo_action,
            redo_action,
            cut_action,
            copy_action,
            paste_action,
            delete_action,
            refresh_table,
            export_translations,
            import_translations,
            manage_langs
        ]

    def setup_recent_menu(self):
        max_count = 8
        recent_menu = QMenu(ftr("open-recent-menu"), self)
        recent_menu.setIcon(QIcon.fromTheme("document-open-recent"))

        recent_files = app_cfg.get_recent_files()
        if recent_files:
            for file in recent_files[:max_count]:
                action = QAction(file, self)
                action.setStatusTip(ftr("open-recent-tooltip", {"file_name": Path(file).name}))
                action.triggered.connect(
                    lambda checked=False, path=file:
                        self.open_file(path)
                )
                recent_menu.addAction(action)
            recent_menu.addSeparator()

        clear_recent_button = QAction(ftr("clear-recent-button"), self)
        clear_recent_button.setStatusTip(ftr("clear-recent-tooltip"))
        clear_recent_button.triggered.connect(lambda: (app_cfg.clear_recent_files(), self._refresh_ui()))
        clear_recent_button.setIcon(QIcon.fromTheme("edit-clear"))
        recent_menu.addAction(clear_recent_button)

        return recent_menu

    def setup_theme_menu(self):
        factory_themes = QStyleFactory.keys()
        current_theme = app_cfg.get_config("theme", "Fusion")

        theme_menu = QMenu(ftr("theme-menu"), self)
        theme_menu.setIcon(QIcon.fromTheme("preferences-desktop-accessibility"))
        theme_menu.setToolTip(ftr("theme-menu-tooltip"))

        for factory_theme in factory_themes:
            action = QAction(factory_theme, self)
            action.setCheckable(True)

            if current_theme == factory_theme:
                action.setChecked(True)
                action.setEnabled(False)
                self._set_theme_mode(factory_theme)
            else:
                action.setChecked(False)
                action.triggered.connect(
                    lambda checked=False, theme=factory_theme: (
                        app_cfg.set_config("theme", theme),
                        self._refresh_ui()
                    )
                )

            theme_menu.addAction(action)

        return theme_menu

    def setup_language_menu(self):
        language_menu = QMenu(ftr("app-language-menu"), self)
        language_menu.setIcon(QIcon.fromTheme("preferences-desktop-locale"))

        current_locale = fluent.current_locale
        available_locales = fluent.get_languages()

        for locale_code, locale_name in available_locales.items():
            action = QAction(locale_name, language_menu)
            action.setCheckable(True)

            if locale_code == current_locale:
                action.setChecked(True)
                action.setEnabled(False)
            else:
                action.setChecked(False)
                action.triggered.connect(
                    lambda checked=False, loc=locale_code: (
                        fluent.change_locale(loc),
                        self._refresh_ui()
                    )
                )

            language_menu.addAction(action)

        return language_menu

    def configure_menu(self, value: bool):
        for action in self.config_actions[2:]:
            action.setEnabled(value)

        if value and self.custom_table.table_model:
            undo_stack = self.custom_table.table_model.undo_stack
            if undo_stack:
                self.config_actions[4].setEnabled(undo_stack.canUndo())
                self.config_actions[5].setEnabled(undo_stack.canRedo())

    def setup_table_controls(self):
        controls = QHBoxLayout()

        self.lang_selector = QComboBox()
        self.lang_selector.setFixedSize(200, 25)
        self.lang_selector.textActivated.connect(self._update_table)

        self.term_count = QLabel()

        controls.addWidget(self.lang_selector)
        controls.addStretch()
        controls.addWidget(self.term_count)
        self.main_layout.addLayout(controls)

        self.custom_table = CustomTable()
        self.main_layout.addWidget(self.custom_table)

    def update_lang_selector(self, is_new_file=False):
        prev_item = self.lang_selector.currentText()
        self.lang_selector.clear()

        languages = manager.get_displayed_languages()
        if languages:
            self.lang_selector.addItem(ftr("all-languages"))
            self.lang_selector.addItems(languages)

            items = []
            for i in range(self.lang_selector.count()):
                items.append(self.lang_selector.itemText(i))

            if prev_item in items:
                self.lang_selector.setCurrentIndex(items.index(prev_item))
            else:
                self.lang_selector.setCurrentIndex(0)

        self._update_table(is_new_file)
        self.term_count.setText(
            ftr("term-count-label", {"count": manager.term_count()})
        )

    def _update_table(self, new_file=False):
        if not manager.content:
            message_box(self, "warning", "warning-no-file")
            return

        if self.lang_selector.currentIndex() != -1:
            terms = manager.content.get("terms", [])

            selected_index = self.lang_selector.currentIndex()
            selected_text = self.lang_selector.currentText()

            if not selected_text:
                message_box(self, "warning", "warning-no-language-selected")
                return

            all_languages = manager.get_languages()

            if selected_index == 0:
                lang_subset = all_languages
            else:
                lang_index = selected_index - 1
                if 0 <= lang_index < len(all_languages):
                    lang_subset = [all_languages[lang_index]]
                else:
                    lang_subset = []

            if new_file:
                self.custom_table.load_table(self, terms, lang_subset)
            else:
                self.custom_table.update_table(terms, lang_subset)

    def _undo_edit(self):
        self.custom_table.undo_edit()

    def _redo_edit(self):
        self.custom_table.redo_edit()

    def _cut_selection(self):
        self.custom_table.cut_selection()

    def _copy_selection(self):
        self.custom_table.copy_selection()

    def _paste_selection(self):
        self.custom_table.paste_selection()

    def _delete_selection(self):
        self.custom_table.delete_selection()

    def open_file(self, path: str):
        path = Path(path)

        if not path.exists():
            message_box(self, "warning", ("warning-file-not-found", {"file_path": str(path)}))
            if str(path) in app_cfg.get_recent_files():
                app_cfg.remove_recent_file(str(path))
                self._refresh_ui()
            return

        if manager.is_modified():
            reply = message_box(
                self, "question", "question-save-file-open",
                standard_buttons=(
                    QMessageBox.StandardButton.Yes
                    | QMessageBox.StandardButton.Save
                    | QMessageBox.StandardButton.No
                    | QMessageBox.StandardButton.Cancel,
                    QMessageBox.StandardButton.Yes
                )
            )

            if reply == QMessageBox.StandardButton.Yes:
                self._save_file()
            elif reply == QMessageBox.StandardButton.Save:
                self._save_file_as()
                if manager.is_modified():
                    return
            elif reply == QMessageBox.StandardButton.Cancel:
                return

        self.temp_thread = QThread()
        self.worker = FileWorker(str(path))
        self.worker.moveToThread(self.temp_thread)

        self.temp_thread.started.connect(self.worker.open)
        self.worker.finished.connect(self._on_opened_file)
        self.worker.finished.connect(self.temp_thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.temp_thread.finished.connect(self.temp_thread.deleteLater)

        self.status_bar_message(("opening-file", {"file_path": str(path)}))
        self.config_actions[0].setDisabled(True)
        self.config_actions[1].setDisabled(True)
        self.temp_thread.start()

    def _save_file(self):
        if not manager.content:
            message_box(self, "warning", "warning-no-file")
            return

        file_path = manager.file_path
        self.status_bar_message(("saving-file", {"file_path": str(file_path)}))
        result = manager.save_dump_file(file_path)

        if result is True:
            self.status_bar_message(("saved-file", {"file_path": str(file_path)}), 10000)
        else:
            message_box(self, "error", result)

    def _save_file_as(self):
        if not manager.content:
            message_box(self, "warning", "warning-no-file")
            return

        extensions = "{} (*{});; {} (*{})".format(
            ftr("json-file"), Fe.JSON.value,
            ftr("text-file"), Fe.TXT.value
        )

        path, _ = QFileDialog.getSaveFileName(
            self, ftr("save-title"), f"{manager.file_name}-NEW", extensions
        )

        if not path:
            return

        file_path = Path(path)
        self.status_bar_message(("saving-file", {"file_path": str(file_path)}))
        result = manager.save_dump_file(file_path)

        if result is True:
            manager.update_file_info(file_path)
            self.status_bar_message(("saved-file", {"file_path": str(file_path)}), 10000)
        else:
            message_box(self, "error", result)

    def status_bar_message(self, text: str | tuple[str, dict[str, Any]] | None = None, timeout: int = 0):
        if text is None:
            return self.statusBar().clearMessage()

        if isinstance(text, tuple):
            text, args = text
        else:
            args = None

        return self.statusBar().showMessage(ftr(text, args), timeout)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            valid_extensions = [Fe.TXT.value, Fe.JSON.value]
            urls = event.mimeData().urls()

            for url in urls:
                file_path = url.toLocalFile()
                if any(file_path.endswith(ext) for ext in valid_extensions):
                    event.acceptProposedAction()
                    return

            event.ignore()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            valid_extensions = [Fe.TXT.value, Fe.JSON.value]

            for url in urls:
                file_path = url.toLocalFile()
                if any(file_path.endswith(ext) for ext in valid_extensions):
                    event.acceptProposedAction()
                    self.open_file(file_path)
                    return

            message_box(self, "error", "error-invalid-file")
            event.ignore()
        else:
            event.ignore()

    def closeEvent(self, event: QCloseEvent):
        if not manager.content:
            event.accept()

        if manager.is_modified():
            event.ignore()
            reply = message_box(
                self, "question", "question-save-file-exit",
                standard_buttons=(
                    QMessageBox.StandardButton.Yes
                    | QMessageBox.StandardButton.No
                    | QMessageBox.StandardButton.Cancel,
                    QMessageBox.StandardButton.Yes
                    )
                )

            if reply == QMessageBox.StandardButton.Yes:
                self._save_file_as()
                if manager.is_modified():
                    return
            elif reply == QMessageBox.StandardButton.Cancel:
                return

        event.accept()

    def _open_file_dialog(self):
        path, _ = QFileDialog.getOpenFileName(
            self, ftr("open-title"), "",
            f"{ftr('dump-file')} (*{Fe.TXT.value}; *{Fe.JSON.value})"
        )

        if not path:
            return

        self.open_file(path)

    def _on_opened_file(self, file_path: str, result: Any):
        if result is True:
            app_cfg.add_recent_file(file_path)
            self.status_bar_message(
                ("opened-file", {"file_path": file_path}), 15000
            )
            self.update_lang_selector(True)
            self.configure_menu(True)
        else:
            self.status_bar_message()
            message_box(self, "error", result)

        self.config_actions[0].setEnabled(True)
        self.config_actions[1].setEnabled(True)
        self._refresh_ui()

    def _open_about_dialog(self):
        about_dialog = About(self)
        about_dialog.show()

    def _refresh_ui(self):
        if self.menuBar().children():
            self.menuBar().clear()
        self.setup_menu_bar()

        if not self.custom_table:
            self.statusBar()
            self.setup_table_controls()

        if manager.content:
            self.update_lang_selector()
            self.configure_menu(True)
        else:
            self.configure_menu(False)

    @staticmethod
    def _toggle_startup_updates(checked: bool):
        app_cfg.set_config("check_updates_on_startup", checked)

    def _set_theme_mode(self, theme: str):
        try:
            application = QApplication.instance()
            application.setStyle(QStyleFactory.create(theme))
        except Exception as e:
            print(f"[ERROR] Error while setting '{theme}' style, defaulting to Fusion...\n", str(e))
            theme = "Fusion"
            application.setStyle(QStyleFactory.create(theme))
            app_cfg.set_config("theme", theme)

        if theme == "Fusion":
            application.setStyleSheet("QComboBox { combobox-popup: 0; }")
        else:
            application.setStyleSheet("QComboBox QAbstractItemView { background: palette(base); }")
