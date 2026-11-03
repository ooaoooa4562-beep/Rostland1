[app]
title = RostLang Launcher
package.name = rostlanglauncher
package.domain = org.rostlang
source.dir = .
source.include_exts = py,kv,rost
version = 0.1.0
requirements = python3,kivy==2.3.1
orientation = portrait
fullscreen = 0
android.minapi = 23
android.api = 35
android.archs = arm64-v8a, armeabi-v7a
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 1
