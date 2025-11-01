import os
import sys
from PySide6.QtGui import QIcon, QAction, QCloseEvent
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QComboBox, QMenu, QMessageBox, QVBoxLayout,
    QFileDialog, QLabel, QHBoxLayout, QWidget, QStyleFactory, QDialogButtonBox
)

from utils.app_config import AppConfig
from utils.app_locales import AppLocale
from utils.enums import FileExts as FE
from utils.exceptions import InvalidExtensionError
from utils.manager import I2Manager
from utils.helpers import pathfind

from gui.about_dialog import About
from gui.custom_table import CustomTable
from gui.export_module import ExportModule
from gui.import_module import ImportModule
from gui.langs_manage import LanguageManager

class I2ManagerUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setMinimumSize(800, 600)
        self.setWindowTitle("I2 Localization Manager")
        self.setWindowIcon(QIcon(pathfind("assets\\icon.ico")))
        self._set_window_size()

        self.config = AppConfig(self)
        self.fluent = AppLocale(self)
        self.manager = I2Manager(self)
        self.ftr = self.fluent.tr
        self.config_actions = []

        self.central_widget = QWidget()
        self.main_layout = QVBoxLayout()
        self.setCentralWidget(self.central_widget)
        self.central_widget.setLayout(self.main_layout)

        self._refresh_ui()

    def setup_menu_bar(self):
        menu_bar = self.menuBar()

        # ====== File Menu ====== #
        file_menu = menu_bar.addMenu(self.ftr("file-menu-title"))

        open_file = QAction(self.ftr("open-button"), self)
        open_file.setStatusTip(self.ftr("open-tooltip"))
        open_file.triggered.connect(self._open_file_dialog)
        open_file.setShortcut("Ctrl+O")

        save_file = QAction(self.ftr("save-button"), self)
        save_file.setStatusTip(self.ftr("save-tooltip"))
        save_file.triggered.connect(self.save_dump_file)
        save_file.setShortcut("Ctrl+S")

        exit_app = QAction(self.ftr("exit-app-button"), self)
        exit_app.setStatusTip(self.ftr("exit-app-tooltip"))
        exit_app.triggered.connect(self.close)
        exit_app.setShortcut("Alt+F4")

        file_menu.addAction(open_file)
        file_menu.addMenu(self.setup_recent_menu())
        file_menu.addActions([
            save_file,
            file_menu.addSeparator(),
            exit_app
        ])

        # ====== Edit Menu ====== #
        edit_menu = menu_bar.addMenu(self.ftr("edit-menu-title"))

        refresh_table = QAction(self.ftr("refresh-table-button"), self)
        refresh_table.setToolTip(self.ftr("refresh-table-tooltip"))
        refresh_table.triggered.connect(self.update_table)
        refresh_table.setShortcut("Ctrl+R")

        edit_menu.addActions([
            refresh_table,
            edit_menu.addSeparator()
        ])
        edit_menu.addMenu(self.setup_theme_menu())
        edit_menu.addMenu(self.setup_language_menu())

        # ====== Tool Menu ====== #
        tool_menu = menu_bar.addMenu(self.ftr("tools-menu-title"))

        export_translations = QAction(self.ftr("export-translations-button"), self)
        export_translations.setStatusTip(self.ftr("export-translations-tooltip"))
        export_translations.triggered.connect(lambda: ExportModule(self))

        import_translations = QAction(self.ftr("import-translations-button"), self)
        import_translations.setStatusTip(self.ftr("import-translations-tooltip"))
        import_translations.triggered.connect(lambda: ImportModule(self))

        manage_langs = QAction(self.ftr("manage-languages-button"), self)
        manage_langs.setStatusTip(self.ftr("manage-languages-tooltip"))
        manage_langs.triggered.connect(lambda: LanguageManager(self))

        tool_menu.addActions([
            export_translations,
            import_translations,
            manage_langs
        ])

        # ====== About Action ====== #
        menu_bar.addAction(self.ftr("about-app"), self._open_about_dialog)

        self.config_actions = [
            save_file,
            refresh_table,
            export_translations,
            import_translations,
            manage_langs
        ]

    def setup_recent_menu(self):
        max_count = 8
        recent_menu = QMenu(self.ftr("open-recent-menu"), self)

        recent_files = self.config.get_recent_files()
        if recent_files:
            for file in recent_files[:max_count]:
                action = QAction(file, self)
                action.setStatusTip(self.ftr("open-recent-tooltip", {"filename": os.path.basename(file)}))
                action.triggered.connect(
                    lambda checked=False, path=file:
                        self.open_dump_file(path)
                )
                recent_menu.addAction(action)
            recent_menu.addSeparator()

        clear_recent_button = QAction(self.ftr("clear-recent-button"), self)
        clear_recent_button.setStatusTip(self.ftr("clear-recent-tooltip"))
        clear_recent_button.triggered.connect(lambda: (self.config.clear_recent_files(), self._refresh_ui()))
        recent_menu.addAction(clear_recent_button)

        return recent_menu

    def setup_theme_menu(self):
        themes = QStyleFactory.keys()
        current_theme = self.config.get_config("theme", "Fusion")

        theme_menu = QMenu(self.ftr("theme-menu"), self)
        theme_menu.setToolTip(self.ftr("theme-menu-tooltip"))

        for theme in themes:
            action = QAction(theme, self)
            action.setCheckable(True)

            if current_theme == theme:
                action.setChecked(True)
                action.setEnabled(False)
                self._set_theme_mode(theme)
            else:
                action.setChecked(False)
                action.triggered.connect(
                    lambda checked=False, theme=theme:
                        (self.config.set_config("theme", theme), self._refresh_ui())
                )

            theme_menu.addAction(action)

        return theme_menu

    def setup_language_menu(self):
        language_menu = QMenu(self.ftr("app-language-menu"), self)

        current_locale = self.fluent.current_locale
        available_locales = self.fluent.get_languages()

        for locale_code, locale_name in available_locales.items():
            action = QAction(locale_name, language_menu)
            action.setCheckable(True)

            if locale_code == current_locale:
                action.setChecked(True)
                action.setEnabled(False)
            else:
                action.setChecked(False)
                action.triggered.connect(
                    lambda checked=False, loc=locale_code:
                        (self.fluent.change_locale(loc), self._refresh_ui())
                )

            language_menu.addAction(action)

        return language_menu

    def configure_menu(self, value):
        for action in self.config_actions:
            action.setEnabled(value)

    def setup_table_controls(self):
        self.controls = QHBoxLayout()

        self.lang_selector = QComboBox()
        self.lang_selector.setFixedSize(200, 25)
        self.lang_selector.currentIndexChanged.connect(self.update_table)

        self.term_count = QLabel()

        self.controls.addWidget(self.lang_selector)
        self.controls.addStretch()
        self.controls.addWidget(self.term_count)
        self.main_layout.addLayout(self.controls)

        self.custom_table = CustomTable()
        self.main_layout.addWidget(self.custom_table)

    def update_lang_selector(self):
        prev_item = self.lang_selector.currentText()

        self.lang_selector.currentIndexChanged.disconnect(self.update_table)
        self.lang_selector.clear()
        self.lang_selector.currentIndexChanged.connect(self.update_table)

        languages = self.manager.get_languages("displayed")
        if languages:
            self.lang_selector.addItem(self.ftr("all-languages"))
            self.lang_selector.addItems(languages)

            items = []
            for i in range(self.lang_selector.count()):
                items.append(self.lang_selector.itemText(i))

            if prev_item in items:
                self.lang_selector.setCurrentIndex(items.index(prev_item))
            else:
                self.lang_selector.setCurrentIndex(0)

        self.term_count.setText(
            self.ftr("term-count-label", {"count": self.manager.term_count()})
        )

    def update_table(self):
        if not self.manager.content:
            self.message_box("warning", "warning-no-file")
            return

        if self.lang_selector.currentIndex() != -1:
            terms = self.manager.content.get("terms", [])

            selected_index = self.lang_selector.currentIndex()
            selected_text = self.lang_selector.currentText()

            if not selected_text:
                self.message_box("warning", "warning-no-language-selected")
                return

            if selected_index == 0:
                lang_subset = {
                    d["code"]: d["name"]
                    for d in self.manager.get_languages()
                }
            else:
                code, name = self.manager.get_language_from_text(selected_text)
                lang_subset = {code: name}

            self.custom_table.update_table(self, terms, lang_subset)

    def open_dump_file(self, path):
        if not os.path.isfile(path):
            self.message_box("warning", ("warning-file-not-found", {"file_path": path}))
            return

        file_path = os.path.abspath(path)
        self.status_bar_message(("opening-file", {"file_path": file_path}))
        result = self.manager.process_dump_file(file_path)

        if result is True:
            self.config.add_recent_file(file_path)
            self.status_bar_message(
                ("opened-file", {"file_path": file_path}),
                15000
            )
            self.configure_menu(True)
            self.update_lang_selector()
        else:
            self.status_bar_message()
            self.message_box("error", result)

    def save_dump_file(self):
        if not self.manager.content:
            self.message_box("warning", "warning-no-file")
            return

        extensions = "{} (*{});; {} (*{})"
        import_type = self.manager.content["structure"]["import"]

        if import_type == FE.TXT.name:
            extensions = extensions.format(
                self.ftr("text-file"), FE.TXT.value,
                self.ftr("json-file"), FE.JSON.value
            )
        elif import_type == FE.JSON.name:
            extensions = extensions.format(
                self.ftr("json-file"), FE.JSON.value,
                self.ftr("text-file"), FE.TXT.value
            )
        else:
            self.message_box("error", ("error-unknown-import-type", {"type": import_type}))
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, self.ftr("save-title"),
            f"{self.manager.filename}_dump", extensions
        )

        if not file_path:
            return

        try:
            file_path = os.path.abspath(file_path)
            extension = os.path.splitext(file_path)[1].lower()

            with open(file_path, "w+", encoding="utf-8") as f:
                if extension == FE.TXT.value:
                    output = self.manager.build_txt_dump()
                elif extension == FE.JSON.value:
                    output = self.manager.build_json_dump()
                else:
                    raise InvalidExtensionError

                f.write(output)

            self.status_bar_message(("saved-file", {"file_path": file_path}))
        except (FileNotFoundError, PermissionError) as e:
            self.message_box("error", ("error-file-access", {"error": str(e)}))
        except TypeError as e:
            self.message_box("error", ("error-invalid-data", {"error": str(e)}))
        except OSError as e:
            self.message_box("error", ("error-save-failed", {"error": str(e)}))
        except InvalidExtensionError:
            self.message_box("error", "error-invalid-extension")

    def report(self, error_text):
        issues_link = '<a href="https://github.com/Veydzher/i2loc-manager/issues">Issues</a>'
        QMessageBox.critical(
            self, self.ftr("error-title"),
            f"{error_text}.\n{self.ftr('report-dev', {'link': issues_link})}",
        )

    def status_bar_message(self, text: str | tuple = "", timeout: int = 0):
        if not text:
            return self.statusBar().clearMessage()

        if isinstance(text, tuple):
            text, args = text
        else:
            args = None

        return self.statusBar().showMessage(self.ftr(text, args), timeout)

    def message_box(self, kind, text, *args, localize = True):
        if isinstance(text, tuple):
            text, var_dict = text
        else:
            var_dict = None

        title = self.ftr(f"{kind}-title")
        message = self.ftr(text, var_dict) if localize else text

        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)

        match kind:
            case "error":
                msg_box.setIcon(QMessageBox.Icon.Critical)
            case "information":
                msg_box.setIcon(QMessageBox.Icon.Information)
            case "question":
                msg_box.setIcon(QMessageBox.Icon.Question)
            case "warning":
                msg_box.setIcon(QMessageBox.Icon.Warning)
            case _:
                msg_box.setIcon(QMessageBox.Icon.Information)

        if args:
            msg_box.setStandardButtons(args[0])
            if len(args) > 1:
                msg_box.setDefaultButton(args[1])

            self.localise_buttons(msg_box)

        return msg_box.exec()

    def localise_buttons(self, box:QMessageBox | QDialogButtonBox):
        # Implement custom buttons localise names (e.g. import-button for Ok button)
        for button in box.buttons():
            button_type = type(box)

            match box.standardButton(button):
                case button_type.StandardButton.Ok:
                    button.setText(self.ftr("ok-button"))
                case button_type.StandardButton.Cancel:
                    button.setText(self.ftr("cancel-button"))
                case button_type.StandardButton.Yes:
                    button.setText(self.ftr("yes-button"))
                case button_type.StandardButton.No:
                    button.setText(self.ftr("no-button"))
                case button_type.StandardButton.Close:
                    button.setText(self.ftr("close-button"))

    def closeEvent(self, event: QCloseEvent):
        if self.manager.content:
            if self.manager.content != self.manager.backup:
                event.ignore()
                reply = self.message_box(
                    "question", "question-save-file",
                    QMessageBox.StandardButton.Yes
                    | QMessageBox.StandardButton.No
                    | QMessageBox.StandardButton.Cancel,
                    QMessageBox.StandardButton.Yes
                )

                if reply == QMessageBox.StandardButton.Yes:
                    self.save_dump_file()
                elif reply == QMessageBox.StandardButton.Cancel:
                    return

        event.accept()

    def _open_file_dialog(self):
        path, _ = QFileDialog.getOpenFileName(
            self, self.ftr("open-title"), "",
            f"{self.ftr('dump-file')} (*{FE.TXT.value}; *{FE.JSON.value})"
        )

        if not path:
            return

        self.open_dump_file(path)

    def _open_about_dialog(self):
        self.about_dialog = About(self)
        self.about_dialog.show()

    def _refresh_ui(self):
        if self.menuBar().children():
            self.menuBar().clear()
        self.setup_menu_bar()

        if not hasattr(self, "custom_table"):
            self.statusBar()
            self.setup_table_controls()

        if self.manager.content:
            self.configure_menu(True)
            self.update_lang_selector()
        else:
            self.configure_menu(False)

    def _set_theme_mode(self, theme):
        try:
            application.setStyle(theme)
        except Exception as e:
            print("[ERROR]", str(e))
            application.setStyle("Fusion")
            self.config.set_config("theme", "Fusion")

        if theme == "Fusion":
            self.setStyleSheet("combobox-popup: 0;")
        else:
            self.setStyleSheet("")

    def _set_window_size(self):
        screen = QApplication.primaryScreen()
        geometry = screen.availableGeometry()
        screen_width = geometry.width()
        screen_height = geometry.height()

        width = int(screen_width * 0.7)
        height = int(screen_height * 0.7)

        width = max(width, self.minimumWidth())
        height = max(height, self.minimumHeight())

        x = (screen_width - width) // 2
        y = (screen_height - height) // 2

        self.setGeometry(x, y, width, height)

if __name__ == "__main__":
    try:
        application = QApplication(sys.argv)
        window = I2ManagerUI()
        window.show()
        sys.exit(application.exec())
    except Exception as e:
        I2ManagerUI().report(str(e))
