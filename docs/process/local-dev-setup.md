# Local Development Setup

This repository is currently in Phase 1 bootstrap state.

The scaffold exists so later tasks can add config schemas, a deterministic Python simulator, a C# subprocess host, and an HTML replay debugger without mixing responsibilities.

## Expected local tools

- Python 3 for future tools and simulator work.
- .NET SDK for the future C# host.
- A modern browser for the future HTML replay debugger.

No heavy dependencies are required for the bootstrap scaffold.

## Repository layout

```text
config/source/      Designer-editable source data placeholder.
config/generated/   Runtime JSON output placeholder; generated files are ignored.
sim-python/         Future pure Python combat simulator package and tests.
host-csharp/        Future C# host that invokes Python as a subprocess.
web-viewer/         Future local HTML replay debugger.
tools/              Future export, validation, and demo-run scripts.
runs/               Generated battle run output; generated files are ignored.
docs/schema/        Future JSON schema drafts for runtime config.
```

## Bootstrap verification

At this stage, verification is structural:

```bash
git status --short
```

Confirm that only intended scaffold files are untracked or changed, and that generated-output folders keep only their `.gitkeep` placeholders.

## Later command flow

The intended Phase 1 flow is documented in `README.md`, but the commands are not implemented during bootstrap:

```bash
python tools/export_xlsx_to_json.py --input config/source --output config/generated
python tools/validate_config.py --input config/generated
python tools/run_demo_battle.py --battle demo_001 --seed 1001 --out runs/demo_001
dotnet run --project host-csharp/IkusaForge.Host -- --battle demo_001 --seed 1001
```

Do not treat these commands as runnable until the corresponding Phase 1 tasks are implemented.
