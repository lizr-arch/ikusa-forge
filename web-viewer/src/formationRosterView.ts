import { troopShapeLabel } from "./troopVisualConfig";
import type { VisualState, VisualUnit } from "./replayState";

interface FormationRosterRenderOptions {
  state: VisualState;
  selectedUnitId: string | null;
  onSelectUnit: (unitId: string) => void;
}

const SIDES = ["ally", "enemy"] as const;

export const renderFormationRoster = (
  container: HTMLElement,
  options: FormationRosterRenderOptions,
): void => {
  container.replaceChildren();
  if (options.state.units.size === 0) {
    container.append(empty("No live state available（未有实时状态）"));
    return;
  }

  const roster = document.createElement("div");
  roster.className = "formation-roster";

  for (const side of SIDES) {
    const list = document.createElement("div");
    list.className = "formation-side";
    const heading = document.createElement("h3");
    heading.className = `formation-side-heading ${side}-heading`;
    heading.textContent = side === "ally" ? "Ally（友军）" : "Enemy（敌军）";
    list.append(heading);

    for (const unit of unitsBySide(options.state, side)) {
      const row = document.createElement("button");
      row.type = "button";
      row.className = `formation-unit ${unit.instanceId === options.selectedUnitId ? "selected" : ""}`;
      row.addEventListener("click", () => options.onSelectUnit(unit.instanceId));

      const tag = document.createElement("span");
      tag.className = `roster-side-badge ${side}`;
      tag.textContent = unit.alive ? "●" : "✝";

      const id = document.createElement("span");
      id.className = "roster-unit-id";
      id.textContent = unit.instanceId;

      const shape = document.createElement("span");
      shape.className = "roster-shape";
      shape.textContent = troopShapeLabel(unit.unitDefId, unit.role, unit.tags);

      const hp = document.createElement("span");
      hp.className = "roster-unit-hp";
      hp.textContent = `${unit.hp}/${unit.maxHp}`;

      const state = document.createElement("span");
      state.className = "roster-combat-state";
      state.textContent = unit.combatState || unit.movementIntent || "idle";

      const engagementRole = document.createElement("span");
      engagementRole.className = "roster-engagement-role";
      engagementRole.textContent = unit.engagementRole || "-";

      const engagementTarget = document.createElement("span");
      engagementTarget.className = "roster-engagement-target";
      engagementTarget.textContent = unit.engagementTarget || "-";

      const desiredDistance = document.createElement("span");
      desiredDistance.className = "roster-desired-distance";
      desiredDistance.textContent = unit.desiredDistance ? `dist:${Math.round(unit.desiredDistance)}` : "-";

      row.append(tag, id, shape, hp, state, engagementRole, engagementTarget, desiredDistance);
      list.append(row);
    }

    roster.append(list);
  }

  container.append(roster);
};

const unitsBySide = (state: VisualState, side: "ally" | "enemy"): VisualUnit[] => {
  return [...state.units.values()]
    .filter((unit) => unit.side === side)
    .sort((left, right) => left.instanceId.localeCompare(right.instanceId));
};

const empty = (message: string): HTMLElement => {
  const element = document.createElement("div");
  element.className = "empty-state";
  element.textContent = message;
  return element;
};
