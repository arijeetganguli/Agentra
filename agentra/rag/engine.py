"""CodeRAGEngine — BM25 retrieval over the code knowledge graph.

Chunks are sourced from the SQLite index (CodeIndexEngine) so no separate file
traversal is needed.  The fitted BM25 index and metadata are persisted to disk
so subsequent queries are near-instant.

rank_bm25 is a required dependency (pure Python, zero ML dependencies).
Every public method degrades gracefully when it is missing, returning empty
results with a clear installation hint.
"""

from __future__ import annotations

import pickle
import re
from pathlib import Path
from typing import TYPE_CHECKING

from agentra.models import AntiPattern, RAGResult, Severity
from agentra.rag.patterns import AntiPatternLibrary

if TYPE_CHECKING:
    from agentra.index.engine import CodeIndexEngine

_BM25_HINT = (
    "rank_bm25 is required for RAG search. "
    "Install it with: pip install agentra[rag]"
)

_SIMILARITY_THRESHOLD = 0.92  # AP-011 duplicate-chunk threshold (Jaccard)


def _tokenize(text: str) -> list[str]:
    """Word tokenizer that preserves dotted names (e.g. os.path)."""
    return re.findall(r"\b\w[\w.]*\b", text.lower())


def _require_bm25():
    try:
        from rank_bm25 import BM25Okapi  # type: ignore[import]
        return BM25Okapi
    except ImportError as e:
        raise ImportError(_BM25_HINT) from e


def _jaccard(text_a: str, text_b: str) -> float:
    """Token-level Jaccard similarity — used for AP-011 duplicate-chunk detection."""
    toks_a = set(_tokenize(text_a))
    toks_b = set(_tokenize(text_b))
    if not toks_a or not toks_b:
        return 0.0
    return len(toks_a & toks_b) / len(toks_a | toks_b)


