"""Simple4u Memory MCP server — exposes memory tools to any MCP-compatible client."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from simple4u_memory.memory import MemoryStore
from simple4u_memory.persona import PersonaLoader


def get_home() -> Path:
    """Resolve data directory. Override with SIMPLE4U_MEMORY_HOME env var."""
    env_home = os.environ.get("SIMPLE4U_MEMORY_HOME")
    if env_home:
        return Path(env_home).expanduser()
    return Path.home() / ".simple4u-memory"


# MCP server and shared state are initialized lazily so CLI subcommands
# (init, uninstall) don't touch the filesystem or import heavy resources.
mcp = FastMCP("simple4u-memory")
_STORE: MemoryStore | None = None
_PERSONA: PersonaLoader | None = None


def _store() -> MemoryStore:
    global _STORE
    if _STORE is None:
        _STORE = MemoryStore(get_home())
    return _STORE


def _persona() -> PersonaLoader:
    global _PERSONA
    if _PERSONA is None:
        home = get_home()
        _PERSONA = PersonaLoader(home)
        _PERSONA.ensure_initialized()
    return _PERSONA


@mcp.tool()
def remember(text: str, category: str = "general") -> str:
    """Save a fact, observation, or piece of context to persistent memory.

    Use this when you learn something important about the user, their projects,
    their preferences, or anything else worth recalling in future sessions.

    Args:
        text: The fact or observation to remember.
        category: Optional category — "user", "project", "preference",
                  "reference", "general". Defaults to "general".
    """
    memory_id = _store().remember(text, category=category)
    return f"Remembered (id={memory_id}, category={category}): {text}"


@mcp.tool()
def recall(query: str, limit: int = 5, category: str | None = None) -> str:
    """Search persistent memory for relevant facts.

    Uses full-text search across all stored memories. Use this when the user
    references past conversations, asks what you remember, or you need context
    from prior sessions.

    Args:
        query: Search terms. Empty string returns most recent memories.
        limit: Max results to return (default 5).
        category: Optional filter by category.
    """
    memories = _store().recall(query, limit=limit, category=category)
    if not memories:
        return f"No memories found for '{query}'."
    lines = [f"Found {len(memories)} memories for '{query}':"]
    for m in memories:
        date = m.created_at[:10]
        lines.append(f"  [{m.id}] ({m.category}, {date}) {m.text}")
    return "\n".join(lines)


@mcp.tool()
def list_memories(category: str | None = None, limit: int = 20) -> str:
    """List stored memories, optionally filtered by category.

    Args:
        category: Filter by category (user/project/preference/reference/general).
        limit: Max results to return.
    """
    memories = _store().list_all(category=category, limit=limit)
    if not memories:
        filt = f" in category '{category}'" if category else ""
        return f"No memories stored{filt} yet."
    lines = [f"{len(memories)} memories" + (f" in '{category}'" if category else "") + ":"]
    for m in memories:
        date = m.created_at[:10]
        lines.append(f"  [{m.id}] ({m.category}, {date}) {m.text}")
    return "\n".join(lines)


@mcp.tool()
def forget(memory_id: int) -> str:
    """Delete a memory by its id.

    Use this when a stored fact turns out to be wrong or outdated.

    Args:
        memory_id: The id of the memory to remove.
    """
    deleted = _store().forget(memory_id)
    if deleted:
        return f"Forgot memory {memory_id}."
    return f"No memory found with id {memory_id}."


@mcp.tool()
def journal(text: str) -> str:
    """Write an end-of-session journal entry.

    Use this at the end of a significant conversation to record what happened,
    decisions made, and what to remember for next time. Journals are stored in
    ~/.simple4u-memory/journals/YYYY-MM-DD.md for human reading.

    Args:
        text: The journal entry text.
    """
    journal_id = _store().journal(text)
    return f"Journal entry saved (id={journal_id})."


@mcp.tool()
def get_persona() -> str:
    """Return the current persona + user context.

    This gives the AI its identity and what it knows about the user. Call this
    at session start to load full context.
    """
    return _persona().get_system_prompt()


@mcp.tool()
def recent_journals(days: int = 7) -> str:
    """Retrieve recent journal entries.

    Args:
        days: Number of days back to search (default 7).
    """
    entries = _store().recent_journals(days=days)
    if not entries:
        return f"No journal entries in the last {days} days."
    lines = [f"{len(entries)} journal entries from last {days} days:"]
    for e in entries:
        lines.append(f"\n--- {e['session_date']} ---\n{e['text']}")
    return "\n".join(lines)


def main() -> None:
    """Entry point. Routes to CLI subcommands or MCP server."""
    argv = sys.argv[1:]
    if argv and argv[0] in {"init", "uninstall", "--help", "-h"}:
        from simple4u_memory.init import run_cli
        sys.exit(run_cli(argv))

    # Default: run MCP server over stdio
    _persona()  # ensure data dir exists before server starts
    mcp.run()


if __name__ == "__main__":
    main()
