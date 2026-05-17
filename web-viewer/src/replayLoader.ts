import type {
  BattleReport,
  DemoScenario,
  ReplayDocument,
  ReplayEvent,
  ReplayTick,
  ScenarioManifest,
} from "./replayTypes";

export type JsonFileResult<T> =
  | { ok: true; fileName: string; data: T }
  | { ok: false; fileName?: string; error: string };

export const readReplayDocumentFile = async (
  file: File | null,
): Promise<JsonFileResult<ReplayDocument>> => {
  return readJsonFile(file, "replay.json", isReplayDocument);
};

export const readBattleReportFile = async (
  file: File | null,
): Promise<JsonFileResult<BattleReport>> => {
  return readJsonFile(file, "battle_report.json", isBattleReport);
};

export type JsonUrlResult<T> =
  | { ok: true; url: string; data: T }
  | { ok: false; url: string; error: string };

export const fetchScenarioManifest = async (
  url = "/samples/manifest.json",
): Promise<JsonUrlResult<ScenarioManifest>> => {
  return fetchJsonUrl(url, "scenario manifest", isScenarioManifest);
};

export const fetchReplayDocument = async (
  url: string,
): Promise<JsonUrlResult<ReplayDocument>> => {
  return fetchJsonUrl(url, "replay.json", isReplayDocument);
};

export const fetchBattleReport = async (
  url: string,
): Promise<JsonUrlResult<BattleReport>> => {
  return fetchJsonUrl(url, "battle_report.json", isBattleReport);
};

const readJsonFile = async <T>(
  file: File | null,
  label: string,
  validate: (value: unknown) => value is T,
): Promise<JsonFileResult<T>> => {
  if (!file) {
    return { ok: false, error: `${label} is not selected.` };
  }

  try {
    const text = await file.text();
    const parsed: unknown = JSON.parse(text);
    if (!validate(parsed)) {
      return {
        ok: false,
        fileName: file.name,
        error: `${file.name} does not match the expected ${label} shape.`,
      };
    }
    return { ok: true, fileName: file.name, data: parsed };
  } catch (error: unknown) {
    return {
      ok: false,
      fileName: file.name,
      error: `${file.name} could not be parsed: ${errorMessage(error)}`,
    };
  }
};

const fetchJsonUrl = async <T>(
  url: string,
  label: string,
  validate: (value: unknown) => value is T,
): Promise<JsonUrlResult<T>> => {
  try {
    const response = await fetch(url, { cache: "no-cache" });
    if (!response.ok) {
      return { ok: false, url, error: `${label} could not be loaded from ${url}: ${response.status}` };
    }
    const parsed: unknown = await response.json();
    if (!validate(parsed)) {
      return { ok: false, url, error: `${url} does not match the expected ${label} shape.` };
    }
    return { ok: true, url, data: parsed };
  } catch (error: unknown) {
    return { ok: false, url, error: `${label} could not be loaded from ${url}: ${errorMessage(error)}` };
  }
};

const isReplayDocument = (value: unknown): value is ReplayDocument => {
  if (!isRecord(value)) {
    return false;
  }
  if (typeof value.schema_version !== "string") {
    return false;
  }
  if (!isRecord(value.metadata)) {
    return false;
  }
  if (!Array.isArray(value.ticks)) {
    return false;
  }
  return value.ticks.every(isReplayTick);
};

const isReplayTick = (value: unknown): value is ReplayTick => {
  if (!isRecord(value) || typeof value.tick !== "number" || !Array.isArray(value.events)) {
    return false;
  }
  return value.events.every(isReplayEvent);
};

const isReplayEvent = (value: unknown): value is ReplayEvent => {
  return (
    isRecord(value) &&
    typeof value.tick === "number" &&
    typeof value.event_id === "string" &&
    typeof value.type === "string" &&
    isRecord(value.payload)
  );
};

const isBattleReport = (value: unknown): value is BattleReport => {
  if (!isRecord(value)) {
    return false;
  }
  if (value.schema_version !== undefined && typeof value.schema_version !== "string") {
    return false;
  }
  if (value.summary !== undefined && !isRecord(value.summary)) {
    return false;
  }
  if (value.units !== undefined && !isRecord(value.units)) {
    return false;
  }
  if (value.top_units !== undefined && !isRecord(value.top_units)) {
    return false;
  }
  if (value.key_moments !== undefined && !Array.isArray(value.key_moments)) {
    return false;
  }
  return true;
};

const isScenarioManifest = (value: unknown): value is ScenarioManifest => {
  if (!isRecord(value) || value.schema_version !== "scenario_manifest.v0.1" || !Array.isArray(value.scenarios)) {
    return false;
  }
  return value.scenarios.every(isDemoScenario);
};

const isDemoScenario = (value: unknown): value is DemoScenario => {
  if (!isRecord(value)) {
    return false;
  }
  return (
    typeof value.id === "string" &&
    typeof value.name === "string" &&
    typeof value.description === "string" &&
    typeof value.replay_url === "string" &&
    typeof value.report_url === "string"
  );
};

const isRecord = (value: unknown): value is Record<string, unknown> => {
  return typeof value === "object" && value !== null && !Array.isArray(value);
};

const errorMessage = (error: unknown): string => {
  if (error instanceof Error) {
    return error.message;
  }
  return String(error);
};
