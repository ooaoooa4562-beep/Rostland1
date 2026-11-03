# RostLang Launcher for Android

This is the Android companion app for RostLang. It is built separately from the desktop PySide6 launcher using Kivy and Buildozer.

## Features in the first alpha

- Create, edit and save `.rost` files in the app's private storage.
- Open files previously saved by the app.
- Run source code with the RostLang interpreter bundled into the APK.
- View program output and errors.

## Build

The GitHub Actions workflow `.github/workflows/build-android.yml` builds a debug APK. Open the repository's **Actions** tab, select **Build RostLang Launcher (Android)**, and download the `RostLangLauncher-Android` artifact after a successful run.

The first alpha uses app-private storage and does not yet include Android's system file picker, syntax highlighting, or interactive `input()` dialogs. Programs can use the interpreter's normal language features that do not require unsupported platform-specific packages.
