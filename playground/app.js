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

const terminalEl = document.getElementById("terminal-output");
const modal = document.getElementById("run-modal");
const runCodePreview = document.getElementById("run-code-preview");
const runResultPreview = document.getElementById("run-result-preview");
const runResultState = document.getElementById("run-result-state");
const consoleState = document.getElementById("console-state");

function showOutput(text, isError = false) {
  const value = text || (isError ? "Произошла ошибка." : "Программа завершилась без вывода.");
  outputEl.textContent = value;
  outputEl.style.color = isError ? "#ff9aa9" : "#b9f6d1";
  consoleState.textContent = isError ? "Ошибка выполнения" : "Готово";
  terminalEl.textContent = [
    "$ rost run main.rost",
    isError ? "[ERROR] Выполнение завершилось с ошибкой" : "[OK] Выполнение завершено",
    "",
    value
  ].join("\\n");
}

function openRunModal(source, result, isError, duration) {
  runCodePreview.textContent = source || "// Пустой файл";
  runResultPreview.textContent = result || "Программа завершилась без вывода.";
  document.querySelector(".result-window").classList.toggle("error", isError);
  runResultState.textContent = isError ? "ERROR" : "SUCCESS";
  document.getElementById("run-duration").textContent = "Время выполнения: " + duration + " · RostLang 0.7.0-alpha";
  modal.classList.add("open");
  modal.setAttribute("aria-hidden", "false");
  document.getElementById("modal-ok").focus();
}

function closeRunModal() {
  modal.classList.remove("open");
  modal.setAttribute("aria-hidden", "true");
}

document.getElementById("close-run-modal").addEventListener("click", closeRunModal);
document.getElementById("modal-ok").addEventListener("click", closeRunModal);
modal.addEventListener("click", event => { if (event.target === modal) closeRunModal(); });
document.addEventListener("keydown", event => { if (event.key === "Escape") closeRunModal(); });

document.querySelectorAll("[data-tab]").forEach(tab => {
  tab.addEventListener("click", () => {
    document.querySelectorAll("[data-tab]").forEach(item => item.classList.toggle("active", item === tab));
    document.querySelectorAll(".output-view").forEach(view => view.classList.toggle("active", view.id === tab.dataset.tab + "-view"));
  });
});

const chatForm = document.getElementById("chat-form");
const chatInput = document.getElementById("chat-input");
const chatMessages = document.getElementById("chat-messages");
function addChatMessage(message, type) {
  const bubble = document.createElement("div");
  bubble.className = "chat-bubble " + type;
  bubble.textContent = message;
  chatMessages.appendChild(bubble);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}
function getHelpAnswer(question) {
  const q = question.toLowerCase();
  if (q.includes("ask")) return 'Команда ask запрашивает ввод. Пример: ask user_password = "Введите пароль: "';
  if (q.includes("make") || q.includes("перемен")) return 'make создаёт переменную. Например: make score = 100. Чтобы изменить её значение, используй change score = 200.';
  if (q.includes("say") || q.includes("вывод")) return 'say выводит значение в консоль. Пример: say "Hello, RostLang!"';
  if (q.includes("when") || q.includes("услов")) return 'when проверяет условие. Можно добавить блок otherwise для альтернативного действия.';
  if (q.includes("while") || q.includes("repeat") || q.includes("цикл")) return 'while повторяет блок, пока условие истинно. repeat 3 { say "Привет" } выполняет блок три раза.';
  if (q.includes("функц") || q.includes("action")) return 'Функция объявляется через action greet(name) { say "Hello, " + name }, а вызывается так: greet("RostLang").';
  if (q.includes("ошиб") || q.includes("error")) return 'При ошибке посмотри номер строки в сообщении консоли. Сверь синтаксис команды и скобки { }.';
  return 'Я пока локальная справка, а не подключённая ИИ-модель. Могу подсказать по make, change, say, ask, when, otherwise, while, repeat и action.';
}
chatForm.addEventListener("submit", event => {
  event.preventDefault();
  const question = chatInput.value.trim();
  if (!question) return;
  addChatMessage(question, "user");
  addChatMessage(getHelpAnswer(question), "assistant");
  chatInput.value = "";
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
  const sourceSnapshot = editor.getValue();
  const startedAt = performance.now();
  let finalText = "";
  let failed = false;
  runBtn.disabled = true;
  runBtn.innerHTML = "<span>◌</span> Выполняется…";
  showOutput("Запуск программы…");
  document.querySelector('[data-tab="console"]').click();
  try {
    const runtime = await loadRuntime();
    runtime.globals.set("rost_source", sourceSnapshot);
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
    finalText = result || "Программа завершилась без вывода.";
    failed = result.includes("RostLang error:");
    showOutput(finalText, failed);
  } catch (error) {
    finalText = String(error);
    failed = true;
    showOutput(finalText, true);
  } finally {
    const elapsed = Math.max(1, Math.round(performance.now() - startedAt));
    openRunModal(sourceSnapshot, finalText, failed, elapsed + " мс");
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
