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
                RostInterpreter().run('name = input("Name: ")\\nprint(name)')
        self.assertEqual(output.getvalue().strip(), "Rostik")

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


if __name__ == "__main__":
    unittest.main()
