# Codex Prompt: Bootstrap Repository

You are working in the `ikusa-forge` repository.

Goal: initialize the repository scaffold for Phase 1.

Read:

- `README.md`
- `AGENTS.md`
- `docs/design/00-project-brief.md`
- `docs/design/01-combat-pillars.md`
- `docs/design/02-mvp-scope-v0.1.md`
- `docs/process/00-web-gpt-codex-workflow.md`
- `docs/process/01-phase-1-task-board.md`

Implement only the repository scaffold. Do not implement full combat logic yet.

Required output:

```text
config/source/.gitkeep
config/generated/.gitkeep
sim-python/ikusa_sim/__init__.py
sim-python/tests/.gitkeep
host-csharp/.gitkeep or minimal solution placeholder
web-viewer/.gitkeep or minimal placeholder
tools/.gitkeep
runs/.gitkeep
docs/schema/.gitkeep
```

Also add:

- `.gitignore`
- `docs/process/local-dev-setup.md`

The `.gitignore` should ignore:

- Python cache
- virtualenvs
- .NET build output
- generated run outputs except `.gitkeep`
- generated config outputs except `.gitkeep`

Do not add heavy dependencies.

Verification:

- print final tree
- ensure no generated/binary noise is committed

Completion report must include:

- changed files
- commands run
- known limitations
- next recommended task
