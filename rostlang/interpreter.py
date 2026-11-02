import ast
import math
import operator
import random
import re
from pathlib import Path

from .errors import RostLangError
from .parser import Parser


class RostObject:
    def __init__(self, class_name):
        self.class_name = class_name
        self.attributes = {}


class ReturnSignal(Exception):
    def __init__(self, value):
        self.value = value


class BreakSignal(Exception):
    pass


class ContinueSignal(Exception):
    pass


class RostInterpreter:
    """RostLang 0.2 alpha interpreter. Evaluates a restricted expression AST."""

    BIN = {
        ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
        ast.Div: operator.truediv, ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod, ast.Pow: operator.pow,
    }
    UNARY = {ast.UAdd: operator.pos, ast.USub: operator.neg, ast.Not: operator.not_}
    CMP = {
        ast.Eq: operator.eq, ast.NotEq: operator.ne, ast.Lt: operator.lt,
        ast.LtE: operator.le, ast.Gt: operator.gt, ast.GtE: operator.ge,
        ast.In: lambda a, b: a in b, ast.NotIn: lambda a, b: a not in b,
    }
    NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

    def __init__(self):
        self.variables = {}
        self.functions = {}
        self.classes = {}
        self.depth = 0
        self.loaded_modules = set()
        self.loading_modules = set()
        self.builtins = {
            "random": lambda: random.random(),
            "random_int": lambda a, b: random.randint(int(a), int(b)),
            "length": len, "text": str, "number": self.to_number,
            "abs": abs, "min": min, "max": max, "sum": sum,
            "round": round, "floor": math.floor, "ceil": math.ceil,
            "sqrt": math.sqrt, "append": self.append, "pop": self.pop,
            "str": str, "int": int, "float": float, "bool": bool,
            "input": input, "range": range,
            "read_text": self.read_text, "write_text": self.write_text,
            "exists": lambda path: Path(str(path)).exists(),
            "list_dir": lambda path=".": [p.name for p in Path(str(path)).iterdir()],
        }

    def run(self, source, filename="<memory>"):
        self.filename = filename
        self.loaded_modules = set()
        self.loading_modules = set()
        program = Parser(source, filename).parse()
        self.execute(program)

    def error(self, message, line=None):
        line = line if line is not None else getattr(self, "line", "?")
        raise RostLangError(f"{self.filename}:{line}: {message}")

    def parse_block(self, top=False):
        result = []
        while self.index < len(self.lines):
            number = self.index + 1
            line = self.lines[self.index].strip()
            self.index += 1
            if not line or line.startswith("#"):
                continue
            if line == "} otherwise {":
                if top:
                    self.error("Unexpected '}'", number)
                # Accept the compact form: } otherwise { on one line.
                self.lines.insert(self.index, "otherwise {")
                return result
            if line == "}":
                if top:
                    self.error("Unexpected '}'", number)
                return result

            if line.startswith("when ") and line.endswith("{"):
                condition = line[5:-1].strip()
                yes = self.parse_block()
                no = []
                if self.index < len(self.lines) and self.lines[self.index].strip() == "otherwise {":
                    self.index += 1
                    no = self.parse_block()
                result.append(("when", condition, yes, no, number))
                continue

            if line.startswith("repeat ") and line.endswith("{"):
                result.append(("repeat", line[7:-1].strip(), self.parse_block(), number))
                continue

            if line.startswith("while ") and line.endswith("{"):
                result.append(("while", line[6:-1].strip(), self.parse_block(), number))
                continue

            if line.startswith("action ") and line.endswith("{"):
                match = re.fullmatch(r"action\s+([A-Za-z_]\w*)\s*\((.*?)\)\s*\{", line)
                if not match:
                    self.error("Use: action name(parameter1, parameter2) {", number)
                name, raw = match.groups()
                params = [p.strip() for p in raw.split(",") if p.strip()]
                if any(not self.NAME.fullmatch(p) for p in params) or len(params) != len(set(params)):
                    self.error("Invalid or duplicate function parameter", number)
                result.append(("action", name, params, self.parse_block(), number))
                continue

            if line.startswith("otherwise"):
                self.error("'otherwise' must follow a 'when' block", number)
            result.append(("line", line, number))

        if not top:
            self.error("Missing closing '}'", len(self.lines) or 1)
        return result

    def execute(self, statements):
        for item in statements:
            kind = item[0]
            if kind == "when":
                _, expr, yes, no, line = item
                self.line = line
                self.execute(yes if self.truth(self.evaluate(expr)) else no)
            elif kind in ("repeat", "while"):
                _, expr, body, line = item
                self.line = line
                if kind == "repeat":
                    count = self.evaluate(expr)
                    if isinstance(count, bool) or not isinstance(count, int) or not 0 <= count <= 100000:
                        self.error("repeat expects an integer from 0 to 100000")
                    iterator = range(count)
                else:
                    iterator = None
                loops = 0
                while True:
                    if kind == "repeat":
                        if loops >= len(iterator):
                            break
                    elif not self.truth(self.evaluate(expr)):
                        break
                    loops += 1
                    if loops > 100000:
                        self.error("Loop exceeded 100000 iterations")
                    try:
                        self.execute(body)
                    except ContinueSignal:
                        continue
                    except BreakSignal:
                        break
            elif kind == "action":
                _, name, params, body, line = item
                self.line = line
                if name in self.functions or name in self.builtins:
                    self.error(f"Function '{name}' already exists")
                self.functions[name] = (params, body)
            elif kind == "for":
                _, name, expr, body, line = item
                self.line = line
                try:
                    values = list(self.evaluate(expr))
                except Exception as exc:
                    self.error(f"for expects an iterable: {exc}")
                if len(values) > 100000:
                    self.error("for loop limited to 100000 items")
                old_value = self.variables.get(name, _MISSING)
                try:
                    for value in values:
                        self.variables[name] = value
                        try:
                            self.execute(body)
                        except ContinueSignal:
                            continue
                        except BreakSignal:
                            break
                finally:
                    if old_value is _MISSING: self.variables.pop(name, None)
                    else: self.variables[name] = old_value
            elif kind == "try":
                _, body, error_name, handler, line = item
                self.line = line
                try:
                    self.execute(body)
                except (RostLangError, ArithmeticError, ValueError, TypeError, IndexError, KeyError) as exc:
                    if not handler: raise
                    old_value = self.variables.get(error_name, _MISSING)
                    self.variables[error_name] = str(exc)
                    try: self.execute(handler)
                    finally:
                        if old_value is _MISSING: self.variables.pop(error_name, None)
                        else: self.variables[error_name] = old_value
            elif kind == "class":
                _, name, body, line = item
                self.line = line
                if name in self.classes or name in self.variables or name in self.functions:
                    self.error(f"Name '{name}' already exists")
                methods = {}
                for statement in body:
                    if statement[0] != "action":
                        self.error("Class bodies currently support methods only")
                    _, method_name, params, method_body, method_line = statement
                    methods[method_name] = (params, method_body)
                    self.functions[name + "." + method_name] = (params, method_body)
                self.classes[name] = methods
            else:
                _, line_text, line = item
                self.line = line
                self.execute_line(line_text)

    def execute_line(self, line):
        if line.startswith("say "):
            print(self.stringify(self.evaluate(line[4:].strip())))
        elif line.startswith("print(") and line.endswith(")"):
            value = self.evaluate(line[6:-1].strip())
            print(self.stringify(value))
        elif line.startswith("print "):
            print(self.stringify(self.evaluate(line[6:].strip())))
        elif line.startswith(("make ", "let ")):
            self.assign(line.split(" ", 1)[1].strip(), True)
        elif line.startswith("change "):
            self.assign(line[7:].strip(), False)
        elif line.startswith("ask "):
            self.ask(line[4:].strip())
        elif line == "stop":
            raise BreakSignal()
        elif line == "skip":
            raise ContinueSignal()
        elif line == "return":
            raise ReturnSignal(None)
        elif line.startswith("return "):
            raise ReturnSignal(self.evaluate(line[7:].strip()))
        elif line.startswith("call "):
            self.evaluate(line[5:].strip())
        elif line.startswith("use "):
            self.load_module(line[4:].strip())
        elif re.match(r"^[A-Za-z_]\w*\s*=", line):
            name = line.split("=", 1)[0].strip()
            self.assign(line, name not in self.variables)
        else:
            self.error(f"Unknown command: {line.split()[0]}")

    def load_module(self, expression):
        try:
            module_name = ast.literal_eval(expression)
        except (ValueError, SyntaxError):
            self.error('use expects a quoted .rost path')
        if not isinstance(module_name, str) or not module_name.endswith('.rost'):
            self.error('use expects a quoted .rost path')
        base = Path(self.filename).parent if self.filename != '<memory>' else Path.cwd()
        module_path = (base / module_name).resolve()
        if module_path in self.loaded_modules:
            return
        if module_path in self.loading_modules:
            self.error('Circular module import: ' + module_name)
        if not module_path.is_file():
            self.error('Module not found: ' + module_name)
        self.loading_modules.add(module_path)
        previous_filename = self.filename
        try:
            self.filename = str(module_path)
            source = module_path.read_text(encoding='utf-8')
            self.execute(Parser(source, str(module_path)).parse())
            self.loaded_modules.add(module_path)
        finally:
            self.filename = previous_filename
            self.loading_modules.discard(module_path)

    def assign(self, text, create):
        if "=" not in text:
            self.error("Expected '=' in assignment")
        name, expr = text.split("=", 1)
        name, expr = name.strip(), expr.strip()
        if not self.NAME.fullmatch(name) or not expr:
            self.error("Invalid variable assignment")
        if create and name in self.variables:
            self.error(f"'{name}' already exists; use change")
        if not create and name not in self.variables:
            self.error(f"'{name}' does not exist; use make")
        self.variables[name] = self.evaluate(expr)

    def ask(self, text):
        if "=" not in text:
            self.error('Use: ask name = "Prompt"')
        name, expr = text.split("=", 1)
        name, expr = name.strip(), expr.strip()
        if not self.NAME.fullmatch(name) or name in self.variables:
            self.error("Invalid or existing input variable")
        self.variables[name] = input(self.stringify(self.evaluate(expr)))

    def evaluate(self, expr):
        try:
            return self.node(ast.parse(expr, mode="eval").body)
        except RostLangError:
            raise
        except Exception as exc:
            self.error(f"Expression error: {exc}")

    def node(self, n):
        if isinstance(n, ast.Constant) and isinstance(n.value, (str, int, float, bool, type(None))):
            return n.value
        if isinstance(n, ast.Name):
            if n.id in self.variables:
                return self.variables[n.id]
            if n.id == "true": return True
            if n.id == "false": return False
            if n.id == "nothing": return None
            self.error(f"Unknown variable: {n.id}")
        if isinstance(n, ast.List):
            return [self.node(x) for x in n.elts]
        if isinstance(n, ast.Tuple):
            return tuple(self.node(x) for x in n.elts)
        if isinstance(n, ast.Dict):
            return {self.node(k): self.node(v) for k, v in zip(n.keys, n.values)}
        if isinstance(n, ast.BinOp) and type(n.op) in self.BIN:
            return self.BIN[type(n.op)](self.node(n.left), self.node(n.right))
        if isinstance(n, ast.UnaryOp) and type(n.op) in self.UNARY:
            return self.UNARY[type(n.op)](self.node(n.operand))
        if isinstance(n, ast.BoolOp):
            values = [self.node(x) for x in n.values]
            return all(values) if isinstance(n.op, ast.And) else any(values)
        if isinstance(n, ast.Compare):
            left = self.node(n.left)
            for op, part in zip(n.ops, n.comparators):
                right = self.node(part)
                if type(op) not in self.CMP or not self.CMP[type(op)](left, right):
                    return False
                left = right
            return True
        if isinstance(n, ast.Subscript):
            return self.node(n.value)[self.node(n.slice)]
        if isinstance(n, ast.Attribute):
            obj = self.node(n.value)
            if isinstance(obj, RostObject):
                if n.attr in obj.attributes: return obj.attributes[n.attr]
                self.error(f"Unknown attribute: {n.attr}")
            self.error("Attribute access is supported only on RostLang objects")
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute):
            obj = self.node(n.func.value)
            args = [self.node(x) for x in n.args]
            if n.keywords: self.error("Named arguments are not supported yet")
            if not isinstance(obj, RostObject): self.error("Method call expects a RostLang object")
            key = obj.class_name + "." + n.func.attr
            if key not in self.functions: self.error(f"Unknown method: {n.func.attr}")
            return self.call_function(key, [obj] + args)
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name):
            name = n.func.id
            args = [self.node(x) for x in n.args]
            if n.keywords:
                self.error("Named arguments are not supported yet")
            if name in self.builtins:
                return self.builtins[name](*args)
            if name in self.classes:
                instance = RostObject(name)
                init = self.classes[name].get("__init__")
                if init:
                    self.call_function(name + ".__init__", [instance] + args)
                elif args:
                    self.error(f"{name}() takes no arguments")
                return instance
            if name in self.functions:
                return self.call_function(name, args)
            self.error(f"Unknown function: {name}")
        self.error(f"Unsupported expression: {type(n).__name__}")

    def call_function(self, name, args):
        params, body = self.functions[name]
        if len(params) != len(args):
            self.error(f"{name}() expects {len(params)} argument(s)")
        if self.depth >= 100:
            self.error("Maximum function call depth reached")
        old = {p: self.variables.get(p, _MISSING) for p in params}
        self.variables.update(dict(zip(params, args)))
        self.depth += 1
        try:
            self.execute(body)
        except ReturnSignal as result:
            return result.value
        finally:
            self.depth -= 1
            for p, value in old.items():
                if value is _MISSING: self.variables.pop(p, None)
                else: self.variables[p] = value
        return None

    @staticmethod
    def read_text(path):
        return Path(str(path)).read_text(encoding="utf-8")

    @staticmethod
    def write_text(path, content):
        Path(str(path)).write_text(str(content), encoding="utf-8")
        return True

    @staticmethod
    def to_number(value):
        try:
            return float(value) if "." in str(value) else int(value)
        except (ValueError, TypeError):
            raise RostLangError(f"Cannot convert {value!r} to a number")

    @staticmethod
    def append(items, value):
        if not isinstance(items, list):
            raise RostLangError("append() expects a list")
        items.append(value)
        return items

    @staticmethod
    def pop(items, index=-1):
        if not isinstance(items, list):
            raise RostLangError("pop() expects a list")
        return items.pop(int(index))

    @staticmethod
    def truth(value):
        return bool(value)

    @staticmethod
    def stringify(value):
        if value is True: return "true"
        if value is False: return "false"
        if value is None: return "nothing"
        return str(value)


_MISSING = object()
