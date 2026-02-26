import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

import requests
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QMessageBox,
    QPushButton, QProgressBar, QFrame, QWidget, QScrollArea
)

from gui.helpers import message_box
from utils.app_config import app_cfg
from utils.app_locales import ftr


def _is_newer_version(latest: str, current: str) -> bool:
    try:
        latest_parts = [int(x) for x in latest.split(".")]
        current_parts = [int(x) for x in current.split(".")]

        max_len = max(len(latest_parts), len(current_parts))
        latest_parts += [0] * (max_len - len(latest_parts))
        current_parts += [0] * (max_len - len(current_parts))

        return latest_parts > current_parts
    except (ValueError, IndexError, TypeError):
        return latest != current


class UpdateChecker(QThread):
    update_available = Signal(dict)
    pending_update = Signal(dict)
    no_update = Signal()
    error = Signal(str)

    def __init__(self, current_version: str):
        super().__init__()
        self.current_version = current_version
        self.repo_url = "https://github.com/Veydzher/i2loc-manager"

        parts = self.repo_url.rstrip("/").split("/")
        self.owner = parts[-2]
        self.repo = parts[-1]

    def run(self):
        pending = app_cfg.get_config("update.pending_update")
        if pending and Path(pending.get("file_path", "")).exists():
            self.pending_update.emit(pending)
            return

        try:
            api_url = f"https://api.github.com/repos/{self.owner}/{self.repo}/releases/latest"

            response = requests.get(api_url, timeout=10)
            response.raise_for_status()

            release_data = response.json()
            latest_version = release_data["tag_name"].lstrip("v")

            if _is_newer_version(latest_version, self.current_version):
                download_url = None
                for asset in release_data.get("assets", []):
                    if asset["name"].endswith(".zip"):
                        download_url = asset["browser_download_url"]
                        break

                if not download_url:
                    print("[UPDATE] Failed to get download url!")

                self.update_available.emit({
                    "version": latest_version,
                    "download_url": download_url,
                    "changelog": release_data.get("body", ftr("no-changelog-available")),
                    "release_name": release_data.get("name", ftr("version-label", {"version": latest_version}))
                })
            else:
                self.no_update.emit()

        except requests.exceptions.RequestException as e:
            self.error.emit(f"Network error: {str(e)}")
        except Exception as e:
            self.error.emit(f"Error checking for updates: {str(e)}")


class UpdateDownloader(QThread):
    progress = Signal(int)  # Download progress percentage
    finished = Signal(str)  # Path to downloaded file
    error = Signal(str)

    def __init__(self, download_url: str, save_path: Path):
        super().__init__()
        self.download_url = download_url
        self.save_path = save_path

    def run(self):
        try:
            response = requests.get(self.download_url, stream=True, timeout=30)
            response.raise_for_status()

            total_size = int(response.headers.get("content-length", 0))
            downloaded = 0

            self.save_path.parent.mkdir(parents=True, exist_ok=True)

            with open(self.save_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)

                        if total_size > 0:
                            progress = int((downloaded / total_size) * 100)
                            self.progress.emit(progress)

            self.finished.emit(str(self.save_path))

        except Exception as e:
            self.error.emit(f"Download error: {str(e)}")


