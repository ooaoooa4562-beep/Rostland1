# Changelog

## 0.4.0-alpha
- Added an initial tokenizer in `rostlang/lexer.py`
- Added a separate brace-block parser in `rostlang/parser.py`
- Added hybrid syntax: `let`, `print`, `if/else`, `def` and ordinary assignment
- Added common conversion, input and range built-ins
- Routed module loading through the new parser
- Added tests for hybrid syntax and lexer errors
- Updated project documentation and version

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
- Added sample programs and unit tests

## 0.1.0-alpha
- Initial interpreter with say, make, change and ask
- Arithmetic expressions and string concatenation
