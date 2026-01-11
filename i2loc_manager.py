import sys
from typing import Any
from pathlib import Path

from PySide6.QtCore import QThread
from PySide6.QtGui import QIcon, QAction, QCloseEvent
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
    report,
    set_window_size
)
from gui.import_module import ImportModule
from gui.langs_manage import LanguageManager

from utils.app_config import config
from utils.app_locales import fluent, ftr
from utils.enums import FileExtension as Fe
from utils.helpers import pathfind
from utils.manager import manager


class I2ManagerUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config_actions = None
        self.lang_selector = None
        self.custom_table = None
        self.term_count = None
        self.temp_thread = None
        self.worker = None

        self.setMinimumSize(800, 600)
        self.setWindowTitle("I2 Localization Manager")
        self.setWindowIcon(QIcon(pathfind("assets\\icon.ico")))
        set_window_size(self)

        self.central_widget = QWidget()
        self.main_layout = QVBoxLayout()
        self.setCentralWidget(self.central_widget)
        self.central_widget.setLayout(self.main_layout)

        self._refresh_ui()

    def setup_menu_bar(self):
        menu_bar = self.menuBar()

        # ====== File Menu ====== #
        file_menu = menu_bar.addMenu(ftr("file-menu-title"))

        open_file = QAction(ftr("open-button"), self)
        open_file.setStatusTip(ftr("open-tooltip"))
        open_file.triggered.connect(self._open_file_dialog)
        open_file.setShortcut("Ctrl+O")

        recent_menu = self.setup_recent_menu()

        save_file = QAction(ftr("save-button"), self)
        save_file.setStatusTip(ftr("save-tooltip"))
        save_file.triggered.connect(self.save_file)
        save_file.setShortcut("Ctrl+S")

        exit_app = QAction(ftr("exit-app-button"), self)
        exit_app.setStatusTip(ftr("exit-app-tooltip"))
        exit_app.triggered.connect(self.close)
        exit_app.setShortcut("Alt+F4")

        file_menu.addAction(open_file)
        file_menu.addMenu(recent_menu)
        file_menu.addActions([
            save_file,
            file_menu.addSeparator(),
            exit_app
        ])

        # ====== Edit Menu ====== #
        edit_menu = menu_bar.addMenu(ftr("edit-menu-title"))

        refresh_table = QAction(ftr("refresh-table-button"), self)
        refresh_table.setStatusTip(ftr("refresh-table-tooltip"))
        refresh_table.triggered.connect(self.update_table)
        refresh_table.setShortcut("Ctrl+R")

        edit_menu.addActions([
            refresh_table,
            edit_menu.addSeparator()
        ])
        edit_menu.addMenu(self.setup_theme_menu())
        edit_menu.addMenu(self.setup_language_menu())

        # ====== Tool Menu ====== #
        tool_menu = menu_bar.addMenu(ftr("tools-menu-title"))

        export_translations = QAction(ftr("export-translations-button"), self)
        export_translations.setStatusTip(ftr("export-translations-tooltip"))
        export_translations.triggered.connect(lambda: ExportModule(self))

        import_translations = QAction(ftr("import-translations-button"), self)
        import_translations.setStatusTip(ftr("import-translations-tooltip"))
        import_translations.triggered.connect(lambda: ImportModule(self))

        manage_langs = QAction(ftr("manage-languages-button"), self)
        manage_langs.setStatusTip(ftr("manage-languages-tooltip"))
        manage_langs.triggered.connect(lambda: LanguageManager(self))

        tool_menu.addActions([
            export_translations,
            import_translations,
            manage_langs
        ])

        # ====== About Action ====== #
        menu_bar.addAction(ftr("about-app"), self._open_about_dialog)

        self.config_actions = [
            open_file,
            recent_menu,
            save_file,
            refresh_table,
            export_translations,
            import_translations,
            manage_langs
        ]

    def setup_recent_menu(self):
        max_count = 8
        recent_menu = QMenu(ftr("open-recent-menu"), self)

        recent_files = config.get_recent_files()
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
        clear_recent_button.triggered.connect(lambda: (config.clear_recent_files(), self._refresh_ui()))
        recent_menu.addAction(clear_recent_button)

        return recent_menu

    def setup_theme_menu(self):
        factory_themes = QStyleFactory.keys()
        current_theme = config.get_config("theme", "Fusion")

        theme_menu = QMenu(ftr("theme-menu"), self)
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
                        config.set_config("theme", theme),
                        self._refresh_ui()
                    )
                )

            theme_menu.addAction(action)

        return theme_menu

    def setup_language_menu(self):
        language_menu = QMenu(ftr("app-language-menu"), self)

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

    def setup_table_controls(self):
        controls = QHBoxLayout()

        self.lang_selector = QComboBox()
        self.lang_selector.setFixedSize(200, 25)
        self.lang_selector.textActivated.connect(self.update_table)

        self.term_count = QLabel()

        controls.addWidget(self.lang_selector)
        controls.addStretch()
        controls.addWidget(self.term_count)
        self.main_layout.addLayout(controls)

        self.custom_table = CustomTable()
        self.main_layout.addWidget(self.custom_table)

    def update_lang_selector(self):
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

        self.update_table()
        self.term_count.setText(
            ftr("term-count-label", {"count": manager.term_count()})
        )

    def update_table(self):
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

            if selected_index == 0:
                lang_subset = {
                    lang["code"]: lang["name"]
                    for lang in manager.get_languages()
                }
            else:
                code, name = manager.get_language_by_index(selected_index-1)
                lang_subset = {code: name}

            self.custom_table.update_table(self, terms, lang_subset)

    def open_file(self, path: str):
        path = Path(path)

        if not path.is_file():
            message_box(self, "warning", ("warning-file-not-found", {"file_path": str(path)}))
            if str(path) in config.get_recent_files():
                config.remove_recent_file(str(path))
                self._refresh_ui()
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

    def save_file(self):
        if not manager.content:
            message_box(self, "warning", "warning-no-file")
            return

        extensions = "{} (*{});; {} (*{})".format(
            ftr("json-file"), Fe.JSON.value,
            ftr("text-file"), Fe.TXT.value
        )

        path, _ = QFileDialog.getSaveFileName(
            self, ftr("save-title"), f"{manager.file_name}_dump", extensions
        )

        if not path:
            return

        file_path = Path(path)
        self.status_bar_message(("saving-file", {"file_path": str(file_path)}))
        result = manager.save_dump_file(file_path)
        if result is True:
            self.status_bar_message(("saved-file", {"file_path": str(file_path)}))
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

    def closeEvent(self, event: QCloseEvent):
        if not manager.content:
            event.accept()

        if manager.is_modified():
            event.ignore()
            reply = message_box(
                self, "question", "question-save-file",
                standard_buttons=(
                    QMessageBox.StandardButton.Yes
                    | QMessageBox.StandardButton.No
                    | QMessageBox.StandardButton.Cancel,
                    QMessageBox.StandardButton.Yes
                    )
                )

            if reply == QMessageBox.StandardButton.Yes:
                self.save_file()
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
            config.add_recent_file(file_path)
            self.status_bar_message(
                ("opened-file", {"file_path": file_path}), 15000
            )
            self.configure_menu(True)
            self.update_lang_selector()
        else:
            self.status_bar_message()
            message_box(self, "error", result)

        self.config_actions[0].setEnabled(True)
        self.config_actions[1].setEnabled(True)
        self._refresh_ui()

    def _open_about_dialog(self):
        self.about_dialog = About(self)
        self.about_dialog.show()

    def _refresh_ui(self):
        if self.menuBar().children():
            self.menuBar().clear()
        self.setup_menu_bar()

        if not self.custom_table:
            self.statusBar()
            self.setup_table_controls()

        if manager.content:
            self.configure_menu(True)
            self.update_lang_selector()
        else:
            self.configure_menu(False)

    @staticmethod
    def _set_theme_mode(theme: str):
        try:
            application.setStyle(theme)
        except Exception as e:
            print("[ERROR] ", str(e))
            application.setStyle("Fusion")
            config.set_config("theme", "Fusion")

        if theme == "Fusion":
            application.setStyleSheet("QComboBox { combobox-popup: 0; }")


if __name__ == "__main__":
    try:
        application = QApplication(sys.argv)
        window = I2ManagerUI()
        window.show()
        sys.exit(application.exec())
    except Exception as exc:
        report(str(exc))
