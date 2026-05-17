import "./styles.css";

import { renderBattleSummary } from "./battleSummaryView";
import { renderBoard, type EventUnitHighlight } from "./boardView";
import { renderEventHighlight } from "./eventHighlightView";
import {
  findLastEventIndexAtOrBeforeTick,
  flattenReplayEvents,
  getReplayMaxTick,
  seekToEvent,
  seekToTick,
  createEmptyVisualState,
  type FlatReplayEvent,
  type VisualState,
} from "./replayState";
import {
  fetchBattleReport,
  fetchReplayDocument,
  fetchScenarioManifest,
  readBattleReportFile,
  readReplayDocumentFile,
} from "./replayLoader";
import { renderReport } from "./reportView";
import { renderScenarioSummary } from "./scenarioSummaryView";
import { renderTimeline, type TimelineFilter } from "./timelineView";
import { renderUnitDetail } from "./unitDetailView";
import type { BattleReport, DemoScenario, ReplayDocument, ScenarioManifest } from "./replayTypes";

const replayInput = element<HTMLInputElement>("replay-file");
const reportInput = element<HTMLInputElement>("report-file");
const loadFilesButton = element<HTMLButtonElement>("load-files");
const scenarioLoader = element<HTMLDivElement>("scenario-loader");
const scenarioManifestState = element<HTMLSpanElement>("scenario-manifest-state");
const scenarioSelect = element<HTMLSelectElement>("scenario-select");
const loadBaselineDemoButton = element<HTMLButtonElement>("load-baseline-demo");
const loadScenarioButton = element<HTMLButtonElement>("load-scenario");
const playPauseButton = element<HTMLButtonElement>("play-pause");
const stepTickButton = element<HTMLButtonElement>("step-tick");
const previousEventButton = element<HTMLButtonElement>("previous-event");
const nextEventButton = element<HTMLButtonElement>("next-event");
const tickSlider = element<HTMLInputElement>("tick-slider");
const speedSelect = element<HTMLSelectElement>("speed-select");
const metadata = element<HTMLDivElement>("metadata");
const statusLine = element<HTMLDivElement>("status");
const tickReadout = element<HTMLDivElement>("tick-readout");
const eventReadout = element<HTMLDivElement>("event-readout");
const replayLoadState = element<HTMLElement>("replay-load-state");
const reportLoadState = element<HTMLElement>("report-load-state");
const boardContainer = element<HTMLDivElement>("board");
const scenarioSummaryContainer = element<HTMLDivElement>("scenario-summary");
const battleSummaryContainer = element<HTMLDivElement>("battle-summary");
const eventHighlightContainer = element<HTMLDivElement>("event-highlight");
const timelineContainer = element<HTMLDivElement>("timeline");
const reportContainer = element<HTMLDivElement>("report");
const unitDetailContainer = element<HTMLDivElement>("unit-detail");

let replay: ReplayDocument | null = null;
let report: BattleReport | null = null;
let flatEvents: FlatReplayEvent[] = [];
let visualState: VisualState = createEmptyVisualState();
let selectedUnitId: string | null = null;
let selectedEventIndex: number | null = null;
let timelineFilter: TimelineFilter = "all";
let playbackTimer: number | null = null;
let loadedReplayFileName: string | null = null;
let loadedReportFileName: string | null = null;
let scenarioManifest: ScenarioManifest | null = null;
let selectedScenarioId: string | null = null;
let loadedScenario: DemoScenario | null = null;

loadFilesButton.addEventListener("click", () => {
  void loadFiles();
});

scenarioSelect.addEventListener("change", () => {
  selectedScenarioId = scenarioSelect.value || null;
});

loadBaselineDemoButton.addEventListener("click", () => {
  const scenario = baselineScenario();
  if (!scenario) {
    setStatus("Scenario manifest is not available.");
    return;
  }
  void loadScenario(scenario);
});

loadScenarioButton.addEventListener("click", () => {
  const scenario = selectedScenario();
  if (!scenario) {
    setStatus("Select a scenario first.");
    return;
  }
  void loadScenario(scenario);
});

playPauseButton.addEventListener("click", () => {
  if (playbackTimer === null) {
    startPlayback();
    return;
  }
  stopPlayback();
  render();
});

