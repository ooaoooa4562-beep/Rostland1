const DEFAULT_CODE = `make name = "RostLang"
say "Hello, " + name

make score = 10
change score = score + 5
say "Score: " + text(score)

when score > 10 {
    say "Great job!"
} otherwise {
    say "Keep learning!"
}`;

const EXAMPLES = {
  hello: `say "Hello, world!"
say "Welcome to RostLang Playground!"`,
  variables: `make name = "Rostik"
make age = 15
say "Name: " + name
say "Age: " + text(age)

change age = age + 1
say "Next year: " + text(age)`,
  conditions: `make score = 85

when score >= 90 {
    say "Excellent!"
} otherwise {
    when score >= 60 {
        say "Good job!"
    } otherwise {
        say "Keep practicing!"
    }
}`,
  loops: `repeat 5 {
    say "RostLang is running!"
}

make count = 1
while count <= 3 {
    say count
    change count = count + 1
}`,
  functions: `action greet(name) {
    say "Hello, " + name
}

greet("RostLang")`,
  lists: `make languages = ["RostLang", "Python", "Lua"]
say languages
say languages[0]
say "Count: " + text(length(languages))`
};

const statusEl = document.getElementById("runtime-status");
const outputEl = document.getElementById("output");
const runBtn = document.getElementById("run-btn");
const editor = CodeMirror.fromTextArea(document.getElementById("code-editor"), {
  mode: "python",
  theme: "dracula",
  lineNumbers: true,
  indentUnit: 4,
  tabSize: 4,
  lineWrapping: true,
  autofocus: true
});

editor.on("cursorActivity", () => {
  const p = editor.getCursor();
  document.getElementById("cursor-info").textContent = `Строка ${p.line + 1}, столбец ${p.ch + 1}`;
});

let pyodide = null;
let runtimePromise = null;

function setStatus(message, state = "") {
  statusEl.className = "status " + state;
  statusEl.querySelector("span").textContent = message;
}

function showOutput(text, isError = false) {
  outputEl.textContent = text || (isError ? "Произошла ошибка." : "Программа завершилась без вывода.");
  outputEl.style.color = isError ? "#ff9aa9" : "#b9f6d1";
}

async function loadRuntime() {
  if (pyodide) return pyodide;
  if (runtimePromise) return runtimePromise;
  runtimePromise = (async () => {
    setStatus("Загрузка Python runtime…");
    pyodide = await loadPyodide();
    setStatus("Загрузка интерпретатора RostLang…");
    const base = "https://raw.githubusercontent.com/ooaoooa4562-beep/Rostland1/main/rostlang/";
    const files = ["__init__.py", "errors.py", "lexer.py", "parser.py", "interpreter.py"];
    pyodide.FS.mkdirTree("/home/pyodide/rostlang");
    for (const file of files) {
      const response = await fetch(base + file);
      if (!response.ok) throw new Error("Не удалось загрузить " + file + " (" + response.status + ")");
      pyodide.FS.writeFile("/home/pyodide/rostlang/" + file, await response.text());
    }
    pyodide.runPython("import sys; sys.path.insert(0, '/home/pyodide')");
    pyodide.runPython("import builtins; from js import prompt; builtins.input = lambda message='': (prompt(message) or '')");
    setStatus("Готово к запуску", "ready");
    return pyodide;
  })().catch(error => {
    runtimePromise = null;
    pyodide = null;
    setStatus("Не удалось загрузить runtime", "error");
    showOutput(String(error), true);
    throw error;
  });
  return runtimePromise;
}

async function runCode() {
  runBtn.disabled = true;
  runBtn.innerHTML = "<span>◌</span> Выполняется…";
  showOutput("Запуск программы…");
  try {
    const runtime = await loadRuntime();
    runtime.globals.set("rost_source", editor.getValue());
    const result = await runtime.runPythonAsync(`
import io, contextlib, traceback
from rostlang.interpreter import RostInterpreter
_buffer = io.StringIO()
_error = None
try:
    with contextlib.redirect_stdout(_buffer):
        RostInterpreter().run(rost_source, "main.rost")
except Exception as exc:
    _error = str(exc)
_output = _buffer.getvalue()
if _error:
    _output = (_output + "\\n" if _output else "") + "RostLang error: " + _error
_output
`);
    showOutput(result, result.includes("RostLang error:"));
  } catch (error) {
    showOutput(String(error), true);
  } finally {
    runBtn.disabled = false;
    runBtn.innerHTML = "<span>▶</span> Запустить код";
  }
}

runBtn.addEventListener("click", runCode);
document.getElementById("clear-output").addEventListener("click", () => showOutput(""));
document.getElementById("reset-btn").addEventListener("click", () => editor.setValue(DEFAULT_CODE));
document.addEventListener("keydown", event => {
  if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
    event.preventDefault();
    runCode();
  }
});

document.getElementById("examples-btn").addEventListener("click", () => {
  const menu = document.getElementById("examples-menu");
  menu.hidden = !menu.hidden;
});
document.querySelectorAll("[data-example]").forEach(button => {
  button.addEventListener("click", () => {
    editor.setValue(EXAMPLES[button.dataset.example]);
    document.getElementById("examples-menu").hidden = true;
  });
});
document.addEventListener("click", event => {
  if (!event.target.closest("#examples-btn") && !event.target.closest("#examples-menu")) {
    document.getElementById("examples-menu").hidden = true;
  }
});
document.querySelectorAll("[data-insert]").forEach(button => {
  button.addEventListener("click", () => {
    const cursor = editor.getCursor();
    editor.replaceRange(button.dataset.insert + "\n", cursor);
    editor.focus();
  });
});

loadRuntime().catch(() => {});
