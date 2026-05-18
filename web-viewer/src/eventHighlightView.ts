import { eventSummary, formatNumber, formatValue } from "./formatters";
import type { FlatReplayEvent, VisualState } from "./replayState";

export const renderEventHighlight = (
  container: HTMLElement,
  currentEvent: FlatReplayEvent | null,
  state: VisualState,
): void => {
  container.replaceChildren();
  if (!currentEvent) {
    container.append(empty("No current event（无当前事件）"));
    return;
  }

  const event = currentEvent.event;
  const block = document.createElement("div");
  block.className = `event-highlight event-highlight-${event.type}`;

  const summary = document.createElement("div");
  summary.className = "event-highlight-summary";
  summary.textContent = eventSummary(event);
  block.append(summary);

  block.append(
    detailGrid([
      ["Event ID（事件 ID）", formatValue(event.event_id)],
      ["Type（类型）", formatValue(event.type)],
      ["Tick（回合）", formatNumber(event.tick)],
      ...eventDetailRows(currentEvent, state),
    ]),
  );

  if (event.type === "battle_end") {
    const end = document.createElement("div");
    end.className = "battle-end-banner";
    const summaryText = readValue(event.payload.summary)
      ?? `${formatValue(readValue(event.payload.winner))} / ${formatValue(readValue(event.payload.reason))}`;
    end.textContent = `Battle ended（战斗结束）: ${formatValue(summaryText)}`;
    block.append(end);
  }

  container.append(block);
};

const eventDetailRows = (
  currentEvent: FlatReplayEvent,
  state: VisualState,
): [string, string][] => {
  const event = currentEvent.event;
  switch (event.type) {
    case "attack":
      return [
        ["Source（来源）", formatValue(readValue(event.payload.attacker))],
        ["Target（目标）", formatValue(readValue(event.payload.target))],
        ["Target Reason（目标原因）", formatValue(readValue(event.payload.target_reason))],
        ["Target Score（目标评分）", formatTargetScore(event.payload.target_score)],
      ];
    case "skill_trigger":
      return [
        ["Source（来源）", formatValue(readValue(event.payload.source))],
        ["Skill（技能）", formatValue(readValue(event.payload.skill))],
        ["Trigger（触发）", formatValue(readValue(event.payload.trigger))],
        ["Targets（目标）", readArray(event.payload.targets).join(", ") || "-"],
        ["Target Reason（目标原因）", formatValue(readValue(event.payload.target_reason))],
        ["Target Score（目标评分）", formatTargetScore(event.payload.target_score)],
      ];
    case "damage":
      return [
        ["Source（来源）", formatValue(readValue(event.payload.source))],
        ["Target（目标）", formatValue(readValue(event.payload.target))],
        ["Amount（数值）", formatNumber(readNumber(event.payload.amount))],
        ["Reason（原因）", formatValue(readValue(event.payload.reason))],
      ];
    case "stat_modifier":
      return [
        ["Source（来源）", formatValue(readValue(event.payload.source))],
        ["Source Type（来源类型）", formatValue(readValue(event.payload.source_type))],
        ["Target（目标）", formatValue(readValue(event.payload.target))],
        ["Stat（属性）", formatValue(readValue(event.payload.stat))],
        ["Amount（数值）", formatNumber(readNumber(event.payload.amount))],
        ["Reason（原因）", formatValue(readValue(event.payload.reason))],
      ];
    case "status_apply":
    case "status_expire":
      return [
        ["ID（ID）", formatValue(readValue(event.payload.id) ?? readValue(event.payload.status_id))],
        ["Source（来源）", formatValue(readValue(event.payload.source))],
        ["Target（目标）", formatValue(readValue(event.payload.target))],
        ["Stat（属性）", formatValue(readValue(event.payload.stat))],
        ["Amount（数值）", formatNumber(readNumber(event.payload.amount))],
        ["Reason（原因）", formatValue(readValue(event.payload.reason))],
        ["Target Reason（目标原因）", formatValue(readValue(event.payload.target_reason))],
      ];
    case "skill_cooldown":
      return [
        ["Source（来源）", formatValue(readValue(event.payload.source))],
        ["Skill（技能）", formatValue(readValue(event.payload.skill))],
        ["Start Tick（开始回合）", formatNumber(readNumber(event.payload.start_tick))],
        ["Ready Tick（就绪回合）", formatNumber(readNumber(event.payload.ready_tick))],
        ["Cooldown Ticks（冷却回合）", formatNumber(readNumber(event.payload.cooldown_ticks))],
      ];
    case "action_scheduled":
      return [
        ["Unit（单位）", formatValue(readValue(event.payload.unit))],
        ["Current Tick（当前回合）", formatNumber(readNumber(event.payload.current_tick))],
        ["Next Action Tick（下次行动回合）", formatNumber(readNumber(event.payload.next_action_tick))],
        ["Action Interval（行动间隔）", formatNumber(readNumber(event.payload.action_interval_ticks))],
        ["Reason（原因）", formatValue(readValue(event.payload.reason))],
      ];
    case "unit_move":
      return [
        ["Unit", formatValue(readValue(event.payload.unit))],
        ["Target", formatValue(readValue(event.payload.target))],
        ["To X", formatNumber(readNumber(event.payload.to_x))],
        ["To Y", formatNumber(readNumber(event.payload.to_y))],
        ["Move Speed", formatNumber(readNumber(event.payload.move_speed))],
        ["Reason", formatValue(readValue(event.payload.reason))],
      ];
    case "target_acquired":
    case "enter_range":
    case "engage_start":
      return [
        ["Unit", formatValue(readValue(event.payload.unit))],
        ["Target", formatValue(readValue(event.payload.target))],
        ["Distance", formatNumber(readNumber(event.payload.distance))],
        ["Attack Range", formatNumber(readNumber(event.payload.attack_range))],
        ["Reason", formatValue(readValue(event.payload.reason))],
      ];
    case "death":
      return [["Unit（单位）", formatValue(readValue(event.payload.unit))]];
    case "battle_end":
      return [
        ["Winner（胜利）", formatValue(readValue(event.payload.winner))],
        ["Reason（原因）", formatValue(readValue(event.payload.reason))],
        ["End Tick（终止回合）", formatNumber(readNumber(event.payload.end_tick))],
        ["Winner Alive（胜利方存活）", formatNumber(readNumber(event.payload.winner_alive))],
        ["Loser Alive（失败方存活）", formatNumber(readNumber(event.payload.loser_alive))],
        ["Winner Total HP（胜利方总血量）", formatNumber(readNumber(event.payload.winner_total_hp))],
        ["Loser Total HP（失败方总血量）", formatNumber(readNumber(event.payload.loser_total_hp))],
        ["Summary（总结）", formatValue(readValue(event.payload.summary))],
      ];
    case "unit_spawn": {
      const unit = asRecord(event.payload.unit);
      return [
        ["Unit（单位）", formatValue(readValue(unit.instance_id))],
        ["Side（阵营）", formatValue(readValue(unit.side))],
        ["Role（角色）", formatValue(readValue(unit.role))],
      ];
    }
    default:
      return [
        ["Applied Event（已应用事件）", formatValue(state.appliedEventId)],
        ["Applied Index（应用序号）", formatNumber(state.appliedEventIndex)],
      ];
  }
};

