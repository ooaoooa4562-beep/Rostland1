# Changelog

## 0.7.0-alpha
- Added Lua-style `Local name = value` declarations with nested block and function scopes
- Added `Module("name")` as a function-style module import command
- Added `Time()` / `time_now()` for the current local date and time
- Added `Period name = 5s` duration declarations (ms, s, m, h, d)
- Added `write_html` and `write_css` helpers for HTML/CSS source files
- Expanded `build_site` to copy complete website folders and preserve assets
- Added tests for the new language features


## 0.6.0-alpha
- Added `build_site(html_path, css_path, output_dir)` to package HTML/CSS into a publishable static site folder
- Added a responsive sample website in `examples/web/` and a `.rost` build script
- Allowed standalone built-in function calls as expression statements
- Added a test for website output and fixed the file-helper test path
- Documented the current limits: browser-side RostLang events and server features are not implemented yet

## 0.5.0-alpha
- Added `for item in iterable { }` loops
- Added `try { } except name { }` error handling
- Added basic classes, instance attributes, `__init__` and methods
- Added UTF-8 text file helpers: `read_text`, `write_text`, `exists`, `list_dir`
- Added tests for classes, loops, exceptions and file APIs
- Updated version and documentation

## 0.4.0-alpha
- Added an initial tokenizer in `rostlang/lexer.py`
- Added a separate brace-block parser in `rostlang/parser.py`
- Added hybrid syntax: `let`, `print`, `if/else`, `def` and ordinary assignment
- Added common conversion, input and range built-ins
- Routed module loading through the new parser
- Added tests for hybrid syntax and lexer errors

## 0.3.0-alpha
- Added relative .rost module imports with the use command
- Modules are loaded once and share variables and actions
- Fixed action declaration parsing
- Added module import tests

## 0.2.0-alpha
- Added when / otherwise conditions
- Added repeat and while loops
- Added stop and skip loop controls
- Added action functions and return values
- Added lists, tuples, dictionaries and indexing
- Added comparisons, boolean values and built-in helpers

## 0.1.0-alpha
- Initial interpreter with say, make, change and ask
- Arithmetic expressions and string concatenation
