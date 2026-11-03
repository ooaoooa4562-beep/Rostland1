from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import QProcess, Qt
from PySide6.QtGui import QAction, QColor, QFont, QSyntaxHighlighter, QTextCharFormat
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSplitter,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)


REPO_ROOT = Path(__file__).resolve().parent.parent
INTERPRETER = REPO_ROOT / "main.py"


class RostHighlighter(QSyntaxHighlighter):
    """Small syntax highlighter for the current RostLang syntax."""

    def __init__(self, document):
        super().__init__(document)
        self.rules = []

        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#c792ea"))
        keyword_format.setFontWeight(QFont.Weight.Bold)
        for word in (
            "say", "make", "change", "ask", "when", "otherwise", "if",
            "else", "while", "repeat", "for", "in", "action", "def",
            "return", "class", "try", "except", "Local", "Period",
            "use", "Module", "stop", "skip", "True", "False", "None",
        ):
            self.rules.append((rf"\\b{word}\\b", keyword_format))

        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#a5d6a7"))
        self.rules.append((r'"[^"\\n]*"|\'[^\'\\n]*\'', string_format))

        number_format = QTextCharFormat()
        number_format.setForeground(QColor("#f78c6c"))
        self.rules.append((r"\\b\\d+(?:\\.\\d+)?\\b", number_format))

        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#718096"))
        comment_format.setFontItalic(True)
        self.rules.append((r"#.*$", comment_format))

    def highlightBlock(self, text):
        import re

        for pattern, fmt in self.rules:
            for match in re.finditer(pattern, text):
                self.setFormat(match.start(), match.end() - match.start(), fmt)


