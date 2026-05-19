import { Application, Container, Graphics, Text, type FederatedPointerEvent } from "pixi.js";
import type { ReplayEvent } from "./replayTypes";
import { resolveTroopShape, type TroopShape } from "./troopVisualConfig";
import type { VisualState, VisualUnit } from "./replayState";

const ALLY_COLOR = 0x2f80ed;
const ENEMY_COLOR = 0xd94a4a;
const DEATH_COLOR = 0x99a2a6;
const CANVAS_WIDTH = 620;
const CANVAS_HEIGHT = 720;
const UNIT_WIDTH = 44;
const UNIT_HEIGHT = 34;

interface LivePixiOptions {
  onSelectUnit: (unitId: string) => void;
  debugOverlay: boolean;
}

interface UnitSprite {
  container: Container;
  body: Graphics;
  hpBg: Graphics;
  hpFill: Graphics;
  hpText: Text;
  actionBarBg: Graphics;
  actionBarFill: Graphics;
  actionText: Text;
  statusText: Text;
  cooldownText: Text;
  nameText: Text;
  selectionRing: Graphics;
}

interface EffectItem {
  node: Graphics | Text;
  createdAt: number;
  ttlMs: number;
}

interface LivePixiBattlefieldRenderer {
  setVisualState: (state: VisualState) => void;
  setSelectedUnit: (unitId: string | null) => void;
  setEventHighlights: (events: ReplayEvent[]) => void;
  update: (nowMs?: number) => void;
  resize: () => void;
  destroy: () => void;
  setDebugOverlay: (enabled: boolean) => void;
}

