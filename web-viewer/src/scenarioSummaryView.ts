import { formatNumber, formatValue } from "./formatters";
import type { BattleReport, DemoScenario, ReplayDocument } from "./replayTypes";

interface ScenarioSummaryOptions {
  scenario: DemoScenario | null;
  replay: ReplayDocument | null;
  report: BattleReport | null;
  eventCount: number;
}

export const renderScenarioSummary = (
  container: HTMLElement,
  options: ScenarioSummaryOptions,
): void => {
  container.replaceChildren();

  if (!options.scenario) {
    const empty = document.createElement("div");
    empty.className = "empty-state";
    empty.textContent = "No curated scenario loaded";
    container.append(empty);
    return;
  }

  const title = document.createElement("div");
  title.className = "scenario-title";
  const name = document.createElement("strong");
  name.textContent = options.scenario.name;
  const id = document.createElement("span");
  id.textContent = options.scenario.id;
  title.append(name, id);

  const description = document.createElement("p");
  description.className = "scenario-description";
  description.textContent = options.scenario.description;

  const replayResult = options.replay?.metadata.result ?? null;
  const summary = options.report?.summary;
  const rows: [string, string][] = [
    ["Scenario ID", options.scenario.id],
    ["Winner", formatValue(options.report?.winner ?? replayResult?.winner)],
    ["Reason", formatValue(options.report?.reason ?? replayResult?.reason)],
    ["End Tick", formatNumber(options.report?.end_tick ?? replayResult?.end_tick)],
    ["Events", formatNumber(options.eventCount)],
    ["Total Damage", formatNumber(summary?.total_damage)],
    ["Status Applied", formatNumber(summary?.total_status_applied)],
    ["Skill Cooldowns", formatNumber(summary?.total_skill_cooldowns)],
    ["Actions Scheduled", formatNumber(summary?.total_actions_scheduled)],
  ];

  container.append(title, description, statGrid(rows));
};

const statGrid = (rows: [string, string][]): HTMLElement => {
  const grid = document.createElement("div");
  grid.className = "stat-grid scenario-summary-grid";
  for (const [label, value] of rows) {
    const item = document.createElement("div");
    item.className = "stat-item";
    const key = document.createElement("span");
    key.textContent = label;
    const val = document.createElement("strong");
    val.textContent = value;
    item.append(key, val);
    grid.append(item);
  }
  return grid;
};
