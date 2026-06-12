# Knowledge Graph Explorer

## Knowledge Graph — Agent Workflow
Before implementing any new function, class, or module:
1. Use `semantic_search` to find semantically similar existing code.
2. Use `grep_search` to find exact usages of related symbols.
3. Use `file_search` to locate files by name or path pattern.
4. Read the top 2-3 matching files to understand established patterns.
5. Only proceed to implementation after understanding what already exists.

Rules:
- Never duplicate existing functionality found during exploration.
- Reuse or extend existing helpers rather than writing new ones.
- Match the coding style and patterns found in discovered files.
