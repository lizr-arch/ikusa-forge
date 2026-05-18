import path from "node:path";
import fs from "node:fs";
import type { ChildProcess } from "node:child_process";
import { spawn } from "node:child_process";
import { expect, test, type Page } from "@playwright/test";

const repoRoot = path.resolve(process.cwd(), "..");
const replayPath = path.join(repoRoot, "runs", "demo_001", "replay.json");
const reportPath = path.join(repoRoot, "runs", "demo_001", "battle_report.json");
const debugTimelinePath = path.join(repoRoot, "runs", "demo_001", "debug_timeline.json");

test("loads curated scenario from manifest", async ({ page }) => {
  await page.goto("/");

  await expect(page).toHaveTitle(/Ikusa Forge SVG Replay Viewer/);
  await expect(page.locator("#scenario-loader")).toBeVisible();
  await expect(page.locator("#scenario-loader")).toContainText("Scenario Selector");
  await expect(page.locator("#scenario-manifest-state")).toContainText("3 scenarios");
  await expect(page.locator("#scenario-select")).toContainText("demo_001");
  await expect(page.locator("#replay-file")).toBeAttached();
  await expect(page.locator("#report-file")).toBeAttached();

  await page.locator("#load-baseline-demo").click();

  await expect(page.locator("#status")).toContainText("scenario loaded（场景已加载）");
  await expect(page.locator("#board-heading")).toContainText("Battlefield（战场）");
  await expect(page.locator("#controls-heading")).toContainText("Battle Control（战斗控制）");
  await expect(page.locator("#live-mode-heading")).toContainText("Live Mode（实时模式）");
  await expect(page.locator("#timeline-heading")).toContainText("Event Log（事件日志）");
  await expect(page.locator("#report-heading")).toContainText("Report Panel（战报面板）");
  await expect(page.locator("text=Ally（友军）")).toBeVisible();
  await expect(page.locator("text=Enemy（敌军）")).toBeVisible();
  await expect(page.locator("#metadata")).toContainText("demo_001");
  await expect(page.locator("#metadata")).toContainText(/seed（种子）\s*1001|seed 1001/);
  await expect(page.locator("#replay-load-state")).toContainText(/samples\/demo_001\/replay\.json loaded/);
  await expect(page.locator("#report-load-state")).toContainText(/samples\/demo_001\/battle_report\.json loaded/);

  await expect(page.locator("#scenario-summary")).toContainText("Baseline Tactical Demo");
  await expect(page.locator("#scenario-summary")).toContainText("demo_001");
  await expect(page.locator("#scenario-summary")).toContainText("ally");
  await expect(page.locator("#scenario-summary")).toContainText("enemy_eliminated");
  await expect(page.locator("#scenario-summary")).toContainText("Status Applied");
  await expect(page.locator("#scenario-summary")).toContainText("Skill Cooldown");
  await expect(page.locator("#scenario-summary")).toContainText("Action Scheduled");

  await expect(page.locator("#battle-summary")).toContainText("ally");
  await expect(page.locator("#battle-summary")).toContainText("enemy_eliminated");
  await expect(page.locator("#battle-summary")).toContainText("240");

  await expect(page.getByRole("img", { name: "Replay board" })).toBeVisible();
  await expect(page.locator(".unit-token")).toHaveCount(12);

  const totalRows = await countTimelineRows(page);
  expect(totalRows).toBeGreaterThan(0);
  await expectFilteredTimelineRows(page, "status_apply");
  await expectFilteredTimelineRows(page, "skill_cooldown");
  await expectFilteredTimelineRows(page, "action_scheduled");

  await page.locator(".timeline-filter select").selectOption("skill_cooldown");
  await page.locator(".timeline-row").first().click();
    await expect(page.locator("#event-highlight")).toContainText(/Ready Tick（就绪回合）|ready_tick/);
  await page.locator(".timeline-filter select").selectOption("action_scheduled");
  await page.locator(".timeline-row").first().click();
    await expect(page.locator("#event-highlight")).toContainText(/Next Action Tick（下次行动回合）|next_action_tick/);

  await page.locator('[aria-label="ally_001"]').click();
  await expect(page.locator("#unit-detail")).toContainText(/Next Action Tick（下次行动）|Next Action/);
  await expect(page.locator("#report")).toContainText("Victory Explanation");
  await expect(page.locator("#report")).toContainText("enemy_eliminated");
});

