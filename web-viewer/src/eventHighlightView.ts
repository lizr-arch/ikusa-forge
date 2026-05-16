import { eventSummary, formatNumber, formatValue } from "./formatters";
import type { FlatReplayEvent, VisualState } from "./replayState";

export const renderEventHighlight = (
  container: HTMLElement,
  currentEvent: FlatReplayEvent | null,
  state: VisualState,
): void => {
  container.replaceChildren();
  if (!currentEvent) {
    container.append(empty("No current event"));
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
      ["Event ID", formatValue(event.event_id)],
      ["Type", formatValue(event.type)],
      ["Tick", formatNumber(event.tick)],
      ...eventDetailRows(currentEvent, state),
    ]),
  );

  if (event.type === "battle_end") {
    const end = document.createElement("div");
    end.className = "battle-end-banner";
    end.textContent = `Battle ended: ${formatValue(readValue(event.payload.winner))} / ${formatValue(
      readValue(event.payload.reason),
    )}`;
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
        ["Source", formatValue(readValue(event.payload.attacker))],
        ["Target", formatValue(readValue(event.payload.target))],
      ];
    case "skill_trigger":
      return [
        ["Source", formatValue(readValue(event.payload.source))],
        ["Skill", formatValue(readValue(event.payload.skill))],
        ["Trigger", formatValue(readValue(event.payload.trigger))],
        ["Targets", readArray(event.payload.targets).join(", ") || "-"],
      ];
    case "damage":
      return [
        ["Source", formatValue(readValue(event.payload.source))],
        ["Target", formatValue(readValue(event.payload.target))],
        ["Amount", formatNumber(readNumber(event.payload.amount))],
        ["Reason", formatValue(readValue(event.payload.reason))],
      ];
    case "death":
      return [["Unit", formatValue(readValue(event.payload.unit))]];
    case "battle_end":
      return [
        ["Winner", formatValue(readValue(event.payload.winner))],
        ["Reason", formatValue(readValue(event.payload.reason))],
        ["End Tick", formatNumber(readNumber(event.payload.end_tick))],
      ];
    case "unit_spawn": {
      const unit = asRecord(event.payload.unit);
      return [
        ["Unit", formatValue(readValue(unit.instance_id))],
        ["Side", formatValue(readValue(unit.side))],
        ["Role", formatValue(readValue(unit.role))],
      ];
    }
    default:
      return [
        ["Applied Event", formatValue(state.appliedEventId)],
        ["Applied Index", formatNumber(state.appliedEventIndex)],
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

const asRecord = (value: unknown): Record<string, unknown> => {
  if (typeof value === "object" && value !== null && !Array.isArray(value)) {
    return value as Record<string, unknown>;
  }
  return {};
};
