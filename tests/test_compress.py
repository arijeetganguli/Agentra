"""Tests for ContextCompressor — compress_file, compress_chunks, estimate_tokens."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from agentra.compress.engine import ContextCompressor


@pytest.fixture
def compressor() -> ContextCompressor:
    return ContextCompressor()


@pytest.fixture
def sample_md(tmp_path: Path) -> Path:
    """A markdown file with typical filler phrases and a code block."""
    content = textwrap.dedent("""\
        # Project Guidelines

        Please note that you should always run tests before committing.
        Make sure to use parameterized queries — never f-strings.
        In order to contribute, please open a pull request.
        You should review the CONTRIBUTING.md file first.

        ## Code Standards

        It is important to keep functions short.
        Remember to handle errors explicitly.

        ```python
        # Please note that this is intentional
        def example():
            pass
        ```

        Be sure to document public APIs.
    """)
    p = tmp_path / "CLAUDE.md"
    p.write_text(content, encoding="utf-8")
    return p


# ── estimate_tokens ───────────────────────────────────────────────────────────


class TestEstimateTokens:
    def test_non_empty_text(self, compressor: ContextCompressor):
        tokens = compressor.estimate_tokens("hello world")
        assert tokens >= 1

    def test_empty_string(self, compressor: ContextCompressor):
        tokens = compressor.estimate_tokens("")
        assert tokens >= 1

    def test_longer_text_more_tokens(self, compressor: ContextCompressor):
        short = compressor.estimate_tokens("hi")
        long = compressor.estimate_tokens("hi " * 100)
        assert long > short

    def test_fallback_when_tiktoken_missing(self, compressor: ContextCompressor):
        """Should fall back to len//4 without raising when tiktoken is absent."""
        import agentra.compress.engine as _eng
        orig = _eng._tiktoken_enc
        try:
            _eng._tiktoken_enc = False  # simulate absent tiktoken
            tokens = compressor.estimate_tokens("hello world this is a test sentence")
            assert tokens >= 1
        finally:
            _eng._tiktoken_enc = orig


# ── compress_file ─────────────────────────────────────────────────────────────


class TestCompressFile:
    def test_returns_three_tuple(self, compressor: ContextCompressor, sample_md: Path):
        result = compressor.compress_file(sample_md)
        assert len(result) == 3
        orig, comp, text = result
        assert isinstance(orig, int) and isinstance(comp, int) and isinstance(text, str)

    def test_reduces_tokens(self, compressor: ContextCompressor, sample_md: Path):
        orig, comp, _text = compressor.compress_file(sample_md)
        # Must produce fewer or equal tokens (filler stripped)
        assert comp <= orig

    def test_filler_stripped_from_bullets(self, compressor: ContextCompressor, tmp_path: Path):
        content = "- Please note that you should run tests.\n- Make sure to commit often.\n"
        f = tmp_path / "test.md"
        f.write_text(content, encoding="utf-8")
        _, _, compressed = compressor.compress_file(f)
        assert "Please note that" not in compressed
        assert "Make sure to" not in compressed

    def test_code_blocks_preserved(self, compressor: ContextCompressor, sample_md: Path):
        _, _, compressed = compressor.compress_file(sample_md)
        # Content inside the code block must survive verbatim
        assert "# Please note that this is intentional" in compressed
        assert "def example():" in compressed

    def test_consecutive_blank_lines_collapsed(self, compressor: ContextCompressor, tmp_path: Path):
        content = "Line one.\n\n\n\nLine two.\n"
        f = tmp_path / "blanks.md"
        f.write_text(content, encoding="utf-8")
        _, _, compressed = compressor.compress_file(f)
        # Should not have 3+ consecutive newlines
        assert "\n\n\n" not in compressed

    def test_urls_preserved(self, compressor: ContextCompressor, tmp_path: Path):
        content = "Please note that https://example.com is the canonical URL.\n"
        f = tmp_path / "urls.md"
        f.write_text(content, encoding="utf-8")
        _, _, compressed = compressor.compress_file(f)
        assert "https://example.com" in compressed

    def test_sentence_case_restored(self, compressor: ContextCompressor, tmp_path: Path):
        """When filler is stripped from a sentence-cased line, first char should be uppercased."""
        content = "- Make sure to run tests before committing.\n"
        f = tmp_path / "case.md"
        f.write_text(content, encoding="utf-8")
        _, _, compressed = compressor.compress_file(f)
        line = [line_text for line_text in compressed.splitlines() if line_text.strip()][0]
        # After stripping "Make sure to ", the first word should be capitalized
        content_part = line.lstrip("- ").strip()
        assert content_part[0].isupper() if content_part else True


# ── compress_chunks ───────────────────────────────────────────────────────────


class TestCompressChunks:
    def _make_chunk(self, cid: int, text: str) -> tuple:
        return (cid, "file.py", 1, "func", text)

    def test_unique_chunks_kept(self, compressor: ContextCompressor):
        chunks = [
            self._make_chunk(1, "def auth_user(token): pass"),
            self._make_chunk(2, "def paginate(items, page): return items[page:]"),
        ]
        result = compressor.compress_chunks(chunks)
        assert len(result) == 2

    def test_duplicate_chunk_removed(self, compressor: ContextCompressor):
        text = "def verify_jwt(token: str) -> bool:\n    payload = jwt.decode(token, SECRET)\n    return True\n"
        # Tiny variation — same tokens, one extra comment
        text2 = text + "# end\n"
        chunks = [self._make_chunk(1, text), self._make_chunk(2, text2)]
        result = compressor.compress_chunks(chunks)
        # Second chunk is >90% overlap — should be dropped
        assert len(result) == 1
        assert result[0][0] == 1  # first chunk kept

    def test_empty_input(self, compressor: ContextCompressor):
        assert compressor.compress_chunks([]) == []

    def test_preserves_order(self, compressor: ContextCompressor):
        chunks = [
            self._make_chunk(3, "def c(): pass"),
            self._make_chunk(1, "def a(): pass"),
            self._make_chunk(2, "def b(): pass"),
        ]
        result = compressor.compress_chunks(chunks)
        assert [c[0] for c in result] == [3, 1, 2]