test("manual file input loading remains available", async ({ page }) => {
  const debugTimeline = JSON.parse(fs.readFileSync(debugTimelinePath, "utf8"));
  const modifierRows = debugTimeline.filter((event: { type?: string }) => event.type === "stat_modifier");
  const statusRows = debugTimeline.filter((event: { type?: string }) => event.type === "status_apply");
  const cooldownRows = debugTimeline.filter((event: { type?: string }) => event.type === "skill_cooldown");
  const actionScheduleRows = debugTimeline.filter((event: { type?: string }) => event.type === "action_scheduled");
  const modifierSourceTypes = new Set(
    debugTimeline
      .filter((event: { type?: string; payload?: { source_type?: string } }) => event.type === "stat_modifier")
      .map((event: { payload?: { source_type?: string } }) => event.payload?.source_type)
      .filter((sourceType): sourceType is string => sourceType === "formation" || sourceType === "synergy"),
  );

  expect(modifierRows.length).toBeGreaterThan(0);
  expect(statusRows.length).toBeGreaterThan(0);
  expect(cooldownRows.length).toBeGreaterThan(0);
  expect(actionScheduleRows.length).toBeGreaterThan(0);
  expect(modifierSourceTypes.has("formation")).toBeTruthy();
  expect(modifierSourceTypes.has("synergy")).toBeTruthy();

  await page.goto("/");

  await expect(page).toHaveTitle(/Ikusa Forge SVG Replay Viewer/);
  await expect(page.locator("#replay-file")).toBeAttached();
  await expect(page.locator("#report-file")).toBeAttached();
  await expect(page.locator("#demo-guidance")).toContainText("Demo Load Guidance");
  await expect(page.locator("#demo-guidance")).toContainText("Demo files expected");
  await expect(page.locator("#demo-guidance")).toContainText("tools/run_demo_battle.py");

  await page.locator("#replay-file").setInputFiles(replayPath);
  await page.locator("#report-file").setInputFiles(reportPath);
  await page.locator("#load-files").click();

  await expect(page.locator("#status")).toContainText("replay.json loaded（已加载）");
  await expect(page.locator("#status")).toContainText("battle_report.json loaded（已加载）");
  await expect(page.locator("#metadata")).toContainText("demo_001");
  await expect(page.locator("#metadata")).toContainText(/seed（种子）\s*1001|seed 1001/);
  await expect(page.locator("#metadata")).toContainText(/events（事件）|events/);
  await expect(page.locator("#replay-load-state")).toContainText(/replay\.json loaded/);
  await expect(page.locator("#report-load-state")).toContainText(/battle_report\.json loaded/);

  await expect(page.locator("#battle-summary")).toContainText("demo_001");
  await expect(page.locator("#battle-summary")).toContainText("ally");
  await expect(page.locator("#battle-summary")).toContainText("enemy_eliminated");
  await expect(page.locator("#battle-summary")).toContainText(/end tick|end_tick/i);
  await expect(page.locator("#battle-summary")).toContainText("240");

  await expect(page.getByRole("img", { name: "Replay board" })).toBeVisible();
  await expect(page.locator(".unit-token")).toHaveCount(12);
  await expect(page.locator('[aria-label="ally_001"]')).toBeVisible();
  await expect(page.locator('[aria-label="enemy_001"]')).toBeVisible();

  const totalRows = await countTimelineRows(page);
  expect(totalRows).toBeGreaterThan(0);
  expect(totalRows).toBeGreaterThan(await countTimelineRows(page, "stat_modifier"));
  await expectFilteredTimelineRows(page, "damage");
  await expectFilteredTimelineRows(page, "skill_trigger");
  await expectFilteredTimelineRows(page, "death");
  await expectFilteredTimelineRows(page, "stat_modifier");
  await expectFilteredTimelineRows(page, "status_apply");
  await expectFilteredTimelineRows(page, "skill_cooldown");
  await expectFilteredTimelineRows(page, "action_scheduled");
  await page.locator(".timeline-filter select").selectOption("all");

  await page.locator('[aria-label="ally_001"]').click();
  await expect(page.locator("#unit-detail")).toContainText("ally_001");
  await expect(page.locator("#unit-detail")).toContainText(/Status（状态）|Active Statuses/);
  await expect(page.locator("#unit-detail")).toContainText(/HP（生命）|HP/);
  await expect(page.locator("#unit-detail")).toContainText(/Cooldown（冷却）|Cooldowns/);
  await expect(page.locator("#unit-detail")).toContainText(/Next Action（下次行动）|Next Action Tick/);

  const initialTick = await page.locator("#tick-readout").textContent();
  const initialEventSummary = await page.locator("#event-highlight .event-highlight-summary").textContent();
  await page.locator("#next-event").click();
  const nextTick = await page.locator("#tick-readout").textContent();
  const nextEventSummary = await page.locator("#event-highlight .event-highlight-summary").textContent();
  expect(nextTick).not.toBe(initialTick);
  expect(nextEventSummary).not.toBe(initialEventSummary);
  await expect(page.locator("#event-readout")).toContainText(/Event（事件） evt_|Event evt_/);
  await expect(page.locator(".timeline-row.selected")).toBeVisible();

  await page.locator("#previous-event").click();
  await expect(page.locator("#tick-readout")).not.toHaveText(nextTick ?? "");

  await page.locator("#tick-slider").evaluate((slider) => {
    const input = slider as HTMLInputElement;
    input.value = "56";
    input.dispatchEvent(new Event("input", { bubbles: true }));
  });
  await expect(page.locator("#tick-readout")).toContainText(/Tick（回合） 56|Tick 56/);

  await page.locator(".timeline-filter select").selectOption("damage");
  await page.locator(".timeline-row").first().click();
  await expect(page.locator("#event-highlight")).toContainText("Reason");
  await expect(page.locator("#event-highlight")).toContainText(/basic_attack|skill:/);

  await page.locator(".timeline-filter select").selectOption("attack");
  const attackRow = page.locator(".timeline-row").first();
  await expect(attackRow).toBeVisible();
  await attackRow.click();
  await expect(page.locator("#event-highlight")).toContainText("Target Reason");
  await expect(page.locator("#event-highlight")).toContainText("Target Score");

  await page.locator(".timeline-filter select").selectOption("skill_trigger");
  const skillRow = page.locator(".timeline-row").first();
  await expect(skillRow).toBeVisible();
  await skillRow.click();
  await expect(page.locator("#event-highlight")).toContainText("Target Reason");
  await expect(page.locator("#event-highlight")).toContainText("Target Score");

  await page.locator(".timeline-filter select").selectOption("stat_modifier");
  const firstModifier = page.locator(".timeline-row").first();
  await expect(firstModifier).toBeVisible();
  await firstModifier.click();
  await expect(page.locator("#event-highlight")).toContainText("modifies");
  await expect(page.locator("#event-highlight")).toContainText("Reason");
  await expect(page.locator("#event-highlight")).toContainText("Source Type");

  await page.locator(".timeline-filter select").selectOption("status_apply");
  const firstStatus = page.locator(".timeline-row").first();
  await expect(firstStatus).toBeVisible();
  await firstStatus.click();
  await expect(page.locator("#event-highlight")).toContainText("status_apply");
  await expect(page.locator("#event-highlight")).toContainText("Reason");

  await page.locator(".timeline-filter select").selectOption("skill_cooldown");
  const firstCooldown = page.locator(".timeline-row").first();
  await expect(firstCooldown).toBeVisible();
  await firstCooldown.click();
  await expect(page.locator("#event-highlight")).toContainText(/Ready Tick（就绪回合）|ready_tick/);

  await page.locator(".timeline-filter select").selectOption("action_scheduled");
  const firstActionSchedule = page.locator(".timeline-row").first();
  await expect(firstActionSchedule).toBeVisible();
  await firstActionSchedule.click();
  await expect(page.locator("#event-highlight")).toContainText(/Next Action Tick（下次行动回合）|next_action_tick/);

  await expect(page.locator("#report")).toContainText("Target Reasons");
  await expect(page.locator("#report")).toContainText("Skill Target Reasons");
  await expect(page.locator("#report")).toContainText("Victory Explanation");
  await expect(page.locator("#report")).toContainText("Status Applied");
  await expect(page.locator("#report")).toContainText("Skill Cooldown");
  await expect(page.locator("#report")).toContainText("Action Scheduled");

  await page.locator('#report .report-table .report-unit-link[data-unit-id="ally_003"]').click();
  await expect(page.locator("#unit-detail")).toContainText("ally_003");
  await expect(page.locator('[aria-label="ally_003"].unit-selected')).toBeVisible();

  await expect(page.locator("#battle-summary")).toContainText("Total Modifiers");
  await expect(page.locator("#report")).toContainText(/Total Modifiers（总修正）|Total Modifiers/);
  await expect(page.locator("#report")).toContainText(/Formation Modifiers（编队修正）|Formation Modifiers/);
  await expect(page.locator("#report")).toContainText(/Synergy Modifiers（协同修正）|Synergy Modifiers/);
  await expect(page.locator("#report")).toContainText(/ATK Bonus（攻击加成）|ATK Bonus/);
  await expect(page.locator("#report")).toContainText(/DEF Bonus（防御加成）|DEF Bonus/);

  await page.locator(".key-moment").filter({ hasText: "enemy_eliminated" }).click();
  await expect(page.locator("#tick-readout")).toContainText(/Tick（回合） 240|Tick 240/);

  await expect(page.locator("#report")).toContainText("enemy_eliminated");
  await expect(page.locator("#report")).toContainText("Total Damage");
  await expect(page.locator("#report")).toContainText(/Top Units（最优单位）|Key Moments（关键时刻）/);
});

