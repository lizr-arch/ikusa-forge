import { formatNumber, formatValue, totalSkillTriggers } from "./formatters";
import type { BattleReport, KeyMoment, UnitReport } from "./replayTypes";

interface ReportRenderOptions {
  selectedUnitId: string | null;
  onSelectUnit: (unitId: string) => void;
  onSeekTick: (tick: number) => void;
}

export const renderReport = (
  container: HTMLElement,
  report: BattleReport | null,
  options: ReportRenderOptions,
): void => {
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
      ["Total Modifiers", formatNumber(report.summary?.total_modifiers)],
      ["Formation Modifiers", formatNumber(report.summary?.formation_modifiers)],
      ["Synergy Modifiers", formatNumber(report.summary?.synergy_modifiers)],
    ]),
  );

  container.append(section("Top Units", renderTopUnits(report, options)));
  container.append(section("Unit Reports", renderUnitTable(report.units ?? {}, options)));
  container.append(section("Key Moments", renderKeyMoments(report, options)));
};

const renderTopUnits = (report: BattleReport, options: ReportRenderOptions): HTMLElement => {
  const list = document.createElement("div");
  list.className = "top-units";
  const units = report.units ?? {};
  const topUnits = report.top_units ?? {};
  list.append(
    topUnitRow(
      "Damage Done",
      topUnits.damage_done ?? [],
      (unit) => units[unit]?.damage_done ?? 0,
      options,
    ),
    topUnitRow(
      "Damage Taken",
      topUnits.damage_taken ?? [],
      (unit) => units[unit]?.damage_taken ?? 0,
      options,
    ),
    topUnitRow(
      "Skill Triggers",
      topUnits.skill_triggers ?? [],
      (unit) => totalSkillTriggers(units[unit]),
      options,
    ),
  );
  return list;
};

const topUnitRow = (
  label: string,
  unitIds: string[],
  valueForUnit: (unitId: string) => number,
  options: ReportRenderOptions,
): HTMLElement => {
  const row = document.createElement("div");
  row.className = "top-unit-row";
  const title = document.createElement("div");
  title.className = "top-unit-title";
  title.textContent = label;
  const values = document.createElement("div");
  values.className = "top-unit-values";
  if (unitIds.length === 0) {
    values.textContent = "-";
  }
  for (const [index, unitId] of unitIds.entries()) {
    if (index > 0) {
      values.append(document.createTextNode(", "));
    }
    values.append(unitButton(unitId, `${unitId} (${valueForUnit(unitId)})`, options));
  }
  row.append(title, values);
  return row;
};

const renderUnitTable = (
  units: Record<string, UnitReport>,
  options: ReportRenderOptions,
): HTMLElement => {
  const wrapper = document.createElement("div");
  wrapper.className = "table-scroll";
  const table = document.createElement("table");
  table.className = "report-table";

  const head = document.createElement("thead");
  const headRow = document.createElement("tr");
  for (const title of ["Unit", "Done", "Taken", "Kills", "Deaths", "Skills", "ATK Bonus", "DEF Bonus", "Modifiers"]) {
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
    row.className = unitId === options.selectedUnitId ? "report-unit-row selected" : "report-unit-row";
    appendCell(row, unitButton(unitId, unitId, options));
    appendCell(row, formatNumber(unitReport.damage_done));
    appendCell(row, formatNumber(unitReport.damage_taken));
    appendCell(row, formatNumber(unitReport.kills));
    appendCell(row, formatNumber(unitReport.deaths));
    appendCell(row, formatNumber(totalSkillTriggers(unitReport)));
    appendCell(row, formatNumber((unitReport.stat_bonuses ?? {}).atk));
    appendCell(row, formatNumber((unitReport.stat_bonuses ?? {}).defense));
    appendCell(row, formatNumber(unitReport.modifiers_received));
    body.append(row);
  }
  if (Object.keys(units).length === 0) {
    const row = document.createElement("tr");
    const cell = document.createElement("td");
    cell.colSpan = 9;
    cell.textContent = "No unit rows";
    row.append(cell);
    body.append(row);
  }
  table.append(body);
  wrapper.append(table);
  return wrapper;
};

const renderKeyMoments = (report: BattleReport, options: ReportRenderOptions): HTMLElement => {
  const list = document.createElement("div");
  list.className = "key-moment-list";
  const keyMoments = report.key_moments ?? [];
  if (keyMoments.length === 0) {
    list.append(empty("No key moments"));
    return list;
  }
  for (const moment of keyMoments) {
    const item = document.createElement("button");
    item.type = "button";
    item.className = "key-moment";
    const seekTick = keyMomentTick(moment);
    item.disabled = seekTick === null;
    if (seekTick !== null) {
      item.addEventListener("click", () => options.onSeekTick(seekTick));
    }
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

const appendCell = (row: HTMLTableRowElement, value: string | HTMLElement): void => {
  const cell = document.createElement("td");
  if (typeof value === "string") {
    cell.textContent = value;
  } else {
    cell.append(value);
  }
  row.append(cell);
};

const unitButton = (
  unitId: string,
  label: string,
  options: ReportRenderOptions,
): HTMLButtonElement => {
  const button = document.createElement("button");
  button.type = "button";
  button.className = unitId === options.selectedUnitId ? "report-unit-link selected" : "report-unit-link";
  button.dataset.unitId = unitId;
  button.textContent = label;
  button.addEventListener("click", () => options.onSelectUnit(unitId));
  return button;
};

const keyMomentTick = (moment: KeyMoment): number | null => {
  const preferred = moment.type === "battle_end" ? moment.end_tick ?? moment.tick : moment.tick;
  return typeof preferred === "number" && Number.isFinite(preferred) ? preferred : null;
};

const empty = (message: string): HTMLElement => {
  const element = document.createElement("div");
  element.className = "empty-state";
  element.textContent = message;
  return element;
};
