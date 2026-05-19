import "./styles.css";

import { createLivePixiBattlefieldRenderer } from "./livePixiBattlefieldRenderer";
import { renderBattleSummary } from "./battleSummaryView";
import { renderBoard, type EventUnitHighlight } from "./boardView";
import { createPerformanceTelemetry, type PerformanceSnapshot } from "./performanceTelemetry";
import { renderEventHighlight } from "./eventHighlightView";
import { renderFormationRoster } from "./formationRosterView";
import {
  appendLiveEvents,
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
import { DEFAULT_LIVE_API_URL, healthLiveApi, resetLiveBattle, startLiveBattle, stepLiveBattle } from "./liveApiClient";
import { createVisualStateBuffer } from "./visualStateBuffer";
import { renderTimeline, type TimelineFilter, type TimelineRenderMode } from "./timelineView";
import { renderUnitDetail } from "./unitDetailView";
import type { BattleReport, DemoScenario, LiveBattleResult, ReplayDocument, ScenarioManifest } from "./replayTypes";

type ViewerMode = "replay" | "live";
type LiveReportMode = "idle" | "in-progress" | "finished";

const LIVE_FRAME_MS = 33;
const LIVE_LOOP_INTERVAL_MS = 250;
const LIVE_TIMELINE_MAX_ROWS = 150;

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
const pixiBattlefieldContainer = element<HTMLDivElement>("pixi-battlefield");
const scenarioSummaryContainer = element<HTMLDivElement>("scenario-summary");
const battleSummaryContainer = element<HTMLDivElement>("battle-summary");
const eventHighlightContainer = element<HTMLDivElement>("event-highlight");
const timelineContainer = element<HTMLDivElement>("timeline");
const reportContainer = element<HTMLElement>("report");
const unitDetailContainer = element<HTMLDivElement>("unit-detail");
const rosterContainer = element<HTMLDivElement>("formation-roster");
const performancePanelContainer = element<HTMLDivElement>("performance-panel");

const telemetry = createPerformanceTelemetry();
const liveStateBuffer = createVisualStateBuffer();

let liveRenderer: ReturnType<typeof createLivePixiBattlefieldRenderer> | null = null;
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
let liveRenderFrameHandle: number | null = null;
let liveStepInFlight = false;
let liveFrameLastRenderTs = 0;
let loadedReplayFileName: string | null = null;
let loadedReportFileName: string | null = null;
let scenarioManifest: ScenarioManifest | null = null;
let selectedScenarioId: string | null = null;
let loadedScenario: DemoScenario | null = null;
let scenarioControlsSignature = "";
let liveSessionId: string | null = null;
let liveApiUrl = DEFAULT_LIVE_API_URL;
let liveBattleId = "demo_001";
let liveSeed = 1001;
let liveEventCursor = 0;
let liveResult: LiveBattleResult | null = null;
let liveFinished = false;
let liveReportMode: LiveReportMode = "idle";

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
  setModeReplay();
  void loadScenario(scenario);
});

loadScenarioButton.addEventListener("click", () => {
  const scenario = selectedScenario();
  if (!scenario) {
    setStatus("Select a scenario first（请先选择场景）.");
    return;
  }
  stopAllPlayback();
  setModeReplay();
  void loadScenario(scenario);
});

playPauseButton.addEventListener("click", () => {
  if (mode !== "replay") {
    return;
  }
  if (playbackTimer === null) {
    startReplayPlayback();
  } else {
    stopReplayPlayback();
    renderReplayFrame();
  }
});

stepTickButton.addEventListener("click", () => {
  if (mode !== "replay") {
    return;
  }
  stopReplayPlayback();
  seekTick(visualState.currentTick + 1);
});

