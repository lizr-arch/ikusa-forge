import type { BattleReport, ReplayEvent, UnitReport } from "./replayTypes";

export const formatNumber = (value: number | null | undefined): string => {
  if (typeof value !== "number" || !Number.isFinite(value)) {
    return "-";
  }
  return String(value);
};

export const formatValue = (value: string | number | null | undefined): string => {
  if (value === null || value === undefined || value === "") {
    return "-";
  }
  return String(value);
};

export const eventSummary = (event: ReplayEvent): string => {
  switch (event.type) {
    case "battle_start":
      return `battle ${text(event.payload.battle_id)} seed ${text(event.payload.seed)}`;
    case "unit_spawn":
      return `spawn ${unitIdFromSpawn(event)}`;
    case "attack":
      return `${text(event.payload.attacker)} attacks ${text(event.payload.target)}`;
    case "skill_trigger":
      return `${text(event.payload.source)} uses ${text(event.payload.skill)} -> ${arrayText(
        event.payload.targets,
      )}`;
    case "damage":
      return `${text(event.payload.source)} deals ${text(event.payload.amount)} to ${text(
        event.payload.target,
      )}`;
    case "death":
      return `${text(event.payload.unit)} dies`;
    case "battle_end":
      return `winner ${text(event.payload.winner)} by ${text(event.payload.reason)}`;
    default:
      return event.type;
  }
};

export const totalSkillTriggers = (unitReport: UnitReport | undefined): number => {
  if (!unitReport) {
    return 0;
  }
  return Object.values(unitReport.skill_triggers ?? {}).reduce((total, value) => total + value, 0);
};

export const getUnitReport = (
  report: BattleReport | null,
  unitId: string,
): UnitReport | undefined => {
  return report?.units?.[unitId];
};

const text = (value: unknown): string => {
  if (value === null || value === undefined || value === "") {
    return "-";
  }
  return String(value);
};

const arrayText = (value: unknown): string => {
  if (!Array.isArray(value)) {
    return "-";
  }
  const strings = value.map((item) => String(item));
  return strings.length > 0 ? strings.join(", ") : "-";
};

const unitIdFromSpawn = (event: ReplayEvent): string => {
  const unit = event.payload.unit;
  if (typeof unit !== "object" || unit === null || Array.isArray(unit)) {
    return "-";
  }
  const instanceId = (unit as Record<string, unknown>).instance_id;
  return text(instanceId);
};