stepTickButton.addEventListener("click", () => {
  stopPlayback();
  seekTick(visualState.currentTick + 1);
});

previousEventButton.addEventListener("click", () => {
  stopPlayback();
  const currentIndex = selectedEventIndex ?? findLastEventIndexAtOrBeforeTick(flatEvents, visualState.currentTick);
  if (currentIndex === null) {
    return;
  }
  seekEvent(Math.max(0, currentIndex - 1));
});

nextEventButton.addEventListener("click", () => {
  stopPlayback();
  const currentIndex = selectedEventIndex ?? findLastEventIndexAtOrBeforeTick(flatEvents, visualState.currentTick);
  const nextIndex = currentIndex === null ? 0 : Math.min(flatEvents.length - 1, currentIndex + 1);
  seekEvent(nextIndex);
});

tickSlider.addEventListener("input", () => {
  stopPlayback();
  seekTick(Number(tickSlider.value));
});

speedSelect.addEventListener("change", () => {
  if (playbackTimer !== null) {
    stopPlayback();
    startPlayback();
  }
});

const loadFiles = async (): Promise<void> => {
  stopPlayback();
  setStatus("Loading files");

  const replayResult = await readReplayDocumentFile(replayInput.files?.[0] ?? null);
  if (!replayResult.ok) {
    setStatus(replayResult.error);
    return;
  }

  const reportFile = reportInput.files?.[0] ?? null;
  let loadedReport: BattleReport | null = null;
  let reportMessage = "battle_report.json not loaded";
  if (reportFile) {
    const reportResult = await readBattleReportFile(reportFile);
    if (!reportResult.ok) {
      setStatus(reportResult.error);
      return;
    }
    loadedReport = reportResult.data;
    reportMessage = `${reportResult.fileName} loaded`;
  }

  replay = replayResult.data;
  report = loadedReport;
  loadedScenario = null;
  loadedReplayFileName = replayResult.fileName;
  loadedReportFileName = loadedReport ? reportMessage.replace(" loaded", "") : null;
  flatEvents = flattenReplayEvents(replay);
  selectedUnitId = null;
  selectedEventIndex = null;
  visualState = seekToTick(replay, 0);
  setStatus(`${replayResult.fileName} loaded; ${reportMessage}`);
  render();
};

const loadScenarioManifest = async (): Promise<void> => {
  const result = await fetchScenarioManifest();
  if (!result.ok) {
    scenarioManifest = null;
    selectedScenarioId = null;
    render();
    return;
  }

  scenarioManifest = result.data;
  selectedScenarioId = baselineScenario()?.id ?? result.data.scenarios[0]?.id ?? null;
  render();
};

const loadScenario = async (scenario: DemoScenario): Promise<void> => {
  stopPlayback();
  setStatus(`Loading scenario ${scenario.id}`);

  const [replayResult, reportResult] = await Promise.all([
    fetchReplayDocument(scenario.replay_url),
    fetchBattleReport(scenario.report_url),
  ]);

  if (!replayResult.ok) {
    setStatus(replayResult.error);
    return;
  }
  if (!reportResult.ok) {
    setStatus(reportResult.error);
    return;
  }

  replay = replayResult.data;
  report = reportResult.data;
  loadedScenario = scenario;
  selectedScenarioId = scenario.id;
  loadedReplayFileName = scenario.replay_url;
  loadedReportFileName = scenario.report_url;
  flatEvents = flattenReplayEvents(replay);
  selectedUnitId = null;
  selectedEventIndex = null;
  timelineFilter = "all";
  visualState = seekToTick(replay, 0);
  setStatus(`scenario loaded: ${scenario.id}`);
  render();
};

const seekTick = (tick: number): void => {
  seekTickInternal(tick, false);
};

const seekTickFromReport = (tick: number): void => {
  timelineFilter = "all";
  seekTickInternal(tick, true);
};

const seekTickInternal = (tick: number, selectLastEvent: boolean): void => {
  if (!replay) {
    return;
  }
  visualState = seekToTick(replay, tick);
  selectedEventIndex = selectLastEvent
    ? findLastEventIndexAtOrBeforeTick(flatEvents, visualState.currentTick)
    : null;
  render();
};