previousEventButton.addEventListener("click", () => {
  if (mode !== "replay") {
    return;
  }
  stopReplayPlayback();
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
  stopReplayPlayback();
  const currentIndex = selectedEventIndex ?? findLastEventIndexAtOrBeforeTick(flatEvents, visualState.currentTick);
  const nextIndex = currentIndex === null ? 0 : Math.min(flatEvents.length - 1, currentIndex + 1);
  seekEvent(nextIndex);
});

tickSlider.addEventListener("input", () => {
  if (mode !== "replay") {
    return;
  }
  stopReplayPlayback();
  seekTick(Number(tickSlider.value));
});

speedSelect.addEventListener("change", () => {
  if (playbackTimer !== null) {
    stopReplayPlayback();
    startReplayPlayback();
  }
});

startLiveButton.addEventListener("click", () => {
  void startLiveBattleLoop();
});
pauseLiveButton.addEventListener("click", () => {
  stopLivePlaybackLoop();
});
resumeLiveButton.addEventListener("click", () => {
  startLivePlaybackLoop();
});
stepLiveButton.addEventListener("click", () => {
  stopLivePlaybackLoop();
  void stepLiveOnce(1);
});
resetLiveButton.addEventListener("click", () => {
  void resetLiveSession();
});

const loadFiles = async (): Promise<void> => {
  stopAllPlayback();
  destroyPixiRenderer();
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
  telemetry.setTotalEvents(flatEvents.length);
  selectedUnitId = null;
  selectedEventIndex = null;
  visualState = seekToTick(replay, 0);
  setStatus(`${replayResult.fileName} loaded（已加载）; ${reportMessage}`);
  renderReplayFrame();
};

const loadScenarioManifest = async (): Promise<void> => {
  const result = await fetchScenarioManifest();
  if (!result.ok) {
    scenarioManifest = null;
    selectedScenarioId = null;
    renderScenarioControls();
    return;
  }

  scenarioManifest = result.data;
  selectedScenarioId = baselineScenario()?.id ?? result.data.scenarios[0]?.id ?? null;
  renderScenarioControls();
};

const loadScenario = async (scenario: DemoScenario): Promise<void> => {
  stopAllPlayback();
  destroyPixiRenderer();
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
  telemetry.setTotalEvents(flatEvents.length);
  selectedUnitId = null;
  selectedEventIndex = null;
  timelineFilter = "all";
  visualState = seekToTick(replay, 0);
  mode = "replay";
  setStatus(`scenario loaded（场景已加载）: ${scenario.id}`);
  renderReplayFrame();
};

const startReplayPlayback = (): void => {
  if (!replay || playbackTimer !== null || mode !== "replay") {
    return;
  }
  const endTick = getReplayMaxTick(replay);
  if (visualState.currentTick >= endTick) {
    visualState = seekToTick(replay, 0);
    selectedEventIndex = null;
  }
  const intervalMs = Math.max(50, Math.round(250 / replaySpeed()));
  playbackTimer = window.setInterval(() => {
    if (!replay) {
      stopReplayPlayback();
      return;
    }
    const currentEndTick = getReplayMaxTick(replay);
    if (visualState.currentTick >= currentEndTick) {
      stopReplayPlayback();
      renderReplayFrame();
      return;
    }
    visualState = seekToTick(replay, Math.min(currentEndTick, visualState.currentTick + 1));
    selectedEventIndex = null;
    renderReplayFrame();
  }, intervalMs);
  renderReplayFrame();
};

const stopReplayPlayback = (): void => {
  if (playbackTimer === null) {
    return;
  }
  window.clearInterval(playbackTimer);
  playbackTimer = null;
};

