# SAE4U Memory

**A persistent memory architecture for Claude — MCP server + hooks +
rules + prompts + templates.** Free and open source. MIT.

Claude forgets you every time you close the chat. SAE4U Memory fixes
that, and goes further: it ships an opinionated *architecture* for
how persistent memory should be organized — not just storage, but
classification, periodic review, persona, cleanup, and session
continuity.

Built by [Simple4u](https://simple4u.io), an engineering firm in New York. Part of the [SAE4U](https://github.com/Simple4uhq) OSS family
alongside [`sae4u-agent`](https://github.com/Simple4uhq/sae4u-agent).

---

## What you get

### Core (works in any MCP client — Claude Desktop, Claude Code, etc.)

- **Two-corpus recall** — `recall(query)` searches BOTH SQLite facts
  AND your markdown memory files (Claude Code auto-memory dirs +
  `~/.sae4u-memory/`) in one call. No re-explaining yourself.
- **Hierarchical memory** — `remember(text, category)` with 5
  categories: `user`, `feedback`, `project`, `reference`, `general`.
- **Session journals** — `journal(text)` for end-of-session notes
  written to `~/.sae4u-memory/journals/YYYY-MM-DD.md` for human reading.
- **Customizable persona** — `persona.md` shapes the AI's identity.
  Default: **Simple**, a peer-level coder friend who remembers things.
- **Local-first** — your memory lives in `~/.sae4u-memory/` on your
  machine. Nothing leaves.

### Architecture (Claude Code with `--code-full`)

- **`hooks/memory-tick.sh`** — UserPromptSubmit hook that fires every
  10 min and forces a brief memory review. Catches borderline
  observations before they fall out of context.
- **`rules/`** — 10 universal feedback rules covering memory
  discipline, session continuity, anti-confabulation, hardcode
  prevention, post-write review.
- **`prompts/`** — opinionated session-open and session-close prompts
  that pair with the architecture.
- **`templates/`** — formats for `MEMORY.md`, feedback rules,
  project facts, and tick logs.
- **`commands/memory-distill.md`** — weekly distill ritual that
  promotes tick-log items to permanent memory interactively.

---

## Install

### Minimum (MCP only)

```bash
git clone https://github.com/Simple4uhq/sae4u-memory
cd sae4u-memory
pip install -e .
sae4u-memory init
```

This wires the MCP server into Claude Desktop and Claude Code, and
appends a guidance block to `~/.claude/CLAUDE.md`. Restart your
client and the memory tools are live.

### Full architecture (Claude Code only)

```bash
sae4u-memory init --code-full
```

Adds:
- Copy `hooks/memory-tick.sh` → `~/.claude/hooks/memory-tick.sh`
- Register the hook in `~/.claude/settings.json` under `hooks.UserPromptSubmit`
- Scaffold `~/.sae4u-memory/MEMORY.md`
- Drop default rules into `~/.sae4u-memory/rules/`

Restart Claude Code. The tick will fire every 10 min and instruct the
AI to review and classify recent context.

### Flags

```bash
sae4u-memory init --desktop        # Claude Desktop only
sae4u-memory init --code           # Claude Code MCP only
sae4u-memory init --code-full      # Claude Code MCP + hook + scaffold
sae4u-memory init --no-claude-md   # skip CLAUDE.md guidance block
sae4u-memory init --dry-run        # preview changes without applying
sae4u-memory uninstall             # remove all config entries
```

---

## Tools exposed (MCP)

| Tool | Purpose |
|------|---------|
| `remember(text, category)` | Save a fact to long-term memory |
| `recall(query, limit, sources)` | Search across SQLite + markdown roots. `sources` = `all` / `sqlite` / `markdown` |
| `list_memories(category)` | Browse what's remembered |
| `forget(memory_id)` | Delete a wrong/outdated memory |
| `journal(text)` | Write an end-of-session note |
| `recent_journals(days)` | Read recent journal entries |
| `get_persona()` | Return full persona + user context |

---

## How memory is organized

```
~/.sae4u-memory/
├── persona.md              # Edit to customize behavior
├── memory.db               # SQLite + FTS5
├── MEMORY.md               # Index of permanent files (loaded at session start)
├── user/                   # User context loaded by get_persona()
│   ├── identity.md
│   ├── projects.md
│   └── preferences.md
├── tick/                   # Day-rolling tick log (NOT indexed in MEMORY.md)
│   └── 2026-05-07.md
├── archive/                # User-confirmed archived files
├── journals/               # End-of-session narratives
│   └── 2026-05-07.md
└── .last_tick              # Epoch of last memory tick
```

The 4-type classification (`user`, `feedback`, `project`, `reference`)
plus the tick / permanent split is the architectural core. See
[`architecture.md`](sae4u_memory/_assets/docs/architecture.md) for the
full explanation.

---

## Documentation

All architecture content lives under [`sae4u_memory/_assets/`](sae4u_memory/_assets/) so it ships with the wheel.

- [`docs/architecture.md`](sae4u_memory/_assets/docs/architecture.md) —
  5 concepts, file layout, the 4 types, what NOT to save
- [`docs/tick-protocol.md`](sae4u_memory/_assets/docs/tick-protocol.md) —
  how the 10-min hook works, what gets written where
- [`docs/persona-customization.md`](sae4u_memory/_assets/docs/persona-customization.md) —
  what's editable, what's loaded at session start
- [`docs/episodic-bridge.md`](sae4u_memory/_assets/docs/episodic-bridge.md) —
  optional pattern for users with a remote dev box
- [`prompts/session-open.md`](sae4u_memory/_assets/prompts/session-open.md) —
  paste this at session start
- [`prompts/session-close.md`](sae4u_memory/_assets/prompts/session-close.md) —
  paste this at session end
- [`commands/memory-distill.md`](sae4u_memory/_assets/commands/memory-distill.md) —
  weekly cleanup ritual
- [`rules/`](sae4u_memory/_assets/rules/) — 10 universal feedback rules
- [`hooks/memory-tick.sh`](sae4u_memory/_assets/hooks/memory-tick.sh) —
  the UserPromptSubmit hook itself
- [`templates/`](sae4u_memory/_assets/templates/) — MEMORY.md, feedback rule, project fact, tick log

---

## Customize

Edit `~/.sae4u-memory/persona.md` to change the AI's identity, voice,
and rules. Edit `~/.sae4u-memory/user/*.md` to pre-fill what the AI
knows about you. Both are loaded fresh on every session start.

The default persona is **Simple** — a peer-level coder friend.
Rename, rewrite, or replace as you see fit.

---

## Environment

- `SAE4U_MEMORY_HOME` — override the data directory
  (default `~/.sae4u-memory`)
- `SAE4U_MARKDOWN_ROOTS` — colon-separated list of markdown roots
  that `recall()` should search. Defaults to all Claude Code
  auto-memory dirs (globbed from `~/.claude/projects/*/memory/`)
  plus `SAE4U_MEMORY_HOME`.

---

## Uninstall

```bash
sae4u-memory uninstall    # remove configs from Claude Desktop + Code
rm ~/.claude/hooks/memory-tick.sh    # if you ran --code-full
rm -rf ~/.sae4u-memory    # optional — also delete stored memories
pip uninstall sae4u-memory
```

---

## Status

**v0.2.0** — memory architecture release. Full export of the pattern
the project authors run in production: hooks + rules + prompts +
templates + persona + extended `init` for Claude Code. Renamed from
`simple4u-memory` to align with the SAE4U OSS family.

Previous: v0.1.3 (under the old name) shipped two-corpus recall and
a working-rules persona. v0.1.x users on PyPI: install fresh from
this repo; the old package is no longer maintained.

---

## Sister project

- [`sae4u-agent`](https://github.com/Simple4uhq/sae4u-agent) —
  multi-tenant control plane and agent runtime template. The
  agents need memory; this is that memory.

---

## License

MIT.
