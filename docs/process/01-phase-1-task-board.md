# Phase 1 Task Board

## Milestone 0: Repository bootstrap

### Task 0.1: Add planning scaffold

Output:

- README.md
- AGENTS.md
- docs/design/*
- docs/process/*
- docs/prompts/codex/*

Acceptance:

- repo explains project purpose
- phase boundaries are clear
- local Codex has prompts to start implementation

---

## Milestone 1: Data system

### Task 1.1: Create config folder structure

Output:

```text
config/source/
config/generated/
```

Acceptance:

- placeholder source files or documented schema exist
- generated folder is ignored except `.gitkeep`

### Task 1.2: Implement JSON schema draft

Output:

```text
docs/schema/*.schema.json
```

Acceptance:

- units/weapons/skills/formations/synergies/encounters/constants schemas exist

### Task 1.3: Implement config exporter

Output:

```text
tools/export_xlsx_to_json.py
```

Acceptance:

- can export sample data to JSON
- handles csv-like list fields
- handles json cells
- prints clear errors

### Task 1.4: Implement config validator

Output:

```text
tools/validate_config.py
```

Acceptance:

- catches duplicate ids
- catches missing references
- catches invalid numeric values

---

## Milestone 2: Python combat core

### Task 2.1: Implement core models

Output:

```text
sim-python/ikusa_sim/*.py
```

Acceptance:

- UnitState, BattleState, BattleEvent exist
- no UI dependency

### Task 2.2: Implement battle loop

Acceptance:

- battle runs from config + encounter + seed
- battle ends in victory/defeat/draw/timeout
- outputs replay.json

### Task 2.3: Implement combat report

Acceptance:

- outputs damage done/taken, kills, skill triggers
- identifies 3-5 key moments

### Task 2.4: Add tests

Acceptance:

- damage formula test
- targeting test
- synergy test
- determinism test

---

## Milestone 3: C# host

### Task 3.1: Create .NET host

Output:

```text
host-csharp/IkusaForge.Host/
```

Acceptance:

- runs from CLI
- invokes Python subprocess
- reads replay/report JSON
- prints summary

### Task 3.2: Add DTOs

Acceptance:

- replay/report DTOs deserialize successfully
- no combat logic in C# yet

---

## Milestone 4: HTML replay viewer

### Task 4.1: Load replay/report files

Acceptance:

- file input loads local replay/report JSON

### Task 4.2: Render 4x3 board

Acceptance:

- units are visible
- hp is visible
- tick step updates board

### Task 4.3: Render timeline/report

Acceptance:

- event list is readable
- damage report table is readable

---

## Milestone 5: Integration

### Task 5.1: One-command demo

Acceptance:

```bash
python tools/run_demo_battle.py --battle demo_001 --seed 1001 --out runs/demo_001
dotnet run --project host-csharp/IkusaForge.Host -- --battle demo_001 --seed 1001
```

### Task 5.2: Phase 1 report

Output:

```text
docs/process/phase-1-report.md
```

Acceptance:

- includes screenshots or artifact paths
- includes tests
- includes remaining risks
