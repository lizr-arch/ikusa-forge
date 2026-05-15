# Codex Prompt: Phase 1 Integration

You are working in the `ikusa-forge` repository.

Goal: integrate Phase 1 into one coherent local workflow.

Read:

- `AGENTS.md`
- all `docs/design/*.md`
- all `docs/process/*.md`
- current code

Tasks:

1. Ensure config export works.
2. Ensure config validation works.
3. Ensure Python battle run works.
4. Ensure C# host can invoke Python battle run.
5. Ensure HTML viewer can load generated replay/report.
6. Add or update local setup documentation.
7. Add a Phase 1 status report.

Required final docs:

```text
docs/process/local-dev-setup.md
docs/process/phase-1-report.md
```

Required commands to verify:

```bash
python tools/export_xlsx_to_json.py --input config/source --output config/generated
python tools/validate_config.py --input config/generated
python tools/run_demo_battle.py --battle demo_001 --seed 1001 --out runs/demo_001
dotnet run --project host-csharp/IkusaForge.Host -- --battle demo_001 --seed 1001
```

Phase 1 report must include:

- current system diagram
- successful commands
- generated artifact paths
- screenshots path if any
- known limitations
- next recommended milestone

Do not implement Godot yet unless explicitly requested.

Completion report must include:

- changed files
- all commands run
- all tests run
- failures and fixes
- unresolved risks