test("live mode controls are visible and API errors are readable", async ({ page }) => {
  await page.goto("/");

  await expect(page.locator("#live-mode-heading")).toBeVisible();
  await expect(page.locator("#start-live-battle")).toBeVisible();
  await expect(page.locator("#live-api-url")).toBeVisible();
  await expect(page.locator("#live-battle-id")).toBeVisible();
  await expect(page.locator("#live-seed")).toBeVisible();

  await page.locator("#live-api-url").fill("http://127.0.0.1:65535");
  await page.locator("#live-battle-id").fill("demo_001");
  await page.locator("#live-seed").fill("1001");
  await page.locator("#start-live-battle").click();

  await expect(page.locator("#live-status-line")).toContainText(/Live API unavailable（实时 API 不可用）|不可用|Live API unavailable/i);
  await expect(page.locator("#status")).toContainText(/Live API unavailable（实时 API 不可用）|不可用|Live API unavailable|failed/i);
});

test("live mode can start and step with local API", async ({ page }) => {
  const generatedUnits = path.join(repoRoot, "config", "generated", "units.json");
  if (!fs.existsSync(generatedUnits)) {
    test.skip(true, "config/generated is not prepared for local live API test");
  }

  const apiPort = 8766;
  const apiUrl = `http://127.0.0.1:${apiPort}`;
  const apiProcess = startLiveApiProcess(apiPort);

  try {
    await waitForLiveApi(apiUrl, apiProcess);

    await page.goto("/");
    await expect(page.locator("#live-mode-heading")).toBeVisible();
    await expect(page.locator("#live-api-url")).toBeVisible();
    await expect(page.locator("#live-battle-id")).toBeVisible();
    await expect(page.locator("#live-seed")).toBeVisible();

    await page.locator("#live-api-url").fill(apiUrl);
    await page.locator("#live-battle-id").fill("demo_001");
    await page.locator("#live-seed").fill("1001");
    await page.locator("#start-live-battle").click();

    await expect(page.locator("#live-session-id")).not.toHaveText("-", { timeout: 10_000 });
    await expect(page.locator("#live-status-line")).toContainText(/connected|running|运行/i, { timeout: 10_000 });
    await expect(page.locator("#metadata")).toContainText(/battle（战斗）\s*demo_001|battle demo_001/);
    await expect(page.locator("#metadata")).toContainText(/seed（种子）\s*1001|seed 1001/);
    await expect(page.locator("#metadata")).toContainText("events ");
    await expect(page.locator("#board")).toBeVisible();
    await expect(page.locator(".unit-token")).toHaveCount(12, { timeout: 10_000 });
    await expect(page.locator(".health-fill")).toHaveCount(12, { timeout: 10_000 });
    await expect(page.locator(".action-bar-bg")).toHaveCount(12, { timeout: 10_000 });
    await expect(page.locator(".unit-status-count")).toHaveCount(12, { timeout: 10_000 });
    await expect(page.locator(".unit-cooldown-count")).toHaveCount(12, { timeout: 10_000 });
    await expect(page.locator("#live-current-tick")).toHaveText(/\d+/);

    let beforeCursor = Number((await page.locator("#live-event-cursor").textContent()) ?? "0");
    let beforeTick = (await page.locator("#tick-readout").textContent()) ?? "Tick 0";
    let beforeTimelineRows = await countTimelineRows(page);
    let effectFound = false;
    for (let attempt = 0; attempt < 6 && !effectFound; attempt += 1) {
      await page.locator("#step-live-battle").click();
      await waitForLiveProgress(page, beforeCursor, beforeTick, beforeTimelineRows);
      effectFound = await hasLiveVisualEffect(page);
      beforeCursor = Number((await page.locator("#live-event-cursor").textContent()) ?? "0");
      beforeTick = (await page.locator("#tick-readout").textContent()) ?? "Tick 0";
      beforeTimelineRows = await countTimelineRows(page);
    }
    expect(effectFound).toBeTruthy();

    await page.locator("#reset-live-battle").click();
    await expect(page.locator("#live-session-id")).toContainText("-", { timeout: 10_000 });
    await expect(page.locator("#live-status")).toContainText(/ready|idle/i, { timeout: 10_000 });
    await expect(page.locator("#live-event-cursor")).toHaveText("0");
  } finally {
    await stopLiveApiProcess(apiProcess);
  }
});

