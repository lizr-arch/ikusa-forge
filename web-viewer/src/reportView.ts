import { formatNumber, formatValue, totalSkillTriggers } from "./formatters";
import type { BattleReport, KeyMoment, LiveBattleResult, UnitReport } from "./replayTypes";

interface ReportRenderOptions {
  selectedUnitId: string | null;
  onSelectUnit: (unitId: string) => void;
  onSeekTick: (tick: number) => void;
  liveMode?: boolean;
  isFinished?: boolean;
  liveResult?: LiveBattleResult | null;
  liveCurrentTick?: number;
}

export const renderReport = (
  container: HTMLElement,
  report: BattleReport | null,
  options: ReportRenderOptions,
): void => {
  container.replaceChildren();
  if (options.liveMode && !options.isFinished && !report) {
    container.append(empty("Live battle in progress（实时战斗进行中）"));
    return;
  }
  if (options.liveMode && options.isFinished && options.liveResult && !report) {
    container.append(
      statGrid([
        ["Snapshot Tick（快照回合）", formatNumber(options.liveCurrentTick)],
        ["Winner（胜利）", formatValue(options.liveResult.winner)],
        ["Reason（原因）", formatValue(options.liveResult.reason)],
        ["End Tick（终止回合）", formatNumber(options.liveResult.end_tick)],
        ["Victory Explanation（胜负解释）", formatValue(options.liveResult.summary)],
      ]),
    );
    return;
  }

  if (!report) {
    container.append(empty("No battle report loaded（未加载战报）"));
    return;
  }

  container.append(
    statGrid([
      ["Winner（胜利）", formatValue(report.winner)],
      ["Reason（原因）", formatValue(report.reason)],
      ["End Tick（终止回合）", formatNumber(report.end_tick)],
      ["Total Damage（总伤害）", formatNumber(report.summary?.total_damage)],
      ["Total Kills（总击杀）", formatNumber(report.summary?.total_kills)],
      ["Skill Triggers（技能触发）", formatNumber(report.summary?.total_skill_triggers)],
      ["Status Applied（状态应用）", formatNumber(report.summary?.total_status_applied)],
      ["Status Expired（状态到期）", formatNumber(report.summary?.total_status_expired)],
      ["Skill Cooldown（技能冷却）", formatNumber(report.summary?.total_skill_cooldowns)],
      ["Action Scheduled（行动调度）", formatNumber(report.summary?.total_actions_scheduled)],
      ["Total Modifiers（总修正）", formatNumber(report.summary?.total_modifiers)],
      ["Formation Modifiers（编队修正）", formatNumber(report.summary?.formation_modifiers)],
      ["Synergy Modifiers（协同修正）", formatNumber(report.summary?.synergy_modifiers)],
      ["Victory Explanation（胜负解释）", formatValue(report.victory_explanation?.summary)],
      ["Target Reasons（目标原因）", formatReasonSummary(report.summary?.target_reason_counts)],
      ["Skill Target Reasons（技能目标原因）", formatReasonSummary(report.summary?.skill_target_reason_counts)],
    ]),
  );

  container.append(section("Top Units（最优单位）", renderTopUnits(report, options)));
  container.append(section("Unit Reports（单位报表）", renderUnitTable(report.units ?? {}, options)));
  container.append(section("Key Moments（关键时刻）", renderKeyMoments(report, options)));
};

const renderTopUnits = (report: BattleReport, options: ReportRenderOptions): HTMLElement => {
  const list = document.createElement("div");
  list.className = "top-units";
  const units = report.units ?? {};
  const topUnits = report.top_units ?? {};
  list.append(
    topUnitRow(
      "Damage Done（伤害输出）",
      topUnits.damage_done ?? [],
      (unit) => units[unit]?.damage_done ?? 0,
      options,
    ),
    topUnitRow(
      "Damage Taken（承受伤害）",
      topUnits.damage_taken ?? [],
      (unit) => units[unit]?.damage_taken ?? 0,
      options,
    ),
    topUnitRow(
      "Skill Triggers（技能触发）",
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
  for (const title of [
    "Unit（单位）",
    "Done（完成）",
    "Taken（承受）",
    "Kills（击杀）",
    "Deaths（死亡）",
    "Skills（技能）",
    "Statuses（状态）",
    "Cooldowns（冷却）",
    "Actions（行动）",
    "Next Action（下次行动）",
    "ATK Bonus（攻击加成）",
    "DEF Bonus（防御加成）",
    "HP Bonus（生命加成）",
    "ATKSPD Bonus（攻速加成）",
    "Modifiers（修正）",
  ]) {
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
    appendCell(row, formatNumber(unitReport.statuses_applied));
    appendCell(row, formatNumber(unitReport.cooldowns_started));
    appendCell(row, formatNumber(unitReport.actions_taken));
    appendCell(row, formatNumber(unitReport.last_next_action_tick));
    appendCell(row, formatNumber((unitReport.stat_bonuses ?? {}).atk));
    appendCell(row, formatNumber((unitReport.stat_bonuses ?? {}).defense));
    appendCell(row, formatNumber((unitReport.stat_bonuses ?? {}).hp));
    appendCell(row, formatNumber((unitReport.stat_bonuses ?? {}).attack_interval_delta));
    appendCell(row, formatNumber(unitReport.modifiers_received));
    body.append(row);
  }
  if (Object.keys(units).length === 0) {
    const row = document.createElement("tr");
    const cell = document.createElement("td");
    cell.colSpan = 15;
    cell.textContent = "No unit rows（无单位行）";
    row.append(cell);
    body.append(row);
  }
  table.append(body);
  wrapper.append(table);
  return wrapper;
};

const formatReasonSummary = (counts: Record<string, number> | undefined): string => {
  if (!counts) {
    return "-";
  }
  const entries = Object.entries(counts)
    .filter(([, value]) => value > 0)
    .sort((left, right) => {
      if (right[1] !== left[1]) {
        return right[1] - left[1];
      }
      return left[0].localeCompare(right[0]);
    });
  if (entries.length === 0) {
    return "-";
  }
  return entries
    .slice(0, 3)
    .map(([reason, count]) => `${reason}:${count}`)
    .join(" | ");
};

const renderKeyMoments = (report: BattleReport, options: ReportRenderOptions): HTMLElement => {
  const list = document.createElement("div");
  list.className = "key-moment-list";
  const keyMoments = report.key_moments ?? [];
  if (keyMoments.length === 0) {
    list.append(empty("No key moments（无关键时刻）"));
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
