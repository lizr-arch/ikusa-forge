export interface PerformanceTelemetry {
  liveMode: boolean;
  fps: number | null;
  avgFrameMs: number | null;
  p95FrameMs: number | null;
  lastFrameMs: number | null;
  lastRenderMs: number | null;
  lastBoardRenderMs: number | null;
  lastTimelineRenderMs: number | null;
  lastStepApiMs: number | null;
  displayedTimelineRows: number;
  totalEvents: number;
}

type MeasureName = "step_api" | "render" | "board" | "timeline";

const MAX_FRAME_SAMPLES = 120;

let telemetry = createDefaultTelemetry();
const measureStarts = new Map<string, number>();
let frameSamples: number[] = [];
let lastFrameRecordedAt: number | null = null;

export const createPerformanceTelemetry = (): PerformanceTelemetry => {
  telemetry = createDefaultTelemetry();
  measureStarts.clear();
  frameSamples = [];
  lastFrameRecordedAt = null;
  return telemetry;
};

export const beginMeasure = (name: string): void => {
  measureStarts.set(name, performance.now());
};

export const endMeasure = (name: MeasureName): number | null => {
  const startedAt = measureStarts.get(name);
  if (startedAt === undefined) {
    return null;
  }

  const duration = performance.now() - startedAt;
  measureStarts.delete(name);

  if (name === "step_api") {
    telemetry.lastStepApiMs = duration;
  } else if (name === "render") {
    telemetry.lastRenderMs = duration;
  } else if (name === "board") {
    telemetry.lastBoardRenderMs = duration;
  } else if (name === "timeline") {
    telemetry.lastTimelineRenderMs = duration;
  }

  return duration;
};

export const recordFrame = (): void => {
  const now = performance.now();
  if (lastFrameRecordedAt !== null) {
    const frameMs = now - lastFrameRecordedAt;
    telemetry.lastFrameMs = frameMs;
    frameSamples.push(frameMs);
    if (frameSamples.length > MAX_FRAME_SAMPLES) {
      frameSamples.shift();
    }
    telemetry.avgFrameMs = average(frameSamples);
    telemetry.p95FrameMs = percentile(frameSamples, 0.95);
    telemetry.fps = telemetry.avgFrameMs && telemetry.avgFrameMs > 0 ? 1000 / telemetry.avgFrameMs : null;
  }
  lastFrameRecordedAt = now;
};

export const getPerformanceSnapshot = (): PerformanceTelemetry => {
  return { ...telemetry };
};

export const formatPerformanceDuration = (value: number | null): string => {
  if (value === null || !Number.isFinite(value)) {
    return "-";
  }
  return `${value.toFixed(1)} ms`;
};

export const formatPerformanceRate = (value: number | null): string => {
  if (value === null || !Number.isFinite(value)) {
    return "-";
  }
  return `${value.toFixed(1)} fps`;
};

export const formatPerformanceCount = (value: number): string => {
  if (!Number.isFinite(value)) {
    return "-";
  }
  return String(Math.max(0, Math.round(value)));
};

export const formatPerformanceMode = (liveMode: boolean): string => {
  return liveMode ? "live（实时）" : "replay（回放）";
};

function createDefaultTelemetry(): PerformanceTelemetry {
  return {
    liveMode: false,
    fps: null,
    avgFrameMs: null,
    p95FrameMs: null,
    lastFrameMs: null,
    lastRenderMs: null,
    lastBoardRenderMs: null,
    lastTimelineRenderMs: null,
    lastStepApiMs: null,
    displayedTimelineRows: 0,
    totalEvents: 0,
  };
}

const average = (values: number[]): number | null => {
  if (values.length === 0) {
    return null;
  }
  const total = values.reduce((sum, value) => sum + value, 0);
  return total / values.length;
};

const percentile = (values: number[], percentileValue: number): number | null => {
  if (values.length === 0) {
    return null;
  }
  const sorted = [...values].sort((left, right) => left - right);
  const index = Math.min(sorted.length - 1, Math.max(0, Math.ceil(sorted.length * percentileValue) - 1));
  return sorted[index];
};
