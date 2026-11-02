# RostLang 0.6.0 Alpha

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

RostLang 0.6 adds an initial HTML/CSS website build helper. Keep your site source files in a folder, then call `build_site` from a `.rost` script:

```rost
build_site("examples/web/index.html", "examples/web/style.css", "site")
say "Website built in ./site"
```

Run it from the repository root:

```bash
python main.py examples/build_website.rost
```

The helper copies the HTML to `site/index.html` and CSS to `site/style.css`. Your HTML should link to the stylesheet with `<link rel="stylesheet" href="style.css">`. Open `site/index.html` in a browser to preview it. The generated `site/` directory is a static website that can be published using a static host such as GitHub Pages.

**Current limitation:** this first web feature only packages HTML and CSS files. RostLang does not yet run inside the browser or handle browser click events, and this helper does not create a server or database. Browser interactivity is a future feature.

## Files

- `read_text(path)` — read UTF-8 text.
- `write_text(path, content)` — write UTF-8 text.
- `exists(path)` — check whether a path exists.
- `list_dir(path=".")` — list directory entries.

These APIs access the filesystem available to the running process. Only use paths you trust.

## Collections and modules

Lists, tuples, dictionaries, indexing and module imports are supported. Use `use "module.rost"` to import a relative `.rost` module. Modules load once per interpreter run.

## Built-ins

`random`, `random_int`, `length`, `text`, `number`, `abs`, `min`, `max`, `sum`, `round`, `floor`, `ceil`, `sqrt`, `append`, `pop`, `str`, `int`, `float`, `bool`, `input`, `range`, `read_text`, `write_text`, `exists`, `list_dir`.

## Architecture

- `rostlang/lexer.py` — tokenizes source characters.
- `rostlang/parser.py` — parses brace-delimited statements and blocks.
- `rostlang/interpreter.py` — evaluates expressions and executes programs.

## Important limitations

**0.5.0 is an alpha release, not yet a complete or production-ready language.** It now has a useful core for learning, but it is not Python-compatible and cannot run arbitrary Python packages. The parser is line-based; blocks require braces. Function scoping is basic. Inheritance, default/named arguments, decorators, generators, async/await, a package manager, networking, databases, GUI/game frameworks, and a native compiler remain future work.

The long-term plan is to grow RostLang into a general-purpose language for scripts, websites, applications and games, adding and testing each capability incrementally.