class UpdateDialog(QDialog):
    def __init__(self, parent=None, update_info: dict = None):
        super().__init__(parent)
        self.download_button = None
        self.skip_button = None
        self.status_label = None
        self.progress_bar = None
        self.progress_container = None
        self.changelog_text = None
        self.update_info = update_info
        self.download_thread = None
        self.update_file_path = None

        self.setWindowTitle(ftr("update-available-title"))
        self.setMinimumSize(550, 450)
        self.setMaximumSize(650, 550)
        self.setModal(True)

        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        header_layout = QVBoxLayout()
        header_layout.setSpacing(10)

        title_container = QHBoxLayout()

        icon_label = QLabel("🎉")
        icon_label.setStyleSheet("font-size: 32px;")
        title_container.addWidget(icon_label)

        title = QLabel(ftr("update-available-message", {
            "version": self.update_info["version"],
            "name": self.update_info["release_name"]
        }))
        title_font = title.font()
        title_font.setPointSize(title_font.pointSize() + 3)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setWordWrap(True)
        title_container.addWidget(title, 1)

        header_layout.addLayout(title_container)

        version_container = QHBoxLayout()
        version_badge = QLabel(ftr("version-label", {"version": self.update_info["version"]}))
        version_font = version_badge.font()
        version_font.setBold(True)
        version_badge.setFont(version_font)
        version_container.addWidget(version_badge)
        version_container.addStretch()
        header_layout.addLayout(version_container)

        layout.addLayout(header_layout)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(line)

        changelog_title = QLabel(ftr("changelog-label"))
        changelog_font = changelog_title.font()
        changelog_font.setBold(True)
        changelog_title.setFont(changelog_font)
        layout.addWidget(changelog_title)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMaximumHeight(200)
        scroll_area.setFrameShape(QFrame.Shape.StyledPanel)

        self.changelog_text = QLabel()
        self.changelog_text.setOpenExternalLinks(True)
        self.changelog_text.setTextFormat(Qt.TextFormat.MarkdownText)
        self.changelog_text.setText(self.update_info["changelog"])
        self.changelog_text.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        self.changelog_text.setWordWrap(True)
        self.changelog_text.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.changelog_text.setMargin(10)

        scroll_area.setWidget(self.changelog_text)
        layout.addWidget(scroll_area)

        self.progress_container = QWidget()
        progress_layout = QVBoxLayout(self.progress_container)
        progress_layout.setContentsMargins(0, 10, 0, 10)
        progress_layout.setSpacing(8)

        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%p%")
        self.progress_bar.setMinimumHeight(25)
        progress_layout.addWidget(self.progress_bar)

        self.status_label = QLabel()
        status_font = self.status_label.font()
        status_font.setBold(True)
        self.status_label.setFont(status_font)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        progress_layout.addWidget(self.status_label)

        self.progress_container.hide()
        layout.addWidget(self.progress_container)

        layout.addStretch()

        line2 = QFrame()
        line2.setFrameShape(QFrame.Shape.HLine)
        line2.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(line2)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        self.skip_button = QPushButton(ftr("skip-update-button"))
        self.skip_button.clicked.connect(self.reject)
        self.skip_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.skip_button.setMinimumWidth(120)

        self.download_button = QPushButton(ftr("download-update-button"))
        self.download_button.clicked.connect(self._start_download)
        self.download_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.download_button.setDefault(True)
        self.download_button.setMinimumWidth(120)

        button_layout.addWidget(self.skip_button)
        button_layout.addStretch()
        button_layout.addWidget(self.download_button)

        layout.addLayout(button_layout)

    def _start_download(self):
        self.download_button.setEnabled(False)
        self.skip_button.setEnabled(False)
        self.progress_container.show()
        self.status_label.setText(ftr("downloading-update"))

        temp_dir = Path.cwd() / "temp"
        temp_dir.mkdir(exist_ok=True)

        download_path = temp_dir / f"update_{self.update_info['version']}.zip"

        self.download_thread = UpdateDownloader(
            self.update_info["download_url"],
            download_path
        )
        self.download_thread.progress.connect(self._update_progress)
        self.download_thread.finished.connect(self._on_download_finished)
        self.download_thread.error.connect(self._on_download_error)
        self.download_thread.start()

    def _update_progress(self, value: int):
        self.progress_bar.setValue(value)
        if value == 100:
            self.status_label.setText(ftr("download-complete"))

    def _on_download_finished(self, file_path: str):
        self.update_file_path = file_path

        app_cfg.set_config("update.pending_update", {
            "version": self.update_info["version"],
            "file_path": str(file_path),
            "download_date": str(Path(file_path).stat().st_mtime)
        })

        self.download_button.hide()
        self.skip_button.setText(ftr("install-later-button"))
        self.skip_button.setEnabled(True)
        self.skip_button.setDefault(False)

        install_button = QPushButton("🚀 " + ftr("install-now-button"))
        install_button.clicked.connect(self._install_update)
        install_button.setCursor(Qt.CursorShape.PointingHandCursor)
        install_button.setDefault(True)
        install_button.setMinimumWidth(120)

        button_layout = self.layout().itemAt(self.layout().count() - 1).layout()
        button_layout.insertWidget(button_layout.count() - 1, install_button)

    def _on_download_error(self, error_msg: str):
        self.status_label.setText(ftr("download-error"))
        message_box(self, "error", ("error-download-failed", {"error": error_msg}))

        self.download_button.setEnabled(True)
        self.skip_button.setEnabled(True)
        self.progress_bar.setValue(0)

    def _install_update(self):
        self.setDisabled(True)
        try:
            extract_dir = Path.cwd() / "temp" / "extracted"
            extract_dir.mkdir(exist_ok=True)

            self.status_label.setText(ftr("installing-update"))

            with zipfile.ZipFile(self.update_file_path, "r") as zip_ref:
                zip_ref.extractall(extract_dir)

            update_script = self.create_update_script(extract_dir)

            if sys.platform == "win32":
                subprocess.Popen([update_script], creationflags=subprocess.CREATE_NEW_CONSOLE)
            else:
                subprocess.Popen(["sh", update_script])

            app_cfg.set_config("update.pending_update", None)

            sys.exit(0)
        except Exception as e:
            message_box(self, "error", ("error-install-failed", {"error": str(e)}))

    @staticmethod
    def create_update_script(source_dir: Path):
        app_dir = Path.cwd()

        if sys.platform == "win32":
            script_path = app_dir / "update.bat"

            script_content = f"""@echo off
            chcp 65001 >nul
            title Updating Application
            echo.
            echo Installing update...
            timeout /t 3 /nobreak >nul

            xcopy "{source_dir}\\*" "{app_dir}" /E /H /C /I /Y /Q >nul 2>&1

            echo Update complete!
            timeout /t 1 /nobreak >nul

            cd /d "{app_dir}"

            if exist "I2-Localization-Manager.exe" (
                start "" "I2-Localization-Manager.exe"
            ) else if exist "main.exe" (
                start "" "main.exe"
            )

            timeout /t 2 /nobreak >nul
            rd /s /q "{source_dir.parent}" >nul 2>&1

            del "%~f0" >nul 2>&1
            """
        else:
            script_path = app_dir / "update.sh"
            script_content = f"""
                #!/bin/bash
                echo "Installing update..."
                sleep 3
            
                # Copy all files
                cp -rf "{source_dir}/"* "{app_dir}/" 2>/dev/null
            
                echo "Update complete!"
                sleep 1
            
                cd "{app_dir}"
            
                # Find and run the executable
                if [ -f "./I2-Localization-Manager" ]; then
                    chmod +x "./I2-Localization-Manager"
                    nohup "./I2-Localization-Manager" >/dev/null 2>&1 &
                elif [ -f "./main" ]; then
                    chmod +x "./main"
                    nohup "./main" >/dev/null 2>&1 &
                fi
            
                # Clean up
                sleep 2
                rm -rf "{source_dir.parent}" 2>/dev/null
                rm -- "$0"
            """

        with open(script_path, "w", encoding="utf-8") as f:
            f.write(script_content)

        if sys.platform != "win32":
            script_path.chmod(0o755)

        return str(script_path)


