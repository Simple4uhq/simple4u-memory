"""Init subcommand — configure Claude Desktop/Code to use simple4u-memory."""

from __future__ import annotations

import argparse
import json
import platform
import sys
from pathlib import Path


MARKER_START = "<!-- simple4u-memory:start -->"
MARKER_END = "<!-- simple4u-memory:end -->"

CLAUDE_MD_BLOCK = f"""
{MARKER_START}
## simple4u-memory

Persistent memory across sessions via MCP tools. Use them actively, not only when asked.

- `get_persona()` — call at session start to load identity + user context
- `recall(query, limit)` — semantic-ish search across BOTH corpora:
    1. SQLite facts saved via `remember`
    2. Markdown files in Claude Code auto-memory dir + simple4u-memory home
       (~/.claude/projects/<slug>/memory/*.md, tick logs, permanent feedback/project files)
  Call this at the start of any substantive request — before answering, pull the
  relevant prior context (feedback rules, project state, recent ticks).
- `remember(text, category)` — save facts about user, projects, preferences
- `journal(text)` — end-of-session recap after significant work
- `list_memories(category)` — browse SQLite-stored memories
- `forget(memory_id)` — remove wrong/outdated SQLite memories

At session start: `get_persona()`.
Before answering a non-trivial request: `recall(topic)` first, then respond.
Whenever something surprising or non-obvious comes up: `remember()` it immediately.
{MARKER_END}
"""


def claude_desktop_config() -> Path | None:
    system = platform.system()
    home = Path.home()
    if system == "Darwin":
        return home / "Library/Application Support/Claude/claude_desktop_config.json"
    if system == "Windows":
        return home / "AppData/Roaming/Claude/claude_desktop_config.json"
    if system == "Linux":
        return home / ".config/Claude/claude_desktop_config.json"
    return None


def claude_code_settings() -> Path:
    return Path.home() / ".claude" / "settings.json"


def claude_code_md() -> Path:
    return Path.home() / ".claude" / "CLAUDE.md"


def ensure_mcp_config(config_path: Path, dry_run: bool) -> str:
    """Add simple4u-memory to mcpServers. Idempotent. Returns status label."""
    existing: dict = {}
    if config_path.exists():
        try:
            existing = json.loads(config_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return f"skipped (invalid JSON): {config_path}"

    servers = existing.setdefault("mcpServers", {})
    entry = servers.get("simple4u-memory")
    if isinstance(entry, dict) and entry.get("command") == "simple4u-memory":
        return f"already set: {config_path}"

    servers["simple4u-memory"] = {"command": "simple4u-memory"}

    if dry_run:
        return f"[dry-run] would write: {config_path}"

    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps(existing, indent=2) + "\n", encoding="utf-8")
    return f"wrote: {config_path}"


def ensure_claude_md(md_path: Path, dry_run: bool) -> str:
    """Append memory guidance block to CLAUDE.md. Idempotent via markers."""
    existing = md_path.read_text(encoding="utf-8") if md_path.exists() else ""
    if MARKER_START in existing:
        return f"already set: {md_path}"

    new_content = existing.rstrip() + "\n" + CLAUDE_MD_BLOCK

    if dry_run:
        return f"[dry-run] would write: {md_path}"

    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(new_content, encoding="utf-8")
    return f"wrote: {md_path}"


def remove_mcp_config(config_path: Path, dry_run: bool) -> str:
    """Remove simple4u-memory from mcpServers. Returns status label."""
    if not config_path.exists():
        return f"not found: {config_path}"
    try:
        existing = json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return f"skipped (invalid JSON): {config_path}"

    servers = existing.get("mcpServers") or {}
    if "simple4u-memory" not in servers:
        return f"not configured: {config_path}"

    del servers["simple4u-memory"]
    if dry_run:
        return f"[dry-run] would remove from: {config_path}"

    config_path.write_text(json.dumps(existing, indent=2) + "\n", encoding="utf-8")
    return f"removed from: {config_path}"


def remove_claude_md(md_path: Path, dry_run: bool) -> str:
    """Remove memory guidance block from CLAUDE.md."""
    if not md_path.exists():
        return f"not found: {md_path}"
    existing = md_path.read_text(encoding="utf-8")
    if MARKER_START not in existing or MARKER_END not in existing:
        return f"not configured: {md_path}"

    start = existing.find(MARKER_START)
    end = existing.find(MARKER_END) + len(MARKER_END)
    cleaned = (existing[:start].rstrip() + "\n" + existing[end:].lstrip()).strip() + "\n"

    if dry_run:
        return f"[dry-run] would clean: {md_path}"

    md_path.write_text(cleaned, encoding="utf-8")
    return f"cleaned: {md_path}"


def cmd_init(args: argparse.Namespace) -> int:
    do_desktop = args.desktop or not args.code
    do_code = args.code or not args.desktop

    print("Setting up simple4u-memory.\n")

    if do_desktop:
        print("Claude Desktop:")
        desktop = claude_desktop_config()
        if desktop is None:
            print(f"  unsupported platform: {platform.system()}")
        else:
            print(f"  {ensure_mcp_config(desktop, args.dry_run)}")
        print()

    if do_code:
        print("Claude Code:")
        print(f"  {ensure_mcp_config(claude_code_settings(), args.dry_run)}")
        print()

    if not args.no_claude_md:
        print("Session guidance (CLAUDE.md):")
        print(f"  {ensure_claude_md(claude_code_md(), args.dry_run)}")
        print()

    if args.dry_run:
        print("Dry run complete. Re-run without --dry-run to apply.")
    else:
        print("Done. Restart Claude Desktop/Code for changes to take effect.")
    return 0


def cmd_uninstall(args: argparse.Namespace) -> int:
    print("Removing simple4u-memory from Claude Desktop/Code configs.\n")

    print("Claude Desktop:")
    desktop = claude_desktop_config()
    if desktop:
        print(f"  {remove_mcp_config(desktop, args.dry_run)}")
    print()

    print("Claude Code:")
    print(f"  {remove_mcp_config(claude_code_settings(), args.dry_run)}")
    print()

    print("Session guidance (CLAUDE.md):")
    print(f"  {remove_claude_md(claude_code_md(), args.dry_run)}")
    print()

    print(
        "Config cleaned. Data directory (~/.simple4u-memory/) left intact.\n"
        "Remove with: rm -rf ~/.simple4u-memory\n"
        "Uninstall package: pip uninstall simple4u-memory"
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="simple4u-memory",
        description="Persistent memory MCP server for Claude.",
    )
    sub = parser.add_subparsers(dest="command")

    init = sub.add_parser("init", help="Configure Claude Desktop/Code to use simple4u-memory")
    init.add_argument("--desktop", action="store_true", help="Configure Claude Desktop only")
    init.add_argument("--code", action="store_true", help="Configure Claude Code only")
    init.add_argument("--no-claude-md", action="store_true", help="Skip CLAUDE.md guidance block")
    init.add_argument("--dry-run", action="store_true", help="Preview changes without applying")
    init.set_defaults(func=cmd_init)

    uninstall = sub.add_parser("uninstall", help="Remove simple4u-memory config from Claude")
    uninstall.add_argument("--dry-run", action="store_true", help="Preview changes without applying")
    uninstall.set_defaults(func=cmd_uninstall)

    return parser


def run_cli(argv: list[str]) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        return 1
    return args.func(args)
