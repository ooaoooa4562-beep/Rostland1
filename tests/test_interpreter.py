import contextlib
import io
import unittest
from rostlang.interpreter import RostInterpreter


class RostLangTests(unittest.TestCase):
    def run_code(self, code):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            runtime = RostInterpreter()
            runtime.run(code)
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


if __name__ == "__main__":
    unittest.main()
