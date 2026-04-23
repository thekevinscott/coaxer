"""CLI entry point for coaxer."""

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
        print(f"Installed skill: /{skill_dir.name} -> {dest / 'SKILL.md'}")


def label(args: list[str]) -> None:
    """Launch the labeling TUI."""
    if len(args) < 1:
        print("Usage: coaxer label <input.json> [--output <output.json>]")
        print()
        print("Input JSON format:")
        print('  {"label_field": "is_collection", "labels": ["true", "false"],')
        print('   "display_fields": ["name", "description"],')
        print('   "examples": [{"name": "foo", "description": "bar"}, ...]}')
        sys.exit(1)

    input_path = args[0]
    output_path = input_path.replace(".json", "_labeled.json")

    i = 1
    while i < len(args):
        if args[i] in ("--output", "-o") and i + 1 < len(args):
            output_path = args[i + 1]
            i += 2
        else:
            i += 1

    from .tui import run_label_tui

    run_label_tui(input_path, output_path)


def main() -> None:
    """Route CLI subcommands."""
    min_args = 2
    if len(sys.argv) < min_args:
        print("Usage: coaxer <command>")
        print("Commands:")
        print("  install    Copy skills into .claude/skills/ in the current project")
        print("  label      Launch the labeling TUI for interactive example labeling")
        sys.exit(1)

    command = sys.argv[1]
    if command == "install":
        install()
    elif command == "label":
        label(sys.argv[2:])
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
