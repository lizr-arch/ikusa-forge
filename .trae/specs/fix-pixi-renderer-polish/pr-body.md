## Summary
- PixiJS live battlefield
- Visual state interpolation
- Faction colors
- Troop shapes
- Formation roster panel
- Pixi click selection
- DOM debug panels preserved

## Verification
- `python tools/export_xlsx_to_json.py --input config/source --output config/generated` -> Exported 7 config tables from config\source\sample_data to config\generated
- `python tools/validate_config.py --input config/generated` -> Config validation passed: config\generated
- `python tools/run_demo_battle.py --battle demo_001 --seed 1001 --config config/generated --out runs/demo_001 --mode basic` -> Battle basic run complete: demo_001 / events: 716 / result: ally / enemy_eliminated
- `python tools/smoke_phase1_mvp.py --run runs/demo_001 --viewer web-viewer --battle demo_001 --seed 1001` -> Phase 1 MVP smoke passed
- `python tools/generate_demo_scenarios.py --source config/source --out web-viewer/public/samples --battle demo_001 --seeds 1001 1002 1003` -> Generated 3 demo scenarios for battle demo_001
- `python tools/smoke_demo_scenarios.py --samples web-viewer/public/samples` -> Demo scenario smoke passed
- `python tools/run_live_api_smoke.py --config config/generated --battle demo_001 --seed 1001` -> Live API smoke passed
- `python -m unittest discover -s sim-python/tests` -> Ran 115 tests in 4.976s; OK
- `cd web-viewer && npm install` -> installed pixi.js and updated lockfile
- `cd web-viewer && npm run typecheck` -> passed
- `cd web-viewer && npm run build` -> built in 254ms
- `cd web-viewer && npm run test:e2e` -> 4 passed (8.7s)
- `git diff --exit-code -- web-viewer/public/samples` -> clean
- `git diff --check` -> clean
- `git diff --cached --check` -> clean

## Tech stack decision
- PixiJS chosen for the live battlefield renderer
- SVG/DOM kept for debug replay UI and surrounding control panels
- Phaser not used
- raw Canvas skipped to avoid a second renderer migration later

## Visual behavior
- Ally / Enemy unit colors
- Troop shape mapping by unit type
- Clean battlefield canvas with HP bars, action bars, and transient effects
- Pixi action bar (行动条) rendered below HP bar
- attack line source field fixed
- Right-side roster/detail panel for selected-unit inspection

## Boundary
- no Python rule change
- no WebSocket
- no C# host
- no Godot
- no terrain/pathfinding
- no React / Vue / Phaser
- PixiJS added only as battlefield renderer
- DOM debug panels preserved
- no visual regression
