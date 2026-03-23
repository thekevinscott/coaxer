"""CLI entry point for dspy-agent-sdk."""

import shutil
import sys
from pathlib import Path

SKILLS_DIR = Path(__file__).parent / "skills"


def install() -> None:
    """Copy bundled skills into .claude/skills/ in the current project."""
    target = Path.cwd() / ".claude" / "skills"

    for skill_dir in SKILLS_DIR.iterdir():
        if not skill_dir.is_dir():
            continue

        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            continue

        dest = target / skill_dir.name
        dest.mkdir(parents=True, exist_ok=True)
        shutil.copy2(skill_md, dest / "SKILL.md")
        print(f"Installed skill: /{ skill_dir.name} -> {dest / 'SKILL.md'}")


def main() -> None:
    """Route CLI subcommands."""
    min_args = 2
    if len(sys.argv) < min_args:
        print("Usage: dspy-agent-sdk <command>")
        print("Commands:")
        print("  install    Copy skills into .claude/skills/ in the current project")
        sys.exit(1)

    command = sys.argv[1]
    if command == "install":
        install()
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
