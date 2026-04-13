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
    env_home = os.environ.get("SIMPLE4U_MEMORY_HOME") or os.environ.get("CLAUDIA_HOME")
    if env_home:
        return Path(env_home).expanduser()
    return Path.home() / ".simple4u-memory"


# Initialize shared state
HOME = get_home()
PERSONA = PersonaLoader(HOME)
PERSONA.ensure_initialized()
STORE = MemoryStore(HOME)

# Create MCP server
mcp = FastMCP("simple4u-memory")


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
    memory_id = STORE.remember(text, category=category)
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
    memories = STORE.recall(query, limit=limit, category=category)
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
    memories = STORE.list_all(category=category, limit=limit)
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
    deleted = STORE.forget(memory_id)
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
    journal_id = STORE.journal(text)
    return f"Journal entry saved (id={journal_id})."


@mcp.tool()
def get_persona() -> str:
    """Return the current persona + user context.

    This gives the AI its identity and what it knows about the user. Call this
    at session start to load full context.
    """
    return PERSONA.get_system_prompt()


@mcp.tool()
def recent_journals(days: int = 7) -> str:
    """Retrieve recent journal entries.

    Args:
        days: Number of days back to search (default 7).
    """
    entries = STORE.recent_journals(days=days)
    if not entries:
        return f"No journal entries in the last {days} days."
    lines = [f"{len(entries)} journal entries from last {days} days:"]
    for e in entries:
        lines.append(f"\n--- {e['session_date']} ---\n{e['text']}")
    return "\n".join(lines)


def main() -> None:
    """Entry point for the simple4u-memory command."""
    mcp.run()


if __name__ == "__main__":
    main()