const seekEvent = (globalIndex: number): void => {
  if (!replay || flatEvents.length === 0) {
    return;
  }
  const clampedIndex = Math.max(0, Math.min(flatEvents.length - 1, globalIndex));
  keepTimelineSelectionVisible(clampedIndex);
  visualState = seekToEvent(replay, clampedIndex);
  selectedEventIndex = clampedIndex;
  render();
};

const startPlayback = (): void => {
  if (!replay || playbackTimer !== null) {
    return;
  }
  const playbackEndTick = getPlaybackEndTick(replay);
  if (visualState.currentTick >= playbackEndTick) {
    visualState = seekToTick(replay, 0);
    selectedEventIndex = null;
  }
  const intervalMs = Math.max(50, Math.round(250 / playbackSpeed()));
  playbackTimer = window.setInterval(() => {
    if (!replay) {
      stopPlayback();
      return;
    }
    const endTick = getPlaybackEndTick(replay);
    if (visualState.currentTick >= endTick) {
      stopPlayback();
      render();
      return;
    }
    visualState = seekToTick(replay, Math.min(endTick, visualState.currentTick + 1));
    selectedEventIndex = null;
    render();
  }, intervalMs);
  render();
};

const stopPlayback = (): void => {
  if (playbackTimer === null) {
    return;
  }
  window.clearInterval(playbackTimer);
  playbackTimer = null;
};

const playbackSpeed = (): number => {
  const value = Number(speedSelect.value);
  return Number.isFinite(value) && value > 0 ? value : 1;
};

const render = (): void => {
  const maxTick = replay ? getReplayMaxTick(replay) : 0;
  const currentEvent = currentEventEntry();
  renderScenarioControls();
  tickSlider.max = String(maxTick);
  tickSlider.value = String(Math.min(visualState.currentTick, maxTick));
  tickSlider.disabled = !replay;
  playPauseButton.disabled = !replay;
  stepTickButton.disabled = !replay;
  previousEventButton.disabled = !replay || flatEvents.length === 0;
  nextEventButton.disabled = !replay || flatEvents.length === 0;
  playPauseButton.textContent = playbackTimer === null ? "Play" : "Pause";
  tickReadout.textContent = `Tick ${visualState.currentTick} / ${maxTick}`;
  eventReadout.textContent = currentEvent
    ? `Event ${currentEvent.event.event_id} (${currentEvent.event.type})`
    : "Event -";
  replayLoadState.textContent = loadedReplayFileName ? `${loadedReplayFileName} loaded` : "not loaded";
  reportLoadState.textContent = loadedReportFileName ? `${loadedReportFileName} loaded` : "not loaded";
  metadata.textContent = replay
    ? `${replay.metadata.battle_id ?? "battle"} | seed ${replay.metadata.seed ?? "-"} | events ${flatEvents.length}`
    : "No replay loaded";

  renderBoard(boardContainer, {
    state: visualState,
    selectedUnitId,
    unitHighlights: unitHighlightsForEvent(currentEvent),
    onSelectUnit: (unitId) => {
      selectUnit(unitId);
    },
  });
  renderBattleSummary(battleSummaryContainer, {
    replay,
    report,
    eventCount: flatEvents.length,
  });
  renderScenarioSummary(scenarioSummaryContainer, {
    scenario: loadedScenario,
    replay,
    report,
    eventCount: flatEvents.length,
  });
  renderEventHighlight(eventHighlightContainer, currentEvent, visualState);
  renderTimeline(timelineContainer, {
    events: flatEvents,
    selectedEventIndex,
    filter: timelineFilter,
    onSelectEvent: (globalIndex) => {
      stopPlayback();
      seekEvent(globalIndex);
    },
    onFilterChange: (filter) => {
      timelineFilter = filter;
      render();
    },
  });
  renderUnitDetail(unitDetailContainer, visualState, report, selectedUnitId);
  renderReport(reportContainer, report, {
    selectedUnitId,
    onSelectUnit: selectUnit,
    onSeekTick: seekTickFromReport,
  });
};

const setStatus = (message: string): void => {
  statusLine.textContent = message;
};

const selectUnit = (unitId: string): void => {
  selectedUnitId = unitId;
  render();
};

const currentEventEntry = (): FlatReplayEvent | null => {
  const index = selectedEventIndex ?? visualState.appliedEventIndex;
  return index === null ? null : flatEvents[index] ?? null;
};

