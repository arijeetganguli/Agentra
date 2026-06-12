# Code Pattern Checker

## Code Pattern Check — Before Marking Complete
Run before considering any task done:
1. `ag patterns --severity high` — fail if any HIGH/CRITICAL smells introduced.
2. Verify no rule from the Security & Governance section was violated.
3. Confirm all touched files follow existing naming and structure conventions.
4. Check that no imports, variables, or functions YOU added are now unused.

Automatic checks:
- Never introduce bare `except: pass` — always log with context.
- Never add f-string SQL/shell construction — use parameterized queries.
- Never hardcode credentials — use environment variables.

> **Governance**: SEC-001
