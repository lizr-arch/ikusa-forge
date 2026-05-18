import type { ReplayEvent, LiveBattleSnapshot } from "./replayTypes";
import {
  buildVisualStateFromSnapshot,
  createEmptyVisualState,
  type VisualState,
} from "./replayState";

export interface VisualStateBuffer {
  clear: () => void;
  pushSnapshot: (snapshot: LiveBattleSnapshot, receivedAt?: number) => void;
  pushEvents: (events: ReplayEvent[]) => void;
  getInterpolatedState: (now: number, interpolationMs?: number) => VisualState;
  getLatestEvents: () => ReplayEvent[];
}

interface BufferedSnapshot {
  state: VisualState;
  receivedAt: number;
}

const DEFAULT_LATEST_EVENTS = 128;
const DEFAULT_INTERPOLATION_MS = 120;

export const createVisualStateBuffer = (): VisualStateBuffer => {
  let previous: BufferedSnapshot | null = null;
  let current: BufferedSnapshot | null = null;
  let latestEvents: ReplayEvent[] = [];

  const now = (): number => (typeof performance !== "undefined" ? performance.now() : Date.now());

  const clear = (): void => {
    previous = null;
    current = null;
    latestEvents = [];
  };

  const pushSnapshot = (snapshot: LiveBattleSnapshot, receivedAt = now()): void => {
    if (snapshot === null || snapshot === undefined) {
      return;
    }
    previous = current;
    current = {
      state: cloneVisualState(buildVisualStateFromSnapshot(snapshot)),
      receivedAt,
    };
  };

  const pushEvents = (events: ReplayEvent[]): void => {
    if (events.length === 0) {
      return;
    }
    latestEvents = [...latestEvents, ...events].slice(-DEFAULT_LATEST_EVENTS);
  };

  const getInterpolatedState = (currentNow: number, interpolationMs = DEFAULT_INTERPOLATION_MS): VisualState => {
    if (!current) {
      return createEmptyVisualState();
    }
    if (!previous) {
      return cloneVisualState(current.state);
    }
    if (interpolationMs <= 0) {
      return cloneVisualState(current.state);
    }
    const elapsed = currentNow - current.receivedAt;
    const alpha = clamp(elapsed / interpolationMs);
    if (alpha >= 1) {
      return cloneVisualState(current.state);
    }
    return interpolateVisualStates(previous.state, current.state, alpha);
  };

  const getLatestEvents = (): ReplayEvent[] => latestEvents;

  return {
    clear,
    pushSnapshot,
    pushEvents,
    getInterpolatedState,
    getLatestEvents,
  };
};

const interpolateVisualStates = (left: VisualState, right: VisualState, ratio: number): VisualState => {
  const result = cloneVisualState(right);
  for (const [unitId, rightUnit] of right.units.entries()) {
    const leftUnit = left.units.get(unitId);
    if (!leftUnit) {
      continue;
    }
    const interpolatedX = lerp(leftUnit.positionX, rightUnit.positionX, ratio);
    const interpolatedY = lerp(leftUnit.positionY, rightUnit.positionY, ratio);
    const target = result.units.get(unitId);
    if (target) {
      target.positionX = interpolatedX;
      target.positionY = interpolatedY;
      target.x = interpolatedX;
      target.y = interpolatedY;
      target.velocityX = rightUnit.velocityX;
      target.velocityY = rightUnit.velocityY;
    }
  }

  return result;
};

const cloneVisualState = (state: VisualState): VisualState => {
  const clonedUnits = new Map<string, any>();
  for (const [unitId, unit] of state.units.entries()) {
    clonedUnits.set(unitId, {
      ...unit,
      statuses: unit.statuses.map((status) => ({ ...status })),
      skillCooldowns: new Map(unit.skillCooldowns),
      statBonuses: new Map(unit.statBonuses),
    });
  }

  return {
    currentTick: state.currentTick,
    units: clonedUnits,
    lastAttack: state.lastAttack ? { ...state.lastAttack } : null,
    lastDamage: state.lastDamage ? { ...state.lastDamage } : null,
    lastModifier: state.lastModifier ? { ...state.lastModifier } : null,
    lastStatus: state.lastStatus ? { ...state.lastStatus } : null,
    lastCooldown: state.lastCooldown ? { ...state.lastCooldown } : null,
    lastActionSchedule: state.lastActionSchedule ? { ...state.lastActionSchedule } : null,
    lastSkill: state.lastSkill ? { ...state.lastSkill } : null,
    lastMove: state.lastMove ? { ...state.lastMove } : null,
    battleResult: state.battleResult ? { ...state.battleResult } : null,
    victory: state.victory ? { ...state.victory } : null,
    appliedEventId: state.appliedEventId,
    appliedEventIndex: state.appliedEventIndex,
  };
};

const lerp = (from: number, to: number, ratio: number): number => from + (to - from) * clamp(ratio);

const clamp = (value: number): number => {
  if (!Number.isFinite(value)) {
    return 0;
  }
  return Math.max(0, Math.min(1, value));
};