const startLivePlaybackLoop = (): void => {
  if (mode !== "live" || liveSessionId === null || isLiveFinished() || livePlaybackTimer !== null) {
    return;
  }
  const intervalMs = Math.max(60, Math.round(LIVE_LOOP_INTERVAL_MS / liveSpeed()));
  livePlaybackTimer = window.setInterval(() => {
    void (async () => {
      if (liveStepInFlight || liveSessionId === null || isLiveFinished()) {
        return;
      }
      liveStepInFlight = true;
      try {
        await stepLiveOnce(liveSpeed());
      } finally {
        liveStepInFlight = false;
      }
    })().catch((error: unknown) => {
      liveStepInFlight = false;
      const message = `live step failed（实时推进失败）: ${errorMessage(error)}`;
      setStatus(message);
      setLiveApiStatus(message);
      stopLivePlaybackLoop();
    });
  }, intervalMs);
  liveStatusValue.textContent = "running（运行中）";
};

const stopLivePlaybackLoop = (): void => {
  if (livePlaybackTimer === null) {
    return;
  }
  window.clearInterval(livePlaybackTimer);
  livePlaybackTimer = null;
  if (mode === "live") {
    liveStatusValue.textContent = "paused（暂停）";
  }
};

const startLiveFrameLoop = (): void => {
  if (liveRenderFrameHandle !== null) {
    return;
  }
  const frame = (timestamp: number): void => {
    if (mode !== "live") {
      liveRenderFrameHandle = null;
      return;
    }
    telemetry.recordFrame(timestamp);
    if (liveFrameLastRenderTs === 0 || timestamp - liveFrameLastRenderTs >= LIVE_FRAME_MS) {
      liveFrameLastRenderTs = timestamp;
      renderLiveFrame(timestamp);
    }
    liveRenderFrameHandle = window.requestAnimationFrame(frame);
  };
  liveRenderFrameHandle = window.requestAnimationFrame(frame);
};

const stopLiveFrameLoop = (): void => {
  if (liveRenderFrameHandle === null) {
    return;
  }
  window.cancelAnimationFrame(liveRenderFrameHandle);
  liveRenderFrameHandle = null;
  liveFrameLastRenderTs = 0;
};

const startLiveBattleLoop = async (): Promise<void> => {
  stopAllPlayback();
  setModeLive();
  telemetry.reset();
  resetLiveStateForNewSession();
  liveApiUrl = liveApiUrlInput.value.trim() || DEFAULT_LIVE_API_URL;
  liveBattleId = liveBattleIdInput.value.trim() || "demo_001";
  const parsedSeed = parseSeed(liveSeedInput.value);
  if (parsedSeed === null) {
    const message = "Seed must be a valid integer（种子必须为整数）";
    setStatus(message);
    setLiveApiStatus(message);
    setModeReplay();
    return;
  }
  liveSeed = parsedSeed;

  setLiveApiStatus("Checking API（正在检查 API）");
  const health = await healthLiveApi(liveApiUrl);
  if (!health.ok) {
    setStatus(health.error);
    setLiveApiStatus(health.error);
    setModeReplay();
    return;
  }

  const started = await startLiveBattle(liveApiUrl, liveBattleId, liveSeed);
  if (!started.ok) {
    setStatus(started.error);
    setLiveApiStatus(started.error);
    setModeReplay();
    return;
  }

  setModeLive();
  ensurePixiRenderer();
  liveSessionId = started.session_id;
  liveEventCursor = started.next_event_index;
  flatEvents = appendLiveEvents([], started.events);
  telemetry.setTotalEvents(flatEvents.length);
  liveResult = started.snapshot.result ?? null;
  liveFinished = Boolean(started.snapshot.finished);
  liveStateBuffer.clear();
  if (started.snapshot) {
    liveStateBuffer.pushSnapshot(started.snapshot, performance.now());
    visualState = liveStateBuffer.getInterpolatedState(performance.now(), 0);
  }
  selectedUnitId = null;
  selectedEventIndex = flatEvents.length > 0 ? flatEvents.length - 1 : null;
  replay = null;
  report = null;
  loadedScenario = null;
  loadedReplayFileName = "live session";
  loadedReportFileName = "live session";
  liveStatusValue.textContent = "running（运行中）";
  setLiveApiStatus(`Connected to（已连接到） ${liveApiUrl}`);
  setStatus("Live battle started（实时战斗已开始）");
  renderLiveStartPanels();
  renderLiveSelectionPanels();
  renderLiveFrame(performance.now());
  if (liveFinished) {
    stopLivePlaybackLoop();
    setLiveApiStatus("Victory（胜负） already determined at start（启动即已完成胜负）");
    setStatus("Live battle finished（实时战斗已结束）");
    renderLiveReportFinal();
  } else {
    startLivePlaybackLoop();
    startLiveFrameLoop();
  }
};

