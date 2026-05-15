# Web GPT + Local Codex Workflow

## Goal

Avoid slow direct GitHub edits from Web GPT.

Use each tool for its best role:

| Role | Owner | Responsibility |
|---|---|---|
| Product/design synthesis | Web GPT | design docs, architecture decisions, task decomposition |
| Implementation | Local Codex | code, tests, commits, PRs |
| Review/audit | Web GPT | inspect reports, challenge assumptions, request fixes |
| Source of truth | GitHub repo | final docs, code, issues, PRs |

## Preferred loop

```text
1. Web GPT produces design pack / task prompt
2. User commits design pack or lets local Codex apply it
3. Local Codex implements on branch
4. Local Codex outputs completion report
5. User pastes report / diff summary / PR link to Web GPT
6. Web GPT audits:
   - scope
   - architecture
   - tests
   - generated outputs
   - known risks
7. Web GPT writes fix prompt if needed
8. Local Codex iterates
```

## When Web GPT should create ZIP packages

Use ZIP for:

- design documents
- task prompts
- review checklists
- issue templates
- schema drafts

Avoid ZIP for:

- large implementation patches
- generated dependency folders
- binary build outputs
- anything likely to conflict with local branches

## When local Codex should implement

Use local Codex for:

- creating project structure
- writing code
- running tests
- formatting
- committing
- opening PRs

## Review input expected from local Codex

Each Codex completion report should include:

```markdown
## Summary

## Changed files

## Commands run

## Tests

## Generated artifacts

## Evidence

## Known limitations

## Next recommended step
```

## Branch naming

Use:

```text
phase1/bootstrap-repo
phase1/config-schema
phase1/python-combat-core
phase1/csharp-host
phase1/html-replay-viewer
phase1/integration
```

## Commit style

Use concise conventional-ish messages:

```text
docs: add phase 1 combat lab design
feat(config): add xlsx to json exporter
feat(sim): add deterministic battle loop
feat(host): add python battle runner
feat(viewer): add replay timeline
test(sim): add determinism coverage
```
