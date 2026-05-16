import { formatNumber, formatValue, totalSkillTriggers } from "./formatters";
import type { BattleReport, UnitReport } from "./replayTypes";

export const renderReport = (container: HTMLElement, report: BattleReport | null): void => {
  container.replaceChildren();
  if (!report) {
    container.append(empty("No battle report loaded"));
    return;
  }

  container.append(
    statGrid([
      ["Winner", formatValue(report.winner)],
      ["Reason", formatValue(report.reason)],
      ["End Tick", formatNumber(report.end_tick)],
      ["Total Damage", formatNumber(report.summary?.total_damage)],
      ["Total Kills", formatNumber(report.summary?.total_kills)],
      ["Skill Triggers", formatNumber(report.summary?.total_skill_triggers)],
    ]),
  );

  container.append(section("Top Units", renderTopUnits(report)));
  container.append(section("Unit Reports", renderUnitTable(report.units ?? {})));
  container.append(section("Key Moments", renderKeyMoments(report)));
};

const renderTopUnits = (report: BattleReport): HTMLElement => {
  const list = document.createElement("div");
  list.className = "top-units";
  const units = report.units ?? {};
  const topUnits = report.top_units ?? {};
  list.append(
    topUnitRow("Damage Done", topUnits.damage_done ?? [], (unit) => units[unit]?.damage_done ?? 0),
    topUnitRow("Damage Taken", topUnits.damage_taken ?? [], (unit) => units[unit]?.damage_taken ?? 0),
    topUnitRow("Skill Triggers", topUnits.skill_triggers ?? [], (unit) => totalSkillTriggers(units[unit])),
  );
  return list;
};

const topUnitRow = (
  label: string,
  unitIds: string[],
  valueForUnit: (unitId: string) => number,
): HTMLElement => {
  const row = document.createElement("div");
  row.className = "top-unit-row";
  const title = document.createElement("div");
  title.className = "top-unit-title";
  title.textContent = label;
  const values = document.createElement("div");
  values.className = "top-unit-values";
  values.textContent =
    unitIds.length > 0
      ? unitIds.map((unitId) => `${unitId} (${valueForUnit(unitId)})`).join(", ")
      : "-";
  row.append(title, values);
  return row;
};

const renderUnitTable = (units: Record<string, UnitReport>): HTMLElement => {
  const wrapper = document.createElement("div");
  wrapper.className = "table-scroll";
  const table = document.createElement("table");
  table.className = "report-table";

  const head = document.createElement("thead");
  const headRow = document.createElement("tr");
  for (const title of ["Unit", "Done", "Taken", "Kills", "Deaths", "Skills"]) {
    const th = document.createElement("th");
    th.textContent = title;
    headRow.append(th);
  }
  head.append(headRow);
  table.append(head);

  const body = document.createElement("tbody");
  for (const [unitId, unitReport] of Object.entries(units).sort(([left], [right]) =>
    left.localeCompare(right),
  )) {
    const row = document.createElement("tr");
    appendCell(row, unitId);
    appendCell(row, formatNumber(unitReport.damage_done));
    appendCell(row, formatNumber(unitReport.damage_taken));
    appendCell(row, formatNumber(unitReport.kills));
    appendCell(row, formatNumber(unitReport.deaths));
    appendCell(row, formatNumber(totalSkillTriggers(unitReport)));
    body.append(row);
  }
  if (Object.keys(units).length === 0) {
    const row = document.createElement("tr");
    const cell = document.createElement("td");
    cell.colSpan = 6;
    cell.textContent = "No unit rows";
    row.append(cell);
    body.append(row);
  }
  table.append(body);
  wrapper.append(table);
  return wrapper;
};

const renderKeyMoments = (report: BattleReport): HTMLElement => {
  const list = document.createElement("div");
  list.className = "key-moment-list";
  const keyMoments = report.key_moments ?? [];
  if (keyMoments.length === 0) {
    list.append(empty("No key moments"));
    return list;
  }
  for (const moment of keyMoments) {
    const item = document.createElement("div");
    item.className = "key-moment";
    const tick = document.createElement("span");
    tick.className = "key-moment-tick";
    tick.textContent = `T${formatNumber(moment.tick)}`;
    const summary = document.createElement("span");
    summary.textContent = moment.summary ?? formatValue(moment.type);
    item.append(tick, summary);
    list.append(item);
  }
  return list;
};

const statGrid = (rows: [string, string][]): HTMLElement => {
  const grid = document.createElement("div");
  grid.className = "stat-grid";
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

const section = (title: string, content: HTMLElement): HTMLElement => {
  const block = document.createElement("section");
  block.className = "report-section";
  const heading = document.createElement("h3");
  heading.textContent = title;
  block.append(heading, content);
  return block;
};

const appendCell = (row: HTMLTableRowElement, value: string): void => {
  const cell = document.createElement("td");
  cell.textContent = value;
  row.append(cell);
};

const empty = (message: string): HTMLElement => {
  const element = document.createElement("div");
  element.className = "empty-state";
  element.textContent = message;
  return element;
};
