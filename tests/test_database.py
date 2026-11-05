import contextlib
import io
import unittest

from rostlang.interpreter import RostInterpreter


class DatabaseLibraryTests(unittest.TestCase):
    def run_rost(self, source):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            RostInterpreter().run(source, "main.rost")
        return output.getvalue()

    def test_crud_and_helpers(self):
        output = self.run_rost("""
use "libraries/database.rost"
make db = DBOpen(":memory:")
DBCreateTable(db, "students", {"id": "INTEGER PRIMARY KEY AUTOINCREMENT", "name": "TEXT NOT NULL", "age": "INTEGER"})
make first = DBInsert(db, "students", {"name": "Ada", "age": 14})
make second = DBInsert(db, "students", {"name": "Linus", "age": 16})
say first
say DBCount(db, "students")
say DBSelect(db, "students", ["name", "age"], "age > ?", [14])
say DBUpdate(db, "students", {"age": 17}, "name = ?", ["Ada"])
say DBSelect(db, "students", ["name", "age"], "name = ?", ["Ada"])
say DBDelete(db, "students", "name = ?", ["Linus"])
say DBTables(db)
say DBCount(db, "students")
DBCommit(db)
DBClose(db)
""")
        self.assertIn("1", output)
        self.assertIn("2", output)
        self.assertIn("Linus", output)
        self.assertIn("Ada", output)
        self.assertIn("students", output)

    def test_delete_requires_where(self):
        with self.assertRaises(Exception):
            self.run_rost("""
make db = DBOpen(":memory:")
DBCreateTable(db, "items", {"name": "TEXT"})
DBDelete(db, "items", "", [])
""")

    def test_identifier_validation(self):
        with self.assertRaises(Exception):
            self.run_rost("""
make db = DBOpen(":memory:")
DBCreateTable(db, "items; DROP TABLE users", {"name": "TEXT"})
""")

    def test_closed_connection_is_rejected(self):
        with self.assertRaises(Exception):
            self.run_rost("""
make db = DBOpen(":memory:")
DBClose(db)
DBCount(db, "items")
""")


if __name__ == "__main__":
    unittest.main()
