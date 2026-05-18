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
    container.append(empty("No unit selected（未选择单位）"));
    return;
  }

  const unit = state.units.get(selectedUnitId);
  if (!unit) {
    container.append(empty(`${selectedUnitId} is not present at this point（该单位当前不存在）`));
    return;
  }

  const unitReport = getUnitReport(report, selectedUnitId);
  container.append(
    detailGrid([
      ["Instance（实例）", unit.instanceId],
      ["Name（名称）", unit.name],
      ["Side（阵营）", unit.side],
      ["Role（角色）", unit.role],
      ["Combat State（战斗状态）", unit.combatState],
      ["Position（位置）", `${unit.x},${unit.y}`],
      ["HP（生命）", `${unit.hp}/${unit.maxHp}`],
      ["Alive（存活）", unit.alive ? "yes（是）" : "no（否）"],
      ["Combat State（战斗状态）", unit.combatState],
      ["ATK（攻击）", formatNumber(unit.atk)],
      ["DEF（防御）", formatNumber(unit.defense)],
      ["Range（射程）", formatNumber(unit.range)],
      ["Guard（护甲）", formatNumber(unit.guardValue)],
      ["Next Action Tick（下次行动）", formatNumber(unit.nextActionTick)],
      ["Status（状态）", formatStatuses(unit)],
      ["Skill Cooldown（技能冷却）", formatCooldown(unit)],
      ["Action Scheduled（行动调度）", formatActionSchedule(unit)],
      ["Skills（技能）", unit.skillIds.length > 0 ? unit.skillIds.join(", ") : "-"],
      ["ATK Bonus（攻击加成）", formatNumber(unit.statBonuses.get("atk"))],
      ["DEF Bonus（防御加成）", formatNumber(unit.statBonuses.get("defense"))],
      ["Range Bonus（射程加成）", formatNumber(unit.statBonuses.get("range"))],
      ["HP Bonus（生命加成）", formatNumber(unit.statBonuses.get("hp"))],
      ["ATKSPD Bonus（攻速加成）", formatNumber(unit.statBonuses.get("attack_interval_delta"))],
      ["Modifiers（修正）", formatNumber(unitReport?.modifiers_received)],
      ["Statuses Applied（状态应用）", formatNumber(unitReport?.statuses_applied)],
      ["Cooldowns Started（冷却启动）", formatNumber(unitReport?.cooldowns_started)],
      ["Actions Taken（行动次数）", formatNumber(unitReport?.actions_taken)],
      ["Report Next Action（报表下次行动）", formatNumber(unitReport?.last_next_action_tick)],
      ["Damage Done（伤害输出）", formatNumber(unitReport?.damage_done)],
      ["Damage Taken（承受伤害）", formatNumber(unitReport?.damage_taken)],
      ["Kills（击杀）", formatNumber(unitReport?.kills)],
      ["Deaths（死亡）", formatNumber(unitReport?.deaths)],
      ["Skill Triggers（技能触发）", formatNumber(totalSkillTriggers(unitReport))],
      ["Tags（标签）", unit.tags.length > 0 ? unit.tags.join(", ") : "-"],
    ]),
  );

  container.append(renderLastMarkers(unit, state));
};

