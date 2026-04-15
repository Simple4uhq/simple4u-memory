"""Markdown memory search — scans .md files in configured roots and ranks by relevance.

Complements the SQLite MemoryStore by searching Claude Code's auto-memory directory
(where MEMORY.md + per-topic files live) and any other markdown corpora the user wires in.

Ranking = weighted keyword scoring with recency bonus for tick logs. No ML deps.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_ROOTS = [
    "~/.claude/projects/-Users-sagenesterets/memory",
    "~/.simple4u-memory",
]

# Tokens shorter than this are dropped from queries (too noisy).
MIN_TERM_LEN = 3

# Field weights for scoring.
WEIGHT_FILENAME = 10.0
WEIGHT_FRONTMATTER = 5.0
WEIGHT_HEADING = 3.0
WEIGHT_BODY = 1.0

# Recency bonus for tick files — newer ticks outrank older permanent files
# when query is ambiguous. Bonus decays over 30 days.
RECENCY_WINDOW_DAYS = 30
RECENCY_MAX_BONUS = 2.0


@dataclass
class MarkdownHit:
    path: Path
    score: float
    snippet: str
    kind: str  # "permanent" | "tick" | "other"
    mtime: float = 0.0
    matched_terms: list[str] = field(default_factory=list)


def resolve_roots(env_var: str = "SIMPLE4U_MARKDOWN_ROOTS") -> list[Path]:
    """Return the list of markdown roots to search.

    Override via SIMPLE4U_MARKDOWN_ROOTS env var (colon-separated paths).
    Defaults to Claude Code auto-memory + simple4u-memory home.
    Missing directories are silently skipped.
    """
    raw = os.environ.get(env_var)
    candidates = raw.split(":") if raw else DEFAULT_ROOTS
    roots: list[Path] = []
    for c in candidates:
        p = Path(c).expanduser()
        if p.exists() and p.is_dir():
            roots.append(p)
    return roots


def _classify(path: Path) -> str:
    parts = {p.lower() for p in path.parts}
    if "tick" in parts:
        return "tick"
    if path.suffix == ".md":
        return "permanent"
    return "other"


def _tokenize_query(query: str) -> list[str]:
    """Split query into lowercase terms, drop stopwords and short tokens."""
    terms = re.findall(r"\w+", query.lower(), flags=re.UNICODE)
    return [t for t in terms if len(t) >= MIN_TERM_LEN]


def _load_file(path: Path) -> tuple[str, str, str]:
    """Return (frontmatter_text, heading_text, body_text) for a markdown file."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return "", "", ""

    frontmatter = ""
    body = text
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            frontmatter = text[3:end]
            body = text[end + 4 :]

    headings = "\n".join(
        line for line in body.splitlines() if line.lstrip().startswith("#")
    )
    return frontmatter, headings, body


def _count_term(haystack: str, term: str) -> int:
    if not haystack or not term:
        return 0
    return haystack.lower().count(term)


def _score_file(
    path: Path, terms: list[str], now: float
) -> tuple[float, list[str], str]:
    """Compute (score, matched_terms, snippet) for a single file."""
    frontmatter, headings, body = _load_file(path)
    if not body and not frontmatter:
        return 0.0, [], ""

    filename = path.name.lower()
    total = 0.0
    matched: list[str] = []

    for term in terms:
        hits = 0.0
        if term in filename:
            hits += WEIGHT_FILENAME
        hits += _count_term(frontmatter, term) * WEIGHT_FRONTMATTER
        hits += _count_term(headings, term) * WEIGHT_HEADING
        hits += _count_term(body, term) * WEIGHT_BODY
        if hits > 0:
            matched.append(term)
            total += hits

    if total == 0:
        return 0.0, [], ""

    kind = _classify(path)
    if kind == "tick":
        try:
            age_days = max(0.0, (now - path.stat().st_mtime) / 86400)
            decay = max(0.0, 1.0 - age_days / RECENCY_WINDOW_DAYS)
            total += decay * RECENCY_MAX_BONUS
        except OSError:
            pass

    snippet = _make_snippet(body, matched)
    return total, matched, snippet


def _make_snippet(body: str, matched_terms: list[str], radius: int = 120) -> str:
    """Pull a short snippet around the first matched term, single-line."""
    if not body:
        return ""
    lower = body.lower()
    idx = -1
    for term in matched_terms:
        found = lower.find(term)
        if found != -1 and (idx == -1 or found < idx):
            idx = found
    if idx == -1:
        # Fall back to first non-empty line.
        for line in body.splitlines():
            stripped = line.strip()
            if stripped:
                return stripped[: 2 * radius]
        return ""

    start = max(0, idx - radius)
    end = min(len(body), idx + radius)
    snippet = body[start:end].replace("\n", " ").strip()
    if start > 0:
        snippet = "…" + snippet
    if end < len(body):
        snippet = snippet + "…"
    return re.sub(r"\s+", " ", snippet)


class MarkdownMemoryStore:
    """Scan markdown roots and rank files by relevance to a query."""

    def __init__(self, roots: list[Path] | None = None):
        self.roots = roots if roots is not None else resolve_roots()

    def _iter_files(self):
        for root in self.roots:
            for path in root.rglob("*.md"):
                if path.is_file() and "egg-info" not in path.parts:
                    yield path

    def search(self, query: str, limit: int = 5) -> list[MarkdownHit]:
        terms = _tokenize_query(query)
        now = datetime.now(timezone.utc).timestamp()

        hits: list[MarkdownHit] = []
        if not terms:
            # Empty query → return most recently modified ticks + permanent files.
            for path in self._iter_files():
                try:
                    mtime = path.stat().st_mtime
                except OSError:
                    continue
                snippet = _make_snippet(_load_file(path)[2], [])
                hits.append(
                    MarkdownHit(
                        path=path,
                        score=mtime,
                        snippet=snippet,
                        kind=_classify(path),
                        mtime=mtime,
                    )
                )
            hits.sort(key=lambda h: h.score, reverse=True)
            return hits[:limit]

        for path in self._iter_files():
            score, matched, snippet = _score_file(path, terms, now)
            if score > 0:
                try:
                    mtime = path.stat().st_mtime
                except OSError:
                    mtime = 0.0
                hits.append(
                    MarkdownHit(
                        path=path,
                        score=score,
                        snippet=snippet,
                        kind=_classify(path),
                        mtime=mtime,
                        matched_terms=matched,
                    )
                )

        hits.sort(key=lambda h: h.score, reverse=True)
        return hits[:limit]
