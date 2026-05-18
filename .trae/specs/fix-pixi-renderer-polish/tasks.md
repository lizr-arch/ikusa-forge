# Tasks

- [ ] Task 1: Fix attack line source field in livePixiBattlefieldRenderer.ts
  - Change `event.payload.source` → `event.payload.attacker ?? event.payload.source` in createEffectFromEvent
  - Verify attack line renders for normal attack events

- [ ] Task 2: Add Pixi action bar (Graphics) to unit sprites
  - Add `actionBarBg: Graphics` and `actionBarFill: Graphics` to UnitSprite interface
  - Create Graphics objects in `createUnitSprite`, addChild them
  - Render in `updateUnitSprite`: draw bg rect + fill rect using `actionIndicatorRatio(unit)`
  - Place below HP bar, subtle styling, dead units show empty/grey bar
  - Update `destroy()` to clean up new Graphics objects

- [ ] Task 3: Fix status_expire check to use event.type
  - Change `event.payload.type === "status_expire"` → `event.type === "status_expire"` in createEffectFromEvent
  - Verify S+ for status_apply, SE for status_expire

- [ ] Task 4: Update Playwright smoke test assertions
  - Verify existing tests still pass (Pixi canvas existence already asserted at line 286-287)
  - Add explicit assertion: Pixi canvas visible after live step
  - Add assertion: performance panel visible after live steps
  - Keep all 4 existing tests passing

- [ ] Task 5: Update PR #24 body via gh pr edit
  - Replace "no new frontend framework" with explicit boundaries
  - Add Pixi action bar and attack line fix to Visual behavior section

- [ ] Task 6: Run full verification
  - Python: export_xlsx_to_json, validate_config, run_demo_battle, smoke_phase1_mvp, generate_demo_scenarios, smoke_demo_scenarios, run_live_api_smoke, unittest
  - Web: npm install, typecheck, build, test:e2e
  - Fixture consistency: git diff --exit-code -- web-viewer/public/samples
  - Diff checks: git diff --check, git diff --cached --check

- [ ] Task 7: Commit + push to phase2/live-pixi-battlefield-renderer
  - git add, commit with message "fix(viewer): polish pixi battlefield effects", git push
  - Wait for CI green

- [ ] Task 8: Output completion report

# Task Dependencies
- Tasks 1, 2, 3 are independent and can run in parallel
- Task 4 depends on Tasks 1-3 (code fixes must be in place)
- Task 5 is independent
- Task 6 depends on Tasks 1-5
- Task 7 depends on Task 6 passing
- Task 8 depends on Task 7 completing
