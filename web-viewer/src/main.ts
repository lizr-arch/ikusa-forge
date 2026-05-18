import "./styles.css";

import { renderBattleSummary } from "./battleSummaryView";
import { renderBoard, type EventUnitHighlight } from "./boardView";
import { renderEventHighlight } from "./eventHighlightView";
import {
  appendLiveEvents,
  buildVisualStateFromSnapshot,
  createEmptyVisualState,
  findLastEventIndexAtOrBeforeTick,
  flattenReplayEvents,
  getReplayMaxTick,
  seekToEvent,
  seekToTick,
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
import {
  DEFAULT_LIVE_API_URL,
  healthLiveApi,
  resetLiveBattle,
  startLiveBattle,
  stepLiveBattle,
} from "./liveApiClient";
import type {
  BattleReport,
  DemoScenario,
  LiveBattleResult,
  ReplayDocument,
  ScenarioManifest,
} from "./replayTypes";

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

const liveApiUrlInput = element<HTMLInputElement>("live-api-url");
const liveBattleIdInput = element<HTMLInputElement>("live-battle-id");
const liveSeedInput = element<HTMLInputElement>("live-seed");
const startLiveButton = element<HTMLButtonElement>("start-live-battle");
const pauseLiveButton = element<HTMLButtonElement>("pause-live-battle");
const resumeLiveButton = element<HTMLButtonElement>("resume-live-battle");
const stepLiveButton = element<HTMLButtonElement>("step-live-battle");
const resetLiveButton = element<HTMLButtonElement>("reset-live-battle");
const liveSpeedSelect = element<HTMLSelectElement>("live-speed-select");

const metadata = element<HTMLDivElement>("metadata");
const statusLine = element<HTMLDivElement>("status");
const tickReadout = element<HTMLDivElement>("tick-readout");
const eventReadout = element<HTMLDivElement>("event-readout");
const replayLoadState = element<HTMLElement>("replay-load-state");
const reportLoadState = element<HTMLElement>("report-load-state");
const liveStatusLine = element<HTMLElement>("live-status-line");
const liveStatusValue = element<HTMLElement>("live-status");
const liveSessionIdValue = element<HTMLElement>("live-session-id");
const liveEventCursorValue = element<HTMLElement>("live-event-cursor");
const liveCurrentTickValue = element<HTMLElement>("live-current-tick");
const liveUnitAliveValue = element<HTMLElement>("live-unit-alive");
const liveLatestEventValue = element<HTMLElement>("live-latest-event");
const liveTransportValue = element<HTMLElement>("live-transport");

const boardContainer = element<HTMLDivElement>("board");
const scenarioSummaryContainer = element<HTMLDivElement>("scenario-summary");
const battleSummaryContainer = element<HTMLDivElement>("battle-summary");
const eventHighlightContainer = element<HTMLDivElement>("event-highlight");
const timelineContainer = element<HTMLDivElement>("timeline");
const reportContainer = element<HTMLElement>("report");
const unitDetailContainer = element<HTMLDivElement>("unit-detail");

type ViewerMode = "replay" | "live";

let mode: ViewerMode = "replay";
let replay: ReplayDocument | null = null;
let report: BattleReport | null = null;
let flatEvents: FlatReplayEvent[] = [];
let visualState: VisualState = createEmptyVisualState();
let selectedUnitId: string | null = null;
let selectedEventIndex: number | null = null;
let timelineFilter: TimelineFilter = "all";
let playbackTimer: number | null = null;
let livePlaybackTimer: number | null = null;
let liveStepInFlight = false;
let loadedReplayFileName: string | null = null;
let loadedReportFileName: string | null = null;
let scenarioManifest: ScenarioManifest | null = null;
let selectedScenarioId: string | null = null;
let loadedScenario: DemoScenario | null = null;

let liveSessionId: string | null = null;
let liveApiUrl = DEFAULT_LIVE_API_URL;
let liveBattleId = "demo_001";
let liveSeed = 1001;
let liveEventCursor = 0;
let liveResult: LiveBattleResult | null = null;
let liveFinished = false;

const LIVE_LOOP_INTERVAL_MS = 250;

liveApiUrlInput.value = DEFAULT_LIVE_API_URL;
liveBattleIdInput.value = liveBattleId;
liveSeedInput.value = String(liveSeed);
liveSpeedSelect.value = "1";

loadFilesButton.addEventListener("click", () => {
  void loadFiles();
});

scenarioSelect.addEventListener("change", () => {
  selectedScenarioId = scenarioSelect.value || null;
});

loadBaselineDemoButton.addEventListener("click", () => {
  const scenario = baselineScenario();
  if (!scenario) {
    setStatus("Scenario manifest is not available（场景清单不可用）.");
    return;
  }
  stopAllPlayback();
  void loadScenario(scenario);
});

loadScenarioButton.addEventListener("click", () => {
  const scenario = selectedScenario();
  if (!scenario) {
    setStatus("Select a scenario first（请先选择场景）.");
    return;
  }
  stopAllPlayback();
  void loadScenario(scenario);
});

playPauseButton.addEventListener("click", () => {
  if (mode !== "replay") {
    return;
  }
  if (playbackTimer === null) {
    startPlayback();
    return;
  }
  stopPlayback();
  render();
});

stepTickButton.addEventListener("click", () => {
  if (mode !== "replay") {
    return;
  }
  stopPlayback();
  seekTick(visualState.currentTick + 1);
});

previousEventButton.addEventListener("click", () => {
  if (mode !== "replay") {
    return;
  }
  stopPlayback();
  const currentIndex = selectedEventIndex ?? findLastEventIndexAtOrBeforeTick(flatEvents, visualState.currentTick);
  if (currentIndex === null) {
    return;
  }
  seekEvent(Math.max(0, currentIndex - 1));
});

nextEventButton.addEventListener("click", () => {
  if (mode !== "replay") {
    return;
  }
  stopPlayback();
  const currentIndex = selectedEventIndex ?? findLastEventIndexAtOrBeforeTick(flatEvents, visualState.currentTick);
  const nextIndex = currentIndex === null ? 0 : Math.min(flatEvents.length - 1, currentIndex + 1);
  seekEvent(nextIndex);
});

tickSlider.addEventListener("input", () => {
  if (mode !== "replay") {
    return;
  }
  stopPlayback();
  seekTick(Number(tickSlider.value));
});

speedSelect.addEventListener("change", () => {
  if (playbackTimer !== null) {
    stopPlayback();
    startPlayback();
  }
});

startLiveButton.addEventListener("click", () => {
  void startLiveBattleLoop();
});
pauseLiveButton.addEventListener("click", () => {
  stopLivePlayback();
});
resumeLiveButton.addEventListener("click", () => {
  startLivePlayback();
});
stepLiveButton.addEventListener("click", () => {
  stopLivePlayback();
  void stepLiveOnce(1);
});
resetLiveButton.addEventListener("click", () => {
  void resetLiveSession();
});

const loadFiles = async (): Promise<void> => {
  stopAllPlayback();
  setModeReplay();
  setStatus("Loading files（正在加载文件）");

  const replayResult = await readReplayDocumentFile(replayInput.files?.[0] ?? null);
  if (!replayResult.ok) {
    setStatus(replayResult.error);
    return;
  }

  const reportFile = reportInput.files?.[0] ?? null;
  let loadedReport: BattleReport | null = null;
  let reportMessage = "battle_report.json not loaded（未加载）";
  if (reportFile) {
    const reportResult = await readBattleReportFile(reportFile);
    if (!reportResult.ok) {
      setStatus(reportResult.error);
      return;
    }
    loadedReport = reportResult.data;
    reportMessage = `${reportResult.fileName} loaded（已加载）`;
  }

  replay = replayResult.data;
  report = loadedReport;
  loadedScenario = null;
  loadedReplayFileName = replayResult.fileName;
  loadedReportFileName = loadedReport ? reportFile?.name ?? "battle_report.json" : null;
  flatEvents = flattenReplayEvents(replay);
  selectedUnitId = null;
  selectedEventIndex = null;
  visualState = seekToTick(replay, 0);
  setStatus(`${replayResult.fileName} loaded（已加载）; ${reportMessage}`);
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
  stopAllPlayback();
  setModeReplay();
  setStatus(`Loading scenario（正在加载场景） ${scenario.id}`);

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
  loadedReplayFileName = scenario.replay_url;
  loadedReportFileName = scenario.report_url;
  selectedScenarioId = scenario.id;
  flatEvents = flattenReplayEvents(replay);
  selectedUnitId = null;
  selectedEventIndex = null;
  timelineFilter = "all";
  visualState = seekToTick(replay, 0);
  mode = "replay";
  setStatus(`scenario loaded（场景已加载）: ${scenario.id}`);
  render();
};

const seekTick = (tick: number): void => {
  if (mode !== "replay") {
    return;
  }
  seekTickInternal(tick, false);
};

const seekTickFromReport = (tick: number): void => {
  timelineFilter = "all";
  seekTickInternal(tick, true);
};

const seekTickInternal = (tick: number, selectLastEvent: boolean): void => {
  if (!replay || mode !== "replay") {
    return;
  }
  visualState = seekToTick(replay, tick);
  selectedEventIndex = selectLastEvent
    ? findLastEventIndexAtOrBeforeTick(flatEvents, visualState.currentTick)
    : null;
  render();
};

const seekEvent = (globalIndex: number): void => {
  if (!replay || flatEvents.length === 0 || mode !== "replay") {
    return;
  }
  const clampedIndex = Math.max(0, Math.min(flatEvents.length - 1, globalIndex));
  keepTimelineSelectionVisible(clampedIndex);
  visualState = seekToEvent(replay, clampedIndex);
  selectedEventIndex = clampedIndex;
  render();
};

const startPlayback = (): void => {
  if (!replay || playbackTimer !== null || mode !== "replay") {
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

const startLivePlayback = (): void => {
  if (mode !== "live" || liveSessionId === null || isLiveFinished()) {
    return;
  }
  if (livePlaybackTimer !== null) {
    return;
  }
  const intervalMs = Math.max(50, Math.round(LIVE_LOOP_INTERVAL_MS / liveSpeed()));
  livePlaybackTimer = window.setInterval(() => {
    void (async () => {
      if (liveStepInFlight || liveSessionId === null || isLiveFinished()) {
        return;
      }
      liveStepInFlight = true;
      await stepLiveOnce(liveSpeed());
      if (isLiveFinished()) {
        stopLivePlayback();
      }
      liveStepInFlight = false;
    })().catch((error: unknown) => {
      liveStepInFlight = false;
      setStatus(`live step failed（实时推进失败）: ${errorMessage(error)}`);
      stopLivePlayback();
    });
  }, intervalMs);
};

const stopLivePlayback = (): void => {
  if (livePlaybackTimer === null) {
    return;
  }
  window.clearInterval(livePlaybackTimer);
  livePlaybackTimer = null;
  liveStatusValue.textContent = "paused（暂停）";
};

const isLiveFinished = (): boolean => {
  if (liveFinished) {
    return true;
  }
  const endTick = liveResult?.end_tick;
  return endTick !== null && endTick !== undefined;
};

const startLiveBattleLoop = async (): Promise<void> => {
  stopAllPlayback();
  setModeLive();
  resetLiveStateForNewSession();
  liveFinished = false;
  liveApiUrl = liveApiUrlInput.value.trim() || DEFAULT_LIVE_API_URL;
  liveBattleId = liveBattleIdInput.value.trim() || "demo_001";
  const seedInput = parseSeed(liveSeedInput.value);
  if (seedInput === null) {
    setStatus("Seed must be a valid integer（种子必须为整数）");
    setLiveApiStatus("Live API unavailable（实时 API 不可用）");
    setModeReplay();
    stopLivePlayback();
    return;
  }
  liveSeed = seedInput;

  setLiveApiStatus("Checking API（正在检查 API）");
  const health = await healthLiveApi(liveApiUrl);
  if (!health.ok) {
    setStatus(health.error);
    setLiveApiStatus(health.error || "Live API unavailable（实时 API 不可用）");
    setModeReplay();
    stopLivePlayback();
    return;
  }

  const started = await startLiveBattle(liveApiUrl, liveBattleId, liveSeed);
  if (!started.ok) {
    setStatus(started.error);
    setLiveApiStatus(started.error);
    setModeReplay();
    stopLivePlayback();
    return;
  }

  setModeLive();
  liveSessionId = started.session_id;
  liveEventCursor = started.next_event_index;
  liveSessionIdValue.textContent = liveSessionId;
  liveResult = toBattleResult(started.snapshot.result);
  liveFinished = !!started.snapshot.finished;
  visualState = buildVisualStateFromSnapshot(started.snapshot);
  flatEvents = appendLiveEvents([], started.events);
  selectedUnitId = null;
  selectedEventIndex = flatEvents.length > 0 ? flatEvents.length - 1 : null;
  replay = null;
  report = null;
  loadedScenario = null;
  loadedReplayFileName = "live session";
  loadedReportFileName = "live session";
  timelineFilter = "all";
  liveStatusValue.textContent = "running（运行中）";
  if (!liveFinished) {
    startLivePlayback();
  } else {
    setLiveApiStatus("Victory（胜负） already determined at start（启动即已完成胜负）");
    setStatus("Live battle finished（实时战斗已结束）");
    stopLivePlayback();
  }
  setLiveApiStatus(`Connected to（已连接到） ${liveApiUrl}`);
  setStatus("Live battle started（实时战斗已开始）");
  render();
};

const stepLiveOnce = async (ticks: number): Promise<void> => {
  if (liveSessionId === null) {
    setLiveApiStatus("No live session（没有实时会话）");
    return;
  }
  setLiveApiStatus("Running live battle（实时进行中）...");
  const response = await stepLiveBattle(liveApiUrl, liveSessionId, Math.max(1, Math.floor(ticks)));
  if (!response.ok) {
    setLiveApiStatus(response.error);
    setStatus(response.error);
    stopLivePlayback();
    return;
  }

  if (response.snapshot) {
    visualState = buildVisualStateFromSnapshot(response.snapshot);
    liveResult = toBattleResult(response.snapshot.result);
    liveFinished = response.snapshot.finished;
  }
  flatEvents = appendLiveEvents(flatEvents, response.events);
  if (response.next_event_index !== undefined) {
    liveEventCursor = response.next_event_index;
  }
  selectedEventIndex = flatEvents.length > 0 ? flatEvents.length - 1 : null;
  selectedUnitId = visualState ? selectedUnitId : null;
  liveEventCursorValue.textContent = String(liveEventCursor);
    setLiveApiStatus("Live battle running（实时进行中）");
  render();

  if (isLiveFinished()) {
    stopLivePlayback();
    setLiveApiStatus("Victory（胜负） complete（胜负完成）");
    setStatus("Live battle finished（实时战斗已结束）");
  }
};

const resetLiveSession = async (): Promise<void> => {
  if (liveSessionId === null) {
    clearLiveState("No live session（没有实时会话）");
    render();
    return;
  }
  stopLivePlayback();
  const result = await resetLiveBattle(liveApiUrl, liveSessionId);
  if (!result.ok) {
    setStatus(result.error);
    setLiveApiStatus(result.error);
    return;
  }
  clearLiveState("Live API ready（实时 API 就绪）");
  render();
};

const liveSpeed = (): number => {
  const value = Number(liveSpeedSelect.value);
  return Number.isFinite(value) && value > 0 ? value : 1;
};

const setModeReplay = (): void => {
  mode = "replay";
  liveSessionId = null;
  liveFinished = false;
  liveStatusValue.textContent = "idle（空闲）";
};

const setModeLive = (): void => {
  mode = "live";
  playbackTimer !== null && stopPlayback();
};

const stopAllPlayback = (): void => {
  stopPlayback();
  stopLivePlayback();
};

const playbackSpeed = (): number => {
  const value = Number(speedSelect.value);
  return Number.isFinite(value) && value > 0 ? value : 1;
};

const resetLiveStateForNewSession = (): void => {
  liveSessionId = null;
  replay = null;
  report = null;
  flatEvents = [];
  visualState = createEmptyVisualState();
  selectedUnitId = null;
  selectedEventIndex = null;
  liveEventCursor = 0;
  liveResult = null;
  liveFinished = false;
  liveSessionIdValue.textContent = "-";
  liveEventCursorValue.textContent = "0";
  liveStatusValue.textContent = "ready（就绪）";
  liveCurrentTickValue.textContent = "0";
  liveUnitAliveValue.textContent = "0/0";
  liveLatestEventValue.textContent = "-";
  liveTransportValue.textContent = "-";
};

const clearLiveState = (message: string): void => {
  setModeReplay();
  resetLiveStateForNewSession();
  liveSessionId = null;
  setLiveApiStatus(message);
  setStatus(message);
  loadedReplayFileName = null;
  loadedReportFileName = null;
  replayLoadState.textContent = "Not loaded（未加载）";
  reportLoadState.textContent = "Not loaded（未加载）";
  scenarioSummaryContainer.textContent = "";
};

const render = (): void => {
  const isLive = mode === "live";
  const maxTick = replay ? getReplayMaxTick(replay) : visualState.currentTick;
  const currentEvent = currentEventEntry();
  renderScenarioControls();
  renderLivePanel();

  tickSlider.max = String(maxTick);
  tickSlider.value = String(Math.min(visualState.currentTick, maxTick));
  tickSlider.disabled = !replay || isLive;
  playPauseButton.disabled = !replay || isLive;
  stepTickButton.disabled = !replay || isLive;
  previousEventButton.disabled = !replay || isLive || flatEvents.length === 0;
  nextEventButton.disabled = !replay || isLive || flatEvents.length === 0;
  playPauseButton.textContent = playbackTimer === null ? "Play（播放）" : "Pause（暂停）";

  tickReadout.textContent = `Tick（回合） ${visualState.currentTick} / ${maxTick}`;
  eventReadout.textContent = currentEvent
    ? `Event（事件） ${currentEvent.event.event_id} (${currentEvent.event.type})`
    : "Event（事件） -";

  metadata.textContent = isLive
    ? `battle（战斗） ${liveBattleId} | seed（种子） ${liveSeed} | events（事件） ${flatEvents.length}`
    : (replay
      ? `${replay.metadata.battle_id ?? "battle（战斗）"} | seed（种子） ${replay.metadata.seed ?? "-"} | events（事件） ${flatEvents.length}`
      : "No replay loaded（未加载回放）");

  replayLoadState.textContent = isLive
    ? "Live mode（实时模式）"
    : loadedReplayFileName
    ? `${loadedReplayFileName} loaded（已加载）`
    : "Not loaded（未加载）";
  reportLoadState.textContent = isLive
    ? "Live mode（实时模式）"
    : loadedReportFileName
    ? `${loadedReportFileName} loaded（已加载）`
    : "Not loaded（未加载）";

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
    liveMode: isLive,
    liveFinished,
    liveCurrentTick: visualState.currentTick,
    liveResult,
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
    autoScrollSelectedEvent: mode !== "live",
    onSelectEvent: (globalIndex) => {
      if (mode === "live") {
        selectedEventIndex = globalIndex;
        render();
        return;
      }
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
    liveMode: isLive,
    isFinished: liveFinished,
    liveResult,
    liveCurrentTick: visualState.currentTick,
  });
};

const setStatus = (message: string): void => {
  statusLine.textContent = message;
};

const setLiveApiStatus = (message: string): void => {
  liveStatusLine.textContent = message;
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
  scenarioManifestState.textContent = scenarios.length > 0
    ? `${scenarios.length} scenarios（${scenarios.length} 个场景）`
    : "Manifest not loaded（场景清单未加载）";
  loadBaselineDemoButton.disabled = scenarios.length === 0 || mode === "live";
  loadScenarioButton.disabled = scenarios.length === 0 || mode === "live";
  scenarioSelect.disabled = scenarios.length === 0 || mode === "live";

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

const renderLivePanel = (): void => {
  liveApiUrlInput.value = liveApiUrl;
  liveBattleIdInput.value = liveBattleId;
  liveSeedInput.value = String(liveSeed);
  liveSessionIdValue.textContent = liveSessionId ?? "-";
  liveEventCursorValue.textContent = String(liveEventCursor);
  liveCurrentTickValue.textContent = String(visualState.currentTick);
  const alive = [...visualState.units.values()].filter((unit) => unit.alive).length;
  const total = visualState.units.size;
  liveUnitAliveValue.textContent = `${alive}/${total}`;
  const latestEvent = flatEvents.length > 0 ? flatEvents[flatEvents.length - 1].event : null;
  liveLatestEventValue.textContent = latestEvent ? `${latestEvent.type} @ ${latestEvent.tick}` : "-";
  liveTransportValue.textContent = "HTTP Polling（HTTP 轮询）";
  if (!liveStatusLine.textContent) {
    liveStatusLine.textContent = "Live API not checked（未检查实时 API）";
  }

  pauseLiveButton.disabled = liveSessionId === null || livePlaybackTimer === null;
  resumeLiveButton.disabled = liveSessionId === null || livePlaybackTimer !== null;
  stepLiveButton.disabled = liveSessionId === null || mode !== "live";
  resetLiveButton.disabled = liveSessionId === null;
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
      addHighlight(highlights, payload.unit, "modifier-target");
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

const toBattleResult = (result: LiveBattleResult | null): LiveBattleResult | null => {
  if (!result) {
    return null;
  }
  return {
    winner: result.winner,
    reason: result.reason,
    end_tick: result.end_tick,
    winner_alive: result.winner_alive,
    loser_alive: result.loser_alive,
    winner_total_hp: result.winner_total_hp,
    loser_total_hp: result.loser_total_hp,
    summary: result.summary,
  };
};

const parseSeed = (value: string): number | null => {
  const parsed = Number.parseInt(value, 10);
  return Number.isFinite(parsed) && parsed >= 0 ? parsed : null;
};

const getPlaybackEndTick = (currentReplay: ReplayDocument): number => {
  const resultEndTick = currentReplay.metadata.result?.end_tick;
  return typeof resultEndTick === "number" && Number.isFinite(resultEndTick)
    ? resultEndTick
    : getReplayMaxTick(currentReplay);
};

const errorMessage = (error: unknown): string => {
  if (error instanceof Error) {
    return error.message;
  }
  return String(error);
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