const stepLiveOnce = async (ticks: number): Promise<void> => {
  if (liveSessionId === null) {
    setLiveApiStatus("No live session（没有实时会话）");
    return;
  }
  const apiStart = performance.now();
  const response = await stepLiveBattle(liveApiUrl, liveSessionId, Math.max(1, Math.floor(ticks)));
  telemetry.recordApiStep(performance.now() - apiStart);

  if (!response.ok) {
    stopLivePlaybackLoop();
    setLiveApiStatus(response.error);
    setStatus(response.error);
    return;
  }

  if (response.snapshot) {
    liveStateBuffer.pushSnapshot(response.snapshot, performance.now());
    visualState = liveStateBuffer.getInterpolatedState(performance.now(), 0);
    liveResult = response.snapshot.result ?? liveResult;
    liveFinished = response.snapshot.finished;
  }
  if (response.events.length > 0) {
    liveStateBuffer.pushEvents(response.events);
    flatEvents = appendLiveEvents(flatEvents, response.events);
    telemetry.setTotalEvents(flatEvents.length);
    liveRenderer?.setEventHighlights(response.events);
  }
  if (response.next_event_index !== undefined) {
    liveEventCursor = response.next_event_index;
  }
  selectedEventIndex = flatEvents.length > 0 ? flatEvents.length - 1 : selectedEventIndex;
  setLiveApiStatus("Live battle running（实时进行中）");
  renderLiveSelectionPanels();
  renderLiveFrame(performance.now());

  if (isLiveFinished()) {
    stopLivePlaybackLoop();
    setLiveApiStatus("Victory（胜负） complete（胜负完成）");
    setStatus("Live battle finished（实时战斗已结束）");
    renderLiveReportFinal();
  }
};

const resetLiveSession = async (): Promise<void> => {
  if (liveSessionId === null) {
    clearLiveState("No live session（没有实时会话）");
    renderReplayFrame();
    return;
  }
  stopLivePlaybackLoop();
  stopLiveFrameLoop();
  const result = await resetLiveBattle(liveApiUrl, liveSessionId);
  if (!result.ok) {
    setStatus(result.error);
    setLiveApiStatus(result.error);
    return;
  }
  destroyPixiRenderer();
  clearLiveState("Live API ready（实时 API 就绪）");
  setModeReplay();
  renderReplayFrame();
};

