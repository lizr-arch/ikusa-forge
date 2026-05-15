# Codex Prompt: HTML Replay Viewer v0.1

You are working in the `ikusa-forge` repository.

Goal: implement a minimal local HTML replay viewer for `replay.json` and `battle_report.json`.

Read:

- `AGENTS.md`
- `docs/design/02-mvp-scope-v0.1.md`
- `docs/design/04-system-overview.md`
- `docs/process/02-review-checklist.md`

Create:

```text
web-viewer/
  index.html
  app.js
  replay_renderer.js
  timeline_panel.js
  report_panel.js
  style.css
```

Requirements:

- works by opening `index.html` locally
- user can load local `replay.json`
- user can load local `battle_report.json`
- supports:
  - play / pause
  - step tick
  - speed control
  - event timeline
  - simple 4x3 board rendering
  - unit hp display
  - damage flash or text feedback
  - report table

No frameworks required unless strongly justified.

Do not require a backend server in v0.1.

Acceptance:

- can load `runs/demo_001/replay.json`
- can show battle start, damage, death, battle end
- can show top damage/tank/kill/skill trigger data

Completion report must include:

- changed files
- how to open viewer
- sample replay used
- known rendering limitations
