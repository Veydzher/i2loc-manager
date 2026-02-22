from PySide6.QtCore import Qt, QMargins
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QLabel, QDialog, QVBoxLayout, QPushButton

from utils.app_locales import fluent


class About(QDialog):
    def __init__(self, mw):
        super().__init__(mw)
        self.ts = fluent.tr_batch([
            "about-app", ("about-app-version", {"version": mw.VERSION}), "close-button",
            ("about-app-desc", {
                "I2Localization": "<a href=http://inter-illusion.com/tools/i2-localization>I2 Localization</a>",
                "UABEA": "<a href=https://github.com/nesrak1/UABEA>UABEA</a>"
            })
        ])

        self.setFixedSize(350, 350)
        self.setWindowTitle(self.ts["about-app"])
        self.setWindowFlags(
            Qt.WindowType.Window
            | Qt.WindowType.CustomizeWindowHint
            | Qt.WindowType.WindowTitleHint
            | Qt.WindowType.WindowCloseButtonHint
        )
        self.setWindowModality(Qt.WindowModality.ApplicationModal)

        layout = QVBoxLayout(self)

        icon_label = QLabel()
        icon_pixmap = QIcon("assets/icon.ico").pixmap(128, 128)
        icon_label.setPixmap(icon_pixmap)

        app_name = QLabel(f"<b>{mw.TITLE}</b>")
        app_version = QLabel(self.ts["about-app-version"])

        app_author = QLabel(
            "© 2026 <a href=https://github.com/Veydzher>veydzh3r</a>",
            openExternalLinks=True,
            textInteractionFlags=Qt.TextInteractionFlag.TextBrowserInteraction,
        )

        app_description = QLabel(
            self.ts["about-app-desc"],
            alignment=Qt.AlignmentFlag.AlignCenter,
            wordWrap=True,
            margin=10,
            openExternalLinks=True,
        )

        close_button = QPushButton(self.ts["close-button"])
        close_button.setFixedSize(75, 30)
        close_button.clicked.connect(self.close)

        layout.addWidget(icon_label, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(app_name, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(app_author, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(app_version, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addSpacing(20)
        layout.addWidget(app_description)
        layout.addSpacing(40)
        layout.addWidget(close_button, alignment=Qt.AlignmentFlag.AlignCenter)
