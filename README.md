# Simple4u Memory — persistent memory for Claude

**An MCP server that gives Claude a memory that survives between sessions.**

Claude forgets you every time you close the chat. Simple4u Memory fixes that.

- **Hierarchical memory** — facts with categories (user, project, preference, reference, general)
- **Full-text search** — SQLite FTS5 across everything remembered
- **Session journals** — end-of-conversation notes you can read like a diary
- **Customizable persona** — edit `~/.simple4u-memory/persona.md` to shape behavior
- **Portable** — works in Claude Desktop, Claude Code, or any MCP client
- **Local-first** — your memory lives in `~/.simple4u-memory/` on your machine

Free and open source. MIT license.

## Install

```bash
pip install simple4u-memory
```

Or from source:

```bash
git clone https://github.com/simple4u/simple4u-memory
cd simple4u-memory
pip install -e .
```

## Use with Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS)
or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "simple4u-memory": {
      "command": "simple4u-memory"
    }
  }
}
```

Restart Claude Desktop. The memory tools will appear in the MCP panel.

## Use with Claude Code

Add to `~/.claude/settings.json`:

```json
{
  "mcpServers": {
    "simple4u-memory": {
      "command": "simple4u-memory"
    }
  }
}
```

Or install as a project-scoped server by adding to `.mcp.json`:

```json
{
  "mcpServers": {
    "simple4u-memory": {
      "command": "simple4u-memory"
    }
  }
}
```

## Tools exposed

| Tool | Purpose |
|------|---------|
| `remember(text, category)` | Save a fact to long-term memory |
| `recall(query, limit)` | Search memories via full-text search |
| `list_memories(category)` | Browse what's remembered |
| `forget(memory_id)` | Delete a wrong/outdated memory |
| `journal(text)` | Write an end-of-session note |
| `recent_journals(days)` | Read recent journal entries |
| `get_persona()` | Return full persona + user context |

## Customize

Your memory lives in `~/.simple4u-memory/`:

```
~/.simple4u-memory/
├── persona.md            # Edit to change AI's behavior
├── memory.db             # SQLite + FTS5 (don't touch unless you know)
├── user/                 # Long-term facts about you
│   ├── identity.md       # Who you are (name, role, values)
│   ├── projects.md       # What you're working on
│   └── preferences.md    # How you like to work
└── journals/
    └── 2026-04-12.md     # End-of-session notes
```

Edit `persona.md` to change tone, rules, behavior. Edit `user/*.md` to pre-fill
facts the AI will know on every session.

## Environment

- `SIMPLE4U_MEMORY_HOME` — override the data directory (default `~/.simple4u-memory`)

## Status

v0.1 — early release. Core memory tools work. Future: semantic embeddings,
memory hierarchies with decay, team-shared memories.

## Part of the Simple4u ecosystem

This is free and open source. If you want a full AI employee with this memory
built in — Gmail, Drive, reminders, daily intelligence, city/industry awareness —
check out [Simple4u](https://simple4uhq.com). $247/mo, 2 months free.

## License

MIT
