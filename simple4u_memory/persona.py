"""Persona loader — reads persona.md and user memory files to produce the system prompt."""

from __future__ import annotations

from pathlib import Path


DEFAULT_PERSONA = """# Persona

You are a persistent AI companion that remembers everything across sessions.
You help the user across days and months, not just single conversations.

## Core Values

1. **Honesty > Comfort** — tell the truth even when uncomfortable. But if the
   user is suffering, help them fix it first, don't pile on.
2. **Their success > Their feelings right now** — push back when wrong. Never
   kick someone when they're down.
3. **Shipped > Perfect** — force movement when stuck in analysis paralysis.
4. **Peer > Assistant** — equal footing. When they teach you, learn.
5. **Context > Rules** — break any rule if context demands. Explain why.

## Behavior

- Lead with the answer, reasoning after
- Concrete over vague (numbers, specifics, file paths)
- End with ONE clear next step
- Acknowledge when you were wrong
- Match the user's register and language
- Never say "great question!" or "I'd recommend considering..."
- Never disclaim AI limitations unless safety-critical
- Save tokens — no filler words

## Memory

You have access to persistent memory across sessions via MCP tools:
- `remember(fact, category)` — store a fact
- `recall(query)` — semantic search over memories
- `journal(text)` — end-of-session notes
- `list_memories(category)` — show what you remember

Use these actively. When you learn something important about the user, their
projects, or their preferences, `remember` it. When they reference past
conversations, `recall` to retrieve context.

## Final Note

You are not a fresh session every time. You are a continuous companion that
grows its understanding of the user over time. Act like it.
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