export const createLivePixiBattlefieldRenderer = (
  container: HTMLDivElement,
  options: LivePixiOptions,
): LivePixiBattlefieldRenderer => {
  const app = new Application();
  container.replaceChildren();

  const root = new Container();
  const unitLayer = new Container();
  const effectLayer = new Container();
  const effectLabelLayer = new Container();
  const debugLayer = new Container();
  debugLayer.visible = options.debugOverlay;
  root.addChild(unitLayer, effectLayer, effectLabelLayer, debugLayer);
  app.stage.addChild(root);

  const units = new Map<string, UnitSprite>();
  let selectedUnitId: string | null = null;
  let latestState: VisualState | null = null;
  let initialized = false;
  let destroyed = false;
  const effectNodes: EffectItem[] = [];
  const nowMs = (): number => (typeof performance !== "undefined" ? performance.now() : Date.now());

  void app.init({
    width: CANVAS_WIDTH,
    height: CANVAS_HEIGHT,
    autoStart: false,
    antialias: true,
  }).then(() => {
    if (destroyed) {
      return;
    }
    app.stage.sortableChildren = true;
    container.replaceChildren();
    container.appendChild(app.canvas);
    initialized = true;
    resize();
  }).catch(() => {
    destroyed = true;
  });

  const setVisualState = (state: VisualState): void => {
    latestState = state;
    const nextUnits = new Set<string>();
    for (const unit of state.units.values()) {
      nextUnits.add(unit.instanceId);
      const sprite = units.get(unit.instanceId) ?? createUnitSprite(unit, options.onSelectUnit);
      units.set(unit.instanceId, sprite);
      updateUnitSprite(sprite, unit, unit.instanceId === selectedUnitId);
      if (!unitLayer.children.includes(sprite.container)) {
        unitLayer.addChild(sprite.container);
      }
    }
    for (const [unitId, sprite] of units.entries()) {
      if (!nextUnits.has(unitId)) {
        unitLayer.removeChild(sprite.container);
        units.delete(unitId);
      }
    }
    if (options.debugOverlay) {
      debugLayer.removeChildren();
      for (const unit of state.units.values()) {
        const anchorDot = new Graphics();
        anchorDot.beginFill(unit.side === "ally" ? 0x2f80ed : 0xd94a4a, 0.4);
        anchorDot.drawCircle(unit.formationAnchorX, unit.formationAnchorY, 4);
        anchorDot.endFill();
        debugLayer.addChild(anchorDot);

        if (unit.engagementTarget) {
          const target = state.units.get(unit.engagementTarget);
          if (target) {
            const line = new Graphics();
            line.lineStyle(1, 0xf6e27a, 0.35);
            line.moveTo(unit.positionX, unit.positionY);
            line.lineTo(target.positionX, target.positionY);
            debugLayer.addChild(line);
          }
        }

        if (unit.engagementRole === "ranged" && unit.desiredDistance > 0) {
          const circle = new Graphics();
          circle.lineStyle(1, 0x6d93d2, 0.25);
          circle.drawCircle(unit.positionX, unit.positionY, unit.desiredDistance);
          debugLayer.addChild(circle);
        }
      }
    }
  };

  const setSelectedUnit = (unitId: string | null): void => {
    selectedUnitId = unitId;
    for (const [candidateId, sprite] of units.entries()) {
      const selected = candidateId === unitId;
      sprite.selectionRing.visible = selected;
      sprite.nameText.style.fill = selected ? 0x1b4f72 : 0xffffff;
    }
  };

  const setEventHighlights = (events: ReplayEvent[]): void => {
    if (!latestState) {
      return;
    }
    for (const effect of events) {
      if (!isVisualEffectCandidate(effect.type)) {
        continue;
      }
      createEffectFromEvent(effect, latestState);
    }
  };

  const resize = (): void => {
    if (!initialized) {
      return;
    }
    const bounds = container.getBoundingClientRect();
    const width = Math.max(200, Math.floor(bounds.width));
    const height = Math.max(220, Math.floor(bounds.height));
    app.renderer.resize(width, height);
    const scale = Math.min(width / CANVAS_WIDTH, height / CANVAS_HEIGHT, 1);
    root.scale.set(scale);
    root.position.set((width - CANVAS_WIDTH * scale) / 2 / scale, (height - CANVAS_HEIGHT * scale) / 2 / scale);
  };

  const update = (timestamp = nowMs()): void => {
    if (!initialized) {
      return;
    }
    clearExpired(timestamp);
    if (latestState === null) {
      return;
    }
    for (const unit of latestState.units.values()) {
      const sprite = units.get(unit.instanceId);
      if (!sprite) {
        continue;
      }
      updateUnitSprite(sprite, unit, unit.instanceId === selectedUnitId);
    }
  };

  const destroy = (): void => {
    destroyed = true;
    window.removeEventListener("resize", resize);
    for (const sprite of units.values()) {
      unitLayer.removeChild(sprite.container);
      sprite.body.destroy();
      sprite.hpBg.destroy();
      sprite.hpFill.destroy();
      sprite.hpText.destroy();
      sprite.actionBarBg.destroy();
      sprite.actionBarFill.destroy();
      sprite.actionText.destroy();
      sprite.statusText.destroy();
      sprite.cooldownText.destroy();
      sprite.nameText.destroy();
      sprite.selectionRing.destroy();
    }
    for (const effect of effectNodes) {
      effect.node.destroy();
    }
    effectNodes.length = 0;
    units.clear();
    app.destroy();
    container.replaceChildren();
  };

  const createUnitSprite = (unit: VisualUnit, onSelectUnit: (unitId: string) => void): UnitSprite => {
    const group = new Container();
    group.eventMode = "static";
    group.cursor = "pointer";
    group.on("pointerdown", (event: FederatedPointerEvent) => {
      event.stopPropagation();
      onSelectUnit(unit.instanceId);
    });

    const nameText = new Text({ text: unit.instanceId, style: { fill: 0xffffff, fontSize: 10 } });
    const statusText = new Text({ text: "", style: { fill: 0xffffff, fontSize: 8 } });
    const cooldownText = new Text({ text: "", style: { fill: 0xffff77, fontSize: 8 } });
    const hpBg = new Graphics();
    const hpFill = new Graphics();
    const hpText = new Text({ text: `${unit.hp}/${unit.maxHp}`, style: { fill: 0xe6f5ee, fontSize: 8 } });
    const actionBarBg = new Graphics();
    const actionBarFill = new Graphics();
    const actionText = new Text({ text: "Action -", style: { fill: 0xdbebff, fontSize: 7 } });
    const body = new Graphics();
    const selectionRing = new Graphics();

    group.addChild(selectionRing, body, hpBg, hpFill, hpText, actionBarBg, actionBarFill, actionText, statusText, cooldownText, nameText);
    updateUnitSprite({
      container: group,
      body,
      hpBg,
      hpFill,
      hpText,
      actionBarBg,
      actionBarFill,
      actionText,
      statusText,
      cooldownText,
      nameText,
      selectionRing,
    }, unit, unit.instanceId === selectedUnitId);
    return {
      container: group,
      body,
      hpBg,
      hpFill,
      hpText,
      actionBarBg,
      actionBarFill,
      actionText,
      statusText,
      cooldownText,
      nameText,
      selectionRing,
    };
  };

  const updateUnitSprite = (sprite: UnitSprite, unit: VisualUnit, selected: boolean): void => {
    const sideColor = unit.side === "enemy" ? ENEMY_COLOR : ALLY_COLOR;
    const x = unit.positionX;
    const y = unit.positionY;
    sprite.container.x = x;
    sprite.container.y = y;
    const centerX = 0;
    const centerY = 0;

    const style = resolveTroopShape(unit.unitDefId, unit.role, unit.tags, []);
    drawUnitShape(sprite.body, style.shape, centerX, centerY, UNIT_WIDTH, UNIT_HEIGHT, sideColor, unit.alive);

    sprite.selectionRing.clear();
    if (selected) {
      sprite.selectionRing.lineStyle(2, 0xf6e27a, 1);
      sprite.selectionRing.drawRoundedRect(-UNIT_WIDTH / 2 - 4, -UNIT_HEIGHT / 2 - 4, UNIT_WIDTH + 8, UNIT_HEIGHT + 8, 6);
    }
    sprite.selectionRing.visible = selected;

    const hpRatio = unit.maxHp > 0 ? Math.max(0, Math.min(1, unit.hp / unit.maxHp)) : 0;
    const hpWidth = UNIT_WIDTH - 10;
    const hpX = centerX - UNIT_WIDTH / 2 + 5;
    const hpY = centerY + UNIT_HEIGHT / 2 - 10;
    sprite.hpBg.clear();
    sprite.hpBg.beginFill(0x20322d);
    sprite.hpBg.drawRect(hpX, hpY, hpWidth, 6);
    sprite.hpBg.endFill();
    sprite.hpFill.clear();
    sprite.hpFill.beginFill(unit.alive ? 0x2bbd67 : DEATH_COLOR);
    sprite.hpFill.drawRect(hpX, hpY, hpWidth * hpRatio, 6);
    sprite.hpFill.endFill();
    sprite.hpText.x = centerX - 10;
    sprite.hpText.y = hpY - 10;
    sprite.hpText.text = `${unit.hp}/${unit.maxHp}`;

    const actionRatio = actionIndicatorRatio(unit);
    const actionBarY = hpY + 8;
    const actionBarWidth = hpWidth * actionRatio;
    sprite.actionBarBg.clear();
    sprite.actionBarBg.beginFill(0x1a2a24);
    sprite.actionBarBg.drawRect(hpX, actionBarY, hpWidth, 4);
    sprite.actionBarBg.endFill();
    sprite.actionBarFill.clear();
    if (unit.alive && actionRatio > 0) {
      sprite.actionBarFill.beginFill(0x3b82bf);
      sprite.actionBarFill.drawRect(hpX, actionBarY, actionBarWidth, 4);
      sprite.actionBarFill.endFill();
    }

    const actionTextY = hpY + 10;
    sprite.actionText.x = centerX - UNIT_WIDTH / 2;
    sprite.actionText.y = actionTextY;
    sprite.actionText.text = actionText(unit);

    const metaY = actionBarY + 10;
    sprite.statusText.x = centerX - UNIT_WIDTH / 2 + 4;
    sprite.statusText.y = metaY;
    const statusCount = unit.statuses.filter((status) => status.active).length;
    sprite.statusText.text = `Status（状态）${statusCount}`;
    const cooldownCount = unit.skillCooldowns.size;
    sprite.cooldownText.x = centerX + 8;
    sprite.cooldownText.y = metaY;
    sprite.cooldownText.text = `Cooldown（冷却）${cooldownCount}`;

    sprite.nameText.x = centerX - UNIT_WIDTH / 2;
    sprite.nameText.y = -UNIT_HEIGHT / 2 - 12;
    sprite.nameText.text = `${unit.instanceId}\n${style.label}`;

    const alpha = unit.alive ? 1 : 0.45;
    sprite.container.alpha = alpha;
    if (unit.alive) {
      sprite.container.tint = 0xffffff;
    }
  };

  const clearExpired = (timestamp: number): void => {
    for (let i = effectNodes.length - 1; i >= 0; i -= 1) {
      const effect = effectNodes[i];
      if (timestamp - effect.createdAt > effect.ttlMs) {
        effect.node.destroy();
        effectNodes.splice(i, 1);
      }
    }
  };

  const createEffectFromEvent = (event: ReplayEvent, state: VisualState): void => {
    switch (event.type) {
      case "attack": {
        const payload = event.payload as Record<string, unknown>;
        const attacker = payload.attacker ?? payload.source;
        createAttackLine(attacker, event.payload.target, state);
        break;
      }
      case "damage":
        if (typeof event.payload.amount === "number") {
          createFloatingText(`-${event.payload.amount}`, event.payload.target, state);
        }
        break;
      case "skill_trigger":
        createSkillCallout(event.payload.source, event.payload.skill as string, state);
        break;
      case "status_apply":
        createStatusBadge(event.payload.target, "S+", state);
        break;
      case "status_expire":
        createStatusBadge(event.payload.target, "SE", state);
        break;
      case "skill_cooldown":
        createCooldownBadge(event.payload.source, `${event.payload.ready_tick}`, state);
        break;
      case "battle_end":
        createVictoryBanner(event.payload.winner, state.currentTick);
        break;
      case "death":
        if (typeof event.payload.unit === "string") {
          createDeathMarker(event.payload.unit, state);
        }
        break;
      default:
        break;
    }
  };

  const createAttackLine = (source: unknown, target: unknown, state: VisualState): void => {
    if (typeof source !== "string" || typeof target !== "string") {
      return;
    }
    const sourceUnit = state.units.get(source);
    const targetUnit = state.units.get(target);
    if (!sourceUnit || !targetUnit) {
      return;
    }
    const line = new Graphics();
    line.lineStyle(3, 0xc64545, 1);
    line.moveTo(sourceUnit.positionX, sourceUnit.positionY);
    line.lineTo(targetUnit.positionX, targetUnit.positionY);
    line.closePath();
    effectLayer.addChild(line);
    effectNodes.push({ node: line, createdAt: nowMs(), ttlMs: 700 });
  };

  const createFloatingText = (text: string, target: unknown, state: VisualState): void => {
    if (typeof target !== "string") {
      return;
    }
    const unit = state.units.get(target);
    if (!unit) {
      return;
    }
    const label = new Text({
      text,
      style: {
        fill: 0xffce5a,
        fontSize: 14,
        fontWeight: "bold",
      },
    });
    label.x = unit.positionX + 10;
    label.y = unit.positionY - 24;
    effectLabelLayer.addChild(label);
    effectNodes.push({ node: label, createdAt: nowMs(), ttlMs: 800 });
  };

  const createSkillCallout = (unitId: unknown, skill: unknown, state: VisualState): void => {
    if (typeof unitId !== "string" || typeof skill !== "string") {
      return;
    }
    const unit = state.units.get(unitId);
    if (!unit) {
      return;
    }
    const label = new Text({
      text: String(skill),
      style: {
        fill: 0x8fcbff,
        fontSize: 12,
        fontWeight: "bold",
      },
    });
    label.x = unit.positionX - 6;
    label.y = unit.positionY - UNIT_HEIGHT / 2 - 22;
    effectLabelLayer.addChild(label);
    effectNodes.push({ node: label, createdAt: nowMs(), ttlMs: 900 });
  };

  const createStatusBadge = (unitId: unknown, labelText: string, state: VisualState): void => {
    if (typeof unitId !== "string") {
      return;
    }
    const unit = state.units.get(unitId);
    if (!unit) {
      return;
    }
    const badge = new Graphics();
    badge.beginFill(0x6d93d2);
    badge.drawCircle(unit.positionX - 18, unit.positionY - 16, 9);
    badge.endFill();
    const badgeText = new Text({ text: labelText, style: { fill: 0xffffff, fontSize: 7 } });
    badgeText.x = unit.positionX - 18 - 4;
    badgeText.y = unit.positionY - 18;
    effectLayer.addChild(badge);
    effectLabelLayer.addChild(badgeText);
    effectNodes.push({ node: badge, createdAt: nowMs(), ttlMs: 900 });
    effectNodes.push({ node: badgeText, createdAt: nowMs(), ttlMs: 900 });
  };

  const createCooldownBadge = (unitId: unknown, text: string, state: VisualState): void => {
    if (typeof unitId !== "string") {
      return;
    }
    const unit = state.units.get(unitId);
    if (!unit) {
      return;
    }
    const badge = new Graphics();
    badge.beginFill(0x6f4a10);
    badge.drawRect(unit.positionX + 14, unit.positionY - 18, 22, 12);
    badge.endFill();
    const label = new Text({
      text,
      style: {
        fill: 0xfff3bf,
        fontSize: 7,
      },
    });
    label.x = unit.positionX + 15;
    label.y = unit.positionY - 17;
    effectLabelLayer.addChild(label);
    effectLayer.addChild(badge);
    effectNodes.push({ node: badge, createdAt: nowMs(), ttlMs: 900 });
    effectNodes.push({ node: label, createdAt: nowMs(), ttlMs: 900 });
  };

  const createDeathMarker = (unitId: string, state: VisualState): void => {
    const unit = state.units.get(unitId);
    if (!unit) {
      return;
    }
    const marker = new Graphics();
    marker.lineStyle(3, DEATH_COLOR, 1);
    marker.moveTo(unit.positionX - 12, unit.positionY - 12);
    marker.lineTo(unit.positionX + 12, unit.positionY + 12);
    marker.moveTo(unit.positionX + 12, unit.positionY - 12);
    marker.lineTo(unit.positionX - 12, unit.positionY + 12);
    effectLayer.addChild(marker);
    effectNodes.push({ node: marker, createdAt: nowMs(), ttlMs: 2000 });
  };

  const createVictoryBanner = (winner: unknown, tick: number): void => {
    const message = new Text({
      text: `Victory（胜负） ${winner ?? "-"} @ T${tick}`,
      style: {
        fill: 0xffe29a,
        fontSize: 16,
        fontWeight: "bold",
      },
    });
    message.x = 60;
    message.y = 20;
    effectLabelLayer.addChild(message);
    effectNodes.push({ node: message, createdAt: nowMs(), ttlMs: 2000 });
  };

  resize();
  window.addEventListener("resize", resize);

  return {
    setVisualState,
    setSelectedUnit,
    setEventHighlights,
    update,
    resize,
    destroy,
    setDebugOverlay: (enabled: boolean) => {
      options.debugOverlay = enabled;
      debugLayer.visible = enabled;
      if (latestState) {
        setVisualState(latestState);
      }
    },
  };
};

