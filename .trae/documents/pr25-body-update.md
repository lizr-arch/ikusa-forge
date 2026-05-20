# Plan: PR #25 Body Update & Artifact Cleanup

## Goal
修复 Web GPT re-review 指出的两个阻塞问题：删除临时文档、更新 PR body 为最新真实数据。

## Prerequisites
- 在 `phase2/formation-and-engagement-system` 分支上工作
- 不改 Python 战斗逻辑、web-viewer 功能、Live API、tests
- 不 merge、不新建 PR

---

## Step 1: 删除临时文档

删除 `tools/` 不在根目录中的临时文件：
```
.trae/documents/fix-formation-engagement-smoke.md
```

---

## Step 2: 更新 PR #25 body

使用 `gh pr edit 25 --body-file <temp_body.md>` 将 PR 描述更新为最新真实数据。

需要写入的 body 内容（先写入临时文件 `_pr_body.md`，执行完 `gh pr edit` 后删除）：

```markdown
## Summary

Adds Formation and Engagement System / 编队与接敌系统:
- Formation Anchor / 编队锚点
- Group Advance / 编队推进
- Engagement Pairing / 接敌配对
- Melee Engagement Lock / 近战接敌锁定
- Ranged Hold Distance / 远程保持距离
- Separation / 单位分离
- PixiJS visual support / PixiJS 可视化支持

## Verification

### Full Python pipeline (132 tests, 0 failures):
```
export_xlsx_to_json: OK
validate_config: OK
run_demo_battle: ally / enemy_eliminated at tick 458
smoke_phase1_mvp: PASSED
  - formation_anchor_update=350
  - engagement_lock=15
  - engagement_release=12
  - ranged_hold=193
generate_demo_scenarios: 3 scenarios, all ally/enemy_eliminated
smoke_demo_scenarios: PASSED
run_live_api_smoke: PASSED
python -m unittest discover -s sim-python/tests: 132 tests OK
```

### Full Web pipeline:
```
npm run typecheck: OK (0 errors)
npm run build: OK
npm run test:e2e: 4/4 passed
```

### CI:
GitHub Actions run: Python Simulator success, Web Viewer success

## Gameplay behavior changed

- **demo_001 seed=1001**: ally wins by enemy_eliminated at tick 458
- **events**: 1670
- **formation_anchor_update**: 350
- **engagement_lock**: 15
- **engagement_release**: 12
- **ranged_hold**: 193
- **All 3 curated seeds**: ally wins consistently
- **ranged_hold is covered in demo_001**: bow/archer-like units (ashigaru_bow, enemy_archer) are correctly classified as ranged and hold at desired distance
- **Melee lock**: frontline units lock onto targets instead of switching every tick
- **Reduced overlap**: separation system pushes overlapping friendlies apart

## Boundary

- no A*
- no navmesh
- no terrain
- no obstacle collision
- no morale
- no cavalry charge
- no Godot/C#
- no Phaser
- no Python-to-TypeScript rule move

## Known limitations

- Battle end_tick changed from original 341 to 458 due to formation/engagement system
- Separation is lightweight, not physical collision
```

---

## Step 3: 快速验证

```bash
git status --short
git diff --check
git diff --cached --check
```

---

## Step 4: 提交并推送

```bash
git add -A .trae/documents/fix-formation-engagement-smoke.md
git commit -m "chore: remove formation smoke task artifact"
git push
```

等待 CI green。

---

## Step 5: 输出 completion report

完成后输出包含：Summary, Removed files, PR body updates, Commands run, Verification, CI status, Known limitations, Next recommended step。
