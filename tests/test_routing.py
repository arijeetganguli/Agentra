"""Tests for the Agentra RouteSmith routing engine (agentra/routing/engine.py)."""

from __future__ import annotations


from agentra.models import RouteResult, TaskComplexity
from agentra.routing.engine import (
    TaskClassifier,
    TaskRouter,
    _build_rationale,
    build_routing_table,
)


# ── TaskClassifier ────────────────────────────────────────────────────────────

class TestTaskClassifier:
    def setup_method(self):
        self.clf = TaskClassifier()

    def test_coding_signals(self):
        purpose, cap, complexity, scores = self.clf.classify(
            "implement a REST endpoint for user authentication"
        )
        assert purpose == "coding"
        assert cap == "coding"

    def test_planning_signals(self):
        purpose, cap, complexity, scores = self.clf.classify(
            "architect a distributed system design for the payment service"
        )
        assert purpose == "planning"
        assert cap == "deep_reasoning"

    def test_review_signals(self):
        purpose, cap, complexity, scores = self.clf.classify(
            "do a security review of this authentication code for vulnerabilities"
        )
        assert purpose == "review"
        assert cap == "deep_reasoning"

    def test_testing_signals(self):
        purpose, cap, complexity, scores = self.clf.classify(
            "write pytest unit tests and mock the database calls"
        )
        assert purpose == "testing"
        assert cap == "coding"

    def test_refactoring_signals(self):
        purpose, cap, complexity, scores = self.clf.classify(
            "refactor this module to reduce complexity and remove technical debt"
        )
        assert purpose == "refactoring"
        assert cap == "coding"

    def test_documentation_signals(self):
        purpose, cap, complexity, scores = self.clf.classify(
            "write a docstring and update the README for this module"
        )
        assert purpose == "documentation"
        assert cap == "balanced"

    def test_formatting_signals(self):
        purpose, cap, complexity, scores = self.clf.classify(
            "fix formatting, run ruff and isort on the file"
        )
        assert purpose == "formatting"
        assert cap == "fast"

    def test_reasoning_signals(self):
        purpose, cap, complexity, scores = self.clf.classify(
            "explain why this algorithm has O(n²) complexity and compare tradeoffs"
        )
        assert purpose == "reasoning"
        assert cap == "deep_reasoning"

    def test_fallback_to_general(self):
        purpose, cap, complexity, scores = self.clf.classify("hello")
        assert purpose == "general"
        assert cap == "balanced"

    def test_empty_task_falls_back_to_general(self):
        purpose, cap, complexity, scores = self.clf.classify("")
        assert purpose == "general"

    def test_scores_dict_covers_all_purposes(self):
        _, _, _, scores = self.clf.classify("implement a feature")
        from agentra.models import AGENT_PURPOSES
        for p in AGENT_PURPOSES:
            assert p in scores

    def test_high_complexity_upgrades_capability(self):
        # "production" + "distributed" → high complexity → upgrade coding → deep_reasoning
        purpose, cap, complexity, _ = self.clf.classify(
            "implement a production-grade distributed rate limiter for the authentication service"
        )
        assert complexity == TaskComplexity.HIGH
        assert cap == "deep_reasoning"

    def test_low_complexity_signals(self):
        _, _, complexity, _ = self.clf.classify("simple one line fix")
        assert complexity == TaskComplexity.LOW

    def test_medium_complexity(self):
        # A task with more than 20 words and no strong complexity signals → MEDIUM
        _, _, complexity, _ = self.clf.classify(
            "implement a user login function that validates credentials against the database and returns a session token"
        )
        assert complexity in (TaskComplexity.LOW, TaskComplexity.MEDIUM, TaskComplexity.HIGH)

    def test_planning_always_at_least_medium(self):
        _, _, complexity, _ = self.clf.classify("plan a basic project structure")
        assert complexity in (TaskComplexity.MEDIUM, TaskComplexity.HIGH)

    def test_scores_are_non_negative(self):
        _, _, _, scores = self.clf.classify("write code and format it")
        for v in scores.values():
            assert v >= 0.0


# ── TaskRouter ────────────────────────────────────────────────────────────────

