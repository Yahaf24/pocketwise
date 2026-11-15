"""Copy the Claude Code agent, skill and hook from claude-setup/ into .claude/ (run once)."""
import shutil
from pathlib import Path

root = Path(__file__).parent
shutil.copytree(root / "claude-setup", root / ".claude", dirs_exist_ok=True)
print("Installed into .claude/:")
for p in sorted((root / ".claude").rglob("*")):
    if p.is_file():
        print("  ", p.relative_to(root))
