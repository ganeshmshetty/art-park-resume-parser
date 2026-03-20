# AI Prompt Template (Use For Every AI Task)

Copy and fill this before asking AI to generate code.

```text
Goal:

File(s) to change:

Current behavior:

Expected behavior:

Input schema:

Output schema:

Constraints:
- Keep module IDs catalog-locked
- Respect API and data contracts in docs/
- Do not break existing endpoint names

Acceptance checks:
- [ ] Lint passes
- [ ] App runs
- [ ] Sample input returns expected shape
- [ ] No contract drift

Do not change:

Related docs:
- docs/PROJECT_CONTEXT.md
- docs/ARCHITECTURE.md
- docs/API_CONTRACT.md
- docs/DATA_CONTRACT.md
```

## Example Quick Prompt
```text
Goal: Add file type validation to POST /analyze.
File(s) to change: api/app/api/routes.py
Expected behavior: reject unsupported files with error shape from API_CONTRACT.
Acceptance checks: test with .pdf and .exe.
```
