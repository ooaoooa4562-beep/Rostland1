# RostLang Launcher 0.1.0

A desktop editor and runner for `.rost` programs, built with Python and PySide6.

## Requirements

- Python 3.10+
- PySide6

## Install

From the repository root:

```bash
python -m pip install -r launcher/requirements.txt
```

## Start

From the repository root:

```bash
python launcher/main.py
```

The launcher uses the interpreter in the repository's `main.py`. Keep the `launcher` folder beside the `rostlang` package and the root `main.py`.

## Features in 0.1.0

- Dark desktop interface
- Open and save `.rost` files
- Basic syntax highlighting
- Run the current file with the repository's RostLang interpreter
- View standard output and errors
- Send text input to a running program
- Stop a running program
- Unsaved-changes warning

## Current limitations

This is an early launcher, not yet a full IDE. It currently edits one file at a time. Project explorer, multiple tabs, autocomplete, integrated debugger, themes, packaging into an installer, and a library manager are planned for later versions.
