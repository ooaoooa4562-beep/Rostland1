"""Tokenizer for RostLang source code.

The lexer is intentionally small in 0.4.0: it recognizes names, literals,
operators, punctuation, comments and line boundaries. Braces remain the
block delimiters in this release.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Token:
    kind: str
    value: str
    line: int
    column: int


class Lexer:
    OPERATORS = ("==", "!=", "<=", ">=", "//", "**", "+=", "-=", "*=", "/=")
    SINGLE = set("+-*/%=<>!()[]{}:,.")
    
    def __init__(self, source, filename="<memory>"):
        self.source = source
        self.filename = filename

    def tokenize(self):
        tokens = []
        for line_number, line in enumerate(self.source.splitlines(), 1):
            i = 0
            while i < len(line):
                char = line[i]
                if char in " \t\r":
                    i += 1
                    continue
                if char == "#":
                    break
                start = i
                if char in "'\"":
                    quote = char
                    i += 1
                    escaped = False
                    while i < len(line):
                        current = line[i]
                        if current == quote and not escaped:
                            i += 1
                            break
                        if current == "\\" and not escaped:
                            escaped = True
                        else:
                            escaped = False
                        i += 1
                    else:
                        raise SyntaxError(f"{self.filename}:{line_number}:{start + 1}: unterminated string")
                    tokens.append(Token("STRING", line[start:i], line_number, start + 1))
                    continue
                if char.isdigit():
                    i += 1
                    while i < len(line) and (line[i].isalnum() or line[i] in "._"):
                        i += 1
                    tokens.append(Token("NUMBER", line[start:i], line_number, start + 1))
                    continue
                if char.isalpha() or char == "_":
                    i += 1
                    while i < len(line) and (line[i].isalnum() or line[i] == "_"):
                        i += 1
                    tokens.append(Token("NAME", line[start:i], line_number, start + 1))
                    continue
                operator = next((op for op in self.OPERATORS if line.startswith(op, i)), None)
                if operator:
                    i += len(operator)
                    tokens.append(Token("OP", operator, line_number, start + 1))
                    continue
                if char in self.SINGLE:
                    i += 1
                    tokens.append(Token("PUNCT", char, line_number, start + 1))
                    continue
                raise SyntaxError(f"{self.filename}:{line_number}:{i + 1}: unexpected character {char!r}")
            tokens.append(Token("NEWLINE", "\\n", line_number, len(line) + 1))
        tokens.append(Token("EOF", "", len(self.source.splitlines()) + 1, 1))
        return tokens
