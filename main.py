import argparse
import sys
from pathlib import Path
from rostlang import __version__
from rostlang.interpreter import RostInterpreter
from rostlang.errors import RostLangError

def main():
    parser = argparse.ArgumentParser(prog="rost", description=f"RostLang {__version__}")
    parser.add_argument("file", nargs="?", help="Path to a .rost program")
    parser.add_argument("--version", action="version", version=__version__)
    args = parser.parse_args()
    if not args.file:
        parser.print_help()
        return
    path = Path(args.file)
    if not path.is_file():
        parser.error(f"File not found: {path}")
    if path.suffix != ".rost":
        parser.error("RostLang files must use the .rost extension")
    try:
        RostInterpreter().run(path.read_text(encoding="utf-8"), str(path))
    except RostLangError as error:
        print(f"RostLang error: {error}", file=sys.stderr)
        raise SystemExit(1)

if __name__ == "__main__":
    main()
