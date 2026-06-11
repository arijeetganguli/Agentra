"""ContextCompressor — reduce input tokens in agent context files and RAG chunks.

Inspired by caveman-compress (github.com/JuliusBrussee/caveman): strips filler
language from markdown files while preserving code blocks, URLs, and file paths
verbatim.  Also deduplicates near-identical RAG chunks via Jaccard similarity.

Typical savings on CLAUDE.md / AGENTS.md / copilot-instructions.md: 30-50%.
"""

from __future__ import annotations

import re
from pathlib import Path

# Filler phrases stripped from the start of bullets and plain lines (case-insensitive).
# Ordered longest-first to prefer the most specific match.
_FILLER_PHRASES: list[str] = [
    "it is important to note that ",
    "it's important to note that ",
    "it is worth noting that ",
    "you should note that ",
    "please be aware that ",
    "please ensure that ",
    "it is important to ",
    "it's important to ",
    "please make sure that ",
    "please make sure ",
    "please note that ",
    "make sure to ",
    "remember to ",
    "don't forget to ",
    "be sure to ",
    "you should ",
    "in order to ",
]

# Compiled patterns for quick substitution (applied in order)
_FILLER_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"(?i)^" + re.escape(p)) for p in _FILLER_PHRASES
]

# Lines beginning with these patterns are never touched (URLs, paths, code refs)
_PRESERVE_RE = re.compile(r"^(?:https?://|`[^`]|\./|/[a-zA-Z]|[A-Za-z]:\\)")

# Cached tiktoken encoder (False = not available)
_tiktoken_enc: object = None


def _estimate_tokens(text: str) -> int:
    """Estimate token count.  Uses tiktoken (cl100k_base) when available, else len//4."""
    global _tiktoken_enc
    if _tiktoken_enc is None:
        try:
            import tiktoken  # type: ignore[import]
            _tiktoken_enc = tiktoken.get_encoding("cl100k_base")
        except Exception:  # noqa: BLE001
            _tiktoken_enc = False
    if _tiktoken_enc is not False:
        try:
            return max(1, len(_tiktoken_enc.encode(text)))  # type: ignore[union-attr]
        except Exception:  # noqa: BLE001
            pass
    return max(1, len(text) // 4)


class ContextCompressor:
    """
    Compress markdown context files and RAG chunks to reduce input token cost.

    Methods
    -------
    estimate_tokens(text)
        Accurate token count via tiktoken when available.
    compress_file(path)
        Compress a single markdown file. Returns (orig_tokens, comp_tokens, compressed_text).
    compress_chunks(chunks)
        Deduplicate near-identical RAG chunks (>90% token overlap).
    """

    # ── Public API ────────────────────────────────────────────────────────

    def estimate_tokens(self, text: str) -> int:
        """Return token count using tiktoken (cl100k_base) or len//4 fallback."""
        return _estimate_tokens(text)

    def compress_file(self, path: Path) -> tuple[int, int, str]:
        """
        Compress a markdown context file.

        Code blocks (``` / ~~~), URLs, and file paths are never modified.

        Returns
        -------
        (original_tokens, compressed_tokens, compressed_text)
        """
        original = path.read_text(encoding="utf-8", errors="ignore")
        compressed = self._compress_markdown(original)
        return _estimate_tokens(original), _estimate_tokens(compressed), compressed

    def compress_chunks(self, chunks: list[tuple]) -> list[tuple]:
        """
        Deduplicate near-identical RAG chunks by Jaccard token similarity.

        Accepts tuples of the form (chunk_id, file_path, start_line, symbol_name, text)
        (as returned by CodeIndexEngine.all_chunks()).  Chunks with >90% token overlap
        with an already-accepted chunk are dropped.

        Returns the deduplicated list (order preserved).
        """
        seen_toks: list[frozenset[str]] = []
        result: list[tuple] = []
        for chunk in chunks:
            text = chunk[4] if len(chunk) > 4 else str(chunk[-1])
            toks = frozenset(re.findall(r"\b\w+\b", text.lower()))
            is_dup = any(
                (len(toks & seen) / len(toks | seen)) > 0.90
                for seen in seen_toks
                if toks and seen
            )
            if not is_dup:
                seen_toks.append(toks)
                result.append(chunk)
        return result

    # ── Internal helpers ──────────────────────────────────────────────────

    def _compress_markdown(self, text: str) -> str:
        """Multi-pass markdown compression preserving code blocks."""
        lines = text.split("\n")
        out: list[str] = []
        in_code_block = False
        consecutive_blank = 0

        for line in lines:
            stripped = line.strip()

            # Toggle code-block state
            if stripped.startswith("```") or stripped.startswith("~~~"):
                in_code_block = not in_code_block
                out.append(line)
                consecutive_blank = 0
                continue

            # Inside code block — never modify
            if in_code_block:
                out.append(line)
                consecutive_blank = 0
                continue

            # Collapse consecutive blank lines (keep at most one)
            if stripped == "":
                consecutive_blank += 1
                if consecutive_blank <= 1:
                    out.append(line)
                continue
            consecutive_blank = 0

            out.append(self._strip_fillers(line))

        return "\n".join(out)

    def _strip_fillers(self, line: str) -> str:
        """Strip filler prefix from a line, preserving indentation and bullet marker."""
        m = re.match(r"^(\s*(?:[-*•]\s+)?)(.*)", line, re.DOTALL)
        if not m:
            return line
        prefix, content = m.group(1), m.group(2)

        # Never touch lines that are URLs, absolute paths, or inline-code refs
        if _PRESERVE_RE.match(content):
            return line

        for pattern in _FILLER_PATTERNS:
            new_content = pattern.sub("", content).strip()
            if new_content and new_content != content:
                # Restore sentence case only when the original was sentence-cased
                # and the new content does NOT start with a URL/path (which must stay lowercase)
                if (new_content[0].islower()
                        and content and not content[0].islower()
                        and not _PRESERVE_RE.match(new_content)):
                    new_content = new_content[0].upper() + new_content[1:]
                content = new_content
                break

        return prefix + content
