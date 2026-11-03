# RostLang Launcher 0.1.0

A desktop editor and runner for `.rost` programs, built with Python and PySide6.

## Run from source

Requirements: Python 3.10+.

From the repository root:

```bash
python -m pip install -r launcher/requirements.txt
python launcher/main.py
```

## Build a Windows EXE locally

On Windows, run:

```bat
launcher\build_windows.bat
```

The script installs build dependencies and creates:

```text
dist/RostLangLauncher.exe
```

The launcher is packaged as a one-file executable. Its RostLang interpreter runtime is bundled inside it, so the target computer does not need Python installed.

## Download the EXE from GitHub Actions

1. Open the repository on GitHub.
2. Select **Actions**.
3. Open **Build RostLang Launcher (Windows)**.
4. Wait for the workflow to finish successfully.
5. Open the completed workflow run.
6. Download the **RostLangLauncher-Windows** artifact.
7. Extract the ZIP and run `RostLangLauncher.exe`.

The workflow runs automatically when files under `launcher/`, `rostlang/`, or the root `main.py` change. It can also be started manually with **Run workflow**.

## Features in 0.1.0

- Dark desktop interface
- Open and save `.rost` files
- Basic syntax highlighting
- Create a starter project
- Run programs with the bundled RostLang runtime
- View standard output and errors
- Send text input to running programs
- Stop a running program
- Unsaved-changes warning

## Current limitations

This is an early launcher, not yet a full IDE. It currently edits one file at a time. Project explorer, multiple tabs, autocomplete, integrated debugger, themes, installer packaging, and a library manager are planned for later versions.
