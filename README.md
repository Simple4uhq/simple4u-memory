# Simple4u Memory — persistent memory for Claude

**An MCP server that gives Claude a memory that survives between sessions.**

Claude forgets you every time you close the chat. Simple4u Memory fixes that.

- **Hierarchical memory** — facts with categories (user, project, preference, reference, general)
- **Two-corpus recall** — searches both SQLite facts AND your markdown memory files (Claude Code auto-memory, feedback rules, project notes, daily tick logs) in one `recall(query)` call
- **Session journals** — end-of-conversation notes you can read like a diary
- **Customizable persona** — edit `~/.simple4u-memory/persona.md` to shape behavior
- **Portable** — works in Claude Desktop, Claude Code, or any MCP client
- **Local-first** — your memory lives in `~/.simple4u-memory/` on your machine, nothing leaves

Free and open source. MIT license.

## Install

```bash
pip install simple4u-memory
```

Or from source:

```bash
git clone https://github.com/Simple4uhq/simple4u-memory
cd simple4u-memory
pip install -e .
```

## Setup — one command

After install, run:

```bash
simple4u-memory init
```

This configures Claude Desktop and Claude Code automatically:
- Adds the MCP server entry to both client configs (idempotent)
- Writes a short guidance block to `~/.claude/CLAUDE.md` so Claude calls
  `get_persona()` at session start and uses `remember()` proactively

Restart Claude Desktop / Claude Code and the memory tools are live.

### Flags

```bash
simple4u-memory init --desktop        # Claude Desktop only
simple4u-memory init --code           # Claude Code only
simple4u-memory init --no-claude-md   # skip CLAUDE.md guidance block
simple4u-memory init --dry-run        # preview changes without applying
simple4u-memory uninstall             # remove all config entries
```

### Manual setup (alternative)

If you prefer editing configs by hand, add this to
`~/Library/Application Support/Claude/claude_desktop_config.json` (macOS),
`%APPDATA%\Claude\claude_desktop_config.json` (Windows),
or `~/.claude/settings.json` (Claude Code):

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
| `recall(query, limit, sources)` | Search memories across SQLite facts + markdown roots (Claude Code auto-memory + persona home). `sources` = `all` / `sqlite` / `markdown` |
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
- `SIMPLE4U_MARKDOWN_ROOTS` — colon-separated list of additional markdown roots `recall()` should search. Defaults to Claude Code auto-memory dir (`~/.claude/projects/<slug>/memory`) + `SIMPLE4U_MEMORY_HOME`.

## Uninstall

```bash
simple4u-memory uninstall   # remove configs from Claude Desktop + Code
pip uninstall simple4u-memory
rm -rf ~/.simple4u-memory   # optional — also delete stored memories
```

## Status

v0.1.2 — two-corpus `recall()` lands (SQLite + markdown). Core memory tools +
setup command stable. Future: adaptive persona, semantic embeddings, team-shared
memories.

## Built by Simple4u

We make AI employees. [simple4uhq.com](https://simple4uhq.com)

## License

MIT
