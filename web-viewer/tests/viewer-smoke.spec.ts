import path from "node:path";
import { expect, test, type Page } from "@playwright/test";

const repoRoot = path.resolve(process.cwd(), "..");
const replayPath = path.join(repoRoot, "runs", "demo_001", "replay.json");
const reportPath = path.join(repoRoot, "runs", "demo_001", "battle_report.json");

test("loads replay and report into the SVG replay viewer", async ({ page }) => {
  await page.goto("/");

  await expect(page).toHaveTitle(/Ikusa Forge SVG Replay Viewer/);
  await expect(page.locator("#replay-file")).toBeAttached();
  await expect(page.locator("#report-file")).toBeAttached();

  await page.locator("#replay-file").setInputFiles(replayPath);
  await page.locator("#report-file").setInputFiles(reportPath);
  await page.locator("#load-files").click();

  await expect(page.locator("#status")).toContainText("replay.json loaded");
  await expect(page.locator("#status")).toContainText("battle_report.json loaded");
  await expect(page.locator("#metadata")).toContainText("demo_001");
  await expect(page.locator("#metadata")).toContainText("seed 1001");
  await expect(page.locator("#metadata")).toContainText("events 217");

  await expect(page.getByRole("img", { name: "Replay board" })).toBeVisible();
  await expect(page.locator(".unit-token")).toHaveCount(12);
  await expect(page.locator('[aria-label="ally_001"]')).toBeVisible();
  await expect(page.locator('[aria-label="enemy_001"]')).toBeVisible();

  await expect(page.locator(".timeline-row")).toHaveCount(217);
  await expectFilteredTimelineRows(page, "damage");
  await expectFilteredTimelineRows(page, "skill_trigger");
  await expectFilteredTimelineRows(page, "death");

  await page.locator('[aria-label="ally_001"]').click();
  await expect(page.locator("#unit-detail")).toContainText("ally_001");

  const initialTick = await page.locator("#tick-readout").textContent();
  await page.locator("#next-event").click();
  const nextTick = await page.locator("#tick-readout").textContent();
  expect(nextTick).not.toBe(initialTick);

  await page.locator("#previous-event").click();
  await expect(page.locator("#tick-readout")).not.toHaveText(nextTick ?? "");

  await page.locator("#tick-slider").evaluate((slider) => {
    const input = slider as HTMLInputElement;
    input.value = "56";
    input.dispatchEvent(new Event("input", { bubbles: true }));
  });
  await expect(page.locator("#tick-readout")).toHaveText("Tick 56");

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
};
