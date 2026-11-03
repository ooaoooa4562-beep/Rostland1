from __future__ import annotations

import contextlib
import io
import os
import threading
from pathlib import Path

from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput

from rostlang import __version__
from rostlang.interpreter import RostInterpreter


KV = """
<RostRoot>:
    orientation: "vertical"
    padding: "12dp"
    spacing: "8dp"
    canvas.before:
        Color:
            rgba: 0.035, 0.055, 0.10, 1
        Rectangle:
            pos: self.pos
            size: self.size
    BoxLayout:
        size_hint_y: None
        height: "42dp"
        Label:
            text: "ROSTLANG"
            bold: True
            color: 0.92, 0.95, 1, 1
            font_size: "20sp"
            halign: "left"
            text_size: self.size
        Label:
            text: "ANDROID  •  " + app.app_version
            color: 0.55, 0.65, 0.82, 1
            font_size: "10sp"
            halign: "right"
            text_size: self.size
    BoxLayout:
        size_hint_y: None
        height: "46dp"
        spacing: "5dp"
        Button:
            text: "New"
            on_release: root.new_file()
        Button:
            text: "Open"
            on_release: root.open_file()
        Button:
            text: "Save"
            on_release: root.save_file()
        Button:
            text: "Run ▶"
            on_release: root.run_code()
    TextInput:
        id: editor
        text: '# Welcome to RostLang!\\nsay "Hello from Android!"\\n'
        multiline: True
        font_name: "Roboto"
        font_size: "14sp"
        background_color: 0.055, 0.085, 0.14, 1
        foreground_color: 0.86, 0.91, 0.98, 1
        cursor_color: 0.45, 0.55, 1, 1
        padding: "10dp"
        size_hint_y: 0.67
    Label:
        text: "OUTPUT / CONSOLE"
        size_hint_y: None
        height: "24dp"
        color: 0.55, 0.68, 0.88, 1
        bold: True
        halign: "left"
        text_size: self.size
    TextInput:
        id: output
        readonly: True
        multiline: True
        font_size: "12sp"
        background_color: 0.025, 0.04, 0.075, 1
        foreground_color: 0.62, 0.9, 0.72, 1
        padding: "8dp"
        size_hint_y: 0.33
"""


class RostRoot(BoxLayout):
    current_file = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_file = None

    def _storage(self):
        folder = Path(App.get_running_app().user_data_dir) / "projects"
        folder.mkdir(parents=True, exist_ok=True)
        return folder

    def new_file(self):
        self.current_file = None
        self.ids.editor.text = '# New RostLang program\nsay "Hello!"\n'
        self.ids.output.text = "New file created."

    def save_file(self):
        if self.current_file is None:
            self._choose_save_name()
            return
        self._write_current()

    def _choose_save_name(self):
        layout = BoxLayout(orientation="vertical", spacing="8dp", padding="8dp")
        name = TextInput(text="main.rost", multiline=False, size_hint_y=None, height="42dp")
        layout.add_widget(Label(text="File name (.rost):", size_hint_y=None, height="28dp"))
        layout.add_widget(name)
        buttons = BoxLayout(size_hint_y=None, height="42dp", spacing="8dp")
        popup = Popup(title="Save RostLang file", content=layout, size_hint=(0.88, 0.35))
        cancel = Button(text="Cancel")
        save = Button(text="Save")
        buttons.add_widget(cancel)
        buttons.add_widget(save)
        layout.add_widget(buttons)
        cancel.bind(on_release=popup.dismiss)
        save.bind(on_release=lambda *_: self._finish_save(name.text, popup))
        popup.open()

    def _finish_save(self, name, popup):
        safe_name = Path(name.strip()).name
        if not safe_name:
            self.ids.output.text = "Please enter a file name."
            return
        if not safe_name.endswith(".rost"):
            safe_name += ".rost"
        self.current_file = self._storage() / safe_name
        popup.dismiss()
        self._write_current()

    def _write_current(self):
        try:
            self.current_file.write_text(self.ids.editor.text, encoding="utf-8")
            self.ids.output.text = "Saved: " + self.current_file.name
        except Exception as exc:
            self.ids.output.text = "Save error: " + str(exc)

    def open_file(self):
        files = sorted(self._storage().glob("*.rost"))
        layout = BoxLayout(orientation="vertical", spacing="6dp", padding="8dp")
        popup = Popup(title="Open RostLang file", content=layout, size_hint=(0.88, 0.75))
        if not files:
            layout.add_widget(Label(text="No .rost files saved yet."))
        for path in files:
            button = Button(text=path.name, size_hint_y=None, height="44dp")
            button.bind(on_release=lambda _btn, p=path: self._load_file(p, popup))
            layout.add_widget(button)
        close = Button(text="Close", size_hint_y=None, height="42dp")
        close.bind(on_release=popup.dismiss)
        layout.add_widget(close)
        popup.open()

    def _load_file(self, path, popup):
        try:
            self.ids.editor.text = path.read_text(encoding="utf-8")
            self.current_file = path
            self.ids.output.text = "Opened: " + path.name
            popup.dismiss()
        except Exception as exc:
            self.ids.output.text = "Open error: " + str(exc)

    def run_code(self):
        source = self.ids.editor.text
        if self.current_file is None:
            self.ids.output.text = "Save this program first, then press Run."
            return
        self.ids.output.text = "Running…"
        threading.Thread(target=self._execute, args=(source, self.current_file), daemon=True).start()

    def _execute(self, source, filename):
        output = io.StringIO()
        try:
            old_cwd = Path.cwd()
            os.chdir(filename.parent)
            try:
                with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
                    RostInterpreter().run(source, str(filename))
            finally:
                os.chdir(old_cwd)
        except Exception as exc:
            output.write(f"RostLang error: {exc}\n")
        result = output.getvalue() or "Program finished. (No output)"
        Clock.schedule_once(lambda _dt: setattr(self.ids.output, "text", result), 0)


class RostLangAndroidApp(App):
    app_version = __version__

    def build(self):
        Builder.load_string(KV)
        return RostRoot()


if __name__ == "__main__":
    RostLangAndroidApp().run()