const renderLastMarkers = (unit: VisualUnit, state: VisualState): HTMLElement => {
  const block = document.createElement("div");
  block.className = "marker-block";
  const heading = document.createElement("h3");
  heading.textContent = "Last Markers（最近标记）";
  block.append(heading);

  const rows: [string, string][] = [];
  if (state.lastAttack && [state.lastAttack.source, state.lastAttack.target].includes(unit.instanceId)) {
      rows.push([
      "Attack（攻击）",
      `T${state.lastAttack.tick} ${state.lastAttack.source} -> ${state.lastAttack.target}`,
    ]);
    if (state.lastAttack.targetReason) {
      rows.push(["Attack Target Reason（攻击目标原因）", state.lastAttack.targetReason]);
    }
    if (state.lastAttack.targetScore) {
      rows.push(["Attack Target Score（攻击目标评分）", formatTargetScore(state.lastAttack.targetScore)]);
    }
  }
  if (
    state.lastSkill &&
    [state.lastSkill.source, ...state.lastSkill.targets].includes(unit.instanceId)
  ) {
    rows.push([
      "Skill（技能）",
      `T${state.lastSkill.tick} ${state.lastSkill.source} ${state.lastSkill.skill}`,
    ]);
    if (state.lastSkill.targetReason) {
      rows.push(["Skill Target Reason（技能目标原因）", state.lastSkill.targetReason]);
    }
    if (state.lastSkill.targetScore) {
      rows.push(["Skill Target Score（技能目标评分）", formatTargetScore(state.lastSkill.targetScore)]);
    }
  }
  if (
    state.lastModifier &&
    [state.lastModifier.source, state.lastModifier.target].includes(unit.instanceId)
  ) {
    rows.push([
      "Modifier（修正）",
      `T${state.lastModifier.tick} ${state.lastModifier.source} ${state.lastModifier.stat} ${state.lastModifier.amount >= 0 ? "+" : ""}${state.lastModifier.amount} (${state.lastModifier.sourceType})`,
    ]);
  }
  if (
    state.lastStatus &&
    [state.lastStatus.source, state.lastStatus.target].includes(unit.instanceId)
  ) {
    rows.push([
      "Status（状态）",
      `T${state.lastStatus.tick} ${state.lastStatus.eventType} ${state.lastStatus.stat} ${state.lastStatus.amount >= 0 ? "+" : ""}${state.lastStatus.amount}`,
    ]);
  }
  if (state.lastCooldown && state.lastCooldown.source === unit.instanceId) {
    rows.push([
      "Cooldown（冷却）",
      `T${state.lastCooldown.tick} ${state.lastCooldown.skill} 就绪（ready） ${state.lastCooldown.readyTick}`,
    ]);
  }
  if (state.lastActionSchedule && state.lastActionSchedule.unit === unit.instanceId) {
    rows.push([
      "Action Schedule（行动安排）",
      `T${state.lastActionSchedule.tick} 下次（next） ${state.lastActionSchedule.nextActionTick}`,
    ]);
  }
  if (
    state.lastDamage &&
    [state.lastDamage.source, state.lastDamage.target].includes(unit.instanceId)
  ) {
    rows.push([
      "Damage（伤害）",
      `T${state.lastDamage.tick} ${formatValue(state.lastDamage.source)} -> ${state.lastDamage.target} ${state.lastDamage.amount}`,
    ]);
  }

  block.append(rows.length > 0 ? detailGrid(rows) : empty("No active marker（无活跃标记）"));
  return block;
};

const formatTargetScore = (score: { final: number; exposure: number; column: number; low_hp: number; threat: number; role: number }): string => {
  return [
    `final=${score.final ?? "-"}`,
    `exposure=${score.exposure ?? "-"}`,
    `column=${score.column ?? "-"}`,
    `low_hp=${score.low_hp ?? "-"}`,
    `threat=${score.threat ?? "-"}`,
    `role=${score.role ?? "-"}`,
  ].join(", ");
};

const formatStatuses = (unit: VisualUnit): string => {
  const active = unit.statuses.filter((status) => status.active);
  if (active.length === 0) {
    return "-";
  }
  return active
    .map((status) => `${status.stat}${status.amount >= 0 ? "+" : ""}${status.amount} (${status.reason})`)
    .join(" | ");
};

const formatCooldown = (unit: VisualUnit): string => {
  if (!unit.lastCooldown) {
    return "-";
  }
  return `${unit.lastCooldown.skill} 就绪（ready） ${unit.lastCooldown.readyTick}`;
};

const formatActionSchedule = (unit: VisualUnit): string => {
  if (!unit.lastActionSchedule) {
    return "-";
  }
  return `下次（next） ${unit.lastActionSchedule.nextActionTick} (${unit.lastActionSchedule.reason})`;
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
