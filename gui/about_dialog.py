from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QDialog, QVBoxLayout, QPushButton

class About(QDialog):
    def __init__(self, mw):
        super().__init__(mw)
        self.ftr = mw.fluent.tr
        self.ts = mw.fluent.tr_batch([
            "about-app", ("about-app-version", {"version": "1.0"}), "close-button",
            ("about-app-desc", {
                "I2Localization":
                    "<a href=http://inter-illusion.com/tools/i2-localization>I2 Localization</a>",
                "UABEA":
                    "<a href=https://github.com/nesrak1/UABEA>UABEA</a>"
            })
        ])

        self.setup_dialog()

    def setup_dialog(self):
        self.setWindowTitle(self.ts["about-app"])
        self.setFixedSize(300, 200)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)

        self.create_layout()

    def create_layout(self):
        layout = QVBoxLayout(self)

        app_name = QLabel("<b>I2 Localization Manager</b>")
        app_version = QLabel(self.ts["about-app-version"])
        app_author = QLabel("© 2025 <a href=https://github.com/Veydzher>veydzh3r</a>")
        app_author.setOpenExternalLinks(True)
        app_author.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)

        app_description = QLabel(self.ts["about-app-desc"])
        app_description.setAlignment(Qt.AlignmentFlag.AlignCenter)
        app_description.setOpenExternalLinks(True)
        app_author.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        app_description.setWordWrap(True)

        close_button = QPushButton(self.ts["close-button"])
        close_button.setFixedSize(75, 30)
        close_button.clicked.connect(self.close)

        layout.addWidget(app_name, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(app_version, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(app_author, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addSpacing(10)
        layout.addWidget(app_description)
        layout.addSpacing(20)
        layout.addWidget(close_button, alignment=Qt.AlignmentFlag.AlignCenter)