class CodeRAGEngine:
    """
    BM25 retrieval engine over code chunks from the knowledge graph.

    Usage::

        rag = CodeRAGEngine(store_path=Path(".agentra"), index_engine=engine)
        rag.build()                          # build BM25 index from indexed chunks
        results = rag.find_similar(query, top_k=5)
        antipatterns = rag.detect_antipatterns(code_text, "myfile.py")
    """

    def __init__(self, store_path: Path, index_engine: "CodeIndexEngine") -> None:
        self.store_path = store_path
        self.store_path.mkdir(parents=True, exist_ok=True)
        self._index = index_engine
        self._library = AntiPatternLibrary()

        self._bm25_path = store_path / "rag_bm25.pkl"
        self._meta_path = store_path / "rag_meta.pkl"

        self._bm25 = None
        self._meta: list[tuple[str, int, str]] = []  # (file_path, start_line, symbol_name)
        self._texts: list[str] = []  # raw chunk texts for Jaccard (AP-011)

    # ── Persistence ───────────────────────────────────────────────────────

    def _save(self) -> None:
        with open(self._bm25_path, "wb") as f:
            pickle.dump(self._bm25, f, protocol=pickle.HIGHEST_PROTOCOL)
        with open(self._meta_path, "wb") as f:
            pickle.dump((self._meta, self._texts), f, protocol=pickle.HIGHEST_PROTOCOL)

    def _load(self) -> bool:
        """Try to load BM25 index from disk. Returns True on success."""
        if not (self._bm25_path.exists() and self._meta_path.exists()):
            return False
        try:
            _require_bm25()  # ensure rank_bm25 is available
            with open(self._bm25_path, "rb") as f:
                self._bm25 = pickle.load(f)  # noqa: S301
            with open(self._meta_path, "rb") as f:
                self._meta, self._texts = pickle.load(f)  # noqa: S301
            return True
        except Exception:  # noqa: BLE001
            return False

    # ── Build / update ────────────────────────────────────────────────────

    def build(self, force: bool = False) -> None:
        """
        Build the BM25 index over all indexed code chunks.

        Pure Python, no ML dependencies. Rebuilds are always full but
        complete in well under one second for typical codebases.
        """
        try:
            BM25Okapi = _require_bm25()
        except ImportError:
            return  # degrade gracefully

        if not force and self._load():
            return  # already built and loaded

        chunks = self._index.all_chunks()
        if not chunks:
            return

        texts: list[str] = []
        meta: list[tuple[str, int, str]] = []

        for _cid, file_path, start_line, symbol_name, text in chunks:
            texts.append(text)
            meta.append((file_path, start_line, symbol_name))

        tokenized_corpus = [_tokenize(t) for t in texts]
        self._bm25 = BM25Okapi(tokenized_corpus)
        self._meta = meta
        self._texts = texts

        try:
            self._save()
        except Exception:  # noqa: BLE001
            pass  # non-fatal; results are still in memory

    def update(self, changed_files: list[Path] | None = None) -> None:
        """Rebuild the BM25 index (always full, fast)."""
        self.build(force=True)

    # ── Query API ─────────────────────────────────────────────────────────

    def _ensure_loaded(self) -> bool:
        if self._bm25 is not None:
            return True
        return self._load()

    def find_similar(self, code_text: str, top_k: int = 5) -> list[tuple[str, int, float]]:
        """
        Find the top-k most similar code chunks to *code_text*.

        Returns list of (file_path, start_line, normalized_bm25_score).
        Scores are normalized to [0, 1] relative to the top result.
        """
        if not code_text.strip():
            return []

        try:
            _require_bm25()
        except ImportError:
            return []

        if not self._ensure_loaded():
            return []

        try:
            query_tokens = _tokenize(code_text)
            if not query_tokens:
                return []

            raw_scores = self._bm25.get_scores(query_tokens)
            max_score = float(max(raw_scores)) if len(raw_scores) > 0 else 0.0
            if max_score <= 0:
                return []

            # Normalize scores to [0, 1] relative to the top result
            norm_scores = [float(s) / max_score for s in raw_scores]

            # Sort by score descending, take top_k
            scored = sorted(enumerate(norm_scores), key=lambda x: x[1], reverse=True)[:top_k]

            results = []
            for idx, score in scored:
                if score < 0.1:
                    break
                file_path, start_line, _symbol = self._meta[idx]
                results.append((file_path, start_line, round(score, 3)))
            return results
        except Exception:  # noqa: BLE001
            return []

    def detect_antipatterns(self, code_text: str, file_path: str, language: str = "python") -> list[AntiPattern]:
        """
        Detect anti-patterns in *code_text* using the pattern library,
        plus duplicate-chunk detection (AP-011) via Jaccard token similarity.
        """
        findings = self._library.scan(code_text, file_path, language)

        # AP-011: duplicate chunk detection via token-level Jaccard similarity
        if self._ensure_loaded() and self._texts:
            try:
                best_score = 0.0
                best_idx = 0
                for i, chunk_text in enumerate(self._texts):
                    score = _jaccard(code_text, chunk_text)
                    if score > best_score:
                        best_score = score
                        best_idx = i

                if best_score >= _SIMILARITY_THRESHOLD and self._meta:
                    similar_file, similar_line, _ = self._meta[best_idx]
                    if similar_file != file_path:
                        findings.append(AntiPattern(
                            pattern_id="AP-011",
                            name="duplicate-chunk",
                            severity=Severity.MEDIUM,
                            description=f"High similarity ({best_score:.0%}) with {similar_file}:{similar_line}.",
                            suggestion="Extract duplicated logic into a shared utility function or base class.",
                            file_path=file_path,
                            line=1,
                            context=f"Similar to {similar_file}:{similar_line}",
                        ))
            except Exception:  # noqa: BLE001
                pass

        return findings

    def detect_antipatterns_file(self, path: Path) -> list[AntiPattern]:
        """Convenience wrapper: detect anti-patterns in a file on disk."""
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            return []
        suffix = path.suffix.lower()
        lang_map = {".py": "python", ".js": "javascript", ".ts": "typescript",
                    ".rs": "rust", ".go": "go", ".java": "java"}
        language = lang_map.get(suffix, "unknown")
        return self.detect_antipatterns(text, str(path), language)

    def suggest_improvements(self, code_text: str) -> list[str]:
        """
        Return actionable improvement suggestions for *code_text*
        based on anti-patterns detected.
        """
        aps = self._library.scan(code_text, "<inline>")
        seen: set[str] = set()
        suggestions: list[str] = []
        for ap in sorted(aps, key=lambda x: {"critical": 0, "high": 1, "medium": 2, "low": 3}.get(x.severity.value, 4)):
            if ap.suggestion and ap.suggestion not in seen:
                seen.add(ap.suggestion)
                suggestions.append(f"[{ap.severity.value.upper()}] {ap.name}: {ap.suggestion}")
        return suggestions[:10]

    def project_antipatterns(self) -> list[AntiPattern]:
        """
        Scan all indexed chunks for anti-patterns.
        Returns a deduplicated, severity-sorted list.
        """
        chunks = self._index.all_chunks()
        all_findings: list[AntiPattern] = []
        seen: set[tuple[str, str, int]] = set()

        for _cid, file_path, start_line, _symbol, text in chunks:
            for ap in self._library.scan(text, file_path):
                key = (ap.pattern_id, file_path, ap.line)
                if key not in seen:
                    seen.add(key)
                    all_findings.append(ap)

        # Sort by severity then file
        sev_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
        all_findings.sort(key=lambda x: (sev_order.get(x.severity.value, 5), x.file_path, x.line))
        return all_findings

    def top_patterns_summary(self, top_n: int = 3) -> list[str]:
        """
        Return human-readable strings describing the most-used code patterns
        in the project (based on most-frequent symbol names in the index).
        """
        rows = self._index._conn.execute(
            "SELECT name, kind, COUNT(*) as cnt FROM symbols "
            "WHERE kind IN ('function', 'class') "
            "GROUP BY name, kind ORDER BY cnt DESC LIMIT ?",
            (top_n * 2,),
        ).fetchall()

        lines: list[str] = []
        seen_names: set[str] = set()
        for name, kind, cnt in rows:
            if name in seen_names or len(name) <= 2:
                continue
            seen_names.add(name)
            lines.append(f"- `{name}` ({kind}, used {cnt}x across project)")
            if len(lines) >= top_n:
                break
        return lines

    def context_token_cost(self) -> int:
        """Estimated token cost of the RAG patterns block injected into agent files."""
        # patterns block is ~300-500 tokens (small, targeted)
        lines = self.top_patterns_summary(3)
        aps = self.project_antipatterns()[:5]
        text = "\n".join(lines) + "\n".join(ap.description for ap in aps)
        return len(text) // 4