class UpdateManager:
    def __init__(self, parent, current_version: str):
        self.silent = None
        self.parent = parent
        self.current_version = current_version
        self.checker_thread = None

    def check_for_updates(self, silent: bool = False):
        self.silent = silent

        if not silent:
            self.parent.status_bar_message("checking-for-updates")

        self.checker_thread = UpdateChecker(self.current_version)
        self.checker_thread.update_available.connect(self._on_update_available)
        self.checker_thread.pending_update.connect(self._on_pending_update)
        self.checker_thread.no_update.connect(lambda: self._on_no_update(silent))
        self.checker_thread.error.connect(lambda err: self._on_error(err, silent))
        self.checker_thread.start()

    def _on_update_available(self, update_info: dict):
        self.parent.status_bar_message()
        dialog = UpdateDialog(self.parent, update_info)
        dialog.exec()

    def _on_pending_update(self, pending: dict):
        self.parent.status_bar_message()
        version = pending.get("version", "UNKNOWN")

        reply = message_box(
            self.parent,
            "question",
            ("question-install-pending-update", {"version": version}),
            standard_buttons=(
                QMessageBox.StandardButton.Yes
                | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes
            )
        )

        if reply == QMessageBox.StandardButton.Yes:
            self._install_pending_update(Path(pending["file_path"]))
        else:
            delete_reply = message_box(
                self.parent,
                "question",
                "question-delete-pending-update",
                standard_buttons=(
                    QMessageBox.StandardButton.Yes
                    | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )
            )

            if delete_reply == QMessageBox.StandardButton.Yes:
                self._cleanup_pending_update()

    def _on_no_update(self, silent: bool):
        self.parent.status_bar_message()
        if not silent:
            message_box(self.parent, "information", "info-no-updates-available")

    def _on_error(self, error_msg: str, silent: bool):
        self.parent.status_bar_message()
        if not silent:
            message_box(self.parent, "error", ("error-check-updates-failed", {"error": error_msg}))

    def _install_pending_update(self, file_path: Path):
        try:
            extract_dir = Path.cwd() / "temp" / "extracted"
            extract_dir.mkdir(parents=True, exist_ok=True)

            self.parent.status_bar_message("installing-update")

            with zipfile.ZipFile(file_path, "r") as zip_ref:
                zip_ref.extractall(extract_dir)

            update_script = UpdateDialog.create_update_script(extract_dir)

            if sys.platform == "win32":
                subprocess.Popen([update_script], creationflags=subprocess.CREATE_NEW_CONSOLE)
            else:
                subprocess.Popen(["sh", update_script])

            sys.exit(0)

        except Exception as e:
            message_box(self.parent, "error", ("error-install-failed", {"error": str(e)}))

    @staticmethod
    def _cleanup_pending_update():
        pending = app_cfg.get_config("update.pending_update", None)
        if pending:
            file_path = Path(pending.get("file_path", ""))
            if file_path.exists():
                try:
                    file_path.unlink()

                    temp_dir = file_path.parent
                    if temp_dir.exists() and temp_dir.name == "temp":
                        shutil.rmtree(temp_dir, ignore_errors=True)
                except (PermissionError, FileNotFoundError, OSError, IsADirectoryError) as e:
                    raise Exception("Error while processing the file: ", str(e))

            app_cfg.set_config("update.pending_update", None)