const renderScenarioControls = (): void => {
  const scenarios = scenarioManifest?.scenarios ?? [];
  scenarioLoader.hidden = scenarios.length === 0;
  scenarioManifestState.textContent = scenarios.length > 0 ? `${scenarios.length} scenarios` : "Manifest not loaded";
  loadBaselineDemoButton.disabled = scenarios.length === 0;
  loadScenarioButton.disabled = scenarios.length === 0;
  scenarioSelect.disabled = scenarios.length === 0;

  const selectedId = selectedScenarioId ?? scenarios[0]?.id;
  scenarioSelect.replaceChildren();
  for (const scenario of scenarios) {
    const option = document.createElement("option");
    option.value = scenario.id;
    option.textContent = `${scenario.id} - ${scenario.name}`;
    option.selected = scenario.id === selectedId;
    scenarioSelect.append(option);
  }
};

const selectedScenario = (): DemoScenario | null => {
  const scenarios = scenarioManifest?.scenarios ?? [];
  const scenarioId = selectedScenarioId ?? scenarioSelect.value;
  return scenarios.find((scenario) => scenario.id === scenarioId) ?? scenarios[0] ?? null;
};

const baselineScenario = (): DemoScenario | null => {
  const scenarios = scenarioManifest?.scenarios ?? [];
  return scenarios.find((scenario) => scenario.id === "demo_001") ?? scenarios[0] ?? null;
};

const unitHighlightsForEvent = (
  entry: FlatReplayEvent | null,
): Map<string, EventUnitHighlight> => {
  const highlights = new Map<string, EventUnitHighlight>();
  if (!entry) {
    return highlights;
  }
  const payload = entry.event.payload;
  switch (entry.event.type) {
    case "attack":
      addHighlight(highlights, payload.attacker, "attack-source");
      addHighlight(highlights, payload.target, "attack-target");
      break;
    case "skill_trigger":
      addHighlight(highlights, payload.source, "skill-source");
      for (const target of readStringArray(payload.targets)) {
        highlights.set(target, "skill-target");
      }
      break;
    case "damage":
      addHighlight(highlights, payload.source, "damage-source");
      addHighlight(highlights, payload.target, "damage-target");
      break;
    case "death":
      addHighlight(highlights, payload.unit, "death");
      break;
    case "stat_modifier":
      addHighlight(highlights, payload.source, "modifier-source");
      addHighlight(highlights, payload.target, "modifier-target");
      break;
    case "status_apply":
    case "status_expire":
      addHighlight(highlights, payload.source, "modifier-source");
      addHighlight(highlights, payload.target, "modifier-target");
      break;
    case "skill_cooldown":
      addHighlight(highlights, payload.source, "skill-source");
      break;
    case "action_scheduled":
      addHighlight(highlights, payload.unit, "skill-source");
      break;
    case "battle_end":
      for (const unit of visualState.units.values()) {
        if (!unit.alive) {
          highlights.set(unit.instanceId, "battle-end");
        }
      }
      break;
    default:
      break;
  }
  return highlights;
};

const addHighlight = (
  highlights: Map<string, EventUnitHighlight>,
  value: unknown,
  highlight: EventUnitHighlight,
): void => {
  if (typeof value === "string" && value) {
    highlights.set(value, highlight);
  }
};

const readStringArray = (value: unknown): string[] => {
  return Array.isArray(value) ? value.filter((item): item is string => typeof item === "string") : [];
};

const keepTimelineSelectionVisible = (globalIndex: number): void => {
  const event = flatEvents[globalIndex]?.event;
  if (event && timelineFilter !== "all" && event.type !== timelineFilter) {
    timelineFilter = "all";
  }
};

const getPlaybackEndTick = (currentReplay: ReplayDocument): number => {
  const resultEndTick = currentReplay.metadata.result?.end_tick;
  return typeof resultEndTick === "number" && Number.isFinite(resultEndTick)
    ? resultEndTick
    : getReplayMaxTick(currentReplay);
};

function element<T extends HTMLElement>(id: string): T {
  const found = document.getElementById(id);
  if (!found) {
    throw new Error(`Missing element #${id}`);
  }
  return found as T;
}

render();
void loadScenarioManifest();
