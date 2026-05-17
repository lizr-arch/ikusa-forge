import path from "node:path";
import fs from "node:fs";
import { expect, test, type Page } from "@playwright/test";

const repoRoot = path.resolve(process.cwd(), "..");
const replayPath = path.join(repoRoot, "runs", "demo_001", "replay.json");
const reportPath = path.join(repoRoot, "runs", "demo_001", "battle_report.json");
const debugTimelinePath = path.join(repoRoot, "runs", "demo_001", "debug_timeline.json");

test("loads replay and report into the SVG replay viewer", async ({ page }) => {
  const debugTimeline = JSON.parse(fs.readFileSync(debugTimelinePath, "utf8"));
  const modifierRows = debugTimeline.filter((event: { type?: string }) => event.type === "stat_modifier");
  const modifierSourceTypes = new Set(
    debugTimeline
      .filter((event: { type?: string; payload?: { source_type?: string } }) => event.type === "stat_modifier")
      .map((event: { payload?: { source_type?: string } }) => event.payload?.source_type)
      .filter((sourceType): sourceType is string => sourceType === "formation" || sourceType === "synergy"),
  );

  expect(modifierRows.length).toBeGreaterThan(0);
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

  await expect(page.locator("#status")).toContainText("replay.json loaded");
  await expect(page.locator("#status")).toContainText("battle_report.json loaded");
  await expect(page.locator("#metadata")).toContainText("demo_001");
  await expect(page.locator("#metadata")).toContainText("seed 1001");
  await expect(page.locator("#metadata")).toContainText("events ");
  await expect(page.locator("#replay-load-state")).toContainText("replay.json loaded");
  await expect(page.locator("#report-load-state")).toContainText("battle_report.json loaded");

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
  await page.locator(".timeline-filter select").selectOption("all");

  await page.locator('[aria-label="ally_001"]').click();
  await expect(page.locator("#unit-detail")).toContainText("ally_001");

  const initialTick = await page.locator("#tick-readout").textContent();
  const initialEventSummary = await page.locator("#event-highlight .event-highlight-summary").textContent();
  await page.locator("#next-event").click();
  const nextTick = await page.locator("#tick-readout").textContent();
  const nextEventSummary = await page.locator("#event-highlight .event-highlight-summary").textContent();
  expect(nextTick).not.toBe(initialTick);
  expect(nextEventSummary).not.toBe(initialEventSummary);
  await expect(page.locator("#event-readout")).toContainText("Event evt_");
  await expect(page.locator(".timeline-row.selected")).toBeVisible();

  await page.locator("#previous-event").click();
  await expect(page.locator("#tick-readout")).not.toHaveText(nextTick ?? "");

  await page.locator("#tick-slider").evaluate((slider) => {
    const input = slider as HTMLInputElement;
    input.value = "56";
    input.dispatchEvent(new Event("input", { bubbles: true }));
  });
  await expect(page.locator("#tick-readout")).toContainText("Tick 56");

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

  await expect(page.locator("#report")).toContainText("Target Reasons");
  await expect(page.locator("#report")).toContainText("Skill Target Reasons");

  await page.locator('#report .report-table .report-unit-link[data-unit-id="ally_003"]').click();
  await expect(page.locator("#unit-detail")).toContainText("ally_003");
  await expect(page.locator('[aria-label="ally_003"].unit-selected')).toBeVisible();

  await expect(page.locator("#battle-summary")).toContainText("Total Modifiers");
  await expect(page.locator("#report")).toContainText("Total Modifiers");
  await expect(page.locator("#report")).toContainText("Formation Modifiers");
  await expect(page.locator("#report")).toContainText("Synergy Modifiers");
  await expect(page.locator("#report")).toContainText("ATK Bonus");
  await expect(page.locator("#report")).toContainText("DEF Bonus");

  await page.locator(".key-moment").filter({ hasText: "Battle ended" }).click();
  await expect(page.locator("#tick-readout")).toContainText("Tick 240");

  await expect(page.locator("#report")).toContainText("enemy_eliminated");
  await expect(page.locator("#report")).toContainText("Total Damage");
  await expect(page.locator("#report")).toContainText(/Top Units|Key Moments/);
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