const renderLiveFrame = (now: number): void => {
  if (mode !== "live") {
    return;
  }
  ensurePixiRenderer();

  const frameState = liveStateBuffer.getInterpolatedState(now, 120);
  visualState = frameState;
  const currentEvent = currentEventEntry();

  boardContainer.hidden = true;
  pixiBattlefieldContainer.hidden = false;

  tickReadout.textContent = `Tick（回合） ${frameState.currentTick}`;
  eventReadout.textContent = currentEvent
    ? `Event（事件） ${currentEvent.event.event_id} (${currentEvent.event.type})`
    : "Event（事件） -";
  metadata.textContent = `battle（战斗） ${liveBattleId} | seed（种子） ${liveSeed} | events（事件） ${flatEvents.length}`;
  replayLoadState.textContent = "Live mode（实时模式）";
  reportLoadState.textContent = "Live mode（实时模式）";
  liveSessionIdValue.textContent = liveSessionId ?? "-";
  liveEventCursorValue.textContent = String(liveEventCursor);
  liveCurrentTickValue.textContent = String(frameState.currentTick);
  liveUnitAliveValue.textContent = `${aliveUnits(frameState)}/${frameState.units.size}`;
  liveLatestEventValue.textContent = latestLiveEventLabel();
  liveTransportValue.textContent = "HTTP Polling（HTTP 轮询）";
  liveStatusValue.textContent = liveFinished ? "finished（已结束）" : livePlaybackTimer === null ? "paused（暂停）" : "running（运行中）";
  pauseLiveButton.disabled = liveSessionId === null || livePlaybackTimer === null;
  resumeLiveButton.disabled = liveSessionId === null || livePlaybackTimer !== null;
  stepLiveButton.disabled = liveSessionId === null || liveFinished;
  resetLiveButton.disabled = liveSessionId === null;

  const pixiStart = performance.now();
  liveRenderer?.setSelectedUnit(selectedUnitId);
  liveRenderer?.setVisualState(frameState);
  liveRenderer?.update(now);
  telemetry.recordPixiRender(performance.now() - pixiStart);

  renderBattleSummary(battleSummaryContainer, {
    replay: null,
    report: null,
    eventCount: flatEvents.length,
    liveMode: true,
    liveFinished,
    liveCurrentTick: frameState.currentTick,
    liveResult,
  });
  renderEventHighlight(eventHighlightContainer, currentEvent, frameState);
  renderTimelinePanel(true);
  renderPerformancePanel();
  renderLiveReportIfNeeded();
  telemetry.setTotalEvents(flatEvents.length);
};

const renderLiveStartPanels = (): void => {
  scenarioSummaryContainer.textContent = "Live battle active（实时战斗进行中）";
  renderLiveReportInProgress();
  renderPerformancePanel();
};

const renderLiveSelectionPanels = (): void => {
  renderFormationRoster(rosterContainer, {
    state: visualState,
    selectedUnitId,
    onSelectUnit: (unitId) => {
      selectUnit(unitId);
    },
  });
  renderUnitDetailPanel();
};

const renderLiveReportIfNeeded = (): void => {
  if (liveFinished) {
    if (liveReportMode !== "finished") {
      renderLiveReportFinal();
    }
    return;
  }
  if (liveReportMode !== "in-progress") {
    renderLiveReportInProgress();
  }
};

const renderLiveReportInProgress = (): void => {
  liveReportMode = "in-progress";
  renderReport(reportContainer, null, {
    selectedUnitId,
    onSelectUnit: selectUnit,
    onSeekTick: seekTickFromReport,
    liveMode: true,
    isFinished: false,
    liveResult,
    liveCurrentTick: visualState.currentTick,
  });
};

const renderLiveReportFinal = (): void => {
  liveReportMode = "finished";
  renderReport(reportContainer, null, {
    selectedUnitId,
    onSelectUnit: selectUnit,
    onSeekTick: seekTickFromReport,
    liveMode: true,
    isFinished: true,
    liveResult,
    liveCurrentTick: visualState.currentTick,
  });
};