class RostLauncher(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_file: Path | None = None
        self.dirty = False
        self.process = QProcess(self)

        self.setWindowTitle("RostLang Launcher")
        self.resize(1180, 760)
        self.setMinimumSize(850, 560)

        self._build_ui()
        self._build_menu()
        self._connect_process()
        self._set_editor_text(
            '# Welcome to RostLang!\n'
            'say "Hello from RostLang Launcher!"\n'
        )
        self.statusBar().showMessage("Ready · RostLang 0.7.0-alpha")

    def _build_ui(self):
        central = QWidget()
        root = QVBoxLayout(central)
        root.setContentsMargins(18, 16, 18, 14)
        root.setSpacing(12)

        header = QHBoxLayout()
        brand = QLabel("ROSTLANG")
        brand.setObjectName("brand")
        version = QLabel("LAUNCHER  0.1.0")
        version.setObjectName("version")
        header.addWidget(brand)
        header.addSpacing(12)
        header.addWidget(version)
        header.addStretch()

        self.file_label = QLabel("Untitled.rost")
        self.file_label.setObjectName("fileLabel")
        header.addWidget(self.file_label)
        root.addLayout(header)

        toolbar = QHBoxLayout()
        self.new_button = self._button("＋  New", "secondary")
        self.open_button = self._button("Open", "secondary")
        self.save_button = self._button("Save", "secondary")
        self.run_button = self._button("▶  Run", "primary")
        self.stop_button = self._button("■  Stop", "danger")
        self.stop_button.setEnabled(False)

        for button in (
            self.new_button, self.open_button, self.save_button,
            self.run_button, self.stop_button,
        ):
            toolbar.addWidget(button)
        toolbar.addStretch()
        root.addLayout(toolbar)

        splitter = QSplitter(Qt.Orientation.Vertical)

        editor_panel = QWidget()
        editor_layout = QVBoxLayout(editor_panel)
        editor_layout.setContentsMargins(0, 0, 0, 0)
        editor_title = QLabel("  EDITOR")
        editor_title.setObjectName("sectionTitle")
        editor_layout.addWidget(editor_title)

        self.editor = QPlainTextEdit()
        self.editor.setObjectName("editor")
        self.editor.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.editor.setTabStopDistance(4 * self.editor.fontMetrics().horizontalAdvance(" "))
        self.highlighter = RostHighlighter(self.editor.document())
        editor_layout.addWidget(self.editor)
        splitter.addWidget(editor_panel)

        console_panel = QWidget()
        console_layout = QVBoxLayout(console_panel)
        console_layout.setContentsMargins(0, 0, 0, 0)
        console_header = QHBoxLayout()
        console_title = QLabel("  OUTPUT")
        console_title.setObjectName("sectionTitle")
        self.clear_button = self._button("Clear", "secondary")
        console_header.addWidget(console_title)
        console_header.addStretch()
        console_header.addWidget(self.clear_button)
        console_layout.addLayout(console_header)

        self.console = QPlainTextEdit()
        self.console.setObjectName("console")
        self.console.setReadOnly(True)
        self.console.setMaximumBlockCount(3000)
        console_layout.addWidget(self.console)

        input_row = QHBoxLayout()
        self.stdin_input = QLineEdit()
        self.stdin_input.setPlaceholderText("Send input to a running RostLang program…")
        self.send_button = self._button("Send", "secondary")
        self.send_button.setEnabled(False)
        input_row.addWidget(self.stdin_input)
        input_row.addWidget(self.send_button)
        console_layout.addLayout(input_row)
        splitter.addWidget(console_panel)
        splitter.setSizes([440, 220])
        root.addWidget(splitter, 1)

        self.setCentralWidget(central)
        self.setStatusBar(QStatusBar())

        self.new_button.clicked.connect(self.new_file)
        self.open_button.clicked.connect(self.open_file)
        self.save_button.clicked.connect(self.save_file)
        self.run_button.clicked.connect(self.run_file)
        self.stop_button.clicked.connect(self.stop_process)
        self.clear_button.clicked.connect(self.console.clear)
        self.send_button.clicked.connect(self.send_input)
        self.stdin_input.returnPressed.connect(self.send_input)
        self.editor.textChanged.connect(self._mark_dirty)

        self.setStyleSheet("""
            QMainWindow, QWidget { background: #0b1020; color: #e6edf7; }
            QLabel#brand { color: #f2f6ff; font-size: 21px; font-weight: 800; letter-spacing: 3px; }
            QLabel#version { color: #8b9bb8; font-size: 10px; font-weight: 700; letter-spacing: 1px; }
            QLabel#fileLabel { color: #a9b8d0; padding: 7px 12px; background: #121b30; border: 1px solid #24324d; border-radius: 8px; }
            QLabel#sectionTitle { color: #8da4c7; font-size: 10px; font-weight: 800; letter-spacing: 2px; padding: 5px 0; }
            QPlainTextEdit { background: #0e1729; border: 1px solid #23334f; border-radius: 10px; padding: 12px; color: #dbe7fa; selection-background-color: #294b83; }
            QPlainTextEdit#editor { font-family: Consolas, 'Cascadia Code', monospace; font-size: 13px; }
            QPlainTextEdit#console { font-family: Consolas, monospace; font-size: 12px; color: #a9e6bd; }
            QLineEdit { background: #111c30; border: 1px solid #2a3b5a; border-radius: 8px; padding: 9px 11px; color: #edf3ff; }
            QPushButton { border: 1px solid #2a3b5a; border-radius: 8px; padding: 9px 14px; color: #dce8fb; background: #15223a; font-weight: 600; }
            QPushButton:hover { background: #203453; }
            QPushButton:disabled { color: #61708a; background: #111827; }
            QPushButton#primary { background: #6d4aff; border-color: #8064ff; color: white; }
            QPushButton#primary:hover { background: #8064ff; }
            QPushButton#danger { background: #351c2b; border-color: #74344e; color: #ffb4c8; }
            QStatusBar { color: #91a2bd; border-top: 1px solid #1c2b43; }
            QSplitter::handle { background: #1b2941; height: 5px; }
        """)

    def _button(self, text, kind):
        button = QPushButton(text)
        button.setObjectName(kind)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        return button

    def _build_menu(self):
        file_menu = self.menuBar().addMenu("File")
        for label, callback, shortcut in (
            ("New", self.new_file, "Ctrl+N"),
            ("Open…", self.open_file, "Ctrl+O"),
            ("Save", self.save_file, "Ctrl+S"),
        ):
            action = QAction(label, self)
            action.setShortcut(shortcut)
            action.triggered.connect(callback)
            file_menu.addAction(action)

        run_menu = self.menuBar().addMenu("Run")
        run_action = QAction("Run current file", self)
        run_action.setShortcut("F5")
        run_action.triggered.connect(self.run_file)
        run_menu.addAction(run_action)

    def _connect_process(self):
        self.process.readyReadStandardOutput.connect(self._read_stdout)
        self.process.readyReadStandardError.connect(self._read_stderr)
        self.process.finished.connect(self._process_finished)
        self.process.errorOccurred.connect(self._process_error)

    def _set_editor_text(self, text):
        self.editor.blockSignals(True)
        self.editor.setPlainText(text)
        self.editor.blockSignals(False)
        self.dirty = False
        self._update_title()

    def _mark_dirty(self):
        self.dirty = True
        self._update_title()

    def _update_title(self):
        name = self.current_file.name if self.current_file else "Untitled.rost"
        self.file_label.setText(name + ("  •" if self.dirty else ""))
        self.setWindowTitle(f"{'*' if self.dirty else ''}{name} — RostLang Launcher")

    def _confirm_discard(self):
        if not self.dirty:
            return True
        answer = QMessageBox.question(
            self,
            "Unsaved changes",
            "Save changes before continuing?",
            QMessageBox.StandardButton.Save
            | QMessageBox.StandardButton.Discard
            | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Save,
        )
        if answer == QMessageBox.StandardButton.Save:
            return self.save_file()
        return answer == QMessageBox.StandardButton.Discard

    def new_file(self):
        if not self._confirm_discard():
            return
        self.current_file = None
        self._set_editor_text('# New RostLang program\nsay "Hello!"\n')
        self.statusBar().showMessage("New file")

    def open_file(self):
        if not self._confirm_discard():
            return
        filename, _ = QFileDialog.getOpenFileName(
            self, "Open RostLang file", "", "RostLang files (*.rost);;All files (*)"
        )
        if not filename:
            return
        try:
            self.current_file = Path(filename).resolve()
            self._set_editor_text(self.current_file.read_text(encoding="utf-8"))
            self.statusBar().showMessage(f"Opened {self.current_file}")
        except OSError as error:
            QMessageBox.critical(self, "Open failed", str(error))

    def save_file(self):
        if self.current_file is None:
            filename, _ = QFileDialog.getSaveFileName(
                self, "Save RostLang file", "main.rost", "RostLang files (*.rost)"
            )
            if not filename:
                return False
            self.current_file = Path(filename)
            if self.current_file.suffix.lower() != ".rost":
                self.current_file = self.current_file.with_suffix(".rost")
        try:
            self.current_file.parent.mkdir(parents=True, exist_ok=True)
            self.current_file.write_text(self.editor.toPlainText(), encoding="utf-8")
            self.dirty = False
            self._update_title()
            self.statusBar().showMessage(f"Saved {self.current_file}")
            return True
        except OSError as error:
            QMessageBox.critical(self, "Save failed", str(error))
            return False

    def run_file(self):
        if self.process.state() != QProcess.ProcessState.NotRunning:
            self.statusBar().showMessage("A program is already running")
            return
        if not INTERPRETER.is_file():
            QMessageBox.critical(
                self, "Interpreter not found",
                f"Could not find the RostLang interpreter at:\n{INTERPRETER}"
            )
            return
        if self.dirty and not self.save_file():
            return
        if self.current_file is None:
            QMessageBox.information(self, "Save first", "Save this program as a .rost file first.")
            return

        self.console.appendPlainText(f"> Running {self.current_file.name}")
        self.process.setProgram(sys.executable)
        self.process.setArguments([str(INTERPRETER), str(self.current_file)])
        self.process.setWorkingDirectory(str(self.current_file.parent))
        self.process.start()
        self.run_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.send_button.setEnabled(True)
        self.statusBar().showMessage("Running…")

    def stop_process(self):
        if self.process.state() != QProcess.ProcessState.NotRunning:
            self.process.terminate()
            if not self.process.waitForFinished(1200):
                self.process.kill()
            self.console.appendPlainText("\n[Launcher] Process stopped.")
        self._set_running(False)

    def send_input(self):
        if self.process.state() == QProcess.ProcessState.NotRunning:
            return
        value = self.stdin_input.text()
        self.process.write((value + "\n").encode("utf-8"))
        self.stdin_input.clear()

    def _read_stdout(self):
        data = bytes(self.process.readAllStandardOutput()).decode("utf-8", errors="replace")
        if data:
            self.console.moveCursor(self.console.textCursor().MoveOperation.End)
            self.console.insertPlainText(data)
            self.console.ensureCursorVisible()

    def _read_stderr(self):
        data = bytes(self.process.readAllStandardError()).decode("utf-8", errors="replace")
        if data:
            self.console.moveCursor(self.console.textCursor().MoveOperation.End)
            self.console.insertPlainText(data)
            self.console.ensureCursorVisible()

    def _process_finished(self, exit_code, exit_status):
        self._read_stdout()
        self._read_stderr()
        self.console.appendPlainText(f"\n[Launcher] Finished with exit code {exit_code}.")
        self._set_running(False)
        self.statusBar().showMessage("Finished")

    def _process_error(self, error):
        self.console.appendPlainText(f"\n[Launcher] Process error: {error}")
        self._set_running(False)

    def _set_running(self, running):
        self.run_button.setEnabled(not running)
        self.stop_button.setEnabled(running)
        self.send_button.setEnabled(running)

    def closeEvent(self, event):
        if not self._confirm_discard():
            event.ignore()
            return
        if self.process.state() != QProcess.ProcessState.NotRunning:
            self.process.kill()
            self.process.waitForFinished(1000)
        event.accept()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("RostLang Launcher")
    app.setStyle("Fusion")
    window = RostLauncher()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