const detailGrid = (rows: [string, string][]): HTMLElement => {
  const grid = document.createElement("div");
  grid.className = "detail-grid";
  for (const [label, value] of rows) {
    const row = document.createElement("div");
    row.className = "detail-row";
    const key = document.createElement("span");
    key.textContent = label;
    const val = document.createElement("strong");
    val.textContent = value;
    row.append(key, val);
    grid.append(row);
  }
  return grid;
};

const empty = (message: string): HTMLElement => {
  const element = document.createElement("div");
  element.className = "empty-state";
  element.textContent = message;
  return element;
};

const readValue = (value: unknown): string | number | null => {
  if (typeof value === "string" || typeof value === "number") {
    return value;
  }
  return null;
};

const readNumber = (value: unknown): number | null => {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
};

const readArray = (value: unknown): string[] => {
  return Array.isArray(value) ? value.map((item) => String(item)) : [];
};

const formatTargetScore = (value: unknown): string => {
  if (typeof value !== "object" || value === null) {
    return "-";
  }
  const payload = value as Record<string, number>;
  const final = formatMaybeNumber(payload.final);
  const exposure = formatMaybeNumber(payload.exposure);
  const column = formatMaybeNumber(payload.column);
  const lowHp = formatMaybeNumber(payload.low_hp);
  const threat = formatMaybeNumber(payload.threat);
  const role = formatMaybeNumber(payload.role);
  if (!Number.isFinite(final) && !Number.isFinite(exposure) && !Number.isFinite(column)) {
    return "-";
  }
  const parts = [
    `final=${final}`,
    `exposure=${exposure}`,
    `column=${column}`,
    `low_hp=${lowHp}`,
    `threat=${threat}`,
    `role=${role}`,
  ];
  return parts.filter((value) => value.endsWith("=NaN") === false).join(", ");
};

const formatMaybeNumber = (value: unknown): number => {
  return typeof value === "number" && Number.isFinite(value) ? value : Number.NaN;
};

const asRecord = (value: unknown): Record<string, unknown> => {
  if (typeof value === "object" && value !== null && !Array.isArray(value)) {
    return value as Record<string, unknown>;
  }
  return {};
};
