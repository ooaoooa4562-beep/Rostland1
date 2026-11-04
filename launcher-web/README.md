# RostLang WebView launcher (experimental)

This branch introduces one shared HTML/CSS/JavaScript launcher UI for Windows and Android.

## Build artifacts

- Windows: `launcher-windows/RostLangLauncher.csproj` publishes a self-contained `.exe` for Windows x64. It uses Microsoft WebView2; the WebView2 Runtime must be available on the target Windows machine.
- Android: `android-web` builds a WebView APK. The GitHub Actions workflow copies the shared UI into Android assets before building.

Run **Build RostLang WebView Launchers** from the Actions tab on the `launcher-webview` branch. Download the Windows and Android artifacts from the completed run.

## Runtime status

`launcher-web/runtime.js` is an experimental JavaScript port, not yet feature-complete or behavior-identical to the Python 0.7 alpha interpreter. The current stage covers basic variables, arithmetic, strings, arrays, conditions, repeat/while/for loops, functions, simple input/output and selected built-ins.

Not yet ported: dictionaries/tuples, classes and methods, module loading, filesystem APIs, complete exception behavior, `stop`/`skip`, full Period/Time semantics, and several edge cases. Do not use this build as a replacement for the Python runtime yet. The original Python interpreter and launchers remain untouched on `main`.

## File handling limitations

The current UI uses browser file input and browser downloads. Android's native Storage Access Framework integration and a richer project/file manager are still pending. This is an early functional shell, not a finished IDE.
