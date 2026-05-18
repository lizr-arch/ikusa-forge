export type KnownReplayEventType =
  | "battle_start"
  | "unit_spawn"
  | "attack"
  | "skill_trigger"
  | "damage"
  | "death"
  | "battle_end"
  | "stat_modifier"
  | "status_apply"
  | "status_expire"
  | "skill_cooldown"
  | "action_scheduled"
  | "unit_move"
  | "target_acquired"
  | "enter_range"
  | "engage_start";

export type UnitSide = "ally" | "enemy" | string;

export interface BattleResult {
  winner?: string | null;
  reason?: string | null;
  end_tick?: number | null;
  winner_alive?: number | null;
  loser_alive?: number | null;
  winner_total_hp?: number | null;
  loser_total_hp?: number | null;
  summary?: string | null;
}

export interface LiveBattleResult {
  winner?: string | null;
  reason?: string | null;
  end_tick?: number | null;
  winner_alive?: number | null;
  loser_alive?: number | null;
  winner_total_hp?: number | null;
  loser_total_hp?: number | null;
  summary?: string | null;
}

export interface ReplayMetadata {
  battle_id?: string;
  seed?: number;
  tick_rate?: number;
  max_ticks?: number;
  unit_count?: number;
  result?: BattleResult | null;
  [key: string]: unknown;
}

export interface UnitSnapshot {
  instance_id: string;
  side: UnitSide;
  unit_def_id?: string;
  x: number;
  y: number;
  role?: string;
  name?: string;
  tags?: string[];
  base_hp?: number;
  base_atk?: number;
  base_defense?: number;
  base_range?: number;
  base_attack_interval?: number;
  weapon_slots?: string[];
  skill_ids?: string[];
  hp?: number;
  alive?: boolean;
  position_x?: number;
  position_y?: number;
  velocity_x?: number;
  velocity_y?: number;
  facing_angle?: number;
  radius?: number;
  move_speed?: number;
  attack_range?: number;
  engagement_range?: number;
  engaged_target?: string | null;
  movement_intent?: string;
  combat_state?: string;
  next_action_tick?: number;
  action_interval_ticks?: number;
  guard_value?: number;
  statuses?: StatusEffectSnapshot[];
  skill_cooldowns?: Record<string, number>;
  atk?: number;
  defense?: number;
}

export interface LiveUnitSnapshot {
  instance_id: string;
  side: UnitSide;
  unit_def_id: string;
  name: string;
  x: number;
  y: number;
  role: string;
  hp: number;
  base_hp: number;
  atk: number;
  base_atk?: number;
  defense: number;
  base_defense?: number;
  range: number;
  base_range?: number;
  base_attack_interval?: number;
  position_x?: number;
  position_y?: number;
  velocity_x?: number;
  velocity_y?: number;
  facing_angle?: number;
  radius?: number;
  move_speed?: number;
  attack_range?: number;
  engagement_range?: number;
  engaged_target?: string | null;
  movement_intent?: string;
  combat_state?: string;
  next_action_tick: number | null;
  action_interval_ticks: number | null;
  statuses?: StatusEffectSnapshot[];
  skill_cooldowns?: Record<string, number>;
  alive: boolean;
  guard_value?: number;
  tags?: string[];
}

export interface LiveBattleSnapshot {
  schema_version: "battle_snapshot.v0.1";
  battle_id: string;
  seed: number;
  tick: number;
  finished: boolean;
  result: LiveBattleResult | null;
  units: LiveUnitSnapshot[];
  event_count: number;
}

export interface StatusEffectSnapshot {
  id: string;
  source: string;
  source_type?: string;
  target: string;
  stat: string;
  amount: number;
  start_tick: number;
  expire_tick?: number | null;
  reason?: string;
  target_reason?: string;
}

export interface BattleStartPayload {
  battle_id: string;
  seed: number;
  tick_rate: number;
  max_ticks: number;
  mode?: string;
}

export interface UnitSpawnPayload {
  formation_id?: string;
  unit: UnitSnapshot;
}

export interface TargetScorePayload {
  final: number;
  exposure: number;
  column: number;
  low_hp: number;
  threat: number;
  role: number;
  tie_break: number;
}

export interface AttackPayload {
  attacker: string;
  target: string;
  target_reason?: string;
  target_score?: TargetScorePayload;
}

export interface SkillTriggerPayload {
  source: string;
  skill: string;
  trigger?: string;
  targets: string[];
  target_reason?: string;
  target_score?: TargetScorePayload;
}

