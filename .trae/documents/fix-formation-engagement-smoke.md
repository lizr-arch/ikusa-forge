# Plan: Fix Formation Engagement Smoke (PR #25 Review Fixes)

## Goal
修复 Web GPT review 指出的 PR #25 问题：Live API smoke step budget、engagement_role 推导、ranged_hold 回归覆盖、fixture 不一致、临时文件清理。

## Prerequisites
- 在 `phase2/formation-and-engagement-system` 分支上工作
- 不新建 PR，不 merge
- 不改变 Live API response shape、不移除 PixiJS、不引入 Phaser/Godot/C#
- 不实现 A*/navmesh/terrain/obstacle collision

---

## Step 1: 修复 Live API smoke step budget

**文件**: `tools/smoke_live_api.py`

**问题**: `--max-steps` 默认值 `100`，但 `demo_001` end_tick=623，每步 5 ticks，共需要 `⌈623/5⌉ = 125` 步。

**修改**:
- 将 `--max-steps` 默认值从 `100` 改为 `150`（安全覆盖 demo_001）
- 或者更好的方式：在 `run_smoke()` 开始时读取 `/api/battle/start` 返回的 snapshot 中的 `max_ticks` 或从 config 推导 max_steps，但最简单的修复就是提高上限到 150。
- 同时在输出中已经记录了 `steps` 数量（已有），无需额外改动。

---

## Step 2: 修复 engagement_role 推导

**文件**: `sim-python/ikusa_sim/runtime_models.py`

**问题**: `__post_init__` 仅根据 formation slot `role` 推导 `engagement_role`。`ashigaru_bow` 的 formation slot role 是 `"support"`，`enemy_archer` 的是 `"left_support"`，两者都匹配 `"support"`，被误判为 `support`。

**修复**:
- 综合 `unit_def_id`、`name`、`tags`、`weapon_slots`、`role` 综合判断
- 优先级规则：
  1. 如果 `tags` 或 `name` 或 `unit_def_id` 包含 `ninja` → `flanker`
  2. 如果 `tags` 或 `name` 或 `unit_def_id` 包含 `bow`/`archer`/`yumi`/`ranged`，或 `weapon_slots` 包含 `bow` → `ranged`（**优先于 support**）
  3. 如果 `tags` 或 `name` 或 `unit_def_id` 包含 `banner`/`flag`/`support` → `support`
  4. 如果 role 包含 `shield`/`spear`/`katana`/`samurai`/`vanguard`/`front` → `frontline`
  5. fallback → `frontline`

- `desired_distance` 推导也需要同步更新（用修正后的 `engagement_role` 判断，而非原始 `role`）

- 注意检查大小写不敏感。

---

## Step 3: 让 ranged_hold 真正被回归覆盖

修复 Step 2 后，`ashigaru_bow` 和 `enemy_archer` 将获得 `engagement_role = "ranged"`，demo_001 应产生 `ranged_hold > 0`。

**文件 1**: `tools/smoke_phase1_mvp.py`  
- 第 157 行：`_expect(counts.get("ranged_hold", 0) >= 0, ...)` 改为 `_expect(counts.get("ranged_hold", 0) > 0, ...)`
- 第 212 行：`_expect(_non_negative(...))` 改为 `_expect(_positive(...))`  
- 第 233 行：`summary.get("total_ranged_holds") == event_counts.get("ranged_hold", 0)` — 已有，保持不变
- 新增：`_expect(any(_as_dict(unit).get("ranged_holds", 0) > 0 for unit in units.values()), "report unit ranged holds", errors)`

**文件 2**: `sim-python/tests/test_formation_engagement.py`  
- 新增测试 `test_demo_001_has_ranged_units`: 用 `demo_001` 初始化后，检查至少一个 unit 的 `engagement_role == "ranged"`
- 新增测试 `test_ranged_hold_event_produced`: 用 `demo_001` 运行足够步数后，检查事件中包含 `"ranged_hold"`
- 新增测试 `test_ranged_desired_distance_greater_than_melee`: 确保弓兵 `desired_distance` > 近战 `desired_distance`

---

## Step 4: 重新生成并提交 fixtures

```bash
python tools/generate_demo_scenarios.py --source config/source --out web-viewer/public/samples --battle demo_001 --seeds 1001 1002 1003
python tools/smoke_demo_scenarios.py --samples web-viewer/public/samples
git diff --exit-code -- web-viewer/public/samples  # 验证 clean 后提交
```

由于 battle 行为已变（end_tick 623, 新事件类型），fixtures 会更新。这是预期行为。

---

## Step 5: 清理 .trae/specs 临时文件

删除：
```
.trae/specs/phase2-formation-and-engagement-system/checklist.md
.trae/specs/phase2-formation-and-engagement-system/spec.md
.trae/specs/phase2-formation-and-engagement-system/tasks.md
```

如果 `phase2-formation-and-engagement-system/` 目录变空，也删除该目录。

---

## Step 6: 运行完整验证

### Python side:
```bash
python tools/export_xlsx_to_json.py --input config/source --output config/generated
python tools/validate_config.py --input config/generated
python tools/run_demo_battle.py --battle demo_001 --seed 1001 --config config/generated --out runs/demo_001 --mode basic
python tools/smoke_phase1_mvp.py --run runs/demo_001 --viewer web-viewer --battle demo_001 --seed 1001
python tools/generate_demo_scenarios.py --source config/source --out web-viewer/public/samples --battle demo_001 --seeds 1001 1002 1003
python tools/smoke_demo_scenarios.py --samples web-viewer/public/samples
python tools/run_live_api_smoke.py --config config/generated --battle demo_001 --seed 1001
python -m unittest discover -s sim-python/tests
```

### Web side:
```bash
cd web-viewer
npm run typecheck
npm run build
npm run test:e2e
```

### Git checks:
```bash
git diff --exit-code -- web-viewer/public/samples
git diff --check
git status --short --branch
```

---

## Step 7: 更新 PR #25 body

用 GitHub MCP update PR body 更新，填入最新的实际数据（end_tick, events count, formation/engagement counts, ranged_hold count 等）。

---

## Step 8: 提交并推送

```bash
git add .
git commit -m "fix(sim): stabilize formation engagement smoke"
git push
```

---

## Step 9: 输出 completion report

Waiting for CI green, then output comprehensive report.

---

## Verification Checklist
- [ ] Live API smoke 不再因 step budget 失败
- [ ] `ashigaru_bow` 和 `enemy_archer` 获得 `engagement_role = "ranged"`
- [ ] `ranged_hold` 事件 > 0
- [ ] smoke_phase1_mvp 全部通过（含 ranged_hold > 0）
- [ ] 122+ Python 测试全部通过
- [ ] TypeScript typecheck 通过
- [ ] npm build 通过
- [ ] 4 e2e 测试通过
- [ ] fixtures clean (git diff --exit-code)
- [ ] CI green
