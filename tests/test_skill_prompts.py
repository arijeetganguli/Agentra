"""Tests for the Skill Prompt Generator."""


import pytest

from agentra.models import Skill
from agentra.skills.prompts import SkillPromptGenerator, _claude_skill, _copilot_prompt
from agentra.skills.registry import BUILTIN_SKILLS


@pytest.fixture
def sample_skill() -> Skill:
    return BUILTIN_SKILLS["fastapi"]


@pytest.fixture
def generator() -> SkillPromptGenerator:
    return SkillPromptGenerator()


class TestCopilotPrompt:
    def test_has_frontmatter(self, sample_skill):
        content = _copilot_prompt(sample_skill)
        assert content.startswith("---\n")
        assert "mode: 'agent'" in content
        assert "description:" in content

    def test_contains_skill_name(self, sample_skill):
        content = _copilot_prompt(sample_skill)
        assert sample_skill.name in content

    def test_contains_instructions(self, sample_skill):
        content = _copilot_prompt(sample_skill)
        assert "FastAPI" in content

    def test_policies_included_when_present(self, sample_skill):
        content = _copilot_prompt(sample_skill)
        for policy in sample_skill.policies:
            assert policy in content

    def test_no_policies_section_when_empty(self):
        skill = Skill(
            id="no-pol",
            name="No Policies",
            description="desc",
            stacks=["python"],
            instructions="Do something.",
        )
        content = _copilot_prompt(skill)
        assert "Governance" not in content


class TestClaudeSkill:
    def test_has_heading(self, sample_skill):
        content = _claude_skill(sample_skill)
        assert content.startswith(f"# {sample_skill.name}")

    def test_contains_instructions(self, sample_skill):
        content = _claude_skill(sample_skill)
        assert "FastAPI" in content


class TestSkillPromptGeneratorFileMap:
    def test_returns_both_platforms(self, generator, sample_skill):
        result = generator.file_map([sample_skill])
        assert f".github/prompts/{sample_skill.id}.prompt.md" in result
        assert f".claude/skills/{sample_skill.id}/SKILL.md" in result

    def test_copilot_prompt_valid(self, generator, sample_skill):
        result = generator.file_map([sample_skill])
        content = result[f".github/prompts/{sample_skill.id}.prompt.md"]
        assert "mode: 'agent'" in content

    def test_multiple_skills(self, generator):
        skills = [BUILTIN_SKILLS["fastapi"], BUILTIN_SKILLS["postgresql"]]
        result = generator.file_map(skills)
        assert len(result) == 4  # 2 skills × 2 platforms


class TestSkillPromptGeneratorWrite:
    def test_writes_copilot_files(self, generator, sample_skill, tmp_path):
        written = generator.generate([sample_skill], tmp_path, copilot=True, claude=False)
        assert len(written) == 1
        fp = written[0]
        assert fp.exists()
        assert fp.suffix == ".md"
        assert "prompts" in str(fp)

    def test_writes_claude_files(self, generator, sample_skill, tmp_path):
        written = generator.generate([sample_skill], tmp_path, copilot=False, claude=True)
        assert len(written) == 1
        fp = written[0]
        assert fp.exists()
        assert fp.name == "SKILL.md"

    def test_writes_both_platforms(self, generator, sample_skill, tmp_path):
        written = generator.generate([sample_skill], tmp_path)
        assert len(written) == 2
        names = {fp.name for fp in written}
        assert "SKILL.md" in names
        assert f"{sample_skill.id}.prompt.md" in names

    def test_creates_parent_dirs(self, generator, sample_skill, tmp_path):
        written = generator.generate([sample_skill], tmp_path)
        for fp in written:
            assert fp.parent.exists()

    def test_all_builtin_skills_generate_cleanly(self, generator, tmp_path):
        skills = list(BUILTIN_SKILLS.values())
        written = generator.generate(skills, tmp_path)
        assert len(written) == len(skills) * 2
        for fp in written:
            assert fp.exists()
            content = fp.read_text(encoding="utf-8")
            assert len(content) > 10  # non-empty


class TestSkillsCLI:
    def test_skills_list(self, tmp_path):
        from typer.testing import CliRunner
        from agentra.cli.main import app

        runner = CliRunner()
        result = runner.invoke(app, ["skills", "list", "--path", str(tmp_path)])
        assert result.exit_code == 0
        assert "fastapi" in result.output.lower()

    def test_skills_list_json(self, tmp_path):
        import json
        from typer.testing import CliRunner
        from agentra.cli.main import app

        runner = CliRunner()
        result = runner.invoke(app, ["skills", "list", "--path", str(tmp_path), "--format", "json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, list)
        ids = {item["id"] for item in data}
        assert "fastapi" in ids

    def test_skills_generate_requires_config_or_flag(self, tmp_path):
        from typer.testing import CliRunner
        from agentra.cli.main import app

        runner = CliRunner()
        # No config, no --skills flag → should exit non-zero
        result = runner.invoke(app, ["skills", "generate", "--path", str(tmp_path)])
        assert result.exit_code != 0

    def test_skills_generate_with_flag(self, tmp_path):
        from typer.testing import CliRunner
        from agentra.cli.main import app

        runner = CliRunner()
        result = runner.invoke(
            app,
            ["skills", "generate", "--path", str(tmp_path), "--skills", "fastapi,postgresql"],
        )
        assert result.exit_code == 0
        assert (tmp_path / ".github" / "prompts" / "fastapi.prompt.md").exists()
        assert (tmp_path / ".claude" / "skills" / "fastapi" / "SKILL.md").exists()
