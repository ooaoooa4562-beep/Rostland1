# RostLang 0.7.0 Alpha

RostLang is an experimental general-purpose language with a hybrid syntax. It combines original commands such as `say` and `make` with selected Python-like syntax. The interpreter is implemented in Python and source files use `.rost`.

## Run

Requires Python 3.10+ and no third-party packages.

```bash
python main.py examples/hello.rost
python main.py examples/v05_demo.rost
python main.py examples/build_website.rost
python main.py --version
python -m unittest discover -s tests -v
```

## Variables and output

```rost
let name = "Rostik"
score = 10
print("Hello, " + name)
change score = score + 1
say score
```

## Conditions and loops

```rost
if score > 5 {
    print("High score")
} else {
    print("Keep trying")
}

for item in ["red", "green", "blue"] {
    print(item)
}

while score < 15 {
    score = score + 1
}
```

The legacy `when/otherwise`, `repeat`, `stop` and `skip` forms remain supported.

## Functions

```rost
def double(value) {
    return value * 2
}
print(double(21))
```

## Classes and objects

```rost
class Player {
    def __init__(self, name) {
        self.name = name
    }

    def greet(self) {
        return "Hello, " + self.name
    }
}
player = Player("Rostik")
print(player.greet())
```

Classes support instance attributes, methods and `__init__`. Inheritance, class attributes, properties and special-method protocols are not implemented yet.

## Error handling

```rost
try {
    value = 10 / 0
} except problem {
    print("The operation failed")
}
```

The current handler catches RostLang errors and common arithmetic, conversion, indexing and key errors.

## Build a static website

RostLang 0.7 can write HTML/CSS source files and package a complete static website folder, including JavaScript and image assets:

```rost
build_site("examples/web", "site")
say "Website built in ./site"
```

Run it from the repository root:

```bash
python main.py examples/build_website.rost
```

When the first argument is a folder, `build_site(source_folder, output_folder)` copies the entire website tree, preserving pages, CSS, JavaScript, images and other assets. The older three-argument form `build_site(html_file, css_file, output_folder)` remains available. Open the output `index.html` in a browser or publish the folder with a static host such as GitHub Pages. RostLang packages standard HTML/CSS/JS files; it does not execute browser JavaScript or provide a browser runtime, backend server or database.

## Files

- `read_text(path)` — read UTF-8 text.
- `write_text(path, content)` — write UTF-8 text.
- `write_html(path, content)` — write an HTML source file.
- `write_css(path, content)` — write a CSS source file.
- `build_site(source_folder, output_folder)` — copy a complete static website and its assets.
- `exists(path)` — check whether a path exists.
- `list_dir(path=".")` — list directory entries.

These APIs access the filesystem available to the running process. Only use paths you trust.

## Database library (SQLite)

Load the standard database module in a `.rost` program:

```rost
use "libraries/database.rost"

make db = DBOpen("school.db")
DBCreateTable(db, "students", {"id": "INTEGER PRIMARY KEY AUTOINCREMENT", "name": "TEXT NOT NULL", "age": "INTEGER"})

DBInsert(db, "students", {"name": "Alex", "age": 14})
say DBSelect(db, "students")
say DBCount(db, "students")

# Use placeholders for values instead of concatenating user input into SQL.
say DBSelect(db, "students", ["name", "age"], "age > ?", [12])

DBUpdate(db, "students", {"age": 15}, "name = ?", ["Alex"])
DBDelete(db, "students", "name = ?", ["Alex"])
DBCommit(db)
DBClose(db)
```

Available functions:

- `DBOpen(path)` — open or create an SQLite database; returns a connection handle.
- `DBClose(db)` — close a connection.
- `DBCreateTable(db, table, columns)` — create a table from a dictionary of column names and supported declarations.
- `DBInsert(db, table, values)` — insert a dictionary of values; returns the new row ID.
- `DBSelect(db, table, columns, where, params)` — return rows as a list of dictionaries. `columns`, `where`, and `params` are optional.
- `DBUpdate(db, table, values, where, params)` — update matching rows and return the affected row count.
- `DBDelete(db, table, where, params)` — delete matching rows and return the affected row count.
- `DBCount(db, table, where, params)` — count rows, optionally matching a condition.
- `DBTables(db)` — list user-created tables.
- `DBCommit(db)` — save the current transaction.

Supported column declarations include `INTEGER`, `REAL`, `TEXT`, `BLOB`, `INTEGER PRIMARY KEY AUTOINCREMENT`, and selected `NOT NULL` / `UNIQUE` forms. Table and column names are validated. Data values use SQLite placeholders (`?`) and separate parameter lists. For safety, `DBUpdate` and `DBDelete` require a non-empty `WHERE` condition. Only put SQL expressions in `where` that are authored by your program; pass external values through `params`.

The native interpreter stores database files on the host filesystem. The browser Playground uses Pyodide's virtual filesystem, so its database files are temporary and may disappear when the page/runtime is reset. Browser SQLite availability is dependent on the Pyodide runtime.

Run the database tests with:

```bash
python -m unittest tests.test_database -v
```

## Local variables

`Local` creates a variable in the current scope. It is visible inside that block and nested blocks, but not after the scope ends. Function parameters are also local.

```rost
Local site_name = "RostLang"

action greet() {
    Local message = "Hello " + site_name
    say message
}

greet()
```

## Modules

Use either the original `use` command or the function-style `Module()` command. A `.rost` extension is optional in `Module()`. Modules load once per run and share the interpreter's global functions and variables.

```rost
Module("math_tools")
# same as: use "math_tools.rost"
```

## Time and periods

`Time()` returns the current local date and time with its timezone. `Period` creates a duration value:

```rost
make started_at = Time()
Period pause = 5s
Period cache_lifetime = 15m
Period lesson = 1.5h
Period deadline = 2d
say started_at
say pause
```

Supported duration units: `ms`, `s`, `m`, `h`, `d`.


## Built-ins

`Time`, `time_now`, `Module`, `write_html`, `write_css`, `build_site`, `random`, `random_int`, `length`, `text`, `number`, `abs`, `min`, `max`, `sum`, `round`, `floor`, `ceil`, `sqrt`, `append`, `pop`, `str`, `int`, `float`, `bool`, `input`, `range`, `read_text`, `write_text`, `exists`, `list_dir`.

## Architecture

- `rostlang/lexer.py` — tokenizes source characters.
- `rostlang/parser.py` — parses brace-delimited statements and blocks.
- `rostlang/interpreter.py` — evaluates expressions and executes programs.

## Important limitations

**0.7.0 is an alpha release, not yet a complete or production-ready language.** It now has a useful core for learning, but it is not Python-compatible and cannot run arbitrary Python packages. The parser is line-based; blocks require braces. Local variables use block scopes; imported modules still share globals and do not yet have isolated namespaces or explicit exports. Inheritance, default/named arguments, decorators, generators, async/await, a package manager, networking, databases, GUI/game frameworks, and a native compiler remain future work.

The long-term plan is to grow RostLang into a general-purpose language for scripts, websites, applications and games, adding and testing each capability incrementally.

## Desktop launcher

RostLang includes an early desktop launcher built with Python and PySide6.

Install its dependency and start the app from the repository root:

```bash
python -m pip install -r launcher/requirements.txt
python launcher/main.py
```

See [launcher/README.md](launcher/README.md) for details. The launcher can create projects, edit and save `.rost` files, run them with this repository's interpreter, display output and send input to running programs.