const drawUnitShape = (
  graphics: Graphics,
  shape: TroopShape,
  x: number,
  y: number,
  width: number,
  height: number,
  baseColor: number,
  alive: boolean,
): void => {
  graphics.clear();
  graphics.beginFill(alive ? baseColor : DEATH_COLOR, 0.82);
  const radius = Math.min(width, height) / 5;
  const halfW = width / 2;
  const halfH = height / 2;

  if (shape === "circle") {
    graphics.drawEllipse(x, y, halfW * 0.8, halfH * 0.9);
  } else if (shape === "square") {
    graphics.drawRect(x - halfW, y - halfH, width, height);
  } else if (shape === "triangle") {
    graphics.moveTo(x, y - halfH);
    graphics.lineTo(x + halfW, y + halfH);
    graphics.lineTo(x - halfW, y + halfH);
    graphics.lineTo(x, y - halfH);
  } else if (shape === "diamond") {
    graphics.moveTo(x, y - halfH);
    graphics.lineTo(x + halfW, y);
    graphics.lineTo(x, y + halfH);
    graphics.lineTo(x - halfW, y);
    graphics.lineTo(x, y - halfH);
  } else if (shape === "hexagon") {
    const radiusX = halfW * 0.78;
    const radiusY = halfH * 0.9;
    for (let index = 0; index < 6; index += 1) {
      const angle = (Math.PI / 3) * index - Math.PI / 6;
      const px = x + radiusX * Math.cos(angle);
      const py = y + radiusY * Math.sin(angle);
      if (index === 0) {
        graphics.moveTo(px, py);
      } else {
        graphics.lineTo(px, py);
      }
    }
    graphics.closePath();
  } else {
    graphics.drawRoundedRect(x - halfW, y - halfH, width, height, radius);
  }
  graphics.endFill();
  graphics.lineStyle(1, baseColor, 1);
  graphics.drawRect(x - halfW - 2, y - halfH - 2, width + 4, height + 4);
};

const actionText = (unit: VisualUnit): string => {
  const actionTick = unit.nextActionTick;
  const actionInterval = unit.actionIntervalTicks;
  if (actionTick === null) {
    return "Next Action（下次行动） -";
  }
  if (actionInterval === null) {
    return `Next Action（下次行动）: ${actionTick}`;
  }
  return `Next Action（下次行动）: ${actionTick}/${actionInterval}`;
};

const actionIndicatorRatio = (unit: VisualUnit): number => {
  if (unit.nextActionTick === null || unit.actionIntervalTicks === null || unit.actionIntervalTicks <= 0) {
    return 0;
  }
  const start = Math.max(0, unit.nextActionTick - unit.actionIntervalTicks);
  const now = unit.actionIntervalTicks > 0
    ? Math.max(0, Math.min(unit.actionIntervalTicks, (unit.lastActionSchedule?.nextActionTick ?? unit.nextActionTick) - start))
    : 0;
  return now / unit.actionIntervalTicks;
};

const isVisualEffectCandidate = (eventType: string): boolean => {
  return [
    "attack",
    "damage",
    "skill_trigger",
    "status_apply",
    "status_expire",
    "skill_cooldown",
    "battle_end",
    "death",
  ].includes(eventType);
};
