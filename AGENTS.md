# AGENTS.md

This repository is for **Ikusa Forge**, a formation auto-battle lab.

Keep this file short. Put detailed design in `docs/`.

## Operating rule

Use this loop:

```text
SPEC -> PLAN -> DO -> VERIFY -> REPORT
```

Do not jump into implementation before the task has:

- goal
- success criteria
- affected files
- test / verification method
- expected output artifact

## Phase 1 boundaries

Phase 1 focuses on:

- config schema
- Python deterministic combat simulator
- replay event stream
- battle report
- C# host calling Python
- HTML replay debugger

Phase 1 should not implement:

- full Godot gameplay
- final art pipeline
- networked PvP
- save system
- large content production

## Determinism rule

Every battle must be reproducible from:

- config files
- battle setup
- seed

Same config + same battle + same seed must produce the same replay and report.

## Evidence rule

Every implementation report must include:

- changed files
- tests run
- command outputs
- generated artifacts
- known limitations

For code review, cite concrete file paths and line ranges when possible.

## Data rule

xlsx is the designer editing format.
JSON is the runtime format.

Do not make the simulator read xlsx directly during normal runtime.

## Architecture rule

Keep combat logic pure and UI-free.

Allowed dependency direction:

```text
config -> simulator -> replay/report -> viewer/host
```

Forbidden dependency direction:

```text
simulator -> web viewer
simulator -> Godot scene
simulator -> C# UI
```

## C# / Python rule

For Phase 1, prefer C# invoking Python as a subprocess.

Do not embed Python.NET until subprocess integration and replay/report are stable.

## Review rule

A PR is not complete unless it answers:

1. What player/combat behavior changed?
2. What data changed?
3. What replay/report proves it?
4. What tests protect it?
5. What is still uncertain?
