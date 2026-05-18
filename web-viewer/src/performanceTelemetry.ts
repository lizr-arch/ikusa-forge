export interface PerformanceSnapshot {
  fps: number;
  avgFrameMs: number;
  p95FrameMs: number;
  lastFrameMs: number;
  lastRenderMs: number;
  lastBoardRenderMs: number;
  lastTimelineRenderMs: number;
  lastApiStepMs: number;
  lastPixiRenderMs: number;
  displayedTimelineRows: number;
  totalEvents: number;
}

interface PerformanceSample {
  frameTimes: number[];
  maxSamples: number;
}

interface MeasureState {
  startedAt: number | null;
}

type PerformanceKey = keyof Omit<PerformanceSnapshot, "fps" | "avgFrameMs" | "p95FrameMs">;

export interface PerformanceTelemetry {
  beginMeasure: (name: PerformanceKey) => void;
  endMeasure: (name: PerformanceKey) => void;
  recordFrame: (nowMs?: number) => void;
  recordBoardRender: (ms: number) => void;
  recordTimelineRender: (ms: number) => void;
  recordApiStep: (ms: number) => void;
  recordPixiRender: (ms: number) => void;
  setRenderedTimelineRows: (count: number) => void;
  setTotalEvents: (count: number) => void;
  getSnapshot: () => PerformanceSnapshot;
  reset: () => void;
}

const DEFAULT_MAX_SAMPLES = 120;

export const createPerformanceTelemetry = (maxSamples = DEFAULT_MAX_SAMPLES): PerformanceTelemetry => {
  const frame: PerformanceSample = {
    frameTimes: [],
    maxSamples,
  };

  const measurements: Record<PerformanceKey, MeasureState> = {
    lastFrameMs: { startedAt: null },
    lastRenderMs: { startedAt: null },
    lastBoardRenderMs: { startedAt: null },
    lastTimelineRenderMs: { startedAt: null },
    lastApiStepMs: { startedAt: null },
    lastPixiRenderMs: { startedAt: null },
    displayedTimelineRows: { startedAt: null },
    totalEvents: { startedAt: null },
  };

  const lastValues: Record<PerformanceKey, number> = {
    lastFrameMs: 0,
    lastRenderMs: 0,
    lastBoardRenderMs: 0,
    lastTimelineRenderMs: 0,
    lastApiStepMs: 0,
    lastPixiRenderMs: 0,
    displayedTimelineRows: 0,
    totalEvents: 0,
  };

  let lastFrameTs: number | null = null;

  const now = (): number => {
    return typeof performance !== "undefined" ? performance.now() : Date.now();
  };

  const clamp = (value: number): number => {
    if (!Number.isFinite(value)) {
      return 0;
    }
    return Math.max(0, Math.round(value * 100) / 100);
  };

  const percentile95 = (values: number[]): number => {
    if (values.length === 0) {
      return 0;
    }
    const sorted = [...values].sort((a, b) => a - b);
    const index = Math.min(sorted.length - 1, Math.floor(sorted.length * 0.95));
    return sorted[index] ?? 0;
  };

  const beginMeasure = (name: PerformanceKey): void => {
    measurements[name].startedAt = now();
  };

  const endMeasure = (name: PerformanceKey): void => {
    const startedAt = measurements[name].startedAt;
    if (startedAt === null) {
      return;
    }
    const value = now() - startedAt;
    measurements[name].startedAt = null;
    lastValues[name] = value;
  };

  const recordRender = (name: "lastRenderMs" | "lastBoardRenderMs" | "lastTimelineRenderMs", ms: number): void => {
    lastValues[name] = Math.max(0, ms);
  };

  const recordFrame = (nowMs = now()): void => {
    if (lastFrameTs !== null) {
      const delta = Math.max(0, nowMs - lastFrameTs);
      frame.frameTimes.push(delta);
      if (frame.frameTimes.length > frame.maxSamples) {
        frame.frameTimes.shift();
      }
      lastValues.lastFrameMs = delta;
    }
    lastFrameTs = nowMs;
  };

  const updateTotal = (name: "displayedTimelineRows" | "totalEvents", count: number): void => {
    lastValues[name] = Math.max(0, Number.isFinite(count) ? Math.floor(count) : 0);
  };

  const getSnapshot = (): PerformanceSnapshot => {
    const avgFrame = frame.frameTimes.length > 0
      ? frame.frameTimes.reduce((total, item) => total + item, 0) / frame.frameTimes.length
      : 0;
    const p95 = percentile95(frame.frameTimes);
    const fps = avgFrame > 0 ? 1000 / avgFrame : 0;

    return {
      fps: Number.isFinite(fps) ? Math.max(0, Math.round(fps * 10) / 10) : 0,
      avgFrameMs: clamp(avgFrame),
      p95FrameMs: clamp(p95),
      lastFrameMs: clamp(lastValues.lastFrameMs),
      lastRenderMs: clamp(lastValues.lastRenderMs),
      lastBoardRenderMs: clamp(lastValues.lastBoardRenderMs),
      lastTimelineRenderMs: clamp(lastValues.lastTimelineRenderMs),
      lastApiStepMs: clamp(lastValues.lastApiStepMs),
      lastPixiRenderMs: clamp(lastValues.lastPixiRenderMs),
      displayedTimelineRows: Number(lastValues.displayedTimelineRows),
      totalEvents: Number(lastValues.totalEvents),
    };
  };

  const reset = (): void => {
    frame.frameTimes.length = 0;
    lastFrameTs = null;
    for (const key of Object.keys(lastValues) as PerformanceKey[]) {
      lastValues[key] = 0;
    }
    for (const key of Object.keys(measurements) as PerformanceKey[]) {
      measurements[key].startedAt = null;
    }
  };

  return {
    beginMeasure,
    endMeasure,
    recordFrame,
    recordBoardRender: (ms: number) => recordRender("lastBoardRenderMs", ms),
    recordTimelineRender: (ms: number) => recordRender("lastTimelineRenderMs", ms),
    recordApiStep: (ms: number) => {
      lastValues.lastApiStepMs = ms;
    },
    recordPixiRender: (ms: number) => {
      lastValues.lastPixiRenderMs = ms;
      recordRender("lastRenderMs", ms);
    },
    setRenderedTimelineRows: (count: number) => updateTotal("displayedTimelineRows", count),
    setTotalEvents: (count: number) => updateTotal("totalEvents", count),
    getSnapshot,
    reset,
  };
};
