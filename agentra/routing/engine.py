"""TaskClassifier + TaskRouter — RouteSmith-style intelligent model routing.

Instead of letting Copilot (or any agent) pick a model arbitrarily, this engine
classifies each task and routes it to the best model for the job:

    router = TaskRouter()
    result = router.route("design a distributed caching layer")
    print(result.purpose)          # "planning"
    print(result.capability_class) # "deep_reasoning"
    print(result.best_model("copilot"))  # "gpt-5.5"
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from agentra.models import (
    AGENT_PURPOSES,
    CAPABILITY_MODELS,
    PURPOSE_CAPABILITY_MAP,
    RouteResult,
    TaskComplexity,
)

if TYPE_CHECKING:
    from agentra.models import ProjectConfig


# ── Signal library ────────────────────────────────────────────────────────────
# Each purpose has weighted keyword signals.
# Higher weight → stronger evidence for that purpose.
#
# Signals are matched case-insensitively against the task text.
# Phrase-level signals (> 1 word) score higher than single-word signals.

_SIGNALS: dict[str, list[tuple[str, float]]] = {
    "planning": [
        ("architect", 2.0), ("architecture", 2.0), ("system design", 2.5),
        ("design a", 1.5), ("design the", 1.5), ("plan", 1.2),
        ("roadmap", 1.8), ("structure", 1.0), ("high-level", 1.5),
        ("how should i", 1.2), ("approach", 1.0), ("strategy", 1.5),
        ("diagram", 1.2), ("blueprint", 1.8), ("scaffold", 1.0),
        ("monolith", 1.2), ("microservice", 1.2), ("distributed", 1.0),
    ],
    "reasoning": [
        ("why", 0.8), ("explain why", 1.8), ("understand", 1.0),
        ("analyze", 1.5), ("analyse", 1.5), ("evaluate", 1.5),
        ("compare", 1.5), ("trade-off", 1.8), ("tradeoff", 1.8),
        ("difference between", 1.8), ("pros and cons", 2.0),
        ("root cause", 2.0), ("investigate", 1.5), ("diagnose", 1.5),
        ("infer", 1.2), ("reason", 1.0), ("logic", 0.8),
        ("how does", 1.0), ("what happens when", 1.2),
    ],
    "review": [
        ("review", 1.5), ("audit", 2.0), ("security review", 2.5),
        ("code review", 2.5), ("vulnerability", 2.0), ("cve", 2.0),
        ("owasp", 2.0), ("check for", 1.2), ("find bugs", 1.5),
        ("spot", 1.0), ("critique", 1.5), ("feedback on", 1.2),
        ("look for issues", 1.5), ("is this secure", 2.0),
        ("injection", 1.5), ("xss", 1.8), ("sql injection", 2.0),
    ],
    "coding": [
        ("implement", 1.5), ("write", 1.0), ("create", 0.8),
        ("build", 0.8), ("add", 0.5), ("generate", 0.8),
        ("code for", 1.5), ("function that", 1.5), ("class that", 1.5),
        ("endpoint", 1.2), ("api", 0.8), ("feature", 0.8),
        ("fix the bug", 1.8), ("fix this", 1.2), ("debug", 1.5),
        ("make it work", 1.5), ("integrate", 1.0), ("connect", 0.8),
        ("parse", 1.0), ("serialize", 1.0), ("query", 0.8),
    ],
    "testing": [
        ("test", 1.0), ("unit test", 2.0), ("integration test", 2.0),
        ("pytest", 2.0), ("jest", 2.0), ("vitest", 2.0),
        ("mock", 1.5), ("stub", 1.5), ("assert", 1.5),
        ("coverage", 1.5), ("tdd", 2.0), ("spec", 1.2),
        ("test case", 2.0), ("fixture", 1.5), ("e2e", 1.8),
        ("end-to-end", 1.8), ("regression", 1.5), ("fuzz", 1.5),
    ],
    "refactoring": [
        ("refactor", 2.0), ("clean up", 1.5), ("clean this", 1.5),
        ("reorganize", 1.5), ("simplify", 1.5), ("extract", 1.2),
        ("dry", 1.5), ("don't repeat", 1.5), ("rename", 1.0),
        ("move", 0.8), ("split", 1.0), ("merge", 0.8),
        ("improve readability", 2.0), ("reduce complexity", 1.8),
        ("technical debt", 2.0), ("code smell", 1.8), ("decouple", 1.5),
    ],
    "documentation": [
        ("document", 1.5), ("docstring", 2.0), ("readme", 2.0),
        ("comment", 1.0), ("describe", 1.0), ("explain", 1.2),
        ("api doc", 2.0), ("swagger", 1.8), ("openapi", 1.8),
        ("markdown", 1.2), ("wiki", 1.5), ("changelog", 1.5),
        ("jsdoc", 2.0), ("sphinx", 2.0), ("mkdocs", 2.0),
    ],
    "formatting": [
        ("format", 1.5), ("lint", 1.5), ("style", 1.0),
        ("indent", 1.5), ("whitespace", 1.5), ("prettier", 2.0),
        ("ruff", 2.0), ("black", 1.8), ("isort", 1.8),
        ("trailing", 1.2), ("sort imports", 1.8), ("fix formatting", 2.0),
        ("autoformat", 2.0), ("pep8", 1.8), ("eslint", 1.8),
    ],
    "general": [
        # catch-all — very low weights, only win if nothing else matches
        ("help", 0.3), ("question", 0.3), ("how", 0.3), ("what", 0.3),
    ],
}

# ── Complexity signals ─────────────────────────────────────────────────────────
# Increase complexity score when these appear.
_HIGH_COMPLEXITY_SIGNALS: list[str] = [
    "production", "enterprise", "scalable", "distributed", "microservice",
    "multi-tenant", "concurrent", "async", "rate limiting", "caching",
    "performance", "security", "authentication", "authorization",
    "kubernetes", "docker", "ci/cd", "pipeline", "migration",
    "across files", "entire codebase", "multiple modules", "full system",
    "end-to-end", "architecture", "design pattern",
]

_LOW_COMPLEXITY_SIGNALS: list[str] = [
    "simple", "quick", "small", "one line", "single function",
    "snippet", "example", "hello world", "basic", "trivial",
]


# ── TaskClassifier ────────────────────────────────────────────────────────────

class TaskClassifier:
    """Classify a task string into (purpose, capability_class, complexity).

    Uses weighted keyword-signal scoring — no ML, zero latency.
    """

    def classify(self, task: str) -> tuple[str, str, TaskComplexity, dict[str, float]]:
        """Return (purpose, capability_class, complexity, scores)."""
        task_lower = task.lower()
        scores: dict[str, float] = {}

        for purpose, signals in _SIGNALS.items():
            total = 0.0
            for phrase, weight in signals:
                # Phrase-level match: count non-overlapping occurrences
                count = len(re.findall(re.escape(phrase), task_lower))
                total += count * weight
            scores[purpose] = round(total, 3)

        # Pick highest-scoring purpose; fall back to "general"
        purpose = max(scores, key=lambda p: scores[p])
        if scores[purpose] == 0.0:
            purpose = "general"

        capability_class = PURPOSE_CAPABILITY_MAP.get(purpose, "balanced")

        # Complexity estimation
        complexity = self._estimate_complexity(task_lower, capability_class)

        # Upgrade capability class for high-complexity tasks
        if complexity == TaskComplexity.HIGH and capability_class in ("coding", "balanced"):
            capability_class = "deep_reasoning"

        return purpose, capability_class, complexity, scores

    def _estimate_complexity(self, task_lower: str, capability_class: str) -> TaskComplexity:
        """Estimate task complexity from text signals and length."""
        word_count = len(task_lower.split())

        high_hits = sum(1 for s in _HIGH_COMPLEXITY_SIGNALS if s in task_lower)
        low_hits = sum(1 for s in _LOW_COMPLEXITY_SIGNALS if s in task_lower)

        # Deep reasoning always starts at medium
        if capability_class == "deep_reasoning":
            if high_hits >= 2 or word_count > 80:
                return TaskComplexity.HIGH
            return TaskComplexity.MEDIUM

        if low_hits > 0 and high_hits == 0 and word_count < 25:
            return TaskComplexity.LOW
        if high_hits >= 2 or word_count > 60:
            return TaskComplexity.HIGH
        if word_count > 20 or high_hits == 1:
            return TaskComplexity.MEDIUM
        return TaskComplexity.LOW


# ── TaskRouter ─────────────────────────────────────────────────────────────────

class TaskRouter:
    """Route a task to the best model per agent platform.

    Wraps TaskClassifier and resolves models using the existing
    CAPABILITY_MODELS + CAPABILITY_FALLBACK_CHAINS tables from models.py.
    """

    def __init__(self, restricted: dict[str, set[str]] | None = None) -> None:
        """
        Args:
            restricted: Per-platform set of model names to skip (e.g. enterprise
                        restrictions). ``{"copilot": {"gpt-5.5"}}``
        """
        self._classifier = TaskClassifier()
        self._restricted = restricted or {}

    def route(
        self,
        task: str,
        platforms: list[str] | None = None,
        config: "ProjectConfig | None" = None,
    ) -> RouteResult:
        """Classify *task* and return the best model per platform.

        Args:
            task: Natural language task description.
            platforms: Platforms to resolve models for. Defaults to all known platforms.
            config: Optional project config; if provided, respects
                    ``model_purpose_preferences`` overrides.
        """

        purpose, cap_class, complexity, scores = self._classifier.classify(task)

        target_platforms = platforms or list(CAPABILITY_MODELS.keys())

        models: dict[str, str] = {}
        for platform in target_platforms:
            # Prefer explicit user override in config (purpose-level)
            if config and platform in config.model_purpose_preferences:
                override = config.model_purpose_preferences[platform].get(purpose)
                if override:
                    models[platform] = override
                    continue

            restricted = self._restricted.get(platform, set())
            from agentra.models import resolve_model_with_fallback
            models[platform] = resolve_model_with_fallback(platform, cap_class, restricted)

        rationale = _build_rationale(task, purpose, cap_class, complexity)

        return RouteResult(
            task_preview=task[:120].strip(),
            purpose=purpose,
            capability_class=cap_class,
            complexity=complexity,
            scores=scores,
            models=models,
            rationale=rationale,
        )

    def route_with_config(self, task: str, config: "ProjectConfig") -> RouteResult:
        """Route using config's agent list and per-purpose overrides."""
        platforms = [ag.value for ag in config.agents]
        return self.route(task, platforms=platforms, config=config)


