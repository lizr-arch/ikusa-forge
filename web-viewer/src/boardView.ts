import type { VisualState, VisualUnit } from "./replayState";

export type EventUnitHighlight =
  | "attack-source"
  | "attack-target"
  | "skill-source"
  | "skill-target"
  | "damage-source"
  | "damage-target"
  | "modifier-source"
  | "modifier-target"
  | "death"
  | "battle-end";

interface BoardRenderOptions {
  state: VisualState;
  selectedUnitId: string | null;
  unitHighlights: Map<string, EventUnitHighlight>;
  onSelectUnit: (unitId: string) => void;
}

interface Point {
  x: number;
  y: number;
}

const SVG_NS = "http://www.w3.org/2000/svg";
const COLS = 4;
const ROWS = 3;
const CELL_WIDTH = 132;
const CELL_HEIGHT = 76;
const ORIGIN_X = 58;
const ENEMY_Y = 54;
const SIDE_GAP = 70;
const ALLY_Y = ENEMY_Y + ROWS * CELL_HEIGHT + SIDE_GAP;
const WIDTH = ORIGIN_X * 2 + COLS * CELL_WIDTH;
const HEIGHT = ALLY_Y + ROWS * CELL_HEIGHT + 48;

export const renderBoard = (container: HTMLElement, options: BoardRenderOptions): void => {
  container.replaceChildren();
  const svg = svgElement("svg");
  setAttrs(svg, {
    viewBox: `0 0 ${WIDTH} ${HEIGHT}`,
    role: "img",
    "aria-label": "Replay board",
  });

  drawSideCells(svg, "enemy", ENEMY_Y);
  drawSideCells(svg, "ally", ALLY_Y);

  const centers = buildUnitCenters(options.state);
  drawAnnotations(svg, options.state, centers);
  drawUnits(svg, options, centers);

  container.append(svg);
};

const drawSideCells = (svg: SVGSVGElement, side: "ally" | "enemy", originY: number): void => {
  const label = svgElement("text");
  label.textContent = side === "ally" ? "Ally" : "Enemy";
  setAttrs(label, {
    x: 12,
    y: originY - 18,
    class: `side-label side-label-${side}`,
  });
  svg.append(label);

  for (let y = 0; y < ROWS; y += 1) {
    for (let x = 0; x < COLS; x += 1) {
      const rect = svgElement("rect");
      setAttrs(rect, {
        x: ORIGIN_X + x * CELL_WIDTH,
        y: originY + y * CELL_HEIGHT,
        width: CELL_WIDTH - 8,
        height: CELL_HEIGHT - 8,
        rx: 8,
        class: "board-cell",
      });
      svg.append(rect);

      const coord = svgElement("text");
      coord.textContent = `${x},${y}`;
      setAttrs(coord, {
        x: ORIGIN_X + x * CELL_WIDTH + 10,
        y: originY + y * CELL_HEIGHT + 18,
        class: "cell-coordinate",
      });
      svg.append(coord);
    }
  }
};

const drawAnnotations = (
  svg: SVGSVGElement,
  state: VisualState,
  centers: Map<string, Point>,
): void => {
  if (state.lastAttack) {
    const source = centers.get(state.lastAttack.source);
    const target = centers.get(state.lastAttack.target);
    if (source && target) {
      const line = svgElement("line");
      setAttrs(line, {
        x1: source.x,
        y1: source.y,
        x2: target.x,
        y2: target.y,
        class: "attack-line",
      });
      svg.append(line);
    }
  }

  if (state.lastSkill) {
    for (const unitId of [state.lastSkill.source, ...state.lastSkill.targets]) {
      const center = centers.get(unitId);
      if (!center) {
        continue;
      }
      const ring = svgElement("circle");
      setAttrs(ring, {
        cx: center.x,
        cy: center.y,
        r: unitId === state.lastSkill.source ? 36 : 31,
        class: unitId === state.lastSkill.source ? "skill-ring skill-ring-source" : "skill-ring",
      });
      svg.append(ring);
    }

    const source = centers.get(state.lastSkill.source);
    if (source) {
      const label = svgElement("text");
      label.textContent = state.lastSkill.skill;
      setAttrs(label, {
        x: source.x,
        y: source.y - 40,
        class: "skill-label",
      });
      svg.append(label);
    }
  }

  if (state.lastModifier) {
    const source = centers.get(state.lastModifier.source);
    const target = centers.get(state.lastModifier.target);
    if (source) {
      const sourceRing = svgElement("rect");
      setAttrs(sourceRing, {
        x: source.x - 42,
        y: source.y - 46,
        width: 84,
        height: 92,
        rx: 10,
        class: "modifier-ring modifier-ring-source",
      });
      svg.append(sourceRing);
    }

    if (target) {
      const targetRing = svgElement("circle");
      setAttrs(targetRing, {
        cx: target.x,
        cy: target.y,
        r: state.lastModifier.stat === "atk" ? 42 : 36,
        class: "modifier-ring modifier-ring-target",
      });
      svg.append(targetRing);

      const summary = svgElement("text");
      summary.textContent = `${state.lastModifier.stat}${state.lastModifier.amount >= 0 ? "+" : ""}${state.lastModifier.amount}`;
      setAttrs(summary, {
        x: target.x,
        y: target.y + 4,
        class: "modifier-label",
      });
      svg.append(summary);
    }

    if (state.lastModifier.reason && target) {
      const reason = svgElement("text");
      reason.textContent = shorten(state.lastModifier.reason, 17);
      setAttrs(reason, {
        x: target.x,
        y: target.y + 18,
        class: "modifier-reason-label",
      });
      svg.append(reason);
    }
  }

  if (state.lastDamage) {
    const target = centers.get(state.lastDamage.target);
    if (target) {
      const text = svgElement("text");
      text.textContent = `-${state.lastDamage.amount}`;
      setAttrs(text, {
        x: target.x + 26,
        y: target.y - 18,
        class: "damage-label",
      });
      svg.append(text);

      if (state.lastDamage.reason) {
        const reason = svgElement("text");
        reason.textContent = shorten(state.lastDamage.reason, 18);
        setAttrs(reason, {
          x: target.x + 26,
          y: target.y - 3,
          class: "damage-reason-label",
        });
        svg.append(reason);
      }
    }
  }
};

