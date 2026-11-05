import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from rostlang.interpreter import RostInterpreter


class RostLangTests(unittest.TestCase):
    def run_code(self, code, filename="<memory>"):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            runtime = RostInterpreter()
            runtime.run(code, filename)
        return output.getvalue().strip().splitlines()

    def test_math(self):
        self.assertEqual(self.run_code("make x = 6 * 7\nsay x"), ["42"])

    def test_when(self):
        self.assertEqual(self.run_code('when 5 > 2 {\n say "yes"\n} otherwise {\n say "no"\n}'), ["yes"])

    def test_repeat(self):
        self.assertEqual(self.run_code('repeat 2 {\n say "go"\n}'), ["go", "go"])

    def test_function(self):
        self.assertEqual(self.run_code("action add(a, b) {\n return a + b\n}\nsay add(4, 5)"), ["9"])

    def test_list(self):
        self.assertEqual(self.run_code('make xs = ["a"]\ncall append(xs, "b")\nsay xs[1]'), ["b"])

    def test_while(self):
        self.assertEqual(self.run_code('make i = 0\nwhile i < 3 {\n say i\n change i = i + 1\n}'), ["0", "1", "2"])

    def test_hybrid_python_style_syntax(self):
        code = '''let name = "RostLang"
score = 20
if score >= 10 {
    print("Welcome, " + name)
} else {
    print("Try again")
}
def double(value) {
    return value * 2
}
answer = double(score)
print(answer)'''
        self.assertEqual(self.run_code(code), ["Welcome, RostLang", "40"])

    def test_lexer_rejects_unexpected_character(self):
        from rostlang.errors import RostLangError
        with self.assertRaises(RostLangError):
            RostInterpreter().run("say @")

    def test_python_style_input_builtin(self):
        import builtins
        from unittest.mock import patch
        output = io.StringIO()
        with patch.object(builtins, "input", return_value="Rostik"):
            with contextlib.redirect_stdout(output):
                RostInterpreter().run('name = input("Name: ")\nprint(name)')
        self.assertEqual(output.getvalue().strip(), "Rostik")

    def test_for_loop(self):
        self.assertEqual(self.run_code("for item in [1, 2, 3] {\n print(item)\n}"), ["1", "2", "3"])

    def test_class_instance_and_method(self):
        code = '''class Player {
    def __init__(self, name) {
        self.name = name
    }
    def greet(self) {
        return "Hello " + self.name
    }
}
player = Player("Rostik")
print(player.greet())'''
        self.assertEqual(self.run_code(code), ["Hello Rostik"])

    def test_try_except(self):
        code = '''try {
    value = 10 / 0
}
except problem {
    print("Caught: " + problem)
}'''
        self.assertEqual(self.run_code(code), ["Caught: <memory>:2: Expression error: division by zero"])

    def test_file_helpers(self):
        with tempfile.TemporaryDirectory() as folder:
            path = str(Path(folder) / "note.txt")
            code = 'write_text("' + path + '", "hello")\nprint(read_text("' + path + '"))'
            self.assertEqual(self.run_code(code), ["hello"])

    def test_build_site(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "index.html").write_text(
                '<!doctype html><html><head><link rel="stylesheet" href="style.css"></head><body>Hello</body></html>',
                encoding="utf-8",
            )
            (root / "style.css").write_text("body { color: red; }", encoding="utf-8")
            output_dir = root / "dist"
            code = 'build_site("' + str(root / "index.html") + '", "' + str(root / "style.css") + '", "' + str(output_dir) + '")'
            self.run_code(code)
            self.assertEqual((output_dir / "index.html").read_text(encoding="utf-8").find("Hello") >= 0, True)
            self.assertEqual((output_dir / "style.css").read_text(encoding="utf-8"), "body { color: red; }")

    def test_module_import(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "tools.rost").write_text("action double(n) {\n return n * 2\n}\n", encoding="utf-8")
            main = root / "main.rost"
            source = 'use "tools.rost"\nsay double(21)'
            main.write_text(source, encoding="utf-8")
            self.assertEqual(self.run_code(source, str(main)), ["42"])

    def test_module_is_loaded_once(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "setup.rost").write_text("make loaded = 1\n", encoding="utf-8")
            main = root / "main.rost"
            source = 'use "setup.rost"\nuse "setup.rost"\nsay loaded'
            main.write_text(source, encoding="utf-8")
            self.assertEqual(self.run_code(source, str(main)), ["1"])


    def test_local_variables_follow_block_scope(self):
        code = '''Local outside = "global"
action demo() {
    Local inside = 7
    change inside = inside + 1
    return inside
}
print(demo())
print(outside)'''
        self.assertEqual(self.run_code(code), ["8", "global"])

    def test_local_inside_if_does_not_escape(self):
        from rostlang.errors import RostLangError
        code = '''if true {
    Local hidden = 12
}
print(hidden)'''
        with self.assertRaises(RostLangError):
            self.run_code(code)

    def test_period_and_time_commands(self):
        code = '''Period short_wait = 5s
Period long_wait = 2m
print(short_wait)
print(long_wait)
print(Time())'''
        output = self.run_code(code)
        self.assertEqual(output[:2], ["0:00:05", "0:02:00"])
        self.assertIn("T", output[2])

    def test_module_function_call(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "tools.rost").write_text(
                "action triple(n) {\n return n * 3\n}\n", encoding="utf-8"
            )
            main = root / "main.rost"
            source = 'Module("tools")\nprint(triple(14))'
            main.write_text(source, encoding="utf-8")
            self.assertEqual(self.run_code(source, str(main)), ["42"])

    def test_build_site_copies_complete_folder(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / "web"
            (source / "assets").mkdir(parents=True)
            (source / "index.html").write_text("<h1>Hello</h1>", encoding="utf-8")
            (source / "style.css").write_text("body { color: red; }", encoding="utf-8")
            (source / "assets" / "app.js").write_text("console.log('ok')", encoding="utf-8")
            destination = root / "dist"
            code = 'build_site("' + str(source) + '", "' + str(destination) + '")'
            self.run_code(code)
            self.assertTrue((destination / "index.html").is_file())
            self.assertTrue((destination / "assets" / "app.js").is_file())


if __name__ == "__main__":
    unittest.main()
