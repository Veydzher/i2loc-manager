from typing import Any

from PySide6.QtCore import Qt, QObject, Signal, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QMessageBox, QDialogButtonBox, QApplication, QWidget, QMainWindow, QPushButton,
    QVBoxLayout, QSizePolicy, QFrame, QToolButton, QCheckBox, QComboBox, QLineEdit
)

from utils.app_config import app_cfg
from utils.app_locales import ftr
from utils.helpers import pathfind
from utils.manager import manager


class FileWorker(QObject):
    finished = Signal(str, object)

    def __init__(self, file_path: str):
        super().__init__()
        self.file_path = file_path

    def open(self):
        try:
            result = manager.open_dump_file(self.file_path)
            self.finished.emit(self.file_path, result)
        except Exception as e:
            raise e from e


class ConfigurableLineEdit(QLineEdit):
    def __init__(self, cfg_key: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setText(app_cfg.get_config(cfg_key, ""))
        self.textChanged.connect(lambda text: app_cfg.set_config(cfg_key, text))


class ConfigurableCheckBox(QCheckBox):
    def __init__(self, localizable_key: str, cfg_key: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setText(ftr(localizable_key))
        self.setChecked(app_cfg.get_config(cfg_key, False))
        self.toggled.connect(lambda checked: app_cfg.set_config(cfg_key, checked))


class ConfigurableComboBox(QComboBox):
    def __init__(self, items: list[tuple[str, Any]], cfg_key: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        cfg_value = app_cfg.get_config(cfg_key, items[0][1] if items else None)
        for key, value in items:
            self.addItem(key, value)

        index = self.findData(cfg_value)
        self.setCurrentIndex(index if index != -1 else 0)
        self.currentIndexChanged.connect(lambda _: app_cfg.set_config(cfg_key, self.currentData()))


class CollapsibleSection(QWidget):
    def __init__(self, title: str = ""):
        super().__init__()

        self._is_collapsed = True
        self._animation_duration = 200

        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.toggle_button = QToolButton()
        self.toggle_button.setStyleSheet("""
            QToolButton {
                border: none;
                background: transparent;
                font-weight: bold;
                text-align: left;
                padding: 5px;
            }
            QToolButton:hover {
                background: palette(mid);
            }
        """)
        self.toggle_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.toggle_button.setArrowType(Qt.ArrowType.RightArrow)
        self.toggle_button.setText(title)
        self.toggle_button.setCheckable(True)
        self.toggle_button.setChecked(False)
        self.toggle_button.clicked.connect(self.toggle)

        self.content_area = QFrame()
        self.content_area.setFrameShape(QFrame.Shape.NoFrame)
        self.content_area.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed
        )

        self.content_layout = QVBoxLayout(self.content_area)
        self.content_layout.setContentsMargins(20, 5, 5, 5)

        self.toggle_animation = QPropertyAnimation(self.content_area, b"maximumHeight")
        self.toggle_animation.setDuration(self._animation_duration)
        self.toggle_animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.toggle_animation.finished.connect(lambda: self.window().adjustSize())

        main_layout.addWidget(self.toggle_button)
        main_layout.addWidget(self.content_area)

        self.content_area.setMaximumHeight(0)
        self.content_area.setMinimumHeight(0)

    def toggle(self):
        if self.toggle_animation.state() == QPropertyAnimation.State.Running:
            return

        checked = self.toggle_button.isChecked()
        arrow_type = Qt.ArrowType.DownArrow if checked else Qt.ArrowType.RightArrow
        self.toggle_button.setArrowType(arrow_type)

        if checked:
            # Expand
            content_height = self.content_area.sizeHint().height()
            self.toggle_animation.setStartValue(0)
            self.toggle_animation.setEndValue(content_height)
        else:
            # Collapse
            current_height = self.content_area.maximumHeight()
            self.toggle_animation.setStartValue(current_height)
            self.toggle_animation.setEndValue(0)

        self.toggle_animation.start()
        self._is_collapsed = not checked

    def set_expanded(self, expanded: bool):
        if self.toggle_animation.state() == QPropertyAnimation.State.Running:
            self.toggle_animation.stop()

        self.toggle_button.blockSignals(True)
        self.toggle_button.setChecked(expanded)
        self.toggle_button.blockSignals(False)

        arrow_type = Qt.ArrowType.DownArrow if expanded else Qt.ArrowType.RightArrow
        self.toggle_button.setArrowType(arrow_type)

        if expanded:
            content_height = self.content_area.sizeHint().height()
            self.content_area.setMaximumHeight(content_height)
        else:
            self.content_area.setMaximumHeight(0)

        self._is_collapsed = not expanded

    def add_widget(self, widget):
        self.content_layout.addWidget(widget)

    def add_layout(self, layout):
        self.content_layout.addLayout(layout)


def localize_buttons(box: QMessageBox | QDialogButtonBox):
    for button in box.buttons():
        button_name = box.standardButton(button).name
        if button_name:
            button.setText(ftr(f"{button_name.lower()}-button"))


class CustomPushButton(QPushButton):
    def __init__(
            self,
            text: str,
            min_w: int = 0,
            min_h: int = 0,
            max_w: int = 100,
            max_h: int = 100
    ):
        super().__init__()
        text = ftr(text) if text.islower() and "-" in text else text
        self.setText(text)
        self.setMinimumSize(min_w, min_h)
        self.setMaximumSize(max_w, max_h)


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
