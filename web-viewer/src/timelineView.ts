import { eventSummary } from "./formatters";
import type { FlatReplayEvent } from "./replayState";

export type TimelineFilter =
  | "all"
  | "attack"
  | "skill_trigger"
  | "damage"
  | "death"
  | "stat_modifier"
  | "status_apply"
  | "skill_cooldown"
  | "action_scheduled"
  | "unit_move"
  | "target_acquired"
  | "enter_range"
  | "engage_start"
  | "battle_end";

export type TimelineRenderMode = "full" | "live_capped";

export const TIMELINE_FILTERS: TimelineFilter[] = [
  "all",
  "attack",
  "skill_trigger",
  "damage",
  "death",
  "stat_modifier",
  "status_apply",
  "skill_cooldown",
  "action_scheduled",
  "unit_move",
  "target_acquired",
  "enter_range",
  "engage_start",
  "battle_end",
];

interface TimelineRenderOptions {
  events: FlatReplayEvent[];
  selectedEventIndex: number | null;
  filter: TimelineFilter;
  onSelectEvent: (globalIndex: number) => void;
  onFilterChange: (filter: TimelineFilter) => void;
  autoScrollSelectedEvent?: boolean;
  renderMode?: TimelineRenderMode;
  maxRows?: number;
}

export const renderTimeline = (container: HTMLElement, options: TimelineRenderOptions): void => {
  container.replaceChildren();

  const toolbar = document.createElement("div");
  toolbar.className = "timeline-toolbar";

  const eventList = filteredEvents(options);
  const renderedEvents = trimForMode(eventList, options.renderMode, options.maxRows);

  const count = document.createElement("div");
  count.className = "timeline-count";
  if (options.renderMode === "live_capped") {
    count.textContent = `Showing latest ${renderedEvents.length} / ${eventList.length} events（显示最近 ${renderedEvents.length} / 共 ${eventList.length} 个事件）`;
  } else {
    count.textContent = `${eventList.length} / ${options.events.length} events（事件）`;
  }
  toolbar.append(count);

  const label = document.createElement("label");
  label.className = "timeline-filter";
  const labelText = document.createElement("span");
  labelText.textContent = "Filter（过滤）";
  const select = document.createElement("select");
  for (const filter of TIMELINE_FILTERS) {
    const option = document.createElement("option");
    option.value = filter;
    option.textContent = filter === "all"
      ? "All / 全部"
      : filter === "attack"
        ? "attack（攻击）"
        : filter === "skill_trigger"
          ? "skill_trigger（技能触发）"
          : filter === "damage"
            ? "damage（伤害）"
            : filter === "death"
              ? "death（死亡）"
              : filter === "stat_modifier"
                ? "stat_modifier（属性修正）"
                : filter === "status_apply"
                  ? "status_apply（状态应用）"
                  : filter === "skill_cooldown"
                    ? "skill_cooldown（技能冷却）"
                    : filter === "action_scheduled"
                      ? "action_scheduled（行动调度）"
                      : filter === "battle_end"
                        ? "battle_end（战斗结束）"
                        : filter;
    option.selected = filter === options.filter;
    select.append(option);
  }
  select.addEventListener("change", () => {
    if (isTimelineFilter(select.value)) {
      options.onFilterChange(select.value);
    }
  });
  label.append(labelText, select);
  toolbar.append(label);
  container.append(toolbar);

  const list = document.createElement("div");
  list.className = "timeline-list";

  if (renderedEvents.length === 0) {
    const empty = document.createElement("div");
    empty.className = "empty-state";
    empty.textContent = "No events（无事件）";
    list.append(empty);
  }

  let selectedRow: HTMLButtonElement | null = null;
  for (const entry of renderedEvents) {
    const row = document.createElement("button");
    row.type = "button";
    row.className = entry.globalIndex === options.selectedEventIndex ? "timeline-row selected" : "timeline-row";
    row.dataset.eventIndex = String(entry.globalIndex);
    if (entry.globalIndex === options.selectedEventIndex) {
      row.setAttribute("aria-current", "true");
      selectedRow = row;
    }
    row.addEventListener("click", () => options.onSelectEvent(entry.globalIndex));

    const tick = document.createElement("span");
    tick.className = "timeline-tick";
    tick.textContent = `T${entry.tick}`;

    const type = document.createElement("span");
    type.className = `event-type event-type-${entry.event.type}`;
    type.textContent = entry.event.type;

    const summary = document.createElement("span");
    summary.className = "timeline-summary";
    summary.textContent = eventSummary(entry.event);

    row.append(tick, type, summary);
    list.append(row);
  }

  container.append(list);
  if (options.autoScrollSelectedEvent ?? true) {
    selectedRow?.scrollIntoView({ block: "nearest" });
  }
};

const filteredEvents = (options: TimelineRenderOptions): FlatReplayEvent[] => {
  if (options.filter === "all") {
    return options.events;
  }
  return options.events.filter((entry) => entry.event.type === options.filter);
};

const trimForMode = (
  events: FlatReplayEvent[],
  mode: TimelineRenderMode = "full",
  maxRows = 150,
): FlatReplayEvent[] => {
  if (mode !== "live_capped") {
    return events;
  }
  if (events.length <= maxRows) {
    return events;
  }
  return events.slice(-maxRows);
};

const isTimelineFilter = (value: string): value is TimelineFilter => {
  return TIMELINE_FILTERS.includes(value as TimelineFilter);
};
