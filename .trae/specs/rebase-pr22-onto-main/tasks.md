# Tasks

- [ ] Task 1: Fetch and rebase phase2/combat-architecture-formalization onto origin/main
  - [ ] 1.1 `git fetch origin`
  - [ ] 1.2 `git switch phase2/combat-architecture-formalization`
  - [ ] 1.3 `git rebase origin/main`

- [ ] Task 2: Resolve all rebase conflicts
  - Key principle: keep PR #24 PixiJS files, keep PR #22 Python additions
  - **Must-keep files from PR #24 (origin/main)**:
    - `web-viewer/src/livePixiBattlefieldRenderer.ts` — full PixiJS renderer
    - `web-viewer/src/visualStateBuffer.ts` — visual state buffer
    - `web-viewer/src/formationRosterView.ts` — formation roster view
    - `web-viewer/src/troopVisualConfig.ts` — troop visual config
    - `web-viewer/src/performanceTelemetry.ts` — performance telemetry
    - `docs/process/live-pixi-battlefield-renderer-v0.1.md` — PixiJS doc
    - `web-viewer/package.json` — must retain pixi.js dependency
    - `web-viewer/package-lock.json` — regenerate from npm install
    - `.trae/specs/fix-pixi-renderer-polish/*` — keep these spec files
  - **Must-keep additions from PR #22**:
    - `sim-python/ikusa_sim/unit_fsm.py` — new FSM module
    - `sim-python/ikusa_sim/decisions.py` — new decisions module
    - `sim-python/ikusa_sim/actions.py` — new actions module
    - `sim-python/tests/test_combat_architecture.py` — new test file
    - `docs/architecture/combat-architecture-v0.1.md` — architecture doc
    - `docs/process/combat-architecture-formalization-v0.1.md` — process doc
    - `sim-python/ikusa_sim/__init__.py` — new exports
  - **Merge carefully** (both branches modified):
    - `web-viewer/src/main.ts` — keep PixiJS code from main, add PR #22 tweaks
    - `web-viewer/src/replayState.ts` — merge both changes
    - `web-viewer/src/replayTypes.ts` — merge both changes
    - `web-viewer/src/timelineView.ts` — merge both changes
    - `web-viewer/src/unitDetailView.ts` — merge both changes
    - `web-viewer/src/boardView.ts` — merge both changes
    - `web-viewer/src/styles.css` — keep PixiJS styles from main, add PR #22 tweaks
    - `web-viewer/index.html` — keep PixiJS canvas from main
    - `web-viewer/tests/viewer-smoke.spec.ts` — keep main's PixiJS tests, add PR #22 tweaks if any
    - `web-viewer/public/samples/**/replay.json` — regenerate after rebase
    - `docs/process/phase-1-summary.md` — merge both
    - `sim-python/ikusa_sim/battle.py` — merge both
    - `sim-python/ikusa_sim/battle_session.py` — merge both

- [ ] Task 3: Run Python verification suite
  - [ ] 3.1 `python tools/export_xlsx_to_json.py --input config/source --output config/generated`
  - [ ] 3.2 `python tools/validate_config.py --input config/generated`
  - [ ] 3.3 `python tools/run_demo_battle.py --battle demo_001 --seed 1001 --config config/generated --out runs/demo_001 --mode basic`
  - [ ] 3.4 `python tools/smoke_phase1_mvp.py --run runs/demo_001 --viewer web-viewer --battle demo_001 --seed 1001`
  - [ ] 3.5 `python tools/generate_demo_scenarios.py --source config/source --out web-viewer/public/samples --battle demo_001 --seeds 1001 1002 1003`
  - [ ] 3.6 `python tools/smoke_demo_scenarios.py --samples web-viewer/public/samples`
  - [ ] 3.7 `python tools/run_live_api_smoke.py --config config/generated --battle demo_001 --seed 1001`
  - [ ] 3.8 `python -m unittest discover -s sim-python/tests`

- [ ] Task 4: Run web verification suite
  - [ ] 4.1 `cd web-viewer && npm install`
  - [ ] 4.2 `npm run typecheck`
  - [ ] 4.3 `npm run build`
  - [ ] 4.4 `npm run test:e2e`

- [ ] Task 5: Run final git checks
  - [ ] 5.1 `git diff --exit-code -- web-viewer/public/samples`
  - [ ] 5.2 `git diff --check`
  - [ ] 5.3 `git diff --cached --check`
  - [ ] 5.4 `git status --short --branch`

- [ ] Task 6: Update PR #22 body via `gh pr edit`
  - Must include: ## Rebase status, ## Verification, ## Runtime behavior, ## Boundary

- [ ] Task 7: Push rebased branch
  - [ ] 7.1 `git push --force-with-lease origin phase2/combat-architecture-formalization`

# Task Dependencies
- Task 2 depends on Task 1
- Tasks 3 and 4 depend on Task 2 (can run in parallel)
- Task 5 depends on Tasks 3 and 4
- Task 6 depends on Task 5
- Task 7 depends on Task 6
