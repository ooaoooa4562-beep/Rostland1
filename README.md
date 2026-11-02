# RostLang 0.3.0 Alpha

RostLang is an experimental general-purpose programming language with original command-style syntax. Its first interpreter is written in Python. Source files use the `.rost` extension.

## Requirements
- Python 3.10+
- No third-party packages

## Run
```bash
python main.py examples/hello.rost
python main.py examples/features.rost
python main.py examples/guess_number.rost
python main.py --version
```

## Language guide

### Modules
Use another `.rost` file relative to the current program. A module is loaded only once and shares the interpreter's variables and actions.
```text
use "math_tools.rost"
say double(21)
```

### Output, variables and input
```text
say "Hello!"
make name = "Rostik"
make points = 10
change points = points + 5
ask nickname = "Your nickname: "
say nickname
```

### Conditions
```text
when points >= 10 {
    say "Level up!"
} otherwise {
    say "Keep trying!"
}
```
Comparisons: == != < <= > >= in not in. Logic: and, or, not. Values: true, false, nothing.

### Loops
```text
repeat 3 {
    say "Again"
}
make i = 0
while i < 3 {
    say i
    change i = i + 1
}
``
Use `stop` to exit a loop and `skip` to continue with its next iteration.

### Functions
```text
action add(a, b) {
    return a + b
}
make total = add(10, 20)
say total
``
Use `call function_name(args)` when calling a function as a statement.

### Collections
Lists and dictionaries are supported in expressions:
```text
make items = ["map", "key"]
call append(items, "compass")
say items[0]
make profile = {"name": "Rostik", "level": 4}
say profile["name"]
``

### Built-ins
- `random()`, `random_int(min, max)`
- `length(value)`, `text(value)`, `number(value)`
- `abs`, `min`, `max`, `sum`, `round`
- `floor`, `ceil`, `sqrt`
- `append(list, value)`, `pop(list[, index])`

Comments are full lines beginning with `#`.

## Tests
```bash
python -m unittest discover -s tests -v
```

## Project structure
```text
Rostland1/
├── main.py
├── rostlang/
├── examples/
└── tests/
```

## Alpha limitations
This is an early interpreter. Blocks use braces and statements are line-based. Function arguments are positional. There is not yet a package manager, class system, async runtime, general file API or native compiler. Module files can be loaded with `use`. Expressions are parsed with Python's AST but only a restricted set of nodes is evaluated; arbitrary Python code is not executed.

## Roadmap
- [x] Variables, input, output and arithmetic
- [x] Conditions and loops
- [x] Functions and return
- [x] Lists and dictionaries
- [x] Random and math helpers
- [x] Unit tests and sample programs
- [ ] Dedicated lexer and parser
- [ ] Modules and package manager
- [ ] Classes and object-oriented features
- [ ] File APIs, debugger and editor support
- [ ] Bytecode compiler
