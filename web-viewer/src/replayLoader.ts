import type { BattleReport, ReplayDocument, ReplayEvent, ReplayTick } from "./replayTypes";

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

const isRecord = (value: unknown): value is Record<string, unknown> => {
  return typeof value === "object" && value !== null && !Array.isArray(value);
};

const errorMessage = (error: unknown): string => {
  if (error instanceof Error) {
    return error.message;
  }
  return String(error);
};
