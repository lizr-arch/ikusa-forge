import { eventSummary } from "./formatters";
import type { FlatReplayEvent } from "./replayState";

export type TimelineFilter =
  | "all"
  | "attack"
  | "skill_trigger"
  | "damage"
  | "death"
  | "stat_modifier"
  | "battle_end";

export const TIMELINE_FILTERS: TimelineFilter[] = [
  "all",
  "attack",
  "skill_trigger",
  "damage",
  "death",
  "stat_modifier",
  "battle_end",
];

interface TimelineRenderOptions {
  events: FlatReplayEvent[];
  selectedEventIndex: number | null;
  filter: TimelineFilter;
  onSelectEvent: (globalIndex: number) => void;
  onFilterChange: (filter: TimelineFilter) => void;
}

export const renderTimeline = (container: HTMLElement, options: TimelineRenderOptions): void => {
  container.replaceChildren();

  const toolbar = document.createElement("div");
  toolbar.className = "timeline-toolbar";

  const count = document.createElement("div");
  count.className = "timeline-count";
  count.textContent = `${filteredEvents(options).length} / ${options.events.length} events`;
  toolbar.append(count);

  const label = document.createElement("label");
  label.className = "timeline-filter";
  const labelText = document.createElement("span");
  labelText.textContent = "Filter";
  const select = document.createElement("select");
  for (const filter of TIMELINE_FILTERS) {
    const option = document.createElement("option");
    option.value = filter;
    option.textContent = filter;
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

  const events = filteredEvents(options);
  if (events.length === 0) {
    const empty = document.createElement("div");
    empty.className = "empty-state";
    empty.textContent = "No events";
    list.append(empty);
  }

  let selectedRow: HTMLButtonElement | null = null;
  for (const entry of events) {
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
  selectedRow?.scrollIntoView({ block: "nearest" });
};

const filteredEvents = (options: TimelineRenderOptions): FlatReplayEvent[] => {
  if (options.filter === "all") {
    return options.events;
  }
  return options.events.filter((entry) => entry.event.type === options.filter);
};

const isTimelineFilter = (value: string): value is TimelineFilter => {
  return TIMELINE_FILTERS.includes(value as TimelineFilter);
};
