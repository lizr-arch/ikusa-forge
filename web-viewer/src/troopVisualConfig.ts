export type TroopShape = "square" | "triangle" | "hexagon" | "circle" | "diamond" | "pentagon" | "roundedRect";

export interface TroopVisualStyle {
  shape: TroopShape;
  label: string;
}

export const resolveTroopShape = (
  unitDefId: string,
  role: string,
  tags: string[],
  weaponSlots: string[] = [],
): TroopVisualStyle => {
  const source = `${unitDefId} ${role} ${tags.join(" ")} ${weaponSlots.join(" ")}`.toLowerCase();
  if (source.includes("shield")) {
    return { shape: "square", label: "Shield（盾兵）" };
  }
  if (source.includes("spear") || source.includes("lance")) {
    return { shape: "triangle", label: "Spear（枪兵）" };
  }
  if (source.includes("bow") || source.includes("archer")) {
    return { shape: "circle", label: "Bow（弓兵）" };
  }
  if (source.includes("ninja")) {
    return { shape: "diamond", label: "Ninja（忍者）" };
  }
  if (source.includes("banner") || source.includes("flag")) {
    return { shape: "pentagon", label: "Banner（旗手）" };
  }
  if (source.includes("katana") || source.includes("samurai")) {
    return { shape: "hexagon", label: "Katana（刀兵）" };
  }
  return { shape: "roundedRect", label: "Unit（单位）" };
};

export const troopShapeLabel = (unitDefId: string, role: string, tags: string[], weaponSlots: string[] = []): string => {
  return resolveTroopShape(unitDefId, role, tags, weaponSlots).label;
};

export const troopShapeName = (shape: TroopShape): string => {
  return shape;
};
