import type { BattleResult, ReplayDocument, ReplayEvent, TargetScorePayload, UnitSnapshot } from "./replayTypes";

export interface VisualUnit {
  instanceId: string;
  side: string;
  unitDefId: string;
  x: number;
  y: number;
  role: string;
  name: string;
  tags: string[];
  maxHp: number;
  hp: number;
  alive: boolean;
  atk: number;
  defense: number;
  range: number;
  guardValue: number;
  skillIds: string[];
  statBonuses: Map<string, number>;
}

export interface AttackAnnotation {
  tick: number;
  source: string;
  target: string;
  targetReason: string | null;
  targetScore: TargetScorePayload | null;
}

export interface DamageAnnotation {
  tick: number;
  source: string | null;
  target: string;
  amount: number;
  reason: string;
}

export interface StatModifierAnnotation {
  tick: number;
  source: string;
  sourceType: string;
  target: string;
  stat: string;
  amount: number;
  reason: string;
}

export interface SkillAnnotation {
  tick: number;
  source: string;
  skill: string;
  trigger: string;
  targets: string[];
  targetReason: string | null;
  targetScore: TargetScorePayload | null;
}

export interface VisualState {
  currentTick: number;
  units: Map<string, VisualUnit>;
  lastAttack: AttackAnnotation | null;
  lastDamage: DamageAnnotation | null;
  lastModifier: StatModifierAnnotation | null;
  lastSkill: SkillAnnotation | null;
  battleResult: BattleResult | null;
  appliedEventId: string | null;
  appliedEventIndex: number | null;
}

export interface FlatReplayEvent {
  globalIndex: number;
  tick: number;
  event: ReplayEvent;
}

export const createEmptyVisualState = (): VisualState => ({
  currentTick: 0,
  units: new Map<string, VisualUnit>(),
  lastAttack: null,
  lastDamage: null,
  lastModifier: null,
  lastSkill: null,
  battleResult: null,
  appliedEventId: null,
  appliedEventIndex: null,
});

export const flattenReplayEvents = (replay: ReplayDocument): FlatReplayEvent[] => {
  const flatEvents: FlatReplayEvent[] = [];
  for (const tickGroup of replay.ticks) {
    for (const event of tickGroup.events) {
      flatEvents.push({
        globalIndex: flatEvents.length,
        tick: event.tick,
        event,
      });
    }
  }
  flatEvents.sort((left, right) => {
    if (left.tick !== right.tick) {
      return left.tick - right.tick;
    }
    return left.globalIndex - right.globalIndex;
  });
  return flatEvents.map((entry, index) => ({ ...entry, globalIndex: index }));
};

export const getReplayMaxTick = (replay: ReplayDocument): number => {
  if (typeof replay.metadata.max_ticks === "number") {
    return replay.metadata.max_ticks;
  }
  return replay.ticks.reduce((maxTick, tickGroup) => Math.max(maxTick, tickGroup.tick), 0);
};

export const seekToTick = (replay: ReplayDocument, targetTick: number): VisualState => {
  const maxTick = getReplayMaxTick(replay);
  const clampedTick = clampTick(targetTick, maxTick);
  const state = createEmptyVisualState();
  const events = flattenReplayEvents(replay);

  for (const entry of events) {
    if (entry.tick > clampedTick) {
      break;
    }
    applyEvent(state, entry.event, entry.globalIndex);
  }

  state.currentTick = clampedTick;
  return state;
};

export const seekToEvent = (replay: ReplayDocument, globalIndex: number): VisualState => {
  const events = flattenReplayEvents(replay);
  const target = events[globalIndex];
  if (!target) {
    return seekToTick(replay, 0);
  }

  const state = createEmptyVisualState();
  for (const entry of events) {
    if (entry.globalIndex > globalIndex) {
      break;
    }
    applyEvent(state, entry.event, entry.globalIndex);
  }
  state.currentTick = target.tick;
  return state;
};

export const applyEvent = (
  state: VisualState,
  event: ReplayEvent,
  globalIndex: number | null = null,
): void => {
  state.currentTick = event.tick;
  state.appliedEventId = event.event_id;
  state.appliedEventIndex = globalIndex;

  switch (event.type) {
    case "unit_spawn":
      applyUnitSpawn(state, event);
      return;
    case "attack":
      state.lastAttack = {
        tick: event.tick,
        source: readString(event.payload.attacker),
        target: readString(event.payload.target),
        targetReason: readNullableString(event.payload.target_reason),
        targetScore: readTargetScore(event.payload.target_score),
      };
      return;
    case "skill_trigger":
      state.lastSkill = {
        tick: event.tick,
        source: readString(event.payload.source),
        skill: readString(event.payload.skill),
        trigger: readString(event.payload.trigger),
        targets: readStringArray(event.payload.targets),
        targetReason: readNullableString(event.payload.target_reason),
        targetScore: readTargetScore(event.payload.target_score),
      };
      return;
    case "damage":
      applyDamage(state, event);
      return;
    case "stat_modifier":
      applyStatModifier(state, event);
      return;
    case "death":
      applyDeath(state, event);
      return;
    case "battle_end":
      state.battleResult = {
        winner: readNullableString(event.payload.winner),
        reason: readNullableString(event.payload.reason),
        end_tick: readNullableNumber(event.payload.end_tick),
      };
      return;
    case "battle_start":
      return;
    default:
      return;
  }
};

