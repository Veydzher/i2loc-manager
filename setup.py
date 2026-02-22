import sys

from cx_Freeze import setup, Executable

base = "Win32GUI" if sys.platform == "win32" else None

executables = [
    Executable(
        script="main.py",
        base="gui",
        target_name="I2-Localization-Manager",
        copyright="Copyright (C) 2026 veydzh3r",
        icon="assets/icon.ico",
        shortcut_name="I2 Localization Manager",
        shortcut_dir="ProgramMenuFolder",
    )
]

build_exe_options = {
    "includes": ["gui", "utils"],
    "excludes": ["tkinter", "unittest", "zoneinfo", "tzdata"],
    "include_files": ["assets", "LICENSE", "README.md"],
    "zip_filename": "lib/library.zip",
    "zip_include_packages": ["encodings"],
    "zip_exclude_packages": ["PySide6", "shiboken6"],
}

setup(
    name="I2-Localization-Manager",
    version="1.1.5",
    description="A lightweight tool for managing I2 Localization assets exported via UABEA as dump files.",
    options={"build_exe": build_exe_options},
    executables=executables,
)