const drawUnits = (
  svg: SVGSVGElement,
  options: BoardRenderOptions,
  centers: Map<string, Point>,
): void => {
  const units = [...options.state.units.values()].sort((left, right) =>
    left.instanceId.localeCompare(right.instanceId),
  );
  for (const unit of units) {
    const center = centers.get(unit.instanceId);
    if (!center) {
      continue;
    }
    drawUnit(svg, unit, center, options);
  }
};

const drawUnit = (
  svg: SVGSVGElement,
  unit: VisualUnit,
  center: Point,
  options: BoardRenderOptions,
): void => {
  const group = svgElement("g");
  const selected = unit.instanceId === options.selectedUnitId;
  const classNames = [
    "unit-token",
    `unit-${unit.side}`,
    unit.alive ? "unit-alive" : "unit-dead",
    eventHighlightClass(options.unitHighlights.get(unit.instanceId)),
    selected ? "unit-selected" : "",
  ]
    .filter(Boolean)
    .join(" ");
  setAttrs(group, {
    class: classNames,
    role: "button",
    tabindex: 0,
    "aria-label": unit.instanceId,
  });

  group.addEventListener("click", () => options.onSelectUnit(unit.instanceId));
  group.addEventListener("keydown", (event: KeyboardEvent) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      options.onSelectUnit(unit.instanceId);
    }
  });

  const x = center.x - 50;
  const y = center.y - 28;
  const rect = svgElement("rect");
  setAttrs(rect, {
    x,
    y,
    width: 100,
    height: 56,
    rx: 8,
    class: "unit-rect",
  });
  group.append(rect);

  const healthBackground = svgElement("rect");
  setAttrs(healthBackground, {
    x: x + 8,
    y: y + 40,
    width: 84,
    height: 6,
    rx: 3,
    class: "health-background",
  });
  group.append(healthBackground);

  const health = svgElement("rect");
  const hpRatio = unit.maxHp > 0 ? Math.max(0, Math.min(1, unit.hp / unit.maxHp)) : 0;
  setAttrs(health, {
    x: x + 8,
    y: y + 40,
    width: 84 * hpRatio,
    height: 6,
    rx: 3,
    class: "health-fill",
  });
  group.append(health);

  appendText(group, unit.instanceId, center.x, y + 15, "unit-id");
  appendText(group, `${shorten(unit.name, 12)} / ${shorten(unit.role, 8)}`, center.x, y + 29, "unit-role");
  appendText(group, `${unit.hp}/${unit.maxHp}`, center.x, y + 54, "unit-hp");

  if (!unit.alive) {
    const slash = svgElement("line");
    setAttrs(slash, {
      x1: x + 12,
      y1: y + 10,
      x2: x + 88,
      y2: y + 46,
      class: "death-slash",
    });
    group.append(slash);
  }

  const highlight = options.unitHighlights.get(unit.instanceId);
  if (highlight) {
    const ring = svgElement("rect");
    setAttrs(ring, {
      x: x - 5,
      y: y - 5,
      width: 110,
      height: 66,
      rx: 11,
      class: `unit-event-ring unit-event-ring-${highlight}`,
    });
    group.append(ring);
  }

  svg.append(group);
};

const buildUnitCenters = (state: VisualState): Map<string, Point> => {
  const centers = new Map<string, Point>();
  for (const unit of state.units.values()) {
    const originY = unit.side === "enemy" ? ENEMY_Y : ALLY_Y;
    centers.set(unit.instanceId, {
      x: ORIGIN_X + unit.x * CELL_WIDTH + (CELL_WIDTH - 8) / 2,
      y: originY + unit.y * CELL_HEIGHT + (CELL_HEIGHT - 8) / 2,
    });
  }
  return centers;
};

const appendText = (
  parent: SVGElement,
  value: string,
  x: number,
  y: number,
  className: string,
): void => {
  const text = svgElement("text");
  text.textContent = value;
  setAttrs(text, {
    x,
    y,
    class: className,
  });
  parent.append(text);
};

const shorten = (value: string, length: number): string => {
  if (value.length <= length) {
    return value;
  }
  return `${value.slice(0, Math.max(0, length - 1))}.`;
};

const eventHighlightClass = (highlight: EventUnitHighlight | undefined): string => {
  return highlight ? `unit-current-event unit-current-${highlight}` : "";
};

const svgElement = <K extends keyof SVGElementTagNameMap>(tag: K): SVGElementTagNameMap[K] => {
  return document.createElementNS(SVG_NS, tag);
};

const setAttrs = (element: Element, attrs: Record<string, string | number>): void => {
  for (const [key, value] of Object.entries(attrs)) {
    element.setAttribute(key, String(value));
  }
};
