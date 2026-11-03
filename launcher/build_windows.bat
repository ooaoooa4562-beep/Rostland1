@echo off
setlocal
cd /d "%~dp0.."

echo [1/4] Installing build dependencies...
py -m pip install -r launcher\requirements-build.txt
if errorlevel 1 goto failed

echo [2/4] Building RostLang runtime...
pyinstaller --noconfirm --clean --onefile --console --name rost_runtime main.py
if errorlevel 1 goto failed

echo [3/4] Building RostLang Launcher...
pyinstaller --noconfirm --clean --onefile --windowed --name RostLangLauncher --add-binary "dist\rost_runtime.exe;." launcher\main.py
if errorlevel 1 goto failed

echo [4/4] Build complete!
echo Executable: %CD%\dist\RostLangLauncher.exe
pause
exit /b 0

:failed
echo.
echo Build failed. Check the error messages above.
pause
exit /b 1
