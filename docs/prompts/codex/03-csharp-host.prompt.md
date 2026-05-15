# Codex Prompt: C# Host v0.1

You are working in the `ikusa-forge` repository.

Goal: implement a minimal C# host that invokes the Python simulator as a subprocess.

Read:

- `AGENTS.md`
- `docs/design/04-system-overview.md`
- `docs/process/03-decision-log.md`
- `docs/process/02-review-checklist.md`

Create:

```text
host-csharp/IkusaForge.Host/
  IkusaForge.Host.csproj
  Program.cs
  PythonBattleRunner.cs
  ReplayModels.cs
  ConfigPaths.cs
```

Requirements:

- .NET 8 or current installed stable .NET SDK
- CLI accepts:
  - `--battle`
  - `--seed`
  - `--repo-root` optional
  - `--python` optional
- Calls:
  - `python tools/run_demo_battle.py --battle <id> --seed <seed> --out runs/<battle_id>`
- Reads:
  - `runs/<battle_id>/replay.json`
  - `runs/<battle_id>/battle_report.json`
- Prints:
  - winner
  - duration
  - top damage dealer
  - top damage taker
  - generated artifact paths

Rules:

- Do not duplicate combat logic in C#.
- Put Python invocation behind `PythonBattleRunner`.
- DTOs should deserialize replay/report but may be partial in v0.1.

Verification:

```bash
dotnet run --project host-csharp/IkusaForge.Host -- --battle demo_001 --seed 1001
```

Completion report must include:

- changed files
- exact command
- stdout summary
- error handling behavior
- known limitations