const expectFilteredTimelineRows = async (
  page: Page,
  filter: string,
): Promise<void> => {
  await page.locator(".timeline-filter select").selectOption(filter);
  await expect(page.locator(".timeline-row").first()).toBeVisible();
  const filteredCount = await countTimelineRows(page, filter);
  expect(filteredCount).toBeGreaterThan(0);
};

const countTimelineRows = async (page: Page, filter?: string): Promise<number> => {
  if (filter) {
    await page.locator(".timeline-filter select").selectOption(filter);
  }
  return Number(await page.locator(".timeline-row").count());
};

const startLiveApiProcess = (port: number): ChildProcess => {
  const server = spawn("python", [
    "tools/run_live_api.py",
    "--config",
    "config/generated",
    "--host",
    "127.0.0.1",
    "--port",
    String(port),
  ], { cwd: repoRoot, stdio: "ignore" });

  return server;
};

const stopLiveApiProcess = async (server: ChildProcess): Promise<void> => {
  if (server.killed || server.exitCode !== null) {
    return;
  }

  server.kill();
  await new Promise<void>((resolve) => {
    server.once("exit", () => {
      resolve();
    });
  });
};

const waitForLiveApi = async (url: string, proc: ChildProcess, timeoutMs = 12_000): Promise<void> => {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    try {
      const response = await fetch(`${url}/api/health`);
      if (response.ok) {
        return;
      }
    } catch (error) {
      // ignore and retry
    }
    if (proc.exitCode !== null) {
      throw new Error(`Live API exited before ready. Code=${proc.exitCode}`);
    }
    await wait(100);
  }
  throw new Error(`Live API failed to start: ${url}`);
};

