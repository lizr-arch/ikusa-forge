import "./styles.css";

import { renderBoard } from "./boardView";
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
import { readBattleReportFile, readReplayDocumentFile } from "./replayLoader";
import { renderReport } from "./reportView";
import { renderTimeline, type TimelineFilter } from "./timelineView";
import { renderUnitDetail } from "./unitDetailView";
import type { BattleReport, ReplayDocument } from "./replayTypes";

const replayInput = element<HTMLInputElement>("replay-file");
const reportInput = element<HTMLInputElement>("report-file");
const loadFilesButton = element<HTMLButtonElement>("load-files");
const playPauseButton = element<HTMLButtonElement>("play-pause");
const stepTickButton = element<HTMLButtonElement>("step-tick");
const previousEventButton = element<HTMLButtonElement>("previous-event");
const nextEventButton = element<HTMLButtonElement>("next-event");
const tickSlider = element<HTMLInputElement>("tick-slider");
const speedSelect = element<HTMLSelectElement>("speed-select");
const metadata = element<HTMLDivElement>("metadata");
const statusLine = element<HTMLDivElement>("status");
const tickReadout = element<HTMLDivElement>("tick-readout");
const boardContainer = element<HTMLDivElement>("board");
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

loadFilesButton.addEventListener("click", () => {
  void loadFiles();
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
  flatEvents = flattenReplayEvents(replay);
  selectedUnitId = null;
  selectedEventIndex = null;
  visualState = seekToTick(replay, 0);
  setStatus(`${replayResult.fileName} loaded; ${reportMessage}`);
  render();
};

const seekTick = (tick: number): void => {
  if (!replay) {
    return;
  }
  visualState = seekToTick(replay, tick);
  selectedEventIndex = null;
  render();
};

const seekEvent = (globalIndex: number): void => {
  if (!replay || flatEvents.length === 0) {
    return;
  }
  const clampedIndex = Math.max(0, Math.min(flatEvents.length - 1, globalIndex));
  visualState = seekToEvent(replay, clampedIndex);
  selectedEventIndex = clampedIndex;
  render();
};

const startPlayback = (): void => {
  if (!replay || playbackTimer !== null) {
    return;
  }
  const intervalMs = Math.max(50, Math.round(250 / playbackSpeed()));
  playbackTimer = window.setInterval(() => {
    if (!replay) {
      stopPlayback();
      return;
    }
    const maxTick = getReplayMaxTick(replay);
    if (visualState.currentTick >= maxTick) {
      stopPlayback();
      render();
      return;
    }
    visualState = seekToTick(replay, visualState.currentTick + 1);
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
  tickSlider.max = String(maxTick);
  tickSlider.value = String(Math.min(visualState.currentTick, maxTick));
  tickSlider.disabled = !replay;
  playPauseButton.disabled = !replay;
  stepTickButton.disabled = !replay;
  previousEventButton.disabled = !replay || flatEvents.length === 0;
  nextEventButton.disabled = !replay || flatEvents.length === 0;
  playPauseButton.textContent = playbackTimer === null ? "Play" : "Pause";
  tickReadout.textContent = `Tick ${visualState.currentTick}`;
  metadata.textContent = replay
    ? `${replay.metadata.battle_id ?? "battle"} | seed ${replay.metadata.seed ?? "-"} | events ${flatEvents.length}`
    : "No replay loaded";

  renderBoard(boardContainer, {
    state: visualState,
    selectedUnitId,
    onSelectUnit: (unitId) => {
      selectedUnitId = unitId;
      render();
    },
  });
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
  renderReport(reportContainer, report);
};

const setStatus = (message: string): void => {
  statusLine.textContent = message;
};

function element<T extends HTMLElement>(id: string): T {
  const found = document.getElementById(id);
  if (!found) {
    throw new Error(`Missing element #${id}`);
  }
  return found as T;
}

render();
