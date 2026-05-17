import { formatNumber, formatValue } from "./formatters";
import type { BattleReport, LiveBattleResult, ReplayDocument } from "./replayTypes";

interface BattleSummaryOptions {
  replay: ReplayDocument | null;
  report: BattleReport | null;
  eventCount: number;
  liveMode?: boolean;
  liveCurrentTick?: number;
  liveFinished?: boolean;
  liveResult?: LiveBattleResult | null;
}

export const renderBattleSummary = (
  container: HTMLElement,
  options: BattleSummaryOptions,
): void => {
  container.replaceChildren();

  const replayResult = options.replay?.metadata.result ?? options.liveResult;
  const liveResult = options.liveResult;
  const summary = options.report?.summary;
  const rows: [string, string][] = [
    ["Battle ID", formatValue(options.replay?.metadata.battle_id ?? options.report?.battle_id)],
    ["Seed", formatNumber(options.replay?.metadata.seed ?? options.report?.seed)],
    ["Winner", formatValue(options.report?.winner ?? liveResult?.winner ?? replayResult?.winner)],
    ["Reason", formatValue(options.report?.reason ?? liveResult?.reason ?? replayResult?.reason)],
    [
      "End Tick",
      options.liveMode ? formatNumber(options.liveCurrentTick ?? replayResult?.end_tick) : formatNumber(
        options.report?.end_tick ?? replayResult?.end_tick,
      ),
    ],
    ["Events", formatNumber(options.eventCount)],
    ["Total Damage", formatNumber(summary?.total_damage)],
    ["Total Kills", formatNumber(summary?.total_kills)],
    ["Skill Triggers", formatNumber(summary?.total_skill_triggers)],
    ["Status Applied（状态应用）", formatNumber(summary?.total_status_applied)],
    ["Skill Cooldown（技能冷却）", formatNumber(summary?.total_skill_cooldowns)],
    ["Action Scheduled（行动调度）", formatNumber(summary?.total_actions_scheduled)],
    ["Total Modifiers", formatNumber(summary?.total_modifiers)],
    ["Formation Modifiers", formatNumber(summary?.formation_modifiers)],
    ["Synergy Modifiers", formatNumber(summary?.synergy_modifiers)],
  ];

  container.append(statGrid(rows));
};

const statGrid = (rows: [string, string][]): HTMLElement => {
  const grid = document.createElement("div");
  grid.className = "stat-grid battle-summary-grid";
  for (const [label, value] of rows) {
    const item = document.createElement("div");
    item.className = "stat-item";
    const key = document.createElement("span");
    key.textContent = label;
    const val = document.createElement("strong");
    val.textContent = value;
    item.append(key, val);
    grid.append(item);
  }
  return grid;
};