# ── Routing decision table (for instruction file injection) ───────────────────

def build_routing_table(
    platform: str,
    config: "ProjectConfig | None" = None,
) -> dict[str, str]:
    """Return {purpose: model} decision table for a platform.

    Respects purpose-level config overrides.  Used by the adapter to
    generate the static routing block embedded in instruction files.
    """
    from agentra.models import resolve_model_with_fallback

    cap_models = CAPABILITY_MODELS.get(platform, {})
    if not cap_models:
        return {}

    table: dict[str, str] = {}
    user_overrides = (config.model_purpose_preferences.get(platform, {}) if config else {})

    for purpose in AGENT_PURPOSES:
        if purpose in user_overrides:
            table[purpose] = user_overrides[purpose]
        else:
            cap_class = PURPOSE_CAPABILITY_MAP.get(purpose, "balanced")
            table[purpose] = resolve_model_with_fallback(platform, cap_class, set())

    return table


# ── Helpers ───────────────────────────────────────────────────────────────────

def _build_rationale(
    task: str,
    purpose: str,
    cap_class: str,
    complexity: TaskComplexity,
) -> str:
    rationale_parts = [
        f"Task classified as **{purpose}** → capability class **{cap_class}**.",
        f"Complexity: **{complexity.value}**.",
    ]
    if complexity == TaskComplexity.HIGH and cap_class == "deep_reasoning":
        rationale_parts.append(
            "High-complexity signals detected — upgraded to deep_reasoning model."
        )
    return " ".join(rationale_parts)
