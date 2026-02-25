import sys

from cx_Freeze import setup, Executable

VERSION = "1.1.0"
TITLE = "I2 Localization Manager"

if __name__ == "__main__":
    base = "Win32GUI" if sys.platform == "win32" else None

    executables = [
        Executable(
            script="main.py",
            base=base,
            target_name=TITLE.replace(" ", "-"),
            copyright="Copyright (C) 2026 veydzh3r",
            icon="assets/icon.ico",
            shortcut_name=TITLE,
            shortcut_dir="ProgramMenuFolder",
        )
    ]

    build_exe_options = {
        "includes": ["gui", "utils"],
        "excludes": ["tkinter", "unittest", "zoneinfo"],
        "include_files": ["assets", "LICENSE"],
        "zip_filename": "lib/library.zip",
        "zip_include_packages": ["encodings"],
        "zip_exclude_packages": ["PySide6", "shiboken6"],
    }

    setup(
        name=TITLE.replace(" ", "-"),
        version=VERSION,
        options={"build_exe": build_exe_options},
        executables=executables,
    )
