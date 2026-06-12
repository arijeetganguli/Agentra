"""Tests for the Agent Integration Adapters."""


import pytest

from agentra.adapters.agents import (
    _parse_md_sections,
    generate_for_agents,
    merge_instruction_content,
    write_agent_files,
)
from agentra.governance.engine import GovernanceEngine
from agentra.models import AgentPlatform, ProjectConfig, StackProfile
from agentra.optimizer.engine import TokenOptimizer


@pytest.fixture
def config() -> ProjectConfig:
    return ProjectConfig(
        project_name="test-project",
        languages=["python"],
        frameworks=["fastapi"],
        agents=[AgentPlatform.CLAUDE, AgentPlatform.CURSOR, AgentPlatform.COPILOT],
        skills=["fastapi", "karpathy"],
    )


@pytest.fixture
def stack() -> StackProfile:
    from agentra.models import DetectedComponent
    return StackProfile(
        languages=[DetectedComponent(name="python", confidence=0.9, source="pyproject.toml")],
        frameworks=[DetectedComponent(name="fastapi", confidence=0.85, source="requirements.txt")],
    )


class TestAdapters:
    def test_generates_claude_md(self, config, stack):
        gov = GovernanceEngine(stack)
        opt = TokenOptimizer()
        files = generate_for_agents(config.agents, config, stack, gov, opt)
        assert "CLAUDE.md" in files
        assert "Agentra" in files["CLAUDE.md"]

    def test_generates_cursorrules(self, config, stack):
        gov = GovernanceEngine(stack)
        opt = TokenOptimizer()
        files = generate_for_agents(config.agents, config, stack, gov, opt)
        assert ".cursorrules" in files

    def test_generates_copilot(self, config, stack):
        gov = GovernanceEngine(stack)
        opt = TokenOptimizer()
        files = generate_for_agents(config.agents, config, stack, gov, opt)
        assert ".github/copilot-instructions.md" in files

    def test_always_generates_agents_md(self, config, stack):
        gov = GovernanceEngine(stack)
        opt = TokenOptimizer()
        files = generate_for_agents(config.agents, config, stack, gov, opt)
        assert "AGENTS.md" in files

    def test_write_files(self, config, stack, tmp_path):
        gov = GovernanceEngine(stack)
        opt = TokenOptimizer()
        files = generate_for_agents(config.agents, config, stack, gov, opt)
        written = write_agent_files(tmp_path, files)
        assert len(written) > 0
        for f in written:
            assert f.exists()

    def test_generated_content_has_security(self, config, stack):
        gov = GovernanceEngine(stack)
        opt = TokenOptimizer()
        files = generate_for_agents(config.agents, config, stack, gov, opt)
        for _, content in files.items():
            assert "Security" in content or "security" in content or "conventions" in content.lower()

    def test_skills_block_shows_invocation_hints(self, stack, tmp_path):
        """Skills block must reference Copilot and Claude Code invocation syntax."""
        config = ProjectConfig(
            project_name="test",
            languages=["python"],
            frameworks=["fastapi"],
            agents=[AgentPlatform.CLAUDE],
            skills=["fastapi"],
        )
        gov = GovernanceEngine(stack)
        opt = TokenOptimizer()
        files = generate_for_agents(config.agents, config, stack, gov, opt)
        claude_md = files["CLAUDE.md"]
        assert "#fastapi" in claude_md
        assert "/skill fastapi" in claude_md

    def test_generated_content_has_response_style_guidance(self, config, stack):
        gov = GovernanceEngine(stack)
        opt = TokenOptimizer()
        files = generate_for_agents(config.agents, config, stack, gov, opt)
        assert "## Response Style" in files["CLAUDE.md"]
        assert "Short flat bullets by default" in files["CLAUDE.md"]
        # Copilot now uses YAML frontmatter — responseStyle is a YAML key
        assert "responseStyle:" in files[".github/copilot-instructions.md"]
        assert "tokenSaver: true" in files[".github/copilot-instructions.md"]
        assert "## Response Style" in files["AGENTS.md"]


class TestParseMdSections:
    def test_preamble_only(self):
        content = "just preamble text\nno headings\n"
        secs = _parse_md_sections(content)
        assert secs == [(None, content)]

    def test_single_section(self):
        content = "preamble\n## Section One\nbody\n"
        secs = _parse_md_sections(content)
        assert secs[0] == (None, "preamble\n")
        assert secs[1][0] == "## Section One"
        assert "body" in secs[1][1]

    def test_multiple_sections(self):
        content = "pre\n## Alpha\nalpha body\n## Beta\nbeta body\n"
        secs = _parse_md_sections(content)
        assert len(secs) == 3
        titles = [h[3:].strip() if h else None for h, _ in secs]
        assert titles == [None, "Alpha", "Beta"]


class TestMergeInstructionContent:
    def _make_existing(self, extra_section: str = "") -> str:
        return (
            "# Agentra old header\n\n"
            "## Detected Stack\n- python\n"
            "## Security & Governance\nold security rules\n"
            + extra_section
        )

    def _make_new(self) -> str:
        return (
            "# Agentra new header\n\n"
            "## Detected Stack\n- python, typescript\n"
            "## Security & Governance\nnew security rules\n"
            "## Active Skills\n- fastapi\n"
        )

    def test_agentra_sections_updated(self):
        result = merge_instruction_content(self._make_existing(), self._make_new())
        assert "new security rules" in result
        assert "old security rules" not in result
        assert "python, typescript" in result

    def test_user_sections_preserved(self):
        existing = self._make_existing("## My Custom Section\ncustom content\n")
        result = merge_instruction_content(existing, self._make_new())
        assert "My Custom Section" in result
        assert "custom content" in result

    def test_new_agentra_sections_appended(self):
        result = merge_instruction_content(self._make_existing(), self._make_new())
        assert "## Active Skills" in result

    def test_preamble_replaced(self):
        result = merge_instruction_content(self._make_existing(), self._make_new())
        assert "new header" in result
        assert "old header" not in result

    def test_idempotent_on_same_content(self):
        new = self._make_new()
        result = merge_instruction_content(new, new)
        # Round-tripping same content should stay stable
        assert "new security rules" in result
        assert "## Active Skills" in result


class TestWriteAgentFilesMerge:
    def test_merge_preserves_user_section(self, config, stack, tmp_path):
        gov = GovernanceEngine(stack)
        opt = TokenOptimizer()

        # First write
        files = generate_for_agents(config.agents, config, stack, gov, opt)
        write_agent_files(tmp_path, files)

        # User adds a custom section to CLAUDE.md
        claude_path = tmp_path / "CLAUDE.md"
        existing = claude_path.read_text(encoding="utf-8")
        claude_path.write_text(existing + "\n## My Project Notes\nKeep this!\n", encoding="utf-8")

        # Second write (re-init) should preserve user section
        write_agent_files(tmp_path, files)
        merged = claude_path.read_text(encoding="utf-8")
        assert "My Project Notes" in merged
        assert "Keep this!" in merged

    def test_no_merge_flag_overwrites(self, config, stack, tmp_path):
        gov = GovernanceEngine(stack)
        opt = TokenOptimizer()
        files = generate_for_agents(config.agents, config, stack, gov, opt)
        write_agent_files(tmp_path, files)

        claude_path = tmp_path / "CLAUDE.md"
        claude_path.write_text("## My Custom\ncustom\n", encoding="utf-8")

        write_agent_files(tmp_path, files, merge=False)
        content = claude_path.read_text(encoding="utf-8")
        assert "My Custom" not in content
