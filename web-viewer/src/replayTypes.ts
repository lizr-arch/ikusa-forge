export type KnownReplayEventType =
  | "battle_start"
  | "unit_spawn"
  | "attack"
  | "skill_trigger"
  | "damage"
  | "death"
  | "battle_end"
  | "stat_modifier";

export type UnitSide = "ally" | "enemy" | string;

export interface BattleResult {
  winner?: string | null;
  reason?: string | null;
  end_tick?: number | null;
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
  next_action_tick?: number;
  action_interval_ticks?: number;
  guard_value?: number;
  skill_cooldowns?: Record<string, number>;
  atk?: number;
  defense?: number;
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
}

export interface ReportSummary {
  total_damage?: number;
  total_kills?: number;
  total_skill_triggers?: number;
  total_modifiers?: number;
  formation_modifiers?: number;
  synergy_modifiers?: number;
  target_reason_counts?: Record<string, number>;
  skill_target_reason_counts?: Record<string, number>;
}

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
  units?: Record<string, UnitReport>;
  top_units?: ReportTopUnits;
  key_moments?: KeyMoment[];
}
