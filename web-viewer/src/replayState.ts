import type { BattleResult, ReplayDocument, ReplayEvent, TargetScorePayload, UnitSnapshot } from "./replayTypes";
import type { LiveBattleSnapshot, LiveUnitSnapshot } from "./replayTypes";

export interface VisualUnit {
  instanceId: string;
  side: string;
  unitDefId: string;
  x: number;
  y: number;
  positionX: number;
  positionY: number;
  velocityX: number;
  velocityY: number;
  facingAngle: number;
  radius: number;
  moveSpeed: number;
  attackRange: number;
  engagementRange: number;
  engagedTarget: string | null;
  movementIntent: string;
  combatState: string;
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
  statuses: VisualStatus[];
  skillCooldowns: Map<string, number>;
  nextActionTick: number | null;
  actionIntervalTicks: number | null;
  lastStatus: StatusAnnotation | null;
  lastCooldown: CooldownAnnotation | null;
  lastActionSchedule: ActionScheduleAnnotation | null;
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

export interface VisualStatus {
  id: string;
  source: string;
  sourceType: string;
  target: string;
  stat: string;
  amount: number;
  startTick: number;
  expireTick: number | null;
  reason: string;
  targetReason: string | null;
  active: boolean;
}

export interface StatusAnnotation extends VisualStatus {
  tick: number;
  eventType: "status_apply" | "status_expire";
}

export interface CooldownAnnotation {
  tick: number;
  source: string;
  skill: string;
  startTick: number;
  readyTick: number;
  cooldownTicks: number;
}

export interface ActionScheduleAnnotation {
  tick: number;
  unit: string;
  currentTick: number;
  nextActionTick: number;
  actionIntervalTicks: number;
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

export interface MoveAnnotation {
  tick: number;
  unit: string;
  target: string | null;
  fromX: number;
  fromY: number;
  toX: number;
  toY: number;
  reason: string;
}

export interface VisualState {
  currentTick: number;
  units: Map<string, VisualUnit>;
  lastAttack: AttackAnnotation | null;
  lastDamage: DamageAnnotation | null;
  lastModifier: StatModifierAnnotation | null;
  lastStatus: StatusAnnotation | null;
  lastCooldown: CooldownAnnotation | null;
  lastActionSchedule: ActionScheduleAnnotation | null;
  lastSkill: SkillAnnotation | null;
  lastMove: MoveAnnotation | null;
  battleResult: BattleResult | null;
  victory: BattleResult | null;
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
  lastStatus: null,
  lastCooldown: null,
  lastActionSchedule: null,
  lastSkill: null,
  lastMove: null,
  battleResult: null,
  victory: null,
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

export const buildVisualStateFromSnapshot = (snapshot: LiveBattleSnapshot): VisualState => {
  const state = createEmptyVisualState();
  state.currentTick = snapshot.tick;
  state.battleResult = snapshot.result
    ? {
      winner: readNullableString(snapshot.result.winner),
      reason: readNullableString(snapshot.result.reason),
      end_tick: readNullableNumber(snapshot.result.end_tick),
      winner_alive: readNullableNumber(snapshot.result.winner_alive),
      loser_alive: readNullableNumber(snapshot.result.loser_alive),
      winner_total_hp: readNullableNumber(snapshot.result.winner_total_hp),
      loser_total_hp: readNullableNumber(snapshot.result.loser_total_hp),
      summary: readNullableString(snapshot.result.summary),
    }
    : null;
  state.victory = state.battleResult;
  for (const snapshotUnit of snapshot.units) {
    const unit = buildLiveUnit(snapshotUnit);
    state.units.set(unit.instanceId, unit);
  }
  return state;
};

export const appendLiveEvents = (
  events: FlatReplayEvent[],
  additions: ReplayEvent[],
): FlatReplayEvent[] => {
  if (additions.length === 0) {
    return events;
  }
  const base = events.length;
  const appended = additions.map((event, index) => ({
    globalIndex: base + index,
    tick: event.tick,
    event,
  }));
  return [...events, ...appended];
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
    case "status_apply":
      applyStatusApply(state, event);
      return;
    case "status_expire":
      applyStatusExpire(state, event);
      return;
    case "skill_cooldown":
      applySkillCooldown(state, event);
      return;
    case "unit_move":
      applyUnitMove(state, event);
      return;
    case "target_acquired":
    case "enter_range":
    case "engage_start":
      applySpatialTargetEvent(state, event);
      return;
    case "action_scheduled":
      applyActionScheduled(state, event);
      return;
    case "death":
      applyDeath(state, event);
      return;
    case "battle_end":
      state.battleResult = {
        winner: readNullableString(event.payload.winner),
        reason: readNullableString(event.payload.reason),
        end_tick: readNullableNumber(event.payload.end_tick),
        winner_alive: readNullableNumber(event.payload.winner_alive),
        loser_alive: readNullableNumber(event.payload.loser_alive),
        winner_total_hp: readNullableNumber(event.payload.winner_total_hp),
        loser_total_hp: readNullableNumber(event.payload.loser_total_hp),
        summary: readNullableString(event.payload.summary),
      };
      state.victory = state.battleResult;
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
    positionX: readNumber(snapshot.position_x, spatialXFromGrid(readNumber(snapshot.x, 0))),
    positionY: readNumber(snapshot.position_y, spatialYFromGrid(readNumber(snapshot.y, 0), readString(snapshot.side))),
    velocityX: readNumber(snapshot.velocity_x, 0),
    velocityY: readNumber(snapshot.velocity_y, 0),
    facingAngle: readNumber(snapshot.facing_angle, 0),
    radius: readNumber(snapshot.radius, 8),
    moveSpeed: readNumber(snapshot.move_speed, 0),
    attackRange: readNumber(snapshot.attack_range, readNumber(snapshot.base_range, 0)),
    engagementRange: readNumber(snapshot.engagement_range, readNumber(snapshot.base_range, 0)),
    engagedTarget: readNullableString(snapshot.engaged_target),
    movementIntent: readString(snapshot.movement_intent, "hold"),
    combatState: readString(snapshot.combat_state, readString(snapshot.movement_intent, "idle")),
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
    statuses: readStatusSnapshots(snapshot.statuses),
    skillCooldowns: readNumberMap(snapshot.skill_cooldowns),
    nextActionTick: readNullableNumber(snapshot.next_action_tick),
    actionIntervalTicks: readNullableNumber(snapshot.action_interval_ticks),
    lastStatus: null,
    lastCooldown: null,
    lastActionSchedule: null,
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

const applyStatusApply = (state: VisualState, event: ReplayEvent): void => {
  const status = readStatus(event.payload, event.tick, "status_apply", true);
  if (!status) {
    return;
  }

  const unit = state.units.get(status.target);
  if (unit) {
    unit.statuses = [
      ...unit.statuses.filter((candidate) => candidate.id !== status.id),
      status,
    ];
    applyStatusStat(unit, status.stat, status.amount);
    unit.lastStatus = status;
  }
  state.lastStatus = status;
};

const applyStatusExpire = (state: VisualState, event: ReplayEvent): void => {
  const target = readString(event.payload.target);
  const statusId = readString(event.payload.id, readString(event.payload.status_id));
  const unit = state.units.get(target);
  const expiredStatus = readStatus(event.payload, event.tick, "status_expire", false);

  if (unit) {
    unit.statuses = unit.statuses.map((status) => {
      if (statusId && status.id !== statusId) {
        return status;
      }
      if (!statusId && expiredStatus && status.stat !== expiredStatus.stat) {
        return status;
      }
      return {
        ...status,
        active: false,
        expireTick: expiredStatus?.expireTick ?? event.tick,
      };
    });
    if (expiredStatus) {
      unit.lastStatus = expiredStatus;
    }
  }
  if (expiredStatus) {
    state.lastStatus = expiredStatus;
  }
};

const applySkillCooldown = (state: VisualState, event: ReplayEvent): void => {
  const source = readString(event.payload.source);
  const skill = readString(event.payload.skill);
  const annotation: CooldownAnnotation = {
    tick: event.tick,
    source,
    skill,
    startTick: readNumber(event.payload.start_tick, event.tick),
    readyTick: readNumber(event.payload.ready_tick, event.tick),
    cooldownTicks: readNumber(event.payload.cooldown_ticks, 0),
  };
  const unit = state.units.get(source);
  if (unit) {
    const cooldowns = new Map(unit.skillCooldowns);
    cooldowns.set(skill, annotation.readyTick);
    unit.skillCooldowns = cooldowns;
    unit.lastCooldown = annotation;
  }
  state.lastCooldown = annotation;
};

const buildLiveUnit = (snapshotUnit: LiveUnitSnapshot): VisualUnit => {
  const snapshot = snapshotUnit as Partial<LiveUnitSnapshot> & Record<string, unknown>;
  return {
    instanceId: readString(snapshot.instance_id),
    side: readString(snapshot.side),
    unitDefId: readString(snapshot.unit_def_id),
    x: readNumber(snapshot.x, 0),
    y: readNumber(snapshot.y, 0),
    positionX: readNumber(snapshot.position_x, spatialXFromGrid(readNumber(snapshot.x, 0))),
    positionY: readNumber(snapshot.position_y, spatialYFromGrid(readNumber(snapshot.y, 0), readString(snapshot.side))),
    velocityX: readNumber(snapshot.velocity_x, 0),
    velocityY: readNumber(snapshot.velocity_y, 0),
    facingAngle: readNumber(snapshot.facing_angle, 0),
    radius: readNumber(snapshot.radius, 8),
    moveSpeed: readNumber(snapshot.move_speed, 0),
    attackRange: readNumber(snapshot.attack_range, readNumber(snapshot.base_range, readNumber(snapshot.range, 0))),
    engagementRange: readNumber(snapshot.engagement_range, readNumber(snapshot.base_range, readNumber(snapshot.range, 0))),
    engagedTarget: readNullableString(snapshot.engaged_target),
    movementIntent: readString(snapshot.movement_intent, "hold"),
    combatState: readString(snapshot.combat_state, readString(snapshot.movement_intent, "idle")),
    role: readString(snapshot.role, "unknown"),
    name: readString(snapshot.name, readString(snapshot.instance_id)),
    tags: readStringArray(snapshot.tags),
    maxHp: readNumber(snapshot.base_hp, readNumber(snapshot.hp, 0)),
    hp: readNumber(snapshot.hp, readNumber(snapshot.base_hp, 0)),
    alive: readBoolean(snapshot.alive, true),
    atk: readNumber(snapshot.atk, 0),
    defense: readNumber(snapshot.defense, 0),
    range: readNumber(snapshot.base_range, readNumber(snapshot.range, 0)),
    guardValue: readNumber(snapshot.guard_value, 0),
    skillIds: [],
    statBonuses: new Map<string, number>(),
    statuses: readStatusSnapshots(snapshot.statuses),
    skillCooldowns: readNumberMap((snapshot as Record<string, unknown>).skill_cooldowns),
    nextActionTick: readNullableNumber(snapshot.next_action_tick),
    actionIntervalTicks: readNullableNumber(snapshot.action_interval_ticks),
    lastStatus: null,
    lastCooldown: null,
    lastActionSchedule: null,
  };
};

const applyActionScheduled = (state: VisualState, event: ReplayEvent): void => {
  const unitId = readString(event.payload.unit);
  const annotation: ActionScheduleAnnotation = {
    tick: event.tick,
    unit: unitId,
    currentTick: readNumber(event.payload.current_tick, event.tick),
    nextActionTick: readNumber(event.payload.next_action_tick, event.tick),
    actionIntervalTicks: readNumber(event.payload.action_interval_ticks, 0),
    reason: readString(event.payload.reason),
  };
  const unit = state.units.get(unitId);
  if (unit) {
    unit.nextActionTick = annotation.nextActionTick;
    unit.actionIntervalTicks = annotation.actionIntervalTicks;
    unit.lastActionSchedule = annotation;
  }
  state.lastActionSchedule = annotation;
};

const applyUnitMove = (state: VisualState, event: ReplayEvent): void => {
  const unitId = readString(event.payload.unit);
  const unit = state.units.get(unitId);
  const toX = readNumber(event.payload.to_x, unit?.positionX ?? 0);
  const toY = readNumber(event.payload.to_y, unit?.positionY ?? 0);
  if (unit) {
    unit.positionX = toX;
    unit.positionY = toY;
    unit.velocityX = readNumber(event.payload.velocity_x, 0);
    unit.velocityY = readNumber(event.payload.velocity_y, 0);
    unit.moveSpeed = readNumber(event.payload.move_speed, unit.moveSpeed);
    unit.movementIntent = readString(event.payload.reason, "move_to_attack_range");
    unit.combatState = unit.movementIntent;
    unit.engagedTarget = readNullableString(event.payload.target);
    unit.combatState = "moving_to_engage";
  }
  state.lastMove = {
    tick: event.tick,
    unit: unitId,
    target: readNullableString(event.payload.target),
    fromX: readNumber(event.payload.from_x, toX),
    fromY: readNumber(event.payload.from_y, toY),
    toX,
    toY,
    reason: readString(event.payload.reason),
  };
};

const applySpatialTargetEvent = (state: VisualState, event: ReplayEvent): void => {
  const unitId = readString(event.payload.unit);
  const targetId = readNullableString(event.payload.target);
  const unit = state.units.get(unitId);
  if (unit) {
    unit.engagedTarget = targetId;
    unit.movementIntent = event.type === "target_acquired" ? "target_acquired" : "engaged";
    unit.combatState = event.type === "target_acquired" ? "moving_to_engage" : "engaged";
  }
};

const applyDeath = (state: VisualState, event: ReplayEvent): void => {
  const unitId = readString(event.payload.unit);
  const unit = state.units.get(unitId);
  if (!unit) {
    return;
  }
  unit.alive = false;
  unit.hp = 0;
  unit.combatState = "dead";
  unit.engagedTarget = null;
  unit.movementIntent = "hold";
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

const readStatus = (
  payload: Record<string, unknown>,
  tick: number,
  eventType: "status_apply" | "status_expire",
  active: boolean,
): StatusAnnotation | null => {
  const target = readString(payload.target);
  if (!target) {
    return null;
  }
  return {
    tick,
    eventType,
    id: readString(payload.id, readString(payload.status_id, `${target}:${tick}:${eventType}`)),
    source: readString(payload.source),
    sourceType: readString(payload.source_type),
    target,
    stat: readString(payload.stat),
    amount: readNumber(payload.amount, 0),
    startTick: readNumber(payload.start_tick, tick),
    expireTick: readNullableNumber(payload.expire_tick),
    reason: readString(payload.reason),
    targetReason: readNullableString(payload.target_reason),
    active,
  };
};

const readStatusSnapshots = (value: unknown): VisualStatus[] => {
  if (!Array.isArray(value)) {
    return [];
  }
  return value
    .map((item) => (typeof item === "object" && item !== null ? readStatus(item as Record<string, unknown>, 0, "status_apply", true) : null))
    .filter((status): status is StatusAnnotation => status !== null)
    .map(({ tick: _tick, eventType: _eventType, ...status }) => status);
};

const readNumberMap = (value: unknown): Map<string, number> => {
  const map = new Map<string, number>();
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    return map;
  }
  for (const [key, item] of Object.entries(value)) {
    if (typeof item === "number" && Number.isFinite(item)) {
      map.set(key, item);
    }
  }
  return map;
};

const applyStatusStat = (unit: VisualUnit, stat: string, amount: number): void => {
  if (stat === "atk") {
    unit.atk += amount;
  } else if (stat === "defense") {
    unit.defense += amount;
  } else if (stat === "range") {
    unit.range += amount;
  } else if (stat === "hp") {
    unit.maxHp += amount;
    unit.hp += amount;
  } else if (stat === "guard_value") {
    unit.guardValue += amount;
  }
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

const spatialXFromGrid = (x: number): number => 80 + x * 56;

const spatialYFromGrid = (y: number, side: string): number => (side === "enemy" ? 80 : 320) + y * 36;
