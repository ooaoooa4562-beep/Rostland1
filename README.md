# RostLang 0.4.0 Alpha

RostLang is an experimental general-purpose programming language with a hybrid syntax: familiar Python-style statements combined with RostLang commands. The interpreter is written in Python. Source files use the `.rost` extension.

## Requirements

- Python 3.10+
- No third-party packages

## Run

```bash
python main.py examples/hello.rost
python main.py examples/features.rost
python main.py --version
python -m unittest discover -s tests -v
```

## Hybrid syntax

Both RostLang commands and selected Python-style forms are supported.

### Variables and output

```rost
make name = "Rostik"
say name

let score = 100
print(score)

score = score + 25
print("New score: " + str(score))
```

- `make` and `let` create variables.
- `change name = value` updates an existing variable.
- `name = value` creates or updates a variable.
- `say expression` and `print(expression)` output values.

### Conditions

```rost
if score >= 100 {
    print("Level up!")
} else {
    say "Keep going!"
}
```

The original `when ... { } otherwise { }` syntax remains supported.

### Loops

```rost
repeat 3 {
    print("Again")
}

let index = 0
while index < 3 {
    print(index)
    index = index + 1
}
```

Use `stop` to exit a loop and `skip` to continue with its next iteration.

### Functions

```rost
def double(value) {
    return value * 2
}

print(double(21))
```

The original `action name(args) { }` syntax remains supported.

### Collections and modules

```rost
let items = ["map", "key"]
call append(items, "compass")
print(items[0])

use "math_tools.rost"
print(double(21))
```

Lists, tuples, dictionaries and indexing are supported. Modules are loaded once, relative to the importing file.

## Built-ins

Current built-ins include `random`, `random_int`, `length`, `text`, `number`, `abs`, `min`, `max`, `sum`, `round`, `floor`, `ceil`, `sqrt`, `append`, `pop`, `str`, `int`, `float`, `bool`, `input` and `range`.

## 0.4.0 architecture

- `rostlang/lexer.py` tokenizes names, literals, operators, punctuation, comments and line boundaries.
- `rostlang/parser.py` parses brace-delimited blocks and builds the interpreter's statement representation.
- `rostlang/interpreter.py` evaluates expressions and executes statements.

This is an incremental parser foundation, not yet a complete Python grammar. Blocks use braces, statements are line-based, and expressions are currently parsed through a restricted Python AST evaluator.

## Current limitations

RostLang is still experimental. It does not yet provide classes, inheritance, decorators, generators, async/await, a package manager, a general file API, networking APIs, GUI/game frameworks or a native compiler. The lexer and parser are an early foundation; the language does not execute arbitrary Python code or automatically support Python packages.

## Roadmap

- [x] Variables, output, input and expressions
- [x] Conditions, loops and functions
- [x] Collections and module imports
- [x] Initial lexer and block parser
- [x] Hybrid Python-style statements
- [ ] Full expression parser and indentation-based blocks
- [ ] Local scopes, keyword/default arguments and classes
- [ ] File APIs, exceptions and package manager
- [ ] Networking, databases and application libraries
- [ ] Graphics, GUI and game development libraries
- [ ] Bytecode compiler and stable 1.0 release