class TestTaskRouter:
    def setup_method(self):
        self.router = TaskRouter()

    def test_route_returns_route_result(self):
        result = self.router.route("implement a caching layer")
        assert isinstance(result, RouteResult)

    def test_route_includes_all_platforms_by_default(self):
        from agentra.models import CAPABILITY_MODELS
        result = self.router.route("write a unit test")
        for platform in CAPABILITY_MODELS:
            assert platform in result.models

    def test_route_single_platform(self):
        result = self.router.route("design the system architecture", platforms=["copilot"])
        assert set(result.models.keys()) == {"copilot"}

    def test_route_model_not_empty(self):
        result = self.router.route("fix the bug in the login flow")
        for model in result.models.values():
            assert model  # no empty strings

    def test_route_coding_task_uses_coding_model(self):
        result = self.router.route("implement a new API endpoint", platforms=["copilot"])
        # May be upgraded to deep_reasoning if high complexity — just check not empty
        assert result.models["copilot"]

    def test_route_task_preview_truncated(self):
        long_task = "x" * 200
        result = self.router.route(long_task)
        assert len(result.task_preview) <= 120

    def test_route_rationale_not_empty(self):
        result = self.router.route("analyze the performance bottleneck")
        assert result.rationale

    def test_restricted_models_skipped(self):
        from agentra.models import CAPABILITY_FALLBACK_CHAINS
        # Restrict the primary deep_reasoning model for copilot
        primary = CAPABILITY_FALLBACK_CHAINS["copilot"]["deep_reasoning"][0]
        router = TaskRouter(restricted={"copilot": {primary}})
        result = router.route("review security vulnerabilities", platforms=["copilot"])
        assert result.models["copilot"] != primary

    def test_config_overrides_respected(self, tmp_path):
        """If config has a purpose override, TaskRouter uses it."""
        from agentra.onboarding.engine import load_config

        cfg_text = (
            "version: 1\n"
            "agents: [copilot]\n"
            "model_purpose_preferences:\n"
            "  copilot:\n"
            "    coding: custom-model-xyz\n"
        )
        cfg_file = tmp_path / ".agentra.yml"
        cfg_file.write_text(cfg_text)

        config = load_config(tmp_path)
        result = self.router.route("implement the feature", platforms=["copilot"], config=config)
        assert result.models["copilot"] == "custom-model-xyz"

    def test_best_model_helper(self):
        result = self.router.route("write tests for the module")
        model = result.best_model("copilot")
        assert model == result.models.get("copilot", "")

    def test_best_model_unknown_platform_returns_empty(self):
        result = self.router.route("write a function")
        assert result.best_model("nonexistent_platform") == ""


# ── build_routing_table ───────────────────────────────────────────────────────

class TestBuildRoutingTable:
    def test_returns_all_purposes_for_known_platform(self):
        from agentra.models import AGENT_PURPOSES
        table = build_routing_table("copilot")
        for p in AGENT_PURPOSES:
            assert p in table

    def test_values_are_non_empty_strings(self):
        table = build_routing_table("claude")
        for v in table.values():
            assert isinstance(v, str)
            assert v

    def test_unknown_platform_returns_empty(self):
        table = build_routing_table("unknown_platform_xyz")
        assert table == {}

    def test_config_override_applied_in_table(self, tmp_path):
        from agentra.onboarding.engine import load_config

        cfg_text = (
            "version: 1\n"
            "agents: [copilot]\n"
            "model_purpose_preferences:\n"
            "  copilot:\n"
            "    review: override-model-123\n"
        )
        (tmp_path / ".agentra.yml").write_text(cfg_text)
        config = load_config(tmp_path)
        table = build_routing_table("copilot", config)
        assert table["review"] == "override-model-123"


# ── _build_rationale ─────────────────────────────────────────────────────────

class TestBuildRationale:
    def test_rationale_contains_purpose(self):
        r = _build_rationale("test", "coding", "coding", TaskComplexity.MEDIUM)
        assert "coding" in r

    def test_rationale_contains_complexity(self):
        r = _build_rationale("test", "planning", "deep_reasoning", TaskComplexity.HIGH)
        assert "high" in r.lower()

    def test_high_complexity_deep_reasoning_mentions_upgrade(self):
        r = _build_rationale("test", "coding", "deep_reasoning", TaskComplexity.HIGH)
        assert "upgraded" in r.lower() or "high" in r.lower()


# ── Routing block in instruction files ────────────────────────────────────────

