"""PostToolUse hook: after Claude writes/edits a file, compile-check Python and re-run the tests.

Exit code 2 sends the error back to Claude so it fixes the problem before moving on.
Works on Windows, macOS and Linux (pure Python, no bash needed).
"""
import json
import os
import py_compile
import subprocess
import sys

event = json.load(sys.stdin)
path = (event.get("tool_input") or {}).get("file_path", "")
project = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())

if path.endswith(".py"):
    try:
        py_compile.compile(path, doraise=True)
    except py_compile.PyCompileError as err:
        print(f"Syntax error in {path}:\n{err.msg}", file=sys.stderr)
        sys.exit(2)

if path.endswith(".py") or path.endswith("vectors.json"):
    run = subprocess.run([sys.executable, "-m", "pytest", "-q", "-x"], cwd=project,
                         capture_output=True, text=True)
    if run.returncode != 0:
        print("Tests are failing after this edit:\n" + run.stdout[-3000:], file=sys.stderr)
        sys.exit(2)
