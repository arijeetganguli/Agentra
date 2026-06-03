"""Skill Prompt Generator — turn Agentra skills into agent-invokable prompt files.

Each skill is materialized as:
  • ``.github/prompts/<skill-id>.prompt.md`` — VS Code Copilot chat prompt
  • ``.claude/skills/<skill-id>/SKILL.md``  — Claude Code skill file

These files allow the coding agent to load a skill's targeted guidance on
demand (e.g. typing ``#fastapi`` in Copilot chat), rather than bloating
every instruction file with all skill content up-front.
"""

from __future__ import annotations

from pathlib import Path

from agentra.models import Skill


# ── Per-platform prompt file generators ──────────────────────────────────────

def _copilot_prompt(skill: Skill) -> str:
    """Render a VS Code Copilot ``.prompt.md`` file for *skill*."""
    policies_note = ""
    if skill.policies:
        policies_note = "\n\n> **Governance**: This skill enforces policies: " + ", ".join(skill.policies) + "."

    examples_block = ""
    if skill.examples:
        examples_block = "\n\n### Examples\n" + "\n".join(f"```\n{ex}\n```" for ex in skill.examples)

    return (
        f"---\n"
        f"mode: 'agent'\n"
        f"description: '{skill.description}'\n"
        f"---\n\n"
        f"# {skill.name}\n\n"
        f"{skill.instructions.strip()}"
        f"{policies_note}"
        f"{examples_block}\n"
    )


def _claude_skill(skill: Skill) -> str:
    """Render a Claude Code ``SKILL.md`` file for *skill*."""
    policies_note = ""
    if skill.policies:
        policies_note = "\n\n> **Governance**: " + ", ".join(skill.policies)

    examples_block = ""
    if skill.examples:
        examples_block = "\n\n## Examples\n" + "\n".join(f"```\n{ex}\n```" for ex in skill.examples)

    return (
        f"# {skill.name}\n\n"
        f"{skill.instructions.strip()}"
        f"{policies_note}"
        f"{examples_block}\n"
    )


# ── Public API ────────────────────────────────────────────────────────────────

class SkillPromptGenerator:
    """Generate agent-invokable prompt files for a list of skills."""

    def generate(
        self,
        skills: list[Skill],
        output_dir: Path,
        *,
        copilot: bool = True,
        claude: bool = True,
    ) -> list[Path]:
        """Write skill prompt files under *output_dir*.

        Returns the list of paths written.
        """
        written: list[Path] = []

        for skill in skills:
            if copilot:
                path = output_dir / ".github" / "prompts" / f"{skill.id}.prompt.md"
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(_copilot_prompt(skill), encoding="utf-8")
                written.append(path)

            if claude:
                path = output_dir / ".claude" / "skills" / skill.id / "SKILL.md"
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(_claude_skill(skill), encoding="utf-8")
                written.append(path)

        return written

    def file_map(self, skills: list[Skill]) -> dict[str, str]:
        """Return ``{rel_path: content}`` for all skill files (no disk I/O)."""
        result: dict[str, str] = {}
        for skill in skills:
            result[f".github/prompts/{skill.id}.prompt.md"] = _copilot_prompt(skill)
            result[f".claude/skills/{skill.id}/SKILL.md"] = _claude_skill(skill)
        return result