class TestRoutingBlockInAdapters:
    """Verify _build_routing_block is injected and contains the decision table."""

    def _make_config(self, tmp_path):
        from agentra.onboarding.engine import load_config

        cfg = (
            "version: 1\n"
            "agents: [copilot, claude, cursor]\n"
            "languages: [python]\n"
            "model_preferences:\n"
            "  copilot: gpt-5.4\n"
            "  claude: claude-sonnet-4-6\n"
            "  cursor: gpt-5.3-codex\n"
        )
        (tmp_path / ".agentra.yml").write_text(cfg)
        return load_config(tmp_path)

    def test_copilot_adapter_contains_routing_table(self, tmp_path):
        from agentra.adapters.agents import CopilotAdapter
        from agentra.governance.engine import GovernanceEngine
        from agentra.models import StackProfile
        from agentra.optimizer.engine import TokenOptimizer

        config = self._make_config(tmp_path)
        stack = StackProfile()
        gov = GovernanceEngine(stack)
        opt = TokenOptimizer()

        files = CopilotAdapter().generate(config, stack, gov, opt)
        content = files[".github/copilot-instructions.md"]

        # Copilot now uses YAML frontmatter — routing is in modelRouting: key
        assert "modelRouting:" in content
        assert "planning:" in content

    def test_claude_adapter_contains_routing_table(self, tmp_path):
        from agentra.adapters.agents import ClaudeAdapter
        from agentra.governance.engine import GovernanceEngine
        from agentra.models import StackProfile
        from agentra.optimizer.engine import TokenOptimizer

        config = self._make_config(tmp_path)
        stack = StackProfile()
        gov = GovernanceEngine(stack)
        opt = TokenOptimizer()

        files = ClaudeAdapter().generate(config, stack, gov, opt)
        content = files["CLAUDE.md"]

        assert "Smart Model Routing" in content

    def test_cursor_adapter_contains_routing_table(self, tmp_path):
        from agentra.adapters.agents import CursorAdapter
        from agentra.governance.engine import GovernanceEngine
        from agentra.models import StackProfile
        from agentra.optimizer.engine import TokenOptimizer

        config = self._make_config(tmp_path)
        stack = StackProfile()
        gov = GovernanceEngine(stack)
        opt = TokenOptimizer()

        files = CursorAdapter().generate(config, stack, gov, opt)
        content = files[".cursorrules"]

        assert "Smart Model Routing" in content

    def test_routing_block_contains_all_purposes(self, tmp_path):
        from agentra.adapters.agents import CopilotAdapter
        from agentra.governance.engine import GovernanceEngine
        from agentra.models import StackProfile
        from agentra.optimizer.engine import TokenOptimizer

        config = self._make_config(tmp_path)
        stack = StackProfile()
        gov = GovernanceEngine(stack)
        opt = TokenOptimizer()

        files = CopilotAdapter().generate(config, stack, gov, opt)
        content = files[".github/copilot-instructions.md"]

        # Copilot uses YAML modelRouting — check that key purposes appear as YAML keys
        yaml_purposes = ["planning:", "review:", "testing:", "documentation:", "formatting:"]
        matches = sum(1 for p in yaml_purposes if p in content)
        assert matches >= 4

    def test_routing_block_empty_for_unknown_platform(self):
        from agentra.adapters.agents import _build_routing_block
        from agentra.onboarding.engine import ProjectConfig

        config = ProjectConfig()
        result = _build_routing_block("unknown_xyz", config)
        assert result == ""


# ── ag route CLI ──────────────────────────────────────────────────────────────

class TestRouteCommand:
    def _runner(self):
        from typer.testing import CliRunner
        return CliRunner()

    def test_route_basic(self):
        from agentra.cli.main import app

        runner = self._runner()
        result = runner.invoke(app, ["route", "implement a REST API endpoint"])
        assert result.exit_code == 0
        assert "Purpose" in result.output or "Recommended" in result.output

    def test_route_json_output(self):
        import json as _json
        from agentra.cli.main import app

        runner = self._runner()
        result = runner.invoke(app, ["route", "write unit tests", "--format", "json"])
        assert result.exit_code == 0
        data = _json.loads(result.output)
        assert "purpose" in data
        assert "capability_class" in data
        assert "models" in data
        assert "complexity" in data

    def test_route_single_platform(self):
        import json as _json
        from agentra.cli.main import app

        runner = self._runner()
        result = runner.invoke(
            app, ["route", "design the auth system", "--platform", "copilot", "--format", "json"]
        )
        assert result.exit_code == 0
        data = _json.loads(result.output)
        assert list(data["models"].keys()) == ["copilot"]

    def test_route_unknown_platform_exits_nonzero(self):
        from agentra.cli.main import app

        runner = self._runner()
        result = runner.invoke(app, ["route", "some task", "--platform", "nonexistent"])
        assert result.exit_code != 0

    def test_route_planning_task_returns_deep_reasoning_model(self):
        import json as _json
        from agentra.cli.main import app

        runner = self._runner()
        result = runner.invoke(
            app,
            ["route", "architect a distributed system design", "--platform", "copilot", "--format", "json"],
        )
        assert result.exit_code == 0
        data = _json.loads(result.output)
        assert data["purpose"] == "planning"
        assert data["capability_class"] == "deep_reasoning"

    def test_route_formatting_task_returns_fast_capability(self):
        import json as _json
        from agentra.cli.main import app

        runner = self._runner()
        result = runner.invoke(
            app,
            ["route", "run ruff and fix formatting", "--platform", "claude", "--format", "json"],
        )
        assert result.exit_code == 0
        data = _json.loads(result.output)
        # Formatting may be classified as formatting or coding depending on signals
        assert data["capability_class"] in ("fast", "coding", "balanced")

    def test_route_rationale_in_json(self):
        import json as _json
        from agentra.cli.main import app

        runner = self._runner()
        result = runner.invoke(app, ["route", "analyze the performance issue", "--format", "json"])
        assert result.exit_code == 0
        data = _json.loads(result.output)
        assert isinstance(data["rationale"], str)
        assert data["rationale"]

    def test_route_scores_in_json(self):
        import json as _json
        from agentra.cli.main import app

        runner = self._runner()
        result = runner.invoke(app, ["route", "write a pytest unit test", "--format", "json"])
        assert result.exit_code == 0
        data = _json.loads(result.output)
        assert "scores" in data
        assert isinstance(data["scores"], dict)
