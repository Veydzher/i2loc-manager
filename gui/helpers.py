from PySide6.QtWidgets import QMessageBox, QDialogButtonBox, QApplication, QWidget, QMainWindow
from PySide6.QtCore import Qt, QObject, Signal
from PySide6.QtGui import QIcon
from typing import Any
from utils.app_locales import ftr
from utils.manager import manager
from utils.helpers import pathfind

class FileWorker(QObject):
    finished = Signal(str, object)

    def __init__(self, file_path: str = ""):
        super().__init__()
        self.file_path = file_path

    def open(self):
        try:
            result = manager.open_dump_file(self.file_path)
            self.finished.emit(self.file_path, result)
        except Exception as e:
            raise e from e

    def run_import(self):
        pass

def localize_buttons(box: QMessageBox | QDialogButtonBox):
    for button in box.buttons():
        button_name = box.standardButton(button).name
        if button_name:
            button.setText(ftr(f"{button_name.lower()}-button"))

def message_box(
        parent: QWidget,
        title: str = "information",
        text: str | tuple[str, dict[str, Any] | None] = "",
        informative_text: str | tuple[str, dict | None] = "",
        detailed_text: str | tuple[str, dict | None] = "",
        localize: bool = True,
        standard_buttons: QMessageBox.StandardButton | tuple = QMessageBox.StandardButton.Ok,
        text_format: Qt.TextFormat = Qt.TextFormat.MarkdownText,
        text_interaction_flags: Qt.TextInteractionFlag = Qt.TextInteractionFlag.TextBrowserInteraction
    ):

    if isinstance(text, tuple):
        text, text_args = text
    else:
        text_args = None

    if isinstance(informative_text, tuple):
        informative_text, informative_args = informative_text
    else:
        informative_args = None

    if isinstance(detailed_text, tuple):
        detailed_text, detailed_args = detailed_text
    else:
        detailed_args = None

    msg_box = QMessageBox(parent, textFormat=text_format, textInteractionFlags=text_interaction_flags)
    msg_box.setWindowTitle(ftr(f"{title}-title"))
    msg_box.setText(ftr(text, text_args) if localize else text)
    if informative_text:
        msg_box.setInformativeText(ftr(informative_text, informative_args) if localize else informative_text)
    if detailed_text:
        msg_box.setDetailedText(ftr(detailed_text, detailed_args) if localize else detailed_text)

    match title:
        case "error":
            msg_box.setIcon(QMessageBox.Icon.Critical)
        case "question":
            msg_box.setIcon(QMessageBox.Icon.Question)
        case "warning":
            msg_box.setIcon(QMessageBox.Icon.Warning)
        case _:
            msg_box.setIcon(QMessageBox.Icon.Information)

    if standard_buttons:
        if isinstance(standard_buttons, tuple):
            msg_box.setStandardButtons(standard_buttons[0])
            if len(standard_buttons) > 1:
                msg_box.setDefaultButton(standard_buttons[1])
        else:
            msg_box.setDefaultButton(standard_buttons)

        localize_buttons(msg_box)

    return msg_box.exec()

def report(error_text):
    issues_link = "https://github.com/Veydzher/i2loc-manager/issues"
    message_box(
        QWidget(windowIcon=QIcon(pathfind("assets\\icon.ico"))), "error",
        error_text,
        ftr("report-dev", {"link": f"[Issues]({issues_link})"}),
        localize=False
    )

def set_window_size(window: QMainWindow):
    screen = QApplication.primaryScreen()
    geometry = screen.availableGeometry()
    screen_width = geometry.width()
    screen_height = geometry.height()

    width = max(int(screen_width * 0.7), window.minimumWidth())
    height = max(int(screen_height * 0.7), window.minimumHeight())

    x = (screen_width - width) // 2
    y = (screen_height - height) // 2

    window.setGeometry(x, y, width, height)