const wait = (ms: number): Promise<void> =>
  new Promise((resolve) => {
    setTimeout(resolve, ms);
  });

const waitForLiveProgress = async (
  page: Page,
  beforeCursor: number,
  beforeTick: string,
  beforeTimelineRows: number,
): Promise<void> => {
  const deadline = Date.now() + 10_000;
  while (Date.now() < deadline) {
    const afterCursor = Number((await page.locator("#live-event-cursor").textContent()) ?? "0");
    const afterTick = (await page.locator("#tick-readout").textContent()) ?? "Tick 0";
    const afterTimelineRows = await countTimelineRows(page);

    if (afterCursor !== beforeCursor || afterTick !== beforeTick || afterTimelineRows > beforeTimelineRows) {
      return;
    }
    await wait(100);
  }
  throw new Error("Live step produced no visible progress");
};

const hasLiveVisualEffect = async (page: Page): Promise<boolean> => {
  const hasAttackLine = await page.locator(".attack-line").count() > 0;
  const hasUnitEventRing = await page.locator(".unit-event-ring").count() > 0;
  const hasDamage = await page.locator(".damage-label").count() > 0;
  const hasSkill = await page.locator(".skill-label").count() > 0;
  const hasStatus = await page.locator(".status-badge").count() > 0;
  const hasCooldown = await page.locator(".cooldown-badge").count() > 0;
  const hasVictory = await page.locator(".victory-banner, .battle-end-banner").count() > 0;
  const hasModifierRing = await page.locator(".modifier-ring").count() > 0;

  return hasAttackLine
    || hasUnitEventRing
    || hasDamage
    || hasSkill
    || hasStatus
    || hasCooldown
    || hasVictory
    || hasModifierRing;
};