export const findLastEventIndexAtOrBeforeTick = (
  events: FlatReplayEvent[],
  tick: number,
): number | null => {
  let found: number | null = null;
  for (const entry of events) {
    if (entry.tick > tick) {
      break;
    }
    found = entry.globalIndex;
  }
  return found;
};

const applyUnitSpawn = (state: VisualState, event: ReplayEvent): void => {
  const unit = asRecord(event.payload.unit);
  const snapshot = unit as Partial<UnitSnapshot>;
  const instanceId = readString(snapshot.instance_id);
  if (!instanceId) {
    return;
  }

  const hp = readNumber(snapshot.hp, readNumber(snapshot.base_hp, 0));
  const maxHp = readNumber(snapshot.base_hp, hp);
  state.units.set(instanceId, {
    instanceId,
    side: readString(snapshot.side),
    unitDefId: readString(snapshot.unit_def_id),
    x: readNumber(snapshot.x, 0),
    y: readNumber(snapshot.y, 0),
    role: readString(snapshot.role, "unknown"),
    name: readString(snapshot.name, instanceId),
    tags: readStringArray(snapshot.tags),
    maxHp,
    hp,
    alive: readBoolean(snapshot.alive, hp > 0),
    atk: readNumber(snapshot.atk, readNumber(snapshot.base_atk, 0)),
    defense: readNumber(snapshot.defense, readNumber(snapshot.base_defense, 0)),
    range: readNumber(snapshot.base_range, 0),
    guardValue: readNumber(snapshot.guard_value, 0),
    skillIds: readStringArray(snapshot.skill_ids),
    statBonuses: new Map<string, number>(),
  });
};

const applyDamage = (state: VisualState, event: ReplayEvent): void => {
  const source = readNullableString(event.payload.source);
  const target = readString(event.payload.target);
  const amount = readNumber(event.payload.amount, 0);
  const targetHpAfter = readNumber(event.payload.target_hp_after, 0);
  const unit = state.units.get(target);
  if (unit) {
    unit.hp = targetHpAfter;
    unit.alive = targetHpAfter > 0 && unit.alive;
  }
  state.lastDamage = {
    tick: event.tick,
    source,
    target,
    amount,
    reason: readString(event.payload.reason),
  };
};

const applyStatModifier = (state: VisualState, event: ReplayEvent): void => {
  const source = readString(event.payload.source);
  const target = readString(event.payload.target);
  const sourceType = readString(event.payload.source_type);
  const stat = readString(event.payload.stat);
  const amount = readNumber(event.payload.amount, 0);
  const unit = state.units.get(target);
  if (unit) {
    if (stat === "atk") {
      unit.atk += amount;
    } else if (stat === "defense") {
      unit.defense += amount;
    } else if (stat === "range") {
      unit.range += amount;
    } else if (stat === "hp") {
      unit.maxHp += amount;
      unit.hp += amount;
    }
    const next = new Map(unit.statBonuses);
    next.set(stat, (next.get(stat) ?? 0) + amount);
    unit.statBonuses = next;
  }
  state.lastModifier = {
    tick: event.tick,
    source,
    sourceType,
    target,
    stat,
    amount,
    reason: readString(event.payload.reason),
  };
};

const applyDeath = (state: VisualState, event: ReplayEvent): void => {
  const unitId = readString(event.payload.unit);
  const unit = state.units.get(unitId);
  if (!unit) {
    return;
  }
  unit.alive = false;
  unit.hp = 0;
};

const clampTick = (tick: number, maxTick: number): number => {
  if (!Number.isFinite(tick)) {
    return 0;
  }
  return Math.max(0, Math.min(maxTick, Math.floor(tick)));
};

const asRecord = (value: unknown): Record<string, unknown> => {
  if (typeof value === "object" && value !== null && !Array.isArray(value)) {
    return value as Record<string, unknown>;
  }
  return {};
};

const readString = (value: unknown, fallback = ""): string => {
  return typeof value === "string" ? value : fallback;
};

const readNullableString = (value: unknown): string | null => {
  if (value === null || value === undefined) {
    return null;
  }
  return typeof value === "string" ? value : String(value);
};

const readNumber = (value: unknown, fallback: number): number => {
  return typeof value === "number" && Number.isFinite(value) ? value : fallback;
};

const readTargetScore = (value: unknown): TargetScorePayload | null => {
  if (typeof value !== "object" || value === null) {
    return null;
  }
  const payload = value as Record<string, unknown>;
  const readValue = (key: string): number => {
    const item = payload[key];
    return typeof item === "number" && Number.isFinite(item) ? item : 0;
  };

  return {
    final: readValue("final"),
    exposure: readValue("exposure"),
    column: readValue("column"),
    low_hp: readValue("low_hp"),
    threat: readValue("threat"),
    role: readValue("role"),
    tie_break: readValue("tie_break"),
  };
};

const readNullableNumber = (value: unknown): number | null => {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
};

const readBoolean = (value: unknown, fallback: boolean): boolean => {
  return typeof value === "boolean" ? value : fallback;
};

const readStringArray = (value: unknown): string[] => {
  if (!Array.isArray(value)) {
    return [];
  }
  return value.filter((item): item is string => typeof item === "string");
};
