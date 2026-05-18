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
const UNIT_WIDTH = 102;
const UNIT_HEIGHT = 60;
const UNIT_PADDING = 8;

export const renderBoard = (container: HTMLElement, options: BoardRenderOptions): void => {
  container.replaceChildren();
  const svg = svgElement("svg");
  setAttrs(svg, {
    viewBox: `0 0 ${WIDTH} ${HEIGHT}`,
    role: "img",
    "aria-label": "Battlefield（战场）",
  });

  drawSideCells(svg, "enemy", ENEMY_Y);
  drawSideCells(svg, "ally", ALLY_Y);

  const centers = buildUnitCenters(options.state);
  drawAnnotations(svg, options.state, centers);
  drawUnits(svg, options, centers);
  drawVictoryBanner(svg, options.state);

  container.append(svg);
};

const drawSideCells = (svg: SVGSVGElement, side: "ally" | "enemy", originY: number): void => {
  const label = svgElement("text");
  label.textContent = side === "ally" ? "Ally（友军）" : "Enemy（敌军）";
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

  if (state.lastStatus) {
    const target = centers.get(state.lastStatus.target);
    if (target) {
      const marker = svgElement("circle");
      setAttrs(marker, {
        cx: target.x - 24,
        cy: target.y - 24,
        r: 14,
        class: "status-badge",
      });
      const markerLabel = svgElement("text");
      markerLabel.textContent = state.lastStatus.eventType === "status_apply" ? "S+" : "SE";
      setAttrs(markerLabel, {
        x: target.x - 24,
        y: target.y - 20,
        class: "status-badge-text",
      });
      svg.append(marker, markerLabel);
    }
  }

  if (state.lastCooldown) {
    const source = centers.get(state.lastCooldown.source);
    if (source) {
      const cooldown = svgElement("rect");
      const remaining = Math.max(0, state.lastCooldown.readyTick - state.lastCooldown.tick);
      setAttrs(cooldown, {
        x: source.x + 26,
        y: source.y - 22,
        width: 24,
        height: 14,
        rx: 4,
        class: "cooldown-badge",
      });
      const label = svgElement("text");
      label.textContent = `CD ${remaining}`;
      setAttrs(label, {
        x: source.x + 38,
        y: source.y - 11,
        class: "cooldown-text",
      });
      svg.append(cooldown, label);
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
    "data-unit-id": unit.instanceId,
    "data-position-x": unit.positionX,
    "data-position-y": unit.positionY,
  });

  group.addEventListener("click", () => options.onSelectUnit(unit.instanceId));
  group.addEventListener("keydown", (event: KeyboardEvent) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      options.onSelectUnit(unit.instanceId);
    }
  });

  const range = svgElement("circle");
  setAttrs(range, {
    cx: center.x,
    cy: center.y,
    r: Math.max(8, unit.attackRange),
    class: "unit-range-circle",
  });
  group.append(range);

  const x = center.x - UNIT_WIDTH / 2;
  const y = center.y - UNIT_HEIGHT / 2;
  const rect = svgElement("rect");
  setAttrs(rect, {
    x,
    y,
    width: UNIT_WIDTH,
    height: UNIT_HEIGHT,
    rx: 8,
    class: "unit-rect",
  });
  group.append(rect);

  const healthBackground = svgElement("rect");
  setAttrs(healthBackground, {
    x: x + UNIT_PADDING,
    y: y + 40,
    width: UNIT_WIDTH - UNIT_PADDING * 2,
    height: 6,
    rx: 3,
    class: "health-background",
  });
  group.append(healthBackground);

  const hpRatio = unit.maxHp > 0 ? Math.max(0, Math.min(1, unit.hp / unit.maxHp)) : 0;
  const health = svgElement("rect");
  setAttrs(health, {
    x: x + UNIT_PADDING,
    y: y + 40,
    width: (UNIT_WIDTH - UNIT_PADDING * 2) * hpRatio,
    height: 6,
    rx: 3,
    class: "health-fill",
  });
  group.append(health);

  const statusCount = unit.statuses.filter((status) => status.active).length;
  const cooldownCount = unit.skillCooldowns.size;
  appendText(group, unit.instanceId, center.x, y + 16, "unit-id");
  appendText(group, `${shorten(unit.name, 12)} / ${shorten(unit.role, 8)}`, center.x, y + 30, "unit-role");
  appendText(group, `${unit.hp}/${unit.maxHp}`, center.x, y + 54, "unit-hp");
  appendText(group, `Status（状态）${statusCount}`, center.x - 28, y - 4, "unit-status-count");
  appendText(group, `Cooldown（冷却）${cooldownCount}`, center.x + 28, y - 4, "unit-cooldown-count");
  appendActionBar(group, x, y + 48, unit, options.state.currentTick);

  if (!unit.alive) {
    const slash = svgElement("line");
    setAttrs(slash, {
      x1: x + 12,
      y1: y + 12,
      x2: x + UNIT_WIDTH - 12,
      y2: y + UNIT_HEIGHT - 12,
      class: "death-slash",
    });
    group.append(slash);
  }

  const nextActionTick = unit.nextActionTick;
  const actionIntervalTicks = unit.actionIntervalTicks;
  const nextActionText = nextActionTick === null
    ? "Next Action（下次行动）: -"
    : actionIntervalTicks === null
      ? `Next Action（下次行动）: ${nextActionTick}`
      : `Next Action（下次行动）: ${nextActionTick}/${actionIntervalTicks}`;
  appendText(group, nextActionText, center.x, y + UNIT_HEIGHT + 10, "unit-action-text");

  const meta = `ATK（攻击） ${unit.atk} / DEF（防御） ${unit.defense}`;
  appendText(group, meta, center.x, y + UNIT_HEIGHT + 22, "unit-meta-text");

  const highlight = options.unitHighlights.get(unit.instanceId);
  if (highlight) {
    const ring = svgElement("rect");
    setAttrs(ring, {
      x: x - 5,
      y: y - 5,
      width: UNIT_WIDTH + 10,
      height: UNIT_HEIGHT + 10,
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
    centers.set(unit.instanceId, {
      x: unit.positionX,
      y: unit.positionY,
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

const appendActionBar = (
  parent: SVGElement,
  x: number,
  y: number,
  unit: VisualUnit,
  currentTick: number,
): void => {
  const actionBarWidth = UNIT_WIDTH - UNIT_PADDING * 2;
  const ratio = getActionRatio(unit, currentTick);
  const progress = Math.max(0, Math.min(actionBarWidth, actionBarWidth * ratio));
  const background = svgElement("rect");
  setAttrs(background, {
    x: x + UNIT_PADDING,
    y,
    width: actionBarWidth,
    height: 4,
    rx: 3,
    class: "action-bar-bg",
  });
  const fill = svgElement("rect");
  setAttrs(fill, {
    x: x + UNIT_PADDING,
    y,
    width: progress,
    height: 4,
    rx: 3,
    class: "action-bar-fill",
  });
  const actionText = unit.nextActionTick === null
    ? "NA"
    : `Action（行动） ${unit.nextActionTick}`;
  const actionTextElement = svgElement("text");
  setAttrs(actionTextElement, {
    x: x + UNIT_WIDTH / 2,
    y: y + 14,
    class: "action-bar-text",
  });
  actionTextElement.textContent = actionText;
  parent.append(background, fill, actionTextElement);
};

const getActionRatio = (unit: VisualUnit, currentTick: number): number => {
  if (unit.nextActionTick === null || unit.actionIntervalTicks === null || unit.actionIntervalTicks <= 0) {
    return 0;
  }
  const cycleStart = Math.max(0, unit.nextActionTick - unit.actionIntervalTicks);
  const local = Math.max(0, Math.min(unit.actionIntervalTicks, currentTick - cycleStart));
  return local / unit.actionIntervalTicks;
};

const eventHighlightClass = (highlight: EventUnitHighlight | undefined): string => {
  return highlight ? `unit-current-event unit-current-${highlight}` : "";
};

const drawVictoryBanner = (svg: SVGSVGElement, state: VisualState): void => {
  const result = state.battleResult;
  if (!result) {
    return;
  }

  const winner = result.winner ?? "Unknown";
  const reason = result.reason ?? "-";
  const endTick = result.end_tick ?? state.currentTick;
  const width = WIDTH - 96;
  const x = (WIDTH - width) / 2;
  const y = 14;
  const rect = svgElement("rect");
  setAttrs(rect, {
    x,
    y,
    width,
    height: 44,
    rx: 10,
    class: "victory-banner",
  });
  const text = svgElement("text");
  text.textContent = `Victory（胜负） ${winner} / ${reason} / tick ${endTick}`;
  setAttrs(text, {
    x: WIDTH / 2,
    y: y + 28,
    class: "victory-banner-text",
  });
  svg.append(rect, text);
};

const svgElement = <K extends keyof SVGElementTagNameMap>(tag: K): SVGElementTagNameMap[K] => {
  return document.createElementNS(SVG_NS, tag);
};

const setAttrs = (element: Element, attrs: Record<string, string | number>): void => {
  for (const [key, value] of Object.entries(attrs)) {
    element.setAttribute(key, String(value));
  }
};