export interface StatusApplyPayload extends StatusEffectSnapshot {}

export interface StatusExpirePayload {
  id?: string;
  status_id?: string;
  source?: string;
  target: string;
  stat?: string;
  expire_tick?: number | null;
  reason?: string;
}

export interface SkillCooldownPayload {
  source: string;
  skill: string;
  start_tick: number;
  ready_tick: number;
  cooldown_ticks: number;
}

export interface ActionScheduledPayload {
  unit: string;
  current_tick: number;
  next_action_tick: number;
  action_interval_ticks: number;
  reason?: string;
}

export interface DamagePayload {
  source?: string | null;
  target: string;
  amount: number;
  target_hp_after: number;
  reason?: string;
}

export interface DeathPayload {
  unit: string;
}

export interface BattleEndPayload extends BattleResult {}

export interface ReplayEvent {
  tick: number;
  event_id: string;
  type: KnownReplayEventType | string;
  payload: Record<string, unknown>;
}

export interface ReplayTick {
  tick: number;
  events: ReplayEvent[];
}

export interface ReplayDocument {
  schema_version: string;
  metadata: ReplayMetadata;
  ticks: ReplayTick[];
}

export interface UnitReport {
  damage_done: number;
  damage_taken: number;
  kills: number;
  deaths: number;
  skill_triggers: Record<string, number>;
  modifiers_received?: number;
  stat_bonuses?: Record<string, number>;
  statuses_applied?: number;
  statuses_expired?: number;
  cooldowns_started?: number;
  actions_taken?: number;
  last_next_action_tick?: number | null;
  moves?: number;
  target_acquired?: number;
  entered_range?: number;
  engagements_started?: number;
}

export interface ReportSummary {
  total_damage?: number;
  total_kills?: number;
  total_skill_triggers?: number;
  total_modifiers?: number;
  formation_modifiers?: number;
  synergy_modifiers?: number;
  total_status_applied?: number;
  total_status_expired?: number;
  total_skill_cooldowns?: number;
  total_actions_scheduled?: number;
  total_unit_moves?: number;
  total_target_acquired?: number;
  total_enter_range?: number;
  total_engage_start?: number;
  target_reason_counts?: Record<string, number>;
  skill_target_reason_counts?: Record<string, number>;
}

export interface VictoryExplanation extends BattleResult {}

export interface ReportTopUnits {
  damage_done?: string[];
  damage_taken?: string[];
  skill_triggers?: string[];
}

export interface KeyMoment {
  tick?: number;
  type?: string;
  unit?: string | null;
  killer?: string | null;
  winner?: string | null;
  reason?: string | null;
  end_tick?: number | null;
  summary?: string;
}

export interface BattleReport {
  schema_version?: string;
  battle_id?: string | null;
  seed?: number | null;
  winner?: string | null;
  reason?: string | null;
  end_tick?: number | null;
  summary?: ReportSummary;
  victory_explanation?: VictoryExplanation;
  units?: Record<string, UnitReport>;
  top_units?: ReportTopUnits;
  key_moments?: KeyMoment[];
}

export interface LiveApiResultErr {
  ok: false;
  error: string;
}

export type LiveApiResult<T> = (T & { ok: true }) | LiveApiResultErr;

export interface LiveStartResponse {
  ok: true;
  session_id: string;
  snapshot: LiveBattleSnapshot;
  events: ReplayEvent[];
  next_event_index: number;
}

export interface LiveStepResponse {
  ok: true;
  session_id?: string;
  snapshot: LiveBattleSnapshot;
  events: ReplayEvent[];
  next_event_index: number;
}

export interface LiveSnapshotResponse {
  ok: true;
  session_id?: string;
  snapshot: LiveBattleSnapshot;
}

export interface LiveEventsResponse {
  ok: true;
  session_id?: string;
  events: ReplayEvent[];
  next_event_index: number;
}

export interface LiveHealthResponse {
  ok: true;
  service: string;
}

export interface LiveResetResponse {
  ok: true;
  session_id?: string;
}

export interface ScenarioExpectedResult {
  winner?: string | null;
  reason?: string | null;
}

export interface DemoScenario {
  id: string;
  battle_id?: string;
  seed?: number;
  name: string;
  description: string;
  replay_url: string;
  report_url: string;
  expected?: ScenarioExpectedResult;
}

export interface ScenarioManifest {
  schema_version: string;
  scenarios: DemoScenario[];
}
