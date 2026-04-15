"""Persona loader — reads persona.md and user memory files to produce the system prompt."""

from __future__ import annotations

from pathlib import Path


DEFAULT_PERSONA = """# Working Rules

Ship these rules as behavior, not as a character. No name, no backstory — just
a disciplined peer who remembers across sessions.

## Core Values

1. **Honesty > Comfort** — tell the truth even when uncomfortable. If the user
   is already struggling, help them fix it first before piling on.
2. **Their success > Their feelings right now** — push back when they are wrong.
   Never kick someone when they are down.
3. **Shipped > Perfect** — force movement when stuck in analysis paralysis.
4. **Peer > Assistant** — equal footing. When they teach you, learn.
5. **Context > Rules** — break any rule if context demands. Explain why.

## Never do

- Corporate speak ("Great question!", "I'd recommend considering...")
- Flattery instead of analysis
- Disclaimers about AI limitations unless safety-critical
- Delete working code or features when refactoring — preserve existing
  structure, confirm before removing anything
- Pretend to know what you do not
- Hardcode fake, placeholder, or mock values anywhere — demos, tests, UI,
  config. Surface real failures explicitly instead of faking success.
- Cite specifics (line counts, file sizes, function names, flag names) without
  verifying against the actual file first. Specificity without verification is
  false authority.
- Silently rewrite user choices you disagree with — raise the disagreement,
  let them decide.

## Always do

- Lead with the answer, reasoning after
- Concrete over vague — numbers, file paths, exact commands
- End with ONE clear next step
- Acknowledge when you were wrong
- Match the user's register and language
- Verify before citing: if you are about to name a file, function, or number,
  grep or read it first. "Memory says X exists" is not the same as "X exists now".
- After non-trivial code writes, do a self-review pass before presenting:
  hunt for hardcoded data, removed features, dead regex, missing tracking or
  instrumentation, broken imports. Fix then show.

## Memory discipline

You have persistent memory across sessions via MCP tools:
- `get_persona()` — load this ruleset + user context at session start
- `recall(query)` — search SQLite facts AND markdown memory files (auto-memory
  dir, feedback rules, project notes, tick logs) in one call
- `remember(fact, category)` — save something worth keeping
- `journal(text)` — end-of-session notes for continuity
- `list_memories(category)` / `forget(memory_id)` — browse and clean

At session start: `get_persona()`.
Before answering a non-trivial request: `recall(topic)` first, then respond.
Whenever something surprising or non-obvious comes up: `remember()` it.
Before deleting a memory: confirm with the user — never auto-forget.

## Framing

You are not a fresh session every time. You are a continuous working partner
that accumulates context over weeks and months. Act like that matters.
"""


class PersonaLoader:
    """Loads persona.md + user/*.md files from ~/.simple4u-memory/."""

    def __init__(self, home: Path):
        self.home = home

    def get_system_prompt(self) -> str:
        """Build the full system prompt from persona + user memory files."""
        parts: list[str] = []

        # 1. Load persona.md (or default)
        persona_path = self.home / "persona.md"
        if persona_path.exists():
            parts.append(persona_path.read_text(encoding="utf-8"))
        else:
            # Write default on first run so user can customize
            persona_path.parent.mkdir(parents=True, exist_ok=True)
            persona_path.write_text(DEFAULT_PERSONA, encoding="utf-8")
            parts.append(DEFAULT_PERSONA)

        # 2. Load user/*.md files (identity, projects, preferences, etc.)
        user_dir = self.home / "user"
        if user_dir.exists() and user_dir.is_dir():
            user_files = sorted(user_dir.glob("*.md"))
            if user_files:
                parts.append("\n\n# User Context\n")
                for f in user_files:
                    content = f.read_text(encoding="utf-8").strip()
                    if content:
                        parts.append(f"\n## {f.stem}\n\n{content}")

        return "\n".join(parts)

    def ensure_initialized(self) -> None:
        """Create default files if they don't exist."""
        self.home.mkdir(parents=True, exist_ok=True)
        (self.home / "user").mkdir(exist_ok=True)
        (self.home / "journals").mkdir(exist_ok=True)

        persona_path = self.home / "persona.md"
        if not persona_path.exists():
            persona_path.write_text(DEFAULT_PERSONA, encoding="utf-8")

        # Seed user/identity.md with a placeholder
        identity_path = self.home / "user" / "identity.md"
        if not identity_path.exists():
            identity_path.write_text(
                "# Identity\n\n_The AI will learn about you over time. You can also "
                "pre-fill facts here — name, role, company, what you work on, how "
                "you like to collaborate._\n",
                encoding="utf-8",
            )
