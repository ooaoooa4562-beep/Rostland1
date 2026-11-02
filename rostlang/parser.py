"""Block parser for RostLang 0.5 hybrid syntax."""
import re
from .lexer import Lexer
from .errors import RostLangError


class Parser:
    def __init__(self, source, filename="<memory>"):
        self.source = source
        self.filename = filename
        self.lines = source.splitlines()
        self.index = 0

    def parse(self):
        try:
            Lexer(self.source, self.filename).tokenize()
        except SyntaxError as exc:
            raise RostLangError(str(exc)) from exc
        return self.parse_block(top=True)

    def error(self, message, line):
        raise RostLangError(f"{self.filename}:{line}: {message}")

    def parse_block(self, top=False):
        result = []
        while self.index < len(self.lines):
            number = self.index + 1
            line = self.lines[self.index].strip()
            self.index += 1
            if not line or line.startswith("#"):
                continue
            if line in ("} otherwise {", "} else {"):
                if top: self.error("Unexpected '}'", number)
                self.lines.insert(self.index, "else {")
                return result
            if line == "}":
                if top: self.error("Unexpected '}'", number)
                return result
            if line.startswith(("when ", "if ")) and line.endswith("{"):
                condition = line.split(" ", 1)[1][:-1].strip()
                yes = self.parse_block()
                no = []
                if self.index < len(self.lines) and self.lines[self.index].strip() in ("otherwise {", "else {"):
                    self.index += 1
                    no = self.parse_block()
                result.append(("when", condition, yes, no, number))
                continue
            if line.startswith(("repeat ", "while ")) and line.endswith("{"):
                keyword = "repeat" if line.startswith("repeat ") else "while"
                result.append((keyword, line[len(keyword):-1].strip(), self.parse_block(), number))
                continue
            if line.startswith("for ") and line.endswith("{"):
                match = re.fullmatch(r"for\s+([A-Za-z_]\w*)\s+in\s+(.+)\s*\{", line)
                if not match: self.error("Use: for item in collection {", number)
                variable, expression = match.groups()
                result.append(("for", variable, expression.strip(), self.parse_block(), number))
                continue
            if line == "try {":
                body = self.parse_block()
                handler = []
                error_name = "error"
                if self.index < len(self.lines) and re.fullmatch(r"except(?:\s+[A-Za-z_]\w*)?\s*\{", self.lines[self.index].strip()):
                    header = self.lines[self.index].strip()
                    self.index += 1
                    match = re.fullmatch(r"except(?:\s+([A-Za-z_]\w*))?\s*\{", header)
                    error_name = match.group(1) or "error"
                    handler = self.parse_block()
                result.append(("try", body, error_name, handler, number))
                continue
            if line.startswith("class ") and line.endswith("{"):
                match = re.fullmatch(r"class\s+([A-Za-z_]\w*)\s*\{", line)
                if not match: self.error("Use: class Name {", number)
                result.append(("class", match.group(1), self.parse_block(), number))
                continue
            if (line.startswith("action ") or line.startswith("def ")) and line.endswith("{"):
                match = re.fullmatch(r"(?:action|def)\s+([A-Za-z_]\w*)\s*\((.*?)\)\s*\{", line)
                if not match: self.error("Use: def name(parameter1, parameter2) {", number)
                name, raw = match.groups()
                params = [p.strip() for p in raw.split(",") if p.strip()]
                if any(not re.fullmatch(r"[A-Za-z_]\w*", p) for p in params) or len(params) != len(set(params)):
                    self.error("Invalid or duplicate function parameter", number)
                result.append(("action", name, params, self.parse_block(), number))
                continue
            if line.startswith(("otherwise", "else", "except")):
                self.error("Unexpected block clause", number)
            result.append(("line", line, number))
        if not top:
            self.error("Missing closing '}'", len(self.lines) or 1)
        return result