const renderReplayFrame = (): void => {
  if (mode === "live") {
    renderLiveFrame(performance.now());
    return;
  }

  const maxTick = replay ? getReplayMaxTick(replay) : visualState.currentTick;
  const currentEvent = currentEventEntry();

  renderScenarioControls();
  renderStaticShell();

  tickSlider.max = String(maxTick);
  tickSlider.value = String(Math.min(visualState.currentTick, maxTick));
  tickSlider.disabled = !replay;
  playPauseButton.disabled = !replay;
  stepTickButton.disabled = !replay;
  previousEventButton.disabled = !replay || flatEvents.length === 0;
  nextEventButton.disabled = !replay || flatEvents.length === 0;
  playPauseButton.textContent = playbackTimer === null ? "Play（播放）" : "Pause（暂停）";

  tickReadout.textContent = `Tick（回合） ${visualState.currentTick} / ${maxTick}`;
  eventReadout.textContent = currentEvent
    ? `Event（事件） ${currentEvent.event.event_id} (${currentEvent.event.type})`
    : "Event（事件） -";

  metadata.textContent = replay
    ? `${replay.metadata.battle_id ?? "battle（战斗）"} | seed（种子） ${replay.metadata.seed ?? "-"} | events（事件） ${flatEvents.length}`
    : "No replay loaded（未加载回放）";
  replayLoadState.textContent = loadedReplayFileName
    ? `${loadedReplayFileName} loaded（已加载）`
    : "Not loaded（未加载）";
  reportLoadState.textContent = loadedReportFileName
    ? `${loadedReportFileName} loaded（已加载）`
    : "Not loaded（未加载）";
  liveStatusLine.textContent = "Live API not checked（尚未检查实时 API）";

  destroyPixiRenderer();
  boardContainer.hidden = false;
  pixiBattlefieldContainer.hidden = true;

  const boardStart = performance.now();
  renderBoard(boardContainer, {
    state: visualState,
    selectedUnitId,
    unitHighlights: unitHighlightsForEvent(currentEvent),
    onSelectUnit: (unitId) => {
      selectUnit(unitId);
    },
  });
  telemetry.recordBoardRender(performance.now() - boardStart);

  renderBattleSummary(battleSummaryContainer, {
    replay,
    report,
    eventCount: flatEvents.length,
    liveMode: false,
    liveFinished: false,
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
  renderTimelinePanel(false);
  renderFormationRoster(rosterContainer, {
    state: visualState,
    selectedUnitId,
    onSelectUnit: (unitId) => {
      selectUnit(unitId);
    },
  });
  renderUnitDetailPanel();
  renderReport(reportContainer, report, {
    selectedUnitId,
    onSelectUnit: selectUnit,
    onSeekTick: seekTickFromReport,
    liveMode: false,
    isFinished: false,
    liveResult,
    liveCurrentTick: visualState.currentTick,
  });
  renderPerformancePanel();
};

const renderUnitDetailPanel = (): void => {
  renderUnitDetail(unitDetailContainer, visualState, report, selectedUnitId);
};

const renderTimelinePanel = (liveMode: boolean): void => {
  const start = performance.now();
  renderTimeline(timelineContainer, {
    events: flatEvents,
    selectedEventIndex,
    filter: timelineFilter,
    autoScrollSelectedEvent: !liveMode,
    renderMode: liveMode ? "live_capped" : "full",
    maxRows: liveMode ? LIVE_TIMELINE_MAX_ROWS : 150,
    onSelectEvent: (globalIndex) => {
      if (mode === "live") {
        selectedEventIndex = globalIndex;
        renderLiveFrame(performance.now());
        return;
      }
      stopReplayPlayback();
      seekEvent(globalIndex);
    },
    onFilterChange: (filter) => {
      timelineFilter = filter;
      if (mode === "live") {
        renderLiveFrame(performance.now());
        return;
      }
      renderReplayFrame();
    },
  });
  telemetry.recordTimelineRender(performance.now() - start);
  telemetry.setRenderedTimelineRows(renderedTimelineRowCount(liveMode));
};

const renderPerformancePanel = (): void => {
  performancePanelContainer.replaceChildren();
  performancePanelContainer.append(performanceGrid(telemetry.getSnapshot()));
};

const performanceGrid = (snapshot: PerformanceSnapshot): HTMLElement => {
  const grid = document.createElement("div");
  grid.className = "stat-grid performance-grid";
  const rows: [string, string][] = [
    ["FPS（帧率）", formatMetric(snapshot.fps, "fps")],
    ["Frame Time（帧耗时）", formatMetric(snapshot.lastFrameMs, "ms")],
    ["Render Time（渲染耗时）", formatMetric(snapshot.lastRenderMs, "ms")],
    ["Pixi Render（Pixi 渲染）", formatMetric(snapshot.lastPixiRenderMs, "ms")],
    ["Board（战场）", formatMetric(snapshot.lastBoardRenderMs, "ms")],
    ["Timeline（事件日志）", formatMetric(snapshot.lastTimelineRenderMs, "ms")],
    ["API Step（接口推进）", formatMetric(snapshot.lastApiStepMs, "ms")],
    ["Timeline Rows（事件行数）", String(snapshot.displayedTimelineRows)],
    ["Total Events（总事件）", String(snapshot.totalEvents)],
  ];
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

const formatMetric = (value: number, suffix: string): string => {
  if (!Number.isFinite(value) || value <= 0) {
    return "-";
  }
  const rounded = Math.round(value * 10) / 10;
  return suffix === "fps" ? String(rounded) : `${rounded}${suffix}`;
};

const renderScenarioControls = (): void => {
  const scenarios = scenarioManifest?.scenarios ?? [];
  const signature = scenarios.map((scenario) => scenario.id).join("|");
  scenarioLoader.hidden = scenarios.length === 0;
  scenarioManifestState.textContent = scenarios.length > 0
    ? `${scenarios.length} scenarios（${scenarios.length} 个场景）`
    : "Manifest not loaded（场景清单未加载）";
  loadBaselineDemoButton.disabled = scenarios.length === 0 || mode === "live";
  loadScenarioButton.disabled = scenarios.length === 0 || mode === "live";
  scenarioSelect.disabled = scenarios.length === 0 || mode === "live";

  if (scenarioControlsSignature === signature) {
    return;
  }
  scenarioControlsSignature = signature;

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

const ensurePixiRenderer = (): void => {
  if (liveRenderer) {
    return;
  }
  liveRenderer = createLivePixiBattlefieldRenderer(pixiBattlefieldContainer, {
    onSelectUnit: (unitId) => {
      selectUnit(unitId);
    },
    debugOverlay: false,
  });
};

const destroyPixiRenderer = (): void => {
  if (!liveRenderer) {
    return;
  }
  liveRenderer.destroy();
  liveRenderer = null;
  pixiBattlefieldContainer.replaceChildren();
};

const renderStaticShell = (): void => {
  boardContainer.hidden = false;
  pixiBattlefieldContainer.hidden = true;
};

const setStatus = (message: string): void => {
  statusLine.textContent = message;
};

const setLiveApiStatus = (message: string): void => {
  liveStatusLine.textContent = message;
};

const aliveUnits = (state: VisualState): number => {
  let count = 0;
  for (const unit of state.units.values()) {
    if (unit.alive) {
      count += 1;
    }
  }
  return count;
};

const latestLiveEventLabel = (): string => {
  const latest = flatEvents.length > 0 ? flatEvents[flatEvents.length - 1].event : null;
  return latest ? `${latest.type} @ ${latest.tick}` : "-";
};

const parseSeed = (value: string): number | null => {
  const parsed = Number.parseInt(value, 10);
  return Number.isFinite(parsed) && parsed >= 0 ? parsed : null;
};

const errorMessage = (error: unknown): string => {
  if (error instanceof Error) {
    return error.message;
  }
  return String(error);
};

const stopAllPlayback = (): void => {
  stopReplayPlayback();
  stopLivePlaybackLoop();
  stopLiveFrameLoop();
};

const setModeReplay = (): void => {
  mode = "replay";
  liveSessionId = null;
  liveFinished = false;
  liveStatusValue.textContent = "idle（空闲）";
  stopLiveFrameLoop();
};

const setModeLive = (): void => {
  mode = "live";
  stopReplayPlayback();
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
  liveReportMode = "idle";
  liveSessionIdValue.textContent = "-";
  liveEventCursorValue.textContent = "0";
  liveStatusValue.textContent = "ready（就绪）";
  liveCurrentTickValue.textContent = "0";
  liveUnitAliveValue.textContent = "0/0";
  liveLatestEventValue.textContent = "-";
  liveTransportValue.textContent = "-";
};

const clearLiveState = (message: string): void => {
  resetLiveStateForNewSession();
  setLiveApiStatus(message);
  setStatus(message);
  loadedReplayFileName = null;
  loadedReportFileName = null;
  replayLoadState.textContent = "Not loaded（未加载）";
  reportLoadState.textContent = "Not loaded（未加载）";
  scenarioSummaryContainer.textContent = "";
  destroyPixiRenderer();
};

const selectUnit = (unitId: string): void => {
  selectedUnitId = unitId;
  if (mode === "live") {
    renderLiveSelectionPanels();
    renderLiveFrame(performance.now());
  } else {
    renderReplayFrame();
  }
};

const seekTick = (tick: number): void => {
  if (mode !== "replay" || !replay) {
    return;
  }
  visualState = seekToTick(replay, tick);
  selectedEventIndex = findLastEventIndexAtOrBeforeTick(flatEvents, visualState.currentTick);
  renderReplayFrame();
};

const seekTickFromReport = (tick: number): void => {
  timelineFilter = "all";
  seekTick(tick);
};

const seekEvent = (globalIndex: number): void => {
  if (!replay || flatEvents.length === 0 || mode !== "replay") {
    return;
  }
  const clampedIndex = Math.max(0, Math.min(flatEvents.length - 1, globalIndex));
  keepTimelineSelectionVisible(clampedIndex);
  visualState = seekToEvent(replay, clampedIndex);
  selectedEventIndex = clampedIndex;
  renderReplayFrame();
};

const replaySpeed = (): number => {
  const value = Number(speedSelect.value);
  return Number.isFinite(value) && value > 0 ? value : 1;
};

const liveSpeed = (): number => {
  const value = Number(liveSpeedSelect.value);
  return Number.isFinite(value) && value > 0 ? value : 1;
};

const isLiveFinished = (): boolean => {
  if (liveFinished) {
    return true;
  }
  const endTick = liveResult?.end_tick;
  return typeof endTick === "number" && visualState.currentTick >= endTick;
};

const baselineScenario = (): DemoScenario | null => {
  const scenarios = scenarioManifest?.scenarios ?? [];
  return scenarios.find((scenario) => scenario.id === "demo_001") ?? scenarios[0] ?? null;
};

const selectedScenario = (): DemoScenario | null => {
  const scenarios = scenarioManifest?.scenarios ?? [];
  const scenarioId = selectedScenarioId ?? scenarioSelect.value;
  return scenarios.find((scenario) => scenario.id === scenarioId) ?? scenarios[0] ?? null;
};

const keepTimelineSelectionVisible = (globalIndex: number): void => {
  const event = flatEvents[globalIndex]?.event;
  if (event && timelineFilter !== "all" && event.type !== timelineFilter) {
    timelineFilter = "all";
  }
};

const unitHighlightsForEvent = (entry: FlatReplayEvent | null): Map<string, EventUnitHighlight> => {
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

const renderedTimelineRowCount = (liveMode: boolean): number => {
  const rows = timelineFilter === "all"
    ? flatEvents
    : flatEvents.filter((entry) => entry.event.type === timelineFilter);
  return liveMode ? Math.min(rows.length, LIVE_TIMELINE_MAX_ROWS) : rows.length;
};

const currentEventEntry = (): FlatReplayEvent | null => {
  const index = selectedEventIndex ?? visualState.appliedEventIndex;
  return index === null ? null : flatEvents[index] ?? null;
};

function element<T extends HTMLElement>(id: string): T {
  const found = document.getElementById(id);
  if (!found) {
    throw new Error(`Missing element #${id}`);
  }
  return found as T;
}

renderReplayFrame();
void loadScenarioManifest();
