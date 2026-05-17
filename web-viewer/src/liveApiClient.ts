import type {
  LiveApiResult,
  LiveHealthResponse,
  LiveResetResponse,
  LiveStartResponse,
  LiveSnapshotResponse,
  LiveStepResponse,
  LiveEventsResponse,
} from "./replayTypes";

export const DEFAULT_LIVE_API_URL = "http://127.0.0.1:8765";

export const healthLiveApi = async (baseUrl: string): Promise<LiveApiResult<LiveHealthResponse>> => {
  return requestJson(`${normalizeBaseUrl(baseUrl)}/api/health`, { method: "GET" });
};

export const startLiveBattle = async (
  baseUrl: string,
  battleId: string,
  seed: number,
): Promise<LiveApiResult<LiveStartResponse>> => {
  return requestJson(`${normalizeBaseUrl(baseUrl)}/api/battle/start`, {
    method: "POST",
    body: JSON.stringify({ battle_id: battleId, seed }),
  });
};

export const stepLiveBattle = async (
  baseUrl: string,
  sessionId: string,
  ticks: number,
): Promise<LiveApiResult<LiveStepResponse>> => {
  return requestJson(`${normalizeBaseUrl(baseUrl)}/api/battle/step`, {
    method: "POST",
    body: JSON.stringify({ session_id: sessionId, ticks }),
  });
};

export const getLiveSnapshot = async (
  baseUrl: string,
  sessionId: string,
): Promise<LiveApiResult<LiveSnapshotResponse>> => {
  const params = new URLSearchParams({ session_id: sessionId });
  return requestJson(`${normalizeBaseUrl(baseUrl)}/api/battle/snapshot?${params.toString()}`, {
    method: "GET",
  });
};

export const getLiveEvents = async (
  baseUrl: string,
  sessionId: string,
  since: number,
): Promise<LiveApiResult<LiveEventsResponse>> => {
  const params = new URLSearchParams({ session_id: sessionId, since: String(since) });
  return requestJson(`${normalizeBaseUrl(baseUrl)}/api/battle/events?${params.toString()}`, {
    method: "GET",
  });
};

export const resetLiveBattle = async (
  baseUrl: string,
  sessionId: string,
): Promise<LiveApiResult<LiveResetResponse>> => {
  return requestJson(`${normalizeBaseUrl(baseUrl)}/api/battle/reset`, {
    method: "POST",
    body: JSON.stringify({ session_id: sessionId }),
  });
};

const requestJson = async <T>(
  url: string,
  options: { method: "GET" | "POST"; body?: string },
): Promise<LiveApiResult<T>> => {
  const init: RequestInit = {
    method: options.method,
    headers: { "content-type": "application/json" },
    body: options.body,
  };
  if (options.method === "GET") {
    delete init.body;
  }

  try {
    const response = await fetch(url, init);
    const text = await response.text();
    const payload = parseJson<T>(text);
    if (payload && typeof payload === "object" && "ok" in payload) {
      if ((payload as { ok: boolean }).ok === false) {
        return payload as LiveApiResult<T>;
      }
      if ((payload as { ok: boolean }).ok === true) {
        return payload as LiveApiResult<T>;
      }
    }
    if (!response.ok) {
      return {
        ok: false,
        error: `Live API request failed with status ${response.status}`,
      };
    }
    return {
      ok: false,
      error: "Invalid JSON response from Live API",
    };
  } catch (error: unknown) {
    return {
      ok: false,
      error: `Live API unavailable（实时 API 不可用）：${errorMessage(error)}`,
    };
  }
};

const parseJson = <T>(text: string): any => {
  try {
    return JSON.parse(text) as T;
  } catch {
    return {
      ok: false,
      error: "Invalid JSON response",
    };
  }
};

const readError = (payload: Record<string, unknown> | null): string => {
  if (!payload || typeof payload !== "object") {
    return "";
  }
  const error = payload.error;
  return typeof error === "string" ? error : "";
};

const normalizeBaseUrl = (value: string): string => {
  return value.trim().replace(/\/+$/, "");
};

const errorMessage = (error: unknown): string => {
  if (error instanceof Error) {
    return error.message;
  }
  return String(error);
};
