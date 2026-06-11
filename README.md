<div align="center">

# Agentra

**Enterprise AI Engineering Control Plane**

Secure, govern, route, and optimize AI coding agents — automatically.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-3776AB?logo=python&logoColor=white)](https://python.org)
[![Tests](https://img.shields.io/badge/tests-306%20passed-3fb950)](tests/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

</div>

---

Agentra is a DevSecOps control plane for AI coding assistants. It auto-detects your project stack, enforces 32 security policies across 8 categories (including the OWASP Top 10), routes each task to the best model via capability-class routing, manages context token budgets, generates tailored instruction files for every major agent platform, and gates builds against real vulnerability scans.

<table>
<tr><td><strong>40+</strong> Technologies Detected</td><td><strong>32</strong> Security Policies</td><td><strong>14</strong> Built-in Skills</td></tr>
<tr><td><strong>8</strong> Agent Platforms</td><td><strong>5</strong> Compliance Frameworks</td><td><strong>24</strong> CLI Commands</td></tr>
</table>

## Quick Start

```bash
# Install
pip install agentra

# Initialize — auto-detect stack, generate agent instruction files
ag init --mode quick

# Minimal-token setup — generate lean instructions and turn token-saver on in one step
ag init --mode token-saver --agents copilot

# Run security vulnerability scan (OWASP Top 10 + SAST + CVE)
ag scan

# Security gate: scan then build only if clean
ag prebuild "docker build ."

# Run security governance checks
ag enforce

# Check a command before running it
ag simulate "rm -rf /tmp/build"

# Install git hooks (pre-commit + pre-push security gates)
ag hooks install

# Generate a Claude Code plugin package
ag plugin

# Run benchmarks and generate reports
ag benchmark

# List available skills and generate agent-invokable prompt files
ag skills list
ag skills generate

# Enable token-saver mode for leaner instruction files
ag token-saver on
ag token-saver status

# Classify a task and route to the best model (RouteSmith mode)
ag route "implement a distributed caching layer with Redis"
ag route "design the authentication system architecture" --platform copilot
ag route "review this code for security vulnerabilities" --format json
```

## Features

| Feature | Description |
|---------|-------------|
| 🔍 **Stack Detection** | Auto-detect languages, frameworks, databases, cloud providers, CI/CD, and agents with confidence scores |
| 🛡 **Security Governance** | 32 policies across 8 categories including OWASP Top 10 (A01–A10) |
| 🔬 **Vulnerability Scanning** | Pre-build OWASP pattern scan, SAST (bandit/semgrep), and dependency CVE scan (pip-audit/npm audit/cargo audit) |
| 🚦 **Pre-Build Security Gates** | Block builds on CRITICAL findings; CI templates for GitHub Actions, GitLab CI, and generic shell |
| 🪝 **Git Hooks** | Auto-install pre-commit (OWASP scan) and pre-push (full scan) hooks with clean install/uninstall |
| 🔌 **Claude Code Plugin** | Distributable plugin package with PreToolUse hook, 4 skills, and Karpathy coding guidelines |
| 🧩 **Skills System** | 14 domain skills materialized as agent-invokable `.prompt.md` (Copilot) and `SKILL.md` (Claude Code) files — load guidance on demand instead of bloating every instruction file |
| 📦 **Token Optimization** | Deduplicate, prioritize, compress, and budget-fit instructions; `ag token-saver` compresses generated context files, and optional `tiktoken` support improves token estimates |
| 🤖 **Smart Model Routing** | RouteSmith-style dynamic task classification routes each request to the capability-matched model. `TaskClassifier` scores 9 purpose categories with weighted keyword signals; high-complexity tasks auto-upgrade to `deep_reasoning`. Decision tables injected into all agent instruction files. `ag route "<task>"` for live classification. |
| 🔌 **Agent Adapters** | Native instruction files for Claude, Cursor, Copilot, Aider, Windsurf, Continue.dev, Roo Code, and universal AGENTS.md |
| ⚙ **Execution Safety** | Risk-classify commands, block destructive patterns, sandbox with approval gates, dry-run mode |
| ✓ **Compliance** | Map violations to SOC2, ISO27001, PCI DSS, HIPAA, NIST frameworks |
| 📊 **Benchmarking** | Before/after metrics for every skill with HTML + Markdown report generation |

## CLI Commands

| Command | Description |
|---------|-------------|
| `ag init` | Initialize project — detect stack, save config, generate agent files |
| `ag detect` | Scan and display detected technologies with confidence scores |
| `ag enforce` | Run security policies against codebase, report violations with risk scoring |
| `ag scan` | Vulnerability scan: OWASP Top 10 patterns, SAST (bandit/semgrep), dependency CVEs |
| `ag scan --incremental` | Incremental scan — only files changed since last `ag index` run |
| `ag index` | Build/update the persistent code knowledge graph and BM25 RAG index |
| `ag patterns` | Detect code smells and anti-patterns using the knowledge graph |
| `ag rag "<query>"` | Search the indexed codebase for similar code before writing new code |
| `ag prebuild <cmd>` | Security gate — scan then run build command only if no CRITICAL findings |
| `ag hooks <action>` | Manage git hooks (install/uninstall/status) and generate CI templates |
| `ag plugin` | Generate a Claude Code plugin package with skills and PreToolUse hook |
| `ag optimize` | Show token optimization analysis: deduplication, compression, budget fitting |
| `ag simulate <cmd>` | Dry-run a command through the execution safety engine |
| `ag explain <rule>` | Display full details of a security policy (e.g., `ag explain SEC-001`) |
| `ag validate` | Full pipeline: governance + compliance + optimization in one command |
| `ag benchmark` | Run skill benchmarks including scan-efficiency comparison (full vs knowledge graph) |
| `ag model list` | Show active model + 9-purpose routing table per agent |
| `ag model set <agent> <model>` | Change model for one agent, regenerate all instruction files |
| `ag model set <agent> <model> --purpose <p>` | Override model for a specific purpose (coding/planning/review/…) |
| `ag model set <agent> --interactive` | Pick from a numbered menu — useful in enterprise/restricted environments |
| `ag model set <agent> <model> --auto-fallback` | Auto-select next best model if the requested one is unavailable |
| `ag model detect` | Probe env vars & settings files to identify the active model per platform |
| `ag graph` | Generate interactive HTML call-graph visualization from the code knowledge graph |
| `ag skills list` | List all built-in skills with active status |
| `ag skills generate` | Generate agent-invokable prompt files for active skills |
| `ag skills generate --skills <ids>` | Generate prompt files for specific skill IDs |
| `ag route "<task>"` | Classify a task and show the best model per platform (RouteSmith mode) |
| `ag route "<task>" --platform <p>` | Route for a single platform (e.g. `copilot`, `claude`) |
| `ag route "<task>" --format json` | Machine-readable routing decision |
| `ag token-saver <action>` | Compress context files, enable token-saver mode, and print RTK/caveman setup guidance |
| `ag audit` | View local audit log of all Agentra actions |
| `ag doctor` | Health check: verify config, agent files, .gitignore |
| `ag version` | Display version |

### Usage Examples

```bash
# Enterprise mode with SOC2 + ISO27001 compliance
ag init --mode enterprise --agents claude,copilot

# Build the code knowledge graph index (run once, then keep updated)
ag index                            # Full index build
ag index --force                    # Force rebuild from scratch
ag index --format json              # Machine-readable output
ag rag "database connection pooling"  # Find similar code with BM25 retrieval

# Detect code smells and anti-patterns
ag patterns                         # Whole project (requires ag index)
ag patterns --file src/api.py       # Single file (no index needed)
ag patterns --severity high         # Filter by severity

# Full vulnerability scan — OWASP + SAST + deps
ag scan

# Incremental scan (only changed files since last ag index)
ag scan --incremental               # Default when index exists
ag scan --no-incremental            # Force full scan

# Scan with specific targets
ag scan --owasp --deps              # OWASP patterns + dependency CVEs
ag scan --sast                     # SAST only (requires bandit or semgrep)
ag scan --format json > report.json  # Machine-readable output

# Security gate before any build
ag prebuild "docker build ."
ag prebuild "python -m pytest" --block-high

# Git hooks
ag hooks install
ag hooks status
ag hooks ci --ci github --output .github/workflows/security.yml

# Generate Claude Code plugin
ag plugin --output my-plugin/
# Then in Claude Code: /plugin add my-plugin/

# Explain a specific policy rule
ag explain DB-001
#   DB-001 — no-auto-drop
#   Severity: CRITICAL │ Category: database
#   Never auto-execute DROP TABLE/DATABASE without explicit approval

# Full validation pipeline
ag validate
#   Governance:  4 violations │ Risk: 29.0 │ Blast Radius: high
#   Compliance:  SOC2: 3 findings │ PCI_DSS: 2 findings
#   Optimization: 3,840 → 2,112 tokens (45.0% reduction)

# Token-saver controls after init
ag token-saver on
ag token-saver status
ag token-saver compress-context
ag token-saver init-rtk
ag token-saver caveman

# Smart model routing — view and manage per-agent model preferences
ag model list                          # Show active model + 9-purpose routing table
ag model set claude claude-opus-4-7    # Override model for one agent
ag model set copilot gpt-5.5 --purpose reasoning  # Override a specific purpose

# Enterprise / restricted environments
ag model set claude --interactive      # Pick from a numbered menu of known models
ag model set claude some-model --auto-fallback  # Auto-pick next best if restricted

# Detect which model is currently active (reads env vars + settings files)
ag model detect

# RouteSmith — classify a task and route it to the best model
ag route "implement a REST endpoint for user auth"
# Purpose: coding  │ Capability: coding  │ Complexity: medium
# Recommended Models:
#   copilot  →  gpt-5.3-codex
#   claude   →  claude-sonnet-4-6
#   cursor   →  gpt-5.3-codex

ag route "architect a distributed event-driven payment system" --platform copilot
# Purpose: planning  │ Capability: deep_reasoning  │ Complexity: high
# copilot  →  gpt-5.5

ag route "write pytest unit tests and mock the database" --format json
# {"purpose": "testing", "capability_class": "coding", "complexity": "medium", ...}

# Visualize the call graph as an interactive HTML report
ag graph                               # Generate code-graph.html, open in browser
ag graph --output reports/graph.html   # Custom output path
ag graph --max-nodes 500               # Show more nodes (default: 300)
ag graph --no-open                     # Generate without opening browser
ag graph --include-orphans             # Include isolated nodes (hidden by default)
#   Platform  │ Model              │ Source
#   ──────────┼────────────────────┼──────────────────────
#   claude    │ claude-sonnet-4-6  │ CLAUDE_MODEL env var
#   aider     │ claude-opus-4-7    │ AIDER_MODEL env var
#   copilot   │ unknown            │ not found in env or settings
```

## Security Policies

32 built-in policies across 8 categories:

| Category | Policies | Key Rules |
|----------|----------|-----------|
| **Database** | DB-001, DB-002, DB-003 | No auto-DROP, no unguarded mutations, require rollback plans |
| **Execution** | EX-001 – EX-005 | No inline shell, no curl\|bash, no eval/exec, no rm -rf, no inline code args (python -c, node -e, bash -c) |
| **Secrets** | SEC-001 – SEC-003 | No hardcoded secrets, no key logging, no secret persistence |
| **Git** | GIT-001 – GIT-003 | No force push, no main commits, no secret commits |
| **Infrastructure** | INF-001 – INF-003 | No public resources, no wildcard IAM, require encryption |
| **Prompt Injection** | PI-001 – PI-003 | Detect injection, hidden injections, validate external instructions |
| **Runtime** | RT-001, RT-002 | No debug in prod, require error handling |
| **Vulnerability (OWASP)** | VULN-001 – VULN-010 | A01 Broken Access Control, A02 Crypto, A03 Injection, A04 Design, A05 Misconfiguration, A06 Components, A07 Auth Failures, A08 Deserialization, A09 Logging, A10 SSRF |

## Agent Adapters

Generates native instruction files for each platform:

| Platform | Output File | Format |
|----------|-------------|--------|
| **Claude** | `CLAUDE.md` | Markdown |
| **Cursor** | `.cursorrules` | Markdown |
| **GitHub Copilot** | `.github/copilot-instructions.md` | Markdown |
| **Aider** | `.aider.conf.yml` | YAML |
| **Windsurf** | `.windsurfrules` | Markdown |
| **Continue.dev** | `.continue/config.json` | JSON |
| **Universal** | `AGENTS.md` | Markdown |

## Architecture

```
agentra/
├── cli/             # Typer CLI with Rich output
├── detection/       # Stack detection engine (40+ technologies)
├── governance/      # Security policy engine (32 rules, 8 categories)
├── scanner/         # Vulnerability scanning: OWASP patterns, SAST, deps CVE
├── index/           # Persistent code knowledge graph (SQLite + tree-sitter)
├── rag/             # BM25 RAG engine + anti-pattern library (12 patterns)
├── compress/        # Context-file compressor and RAG chunk deduplicator
├── hooks/           # Git hook management + CI template generation
├── plugin/          # Claude Code plugin generator
├── optimizer/       # Token optimization (dedup, prioritize, compress, budget-fit)
├── routing/         # RouteSmith task classifier + model router
├── adapters/        # Agent platform adapters (7 platforms)
├── skills/          # Domain skill packs (14 built-in)
├── execution/       # Execution safety engine (risk classify, sandbox, approve)
├── onboarding/      # Project initialization (5 modes)
├── compliance/      # Compliance mapping (SOC2, ISO27001, PCI DSS, HIPAA, NIST)
├── benchmarks/      # Skill benchmarking with before/after metrics
├── renderers/       # HTML + Markdown report generation
├── risk/            # Risk scoring and blast radius estimation
├── telemetry/       # Local-only JSON audit logging
└── models.py        # Pydantic data models
```

## Onboarding Modes

| Mode | Security | Compliance | Token Budget | Best For |
|------|----------|------------|-------------|----------|
| `quick` | Standard | — | 12k / 4k / 2k | Fast dev setup |
| `guided` | Strict | All 5 frameworks | 12k / 4k / 2k | Interactive comprehensive |
| `enterprise` | Enterprise | SOC2 + ISO27001 | 16k / 6k / 3k | Production deployments |
| `ci` | Standard | — | 8k / 3k / 1.5k | CI/CD pipelines |
| `token-saver` | Standard | — | 6k / 2k / 1k | Minimal-token coding with lean instruction files and token-saver enabled |

## Benchmarking & Reports

Every skill is benchmarked with before/after metrics:

- **Instruction Token Cost** — tokens consumed by skill instructions
- **Security Policy Coverage** — policies activated by the skill
- **Context Relevance** — stack-match relevance score (0–1)
- **Instruction Compression** — compression ratio achieved

```bash
ag benchmark --output reports/
# ✓ Benchmark report (MD):   reports/benchmark-report.md
# ✓ Benchmark report (HTML): reports/benchmark-report.html
```

The HTML report is a self-contained dark-themed dashboard with stat cards, metric bars, and tables. Open it directly in a browser.

## Configuration

Agentra uses `.agentra.yml`:

```yaml
project:
  name: my-project
  languages: [python]
  frameworks: [fastapi]
  sdks: [openai]

security:
  mode: enterprise
  edr_safe: true
  compliance: [SOC2, ISO27001]

optimization:
  minimal_context: true
  token_budget:
    input: 12000
    output: 4000

agents: [claude, copilot, cursor]
skills: [fastapi, postgresql, karpathy]
karpathy_guidelines: true   # Embed behavioral coding guidelines in all agent files
scanner_enabled: true       # Enable pre-build vulnerability scanning
```

## Pre-Build Security Gates

Agentra intercepts builds before they run and gates on vulnerability findings:

```bash
# Manual gate
ag prebuild "docker build ."
# → Runs OWASP + SAST + deps scan
# → Blocks if CRITICAL findings (exit 1)
# → Warns on HIGH findings (continues)

# Git hook gate (auto-runs on every commit/push)
ag hooks install
# → pre-commit: OWASP scan (fast, <5s)
# → pre-push:   full scan (OWASP + SAST + deps)

# CI pipeline gate
ag hooks ci --ci github --output .github/workflows/security.yml
ag hooks ci --ci gitlab --output .gitlab-ci.yml
```

Scanner degrades gracefully — `bandit`, `semgrep`, `pip-audit`, `npm audit`, and `cargo audit` are all optional. The built-in OWASP regex scanner works with no extra dependencies.

## Intelligent Instruction Merging

When you run `ag init` or `ag model set` on a project that already has instruction files, Agentra **merges** the new content instead of overwriting:

- **Agentra-owned sections** (`## Detected Stack`, `## Security & Governance`, `## Active Skills`, etc.) are always refreshed with the latest generated content.
- **User-added `## ` sections** are preserved verbatim in their original position.
- The Agentra header (preamble) is always updated to the latest version.
- Non-markdown files (`.aider.conf.yml`, `.continue/config.json`) are always replaced since they use structured formats.

```bash
# Safe to re-run — your custom sections are preserved
ag init

# Force a clean overwrite (no merge)
# (use write_agent_files(..., merge=False) in Python API)
```

## Smart Model Routing (RouteSmith Mode)

Instead of letting Copilot's "auto" mode pick any model, Agentra classifies each task and routes it to the capability-matched model before the agent responds.

```bash
ag route "implement a distributed caching layer with Redis"
# Purpose: coding │ Capability: coding │ Complexity: high
# Upgraded to deep_reasoning — high-complexity signals detected.
#
# Recommended Models:
#   copilot  →  gpt-5.5        (deep_reasoning)
#   claude   →  claude-opus-4-7
#   cursor   →  claude-4-7

ag route "fix the typo in the README" --platform copilot
# Purpose: general │ Capability: balanced │ Complexity: low
# copilot  →  gpt-5.4
```

### How it works

1. **`TaskClassifier`** scores 9 purpose categories (planning, reasoning, review, coding, testing, refactoring, documentation, general, formatting) using weighted keyword signals — zero latency, no ML required.
2. **Complexity estimation** upgrades `coding` → `deep_reasoning` when high-complexity signals appear (`production`, `distributed`, `architecture`, `multi-tenant`, etc.).
3. **`TaskRouter`** resolves the best model per platform using `CAPABILITY_MODELS` + `CAPABILITY_FALLBACK_CHAINS`, respecting per-purpose config overrides and enterprise model restrictions.
4. **Decision table injected** into every agent instruction file as a `## Smart Model Routing` section — agents self-select the right model before responding.

```yaml
# .agentra.yml — override routing decisions per purpose
model_purpose_preferences:
  copilot:
    review: gpt-5.5        # Always use deep model for security review
    formatting: gpt-5-mini # Use fast model for style fixes
```

```bash
# Restrict unavailable models (enterprise plan limits)
# TaskRouter skips restricted models and picks the next best from the fallback chain
```

| Signal Group | Key Phrases | Capability | Example Model (Copilot) |
|---|---|---|---|
| Planning | "architect", "design", "roadmap" | `deep_reasoning` | `gpt-5.5` |
| Reasoning | "analyze", "compare", "tradeoff" | `deep_reasoning` | `gpt-5.5` |
| Code Review | "review", "audit", "vulnerability" | `deep_reasoning` | `gpt-5.5` |
| Implementation | "implement", "write", "fix" | `coding` | `gpt-5.3-codex` |
| Testing | "test", "mock", "pytest" | `coding` | `gpt-5.3-codex` |
| Documentation | "document", "readme", "docstring" | `balanced` | `gpt-5.4` |
| Formatting | "format", "lint", "ruff" | `fast` | `gpt-5.4` |

## Skills as Agent-Invokable Prompts

Skills are no longer just static text injected into every instruction file. Each skill is now materialized as a **standalone prompt file** that agents load on demand:

| Platform | File | How to invoke |
|----------|------|---------------|
| **GitHub Copilot** | `.github/prompts/<skill>.prompt.md` | Type `#<skill>` in chat |
| **Claude Code** | `.claude/skills/<skill>/SKILL.md` | Type `/skill <skill>` |

This keeps instruction files lean (only the active skills table is injected) while giving the model full, targeted guidance exactly when it's needed.

```bash
# Generate prompt files for all active skills
ag skills generate

# Generate for specific skills
ag skills generate --skills fastapi,postgresql,kubernetes

# List all skills with active status
ag skills list

# Skip one platform
ag skills generate --no-claude    # Copilot only
ag skills generate --no-copilot   # Claude Code only
```

The `## Active Skills` block in every instruction file tells agents how to invoke each skill:

```markdown
## Active Skills
| Skill       | Copilot    | Claude Code      | Description                    |
|-------------|------------|------------------|--------------------------------|
| **fastapi** | `#fastapi` | `/skill fastapi` | Production FastAPI patterns... |
```

## Claude Code Plugin

Agentra ships as a distributable Claude Code plugin:

```bash
# Generate plugin package
ag plugin --output .agentra-plugin/

# Install in Claude Code
/plugin add .agentra-plugin/
```

The plugin includes:
- **PreToolUse hook** — intercepts `bash`, `make`, `npm run`, `cargo`, `docker` commands and runs `ag scan --owasp` automatically
- **`/agentra-scan`** — run a full vulnerability scan
- **`/agentra-enforce`** — run governance policy checks
- **`/agentra-prebuild`** — security gate before a build
- **`agentra-guardian`** — always-on skill with Karpathy coding guidelines + security baseline

## Karpathy Coding Guidelines

All generated agent instruction files include Andrej Karpathy's 4 behavioral coding rules:

1. **Think Before Coding** — Read the full task before writing any code
2. **Simplicity First** — Prefer the simplest solution that works; complexity is a liability
3. **Surgical Changes** — Change only what is necessary; don't refactor opportunistically
4. **Goal-Driven Execution** — Every line must serve the stated task; delete code that doesn't

These are embedded in `CLAUDE.md`, `.cursorrules`, `.github/copilot-instructions.md`, `.windsurfrules`, and `AGENTS.md` by default (`karpathy_guidelines: true`).

## Enterprise Features

Install optional extras depending on how much code intelligence and token accounting you want:

```bash
pip install "agentra[enterprise]"
pip install "agentra[rag]"
```

- `enterprise` adds the optional graph/index dependencies used for deeper code intelligence.
- `rag` adds `tiktoken` for more accurate token estimation while keeping BM25 retrieval available.

### Code Knowledge Graph

Agentra builds and maintains a **persistent SQLite knowledge graph** (`code_index.db`) of your codebase using tree-sitter multi-language AST parsing. Once indexed, scans and agent context generation are incremental — only files changed since the last index run are reprocessed.

```bash
ag index                    # Build or update the knowledge graph
ag index --force            # Full rebuild from scratch
```

The index stores:
- All functions, classes, methods, and imports with line ranges and docstrings
- Call edges between symbols for dependency and hotspot analysis
- SHA-256 content hashes per file for change detection
- Code chunks for BM25 retrieval

**Languages supported:** Python, JavaScript, TypeScript, Rust, Go, Java, Ruby, C, C++, C# (via tree-sitter), with regex-based fallback for all other file types.

**Call graph extraction** uses the best available tool per language — pyan3 for whole-project Python analysis (cross-file, module-level calls), tree-sitter `call_expression` queries for all other supported languages. Both are optional and degrade gracefully if not installed. Import-only nodes and true orphans are filtered from the graph by default; pass `--include-orphans` to show them.

### BM25 Code RAG

The RAG engine builds a BM25 index over tokenized code chunks using `rank-bm25`. When generating agent instruction files (`CLAUDE.md`, `.cursorrules`, etc.), Agentra injects a **Codebase Patterns** section with:

- **Established patterns** — the top-3 most prevalent idioms in the codebase
- **Known code smells** — the 5 highest-severity anti-patterns to avoid repeating

This gives coding agents targeted, project-specific context instead of generic boilerplate, reducing agent context tokens by ~60–80% in steady state.

### Token-Saver Mode

`ag token-saver` is the dedicated low-token workflow for generated instruction files:

- `ag init --mode token-saver` generates leaner agent files up front and enables token-saver automatically.
- `ag token-saver on` compresses `CLAUDE.md`, `AGENTS.md`, and `.github/copilot-instructions.md`, writes backups to `.agentra/backups/`, and injects a brevity block where appropriate.
- `ag token-saver off` restores the original files from backup.
- `ag token-saver status` shows whether the mode is enabled and how many tokens each tracked context file uses.
- `ag token-saver init-rtk` and `ag token-saver caveman` print setup instructions for external token-reduction helpers and add usage blocks to the relevant instruction files.

Use `ag init --mode token-saver` when you want the leanest default setup from the start. Use `ag token-saver on` when you want to compress an existing project after a normal init.

### Anti-Pattern Detection

12 built-in anti-pattern rules run on every file:

| ID | Name | Description |
|----|------|-------------|
| AP-001 | god-class | Classes > 300 lines |
| AP-002 | long-method | Functions > 50 lines |
| AP-003 | deep-nesting | Indentation > 4 levels |
| AP-004 | magic-number | Bare integer literals ≥ 2 digits |
| AP-005 | mutable-default-arg | `def f(x=[])` pattern |
| AP-006 | bare-except | `except:` with no exception type |
| AP-007 | wildcard-import | `from x import *` |
| AP-008 | commented-code | 5+ consecutive comment lines |
| AP-009 | todo-density | > 5 TODO/FIXME per file |
| AP-010 | missing-type-hints | Public functions without annotations |
| AP-011 | duplicate-chunk | Token Jaccard overlap > 0.90 |
| AP-012 | global-mutation | `global x` inside functions |

```bash
ag patterns                         # Scan whole project
ag patterns --file src/api.py       # Single file scan
ag patterns --severity high         # Filter by severity
ag patterns --format json           # Machine-readable output
```

### Incremental Scanning

Once the knowledge graph is built, `ag scan` automatically uses incremental mode:

```bash
ag scan --incremental               # Default: only changed files
ag scan --no-incremental            # Force full scan
```

In steady state (10% of files change per run), this reduces scan token cost by ~90% and wall time proportionally.

### Scan Efficiency Benchmark

`ag benchmark` now includes a **Scan Efficiency** benchmark that compares full scan vs knowledge-graph-incremental scan across four metrics: files traversed, content tokens scanned, agent context tokens, and scan wall time. Run without an index for projected values; run after `ag index` for real measurements.

### Configuration

```yaml
# .agentra.yml (enterprise sections)
index:
  path: .agentra          # Where to store code_index.db and RAG store
  enabled: true
  exclude:                # Patterns to exclude from indexing
    - "*.generated.*"
    - "migrations/"

rag:
  enabled: true
  top_k: 5               # Similar chunks to retrieve
  antipatterns: true     # Run anti-pattern detection during indexing
  include_in_agent_files: true  # Inject patterns block into CLAUDE.md etc.
```

## Documentation

Full interactive documentation is available at [`docs/index.html`](docs/index.html) — a storybook-style guide covering every feature, command, policy, skill, and adapter with usage examples. A Markdown version is at [`docs/index.md`](docs/index.md).

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests (306 passed, 1 skipped)
pytest tests/ -v

# Lint
ruff check agentra/

# Type check
mypy agentra/
```

## Acknowledgements

This project was inspired by [agent-policykit](https://github.com/sidrat2612/agent-policykit) by **Siddharth Rathore**. Thanks for the idea and the foundational work that sparked Agentra.

## License

MIT
