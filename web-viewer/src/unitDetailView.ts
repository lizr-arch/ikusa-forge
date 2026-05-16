import { formatNumber, formatValue, getUnitReport, totalSkillTriggers } from "./formatters";
import type { VisualState, VisualUnit } from "./replayState";
import type { BattleReport } from "./replayTypes";

export const renderUnitDetail = (
  container: HTMLElement,
  state: VisualState,
  report: BattleReport | null,
  selectedUnitId: string | null,
): void => {
  container.replaceChildren();
  if (!selectedUnitId) {
    container.append(empty("No unit selected"));
    return;
  }

  const unit = state.units.get(selectedUnitId);
  if (!unit) {
    container.append(empty(`${selectedUnitId} is not present at this point`));
    return;
  }

  const unitReport = getUnitReport(report, selectedUnitId);
  container.append(
    detailGrid([
      ["Instance", unit.instanceId],
      ["Name", unit.name],
      ["Side", unit.side],
      ["Role", unit.role],
      ["Position", `${unit.x},${unit.y}`],
      ["HP", `${unit.hp}/${unit.maxHp}`],
      ["Alive", unit.alive ? "yes" : "no"],
      ["ATK", formatNumber(unit.atk)],
      ["DEF", formatNumber(unit.defense)],
      ["Range", formatNumber(unit.range)],
      ["Guard", formatNumber(unit.guardValue)],
      ["Skills", unit.skillIds.length > 0 ? unit.skillIds.join(", ") : "-"],
      ["Damage Done", formatNumber(unitReport?.damage_done)],
      ["Damage Taken", formatNumber(unitReport?.damage_taken)],
      ["Kills", formatNumber(unitReport?.kills)],
      ["Deaths", formatNumber(unitReport?.deaths)],
      ["Skill Triggers", formatNumber(totalSkillTriggers(unitReport))],
      ["Tags", unit.tags.length > 0 ? unit.tags.join(", ") : "-"],
    ]),
  );

  container.append(renderLastMarkers(unit, state));
};

const renderLastMarkers = (unit: VisualUnit, state: VisualState): HTMLElement => {
  const block = document.createElement("div");
  block.className = "marker-block";
  const heading = document.createElement("h3");
  heading.textContent = "Last Markers";
  block.append(heading);

  const rows: [string, string][] = [];
  if (state.lastAttack && [state.lastAttack.source, state.lastAttack.target].includes(unit.instanceId)) {
    rows.push([
      "Attack",
      `T${state.lastAttack.tick} ${state.lastAttack.source} -> ${state.lastAttack.target}`,
    ]);
  }
  if (
    state.lastSkill &&
    [state.lastSkill.source, ...state.lastSkill.targets].includes(unit.instanceId)
  ) {
    rows.push([
      "Skill",
      `T${state.lastSkill.tick} ${state.lastSkill.source} ${state.lastSkill.skill}`,
    ]);
  }
  if (
    state.lastDamage &&
    [state.lastDamage.source, state.lastDamage.target].includes(unit.instanceId)
  ) {
    rows.push([
      "Damage",
      `T${state.lastDamage.tick} ${formatValue(state.lastDamage.source)} -> ${state.lastDamage.target} ${state.lastDamage.amount}`,
    ]);
  }

  block.append(rows.length > 0 ? detailGrid(rows) : empty("No active marker"));
  return block;
};

const detailGrid = (rows: [string, string][]): HTMLElement => {
  const grid = document.createElement("div");
  grid.className = "detail-grid";
  for (const [label, value] of rows) {
    const item = document.createElement("div");
    item.className = "detail-row";
    const key = document.createElement("span");
    key.textContent = label;
    const val = document.createElement("strong");
    val.textContent = value;
    item.append(key, val);
    grid.append(item);
  }
  return grid;
};

const empty = (message: string): HTMLElement => {
  const element = document.createElement("div");
  element.className = "empty-state";
  element.textContent = message;
  return element;
};
