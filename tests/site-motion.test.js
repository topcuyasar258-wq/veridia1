const assert = require("node:assert/strict");
const test = require("node:test");

const motion = require("../assets/site-motion.js");
const story = require("../assets/site-motion-story.js");

class FakeClassList {
  constructor() {
    this.values = new Set();
  }

  add(...names) {
    names.forEach((name) => this.values.add(name));
  }

  remove(...names) {
    names.forEach((name) => this.values.delete(name));
  }

  contains(name) {
    return this.values.has(name);
  }

  toggle(name, force) {
    if (force === undefined ? !this.contains(name) : force) {
      this.add(name);
      return true;
    }

    this.remove(name);
    return false;
  }
}

class FakeStyle {
  constructor() {
    this.values = new Map();
  }

  setProperty(name, value) {
    this.values.set(name, value);
  }

  getPropertyValue(name) {
    return this.values.get(name) || "";
  }

  removeProperty(name) {
    this.values.delete(name);
  }
}

class FakeElement {
  constructor(
    name,
    {
      card = false,
      legacy = false,
      unavailable = false,
      rect = { left: 10, top: 20, bottom: 120 },
    } = {},
  ) {
    this.name = name;
    this.isCard = card;
    this.legacy = legacy;
    this.unavailable = unavailable;
    this.rect = rect;
    this.parentElement = null;
    this.children = [];
    this.classList = new FakeClassList();
    this.style = new FakeStyle();
    this.dataset = {};
    this.attributes = new Map();
    this.listeners = new Map();
    this.queryResults = new Map();
    this.isConnected = true;
  }

  matches(selector) {
    if (selector === ".reveal") {
      return this.legacy;
    }

    return selector === motion.SELECTORS.card && this.isCard;
  }

  closest(selector) {
    if (selector === ".reveal") {
      if (this.legacy) {
        return this;
      }

      return this.parentElement ? this.parentElement.closest(selector) : null;
    }

    if (selector.includes("[hidden]")) {
      if (this.unavailable) {
        return this;
      }

      return this.parentElement ? this.parentElement.closest(selector) : null;
    }

    return null;
  }

  contains(candidate) {
    let current = candidate;
    while (current) {
      if (current === this) {
        return true;
      }
      current = current.parentElement;
    }
    return false;
  }

  querySelectorAll(selector) {
    return this.queryResults.get(selector) || [];
  }

  querySelector(selector) {
    return this.querySelectorAll(selector)[0] || null;
  }

  appendChild(child) {
    child.parentElement = this;
    child.isConnected = true;
    this.children.push(child);
    return child;
  }

  setAttribute(name, value) {
    this.attributes.set(name, value);
  }

  addEventListener(type, listener) {
    this.listeners.set(type, listener);
  }

  removeEventListener(type) {
    this.listeners.delete(type);
  }

  dispatch(type, event = {}) {
    const listener = this.listeners.get(type);
    if (listener) {
      listener(event);
    }
  }

  getBoundingClientRect() {
    return this.rect;
  }

  remove() {
    if (this.parentElement) {
      this.parentElement.children = this.parentElement.children.filter(
        (child) => child !== this,
      );
    }
    this.parentElement = null;
    this.isConnected = false;
  }
}

class FakeMediaQuery {
  constructor(matches) {
    this.matches = matches;
    this.listeners = new Map();
  }

  addEventListener(type, listener) {
    this.listeners.set(type, listener);
  }

  removeEventListener(type) {
    this.listeners.delete(type);
  }

  change(matches) {
    this.matches = matches;
    const listener = this.listeners.get("change");
    if (listener) {
      listener({ matches });
    }
  }
}

function createEnvironment({
  canvas2d = false,
  reduced = false,
  finePointer = true,
  scrambleViewport = true,
  saveData = false,
  intersectionObserver = true,
  sectionTop = 1100,
  legacyTop = 1180,
} = {}) {
  const root = new FakeElement("html");
  root.clientHeight = 720;
  const hero = new FakeElement("hero", {
    rect: { left: 10, top: 0, bottom: 320 },
  });
  const heroLabel = new FakeElement("hero-label");
  const heroTitle = new FakeElement("hero-title");
  const section = new FakeElement("section", {
    rect: { left: 10, top: sectionTop, bottom: sectionTop + 320 },
  });
  const cardParent = new FakeElement("card-parent");
  const card = new FakeElement("card", { card: true });
  const legacyCard = new FakeElement("legacy-card", {
    card: true,
    legacy: true,
    rect: { left: 10, top: legacyTop, bottom: legacyTop + 220 },
  });
  const hiddenCard = new FakeElement("hidden-card", {
    card: true,
    unavailable: true,
  });
  const cta = new FakeElement("cta");
  const link = new FakeElement("link");

  hero.appendChild(heroLabel);
  hero.appendChild(heroTitle);
  cardParent.appendChild(card);
  cardParent.appendChild(legacyCard);
  cardParent.appendChild(hiddenCard);

  const documentListeners = new Map();
  const queryCounts = new Map();
  const document = {
    documentElement: root,
    visibilityState: "visible",
    querySelector(selector) {
      return selector === motion.SELECTORS.hero ? hero : null;
    },
    querySelectorAll(selector) {
      queryCounts.set(selector, (queryCounts.get(selector) || 0) + 1);
      const results = new Map([
        [motion.SELECTORS.card, [card, legacyCard, hiddenCard]],
        [motion.SELECTORS.section, [hero, section]],
        [motion.SELECTORS.cta, [cta]],
        [motion.SELECTORS.link, [link]],
        [".reveal", [legacyCard]],
        [".reveal .reveal", []],
      ]);
      return results.get(selector) || [];
    },
    createElement(name) {
      const element = new FakeElement(name);
      if (name === "canvas" && canvas2d) {
        element.getContext = (type) =>
          type === "2d"
            ? {
                setTransform() {},
              }
            : null;
      }
      return element;
    },
    addEventListener(type, listener) {
      if (!documentListeners.has(type)) {
        documentListeners.set(type, new Set());
      }
      documentListeners.get(type).add(listener);
    },
    removeEventListener(type, listener) {
      const listeners = documentListeners.get(type);
      if (listeners) {
        listeners.delete(listener);
      }
    },
  };

  const reducedQuery = new FakeMediaQuery(reduced);
  const finePointerQuery = new FakeMediaQuery(finePointer);
  const scrambleViewportQuery = new FakeMediaQuery(scrambleViewport);
  const animationFrames = new Map();
  let nextFrame = 1;
  const observers = [];

  class FakeIntersectionObserver {
    constructor(callback, options) {
      this.callback = callback;
      this.options = options;
      this.observed = new Set();
      this.unobserved = new Set();
      this.disconnected = false;
      observers.push(this);
    }

    observe(target) {
      this.observed.add(target);
    }

    unobserve(target) {
      this.unobserved.add(target);
      this.observed.delete(target);
    }

    disconnect() {
      this.disconnected = true;
      this.observed.clear();
    }

    intersect(target, isIntersecting = true) {
      this.callback([{ target, isIntersecting }]);
    }
  }

  const global = {
    document,
    innerHeight: 720,
    navigator: { connection: { saveData } },
    matchMedia(query) {
      if (query.includes("prefers-reduced-motion")) {
        return reducedQuery;
      }

      if (query.includes("min-width")) {
        return scrambleViewportQuery;
      }

      return finePointerQuery;
    },
    requestAnimationFrame(callback) {
      const frame = nextFrame;
      nextFrame += 1;
      animationFrames.set(frame, callback);
      return frame;
    },
    cancelAnimationFrame(frame) {
      animationFrames.delete(frame);
    },
  };
  if (intersectionObserver) {
    global.IntersectionObserver = FakeIntersectionObserver;
  }

  return {
    global,
    root,
    hero,
    heroLabel,
    heroTitle,
    section,
    card,
    legacyCard,
    hiddenCard,
    cta,
    link,
    reducedQuery,
    scrambleViewportQuery,
    queryCounts,
    observers,
    pendingAnimationFrames() {
      return animationFrames.size;
    },
    flushAnimationFrames() {
      while (animationFrames.size) {
        const queued = Array.from(animationFrames.values());
        animationFrames.clear();
        queued.forEach((callback) => callback());
      }
    },
    setVisibility(value) {
      document.visibilityState = value;
      const listeners = documentListeners.get("visibilitychange");
      if (listeners) {
        listeners.forEach((listener) => listener());
      }
    },
  };
}

test("stagger delay is sanitized and capped", () => {
  assert.equal(motion.cappedStaggerDelay(0), 0);
  assert.equal(
    motion.cappedStaggerDelay(2),
    motion.POLICY.staggerStepMs * 2,
  );
  assert.equal(
    motion.cappedStaggerDelay(999),
    motion.POLICY.staggerMaxMs,
  );
  assert.equal(motion.cappedStaggerDelay(-2), 0);
  assert.equal(motion.cappedStaggerDelay("not-a-number"), 0);
});

test("scramble timing is scattered, sanitized, and capped", () => {
  assert.equal(motion.scrambleDelay(0), 0);
  assert.equal(motion.scrambleDelay(1), motion.POLICY.scrambleColumnStepMs);
  assert.equal(
    motion.scrambleDelay(motion.POLICY.scrambleColumns),
    motion.POLICY.scrambleRowStepMs,
  );
  assert.equal(motion.scrambleDelay(-5), 0);
  assert.equal(motion.scrambleDelay("invalid"), 0);
  assert.ok(
    motion.scrambleDelay(999) <= motion.POLICY.scrambleDelayMaxMs,
  );
});

test("scramble glyphs resolve to the original copy without changing whitespace", () => {
  assert.equal(motion.selectScrambleGlyph(" ", 0.2, 0.5), " ");
  assert.equal(motion.selectScrambleGlyph("\n", 0.8, 0.5), "\n");
  assert.equal(motion.selectScrambleGlyph("V", 1, 0.2), "V");
  assert.equal(motion.selectScrambleGlyph("V", 2, 0.2), "V");

  const glyph = motion.selectScrambleGlyph("V", 0.4, 0.25);
  assert.equal(glyph.length, 1);
  assert.ok(motion.POLICY.scrambleGlyphs.includes(glyph));
  assert.notEqual(glyph, " ");
});

test("sphere points are deterministic, normalized, and newly allocated", () => {
  const first = motion.createSpherePoints(24);
  const second = motion.createSpherePoints(24);

  assert.equal(first.length, 24);
  assert.deepEqual(first, second);
  assert.notEqual(first, second);
  first.forEach((point) => {
    const radius = Math.hypot(point.x, point.y, point.z);
    assert.ok(Math.abs(radius - 1) < 0.000001);
  });
  assert.deepEqual(motion.createSpherePoints(-2), []);
  assert.deepEqual(motion.createSpherePoints("invalid"), []);
});

test("canvas backing store stays inside its memory budget", () => {
  assert.deepEqual(
    motion.calculateCanvasBackingStore(1000, 600, 1.5),
    { height: 900, scale: 1.5, width: 1500 },
  );

  const huge = motion.calculateCanvasBackingStore(100000, 100000, 1.5);
  assert.ok(huge.width <= motion.POLICY.globeMaxBackingWidth);
  assert.ok(huge.height <= motion.POLICY.globeMaxBackingHeight);
  assert.ok(
    huge.width * huge.height <= motion.POLICY.globeMaxBackingPixels,
  );
  assert.ok(Number.isFinite(huge.scale));
  assert.ok(huge.scale > 0);

  assert.deepEqual(
    motion.calculateCanvasBackingStore(Infinity, Number.NaN, 2),
    { height: 1, scale: 1, width: 1 },
  );
});

test("scramble character counting excludes whitespace", () => {
  assert.equal(motion.countScrambleCharacters("Veridia\n Ajans"), 12);
  assert.equal(motion.countScrambleCharacters(null), 0);
});

test("sticky story progress is finite, clamped, and reversible", () => {
  assert.equal(story.calculateStickyProgress(100, 3600, 900, 100), 0);
  assert.equal(story.calculateStickyProgress(-1250, 3600, 900, 100), 0.5);
  assert.equal(story.calculateStickyProgress(-2600, 3600, 900, 100), 1);
  assert.equal(story.calculateStickyProgress(500, 3600, 900, 100), 0);
  assert.equal(story.calculateStickyProgress(-4000, 3600, 900, 100), 1);
  assert.equal(story.calculateStickyProgress(0, 0, 0, 0), 0);
  assert.equal(
    story.calculateStickyProgress(Infinity, Number.NaN, 900, 0),
    0,
  );
});

test("story timeline moves focus, changes copy, and fractures at the exit", () => {
  const start = story.resolveStoryTimeline(0);
  assert.equal(start.activeScene, 0);
  assert.equal(start.focus, 0);
  assert.equal(start.fracture, 0);
  assert.equal(start.exit, 0);
  assert.equal(start.opacities[0], 1);

  const middle = story.resolveStoryTimeline(0.44);
  assert.equal(middle.activeScene, 1);
  assert.ok(middle.focus > 0.85);
  assert.equal(middle.fracture, 0);
  assert.ok(middle.opacities[1] > 0.9);

  const finalCopy = story.resolveStoryTimeline(0.7);
  assert.equal(finalCopy.activeScene, 2);
  assert.equal(finalCopy.focus, 1);
  assert.equal(finalCopy.fracture, 0);
  assert.ok(finalCopy.opacities[2] > 0.9);

  const fracture = story.resolveStoryTimeline(0.9);
  assert.equal(fracture.activeScene, 2);
  assert.ok(fracture.fracture > 0);
  assert.ok(fracture.fracture < 1);

  const lateExit = story.resolveStoryTimeline(0.98);
  assert.equal(lateExit.activeScene, 2);
  assert.ok(lateExit.opacities[2] > 0.5);

  const end = story.resolveStoryTimeline(1);
  assert.equal(end.activeScene, -1);
  assert.equal(end.fracture, 1);
  assert.equal(end.exit, 1);

  for (let step = -10; step <= 110; step += 1) {
    const state = story.resolveStoryTimeline(step / 100);
    assert.ok([-1, 0, 1, 2].includes(state.activeScene));
    [
      state.progress,
      state.focus,
      state.fracture,
      state.exit,
      ...state.opacities,
    ].forEach((value) => {
      assert.ok(Number.isFinite(value));
      assert.ok(value >= 0 && value <= 1);
    });
  }
});

test("sphere fracture is deterministic, monotonic, and immutable", () => {
  const point = Object.freeze({ x: 0.4, y: -0.2, z: 0.8 });
  const intact = story.fractureSpherePoint(point, 12, 0);
  const halfway = story.fractureSpherePoint(point, 12, 0.5);
  const fractured = story.fractureSpherePoint(point, 12, 1);

  assert.deepEqual(intact, point);
  assert.notEqual(intact, point);
  assert.deepEqual(
    fractured,
    story.fractureSpherePoint(point, 12, 1),
  );

  const distance = (candidate) =>
    Math.hypot(
      candidate.x - point.x,
      candidate.y - point.y,
      candidate.z - point.z,
    );
  assert.ok(distance(halfway) > 0);
  assert.ok(distance(fractured) > distance(halfway));
  assert.deepEqual(point, { x: 0.4, y: -0.2, z: 0.8 });
});

test("reduced motion includes both media preference and save-data", () => {
  assert.equal(motion.shouldReduceMotion(false, false), false);
  assert.equal(motion.shouldReduceMotion(true, false), true);
  assert.equal(motion.shouldReduceMotion({ matches: true }, false), true);
  assert.equal(motion.shouldReduceMotion({ matches: false }, true), true);
});

test("init is a no-op without a browser document", () => {
  assert.doesNotThrow(() => motion.init()());
  assert.doesNotThrow(() => motion.init({})());
});

test("reduced-motion preference leaves the page static from startup", () => {
  const environment = createEnvironment({ reduced: true });
  const cleanup = motion.init(environment.global);

  assert.equal(environment.root.dataset.vMotion, "static");
  assert.equal(environment.root.dataset.vMotionInitialized, "true");
  assert.equal(environment.root.classList.contains("v-motion-enabled"), false);
  assert.equal(environment.observers.length, 0);
  assert.equal(environment.card.classList.contains("v-motion-reveal"), false);
  assert.doesNotThrow(cleanup);
});

test("normal init only stages below-the-fold sections, preserves cards, and cleans up", () => {
  const environment = createEnvironment();
  const cleanup = motion.init(environment.global);

  assert.equal(environment.root.dataset.vMotion, "ready");
  assert.equal(environment.root.classList.contains("v-motion-enabled"), true);
  assert.equal(environment.hero.classList.contains("v-motion-hero"), true);
  assert.equal(environment.card.classList.contains("v-motion-card"), true);
  assert.equal(environment.card.classList.contains("v-motion-reveal"), false);
  assert.equal(environment.section.classList.contains("v-motion-reveal"), true);
  assert.equal(environment.legacyCard.classList.contains("v-motion-card"), true);
  assert.equal(
    environment.legacyCard.classList.contains("v-motion-reveal"),
    true,
  );
  assert.equal(environment.hiddenCard.classList.contains("v-motion-card"), false);
  assert.equal(environment.cta.classList.contains("v-motion-cta"), true);
  assert.equal(environment.link.classList.contains("v-motion-link"), true);
  assert.equal(environment.observers.length, 1);

  const observer = environment.observers[0];
  observer.intersect(environment.section, false);
  assert.equal(environment.section.classList.contains("is-visible"), false);
  observer.intersect(environment.section);
  assert.equal(environment.section.classList.contains("is-visible"), true);
  assert.equal(observer.unobserved.has(environment.section), true);

  environment.card.dispatch("pointermove", { clientX: 45, clientY: 70 });
  environment.card.dispatch("pointermove", { clientX: 45, clientY: 70 });
  environment.flushAnimationFrames();
  assert.equal(environment.card.style.getPropertyValue("--v-motion-x"), "35px");
  assert.equal(environment.card.style.getPropertyValue("--v-motion-y"), "50px");
  environment.card.dispatch("pointerleave");
  assert.equal(environment.card.style.getPropertyValue("--v-motion-x"), "50%");

  environment.setVisibility("hidden");
  assert.equal(environment.root.classList.contains("v-motion-paused"), true);
  environment.setVisibility("visible");
  assert.equal(environment.root.classList.contains("v-motion-paused"), false);

  cleanup();
  assert.equal(environment.root.classList.contains("v-motion-enabled"), false);
  assert.equal(environment.root.dataset.vMotion, undefined);
  assert.equal(observer.disconnected, true);
  assert.equal(environment.hero.classList.contains("v-motion-hero"), false);
  assert.equal(environment.card.classList.contains("v-motion-card"), false);
  assert.equal(environment.cta.classList.contains("v-motion-cta"), false);
  assert.equal(environment.link.classList.contains("v-motion-link"), false);
  assert.equal(environment.section.classList.contains("v-motion-reveal"), false);
  assert.equal(environment.section.classList.contains("is-visible"), false);
  assert.equal(
    environment.section.style.getPropertyValue("--v-motion-delay"),
    "",
  );
  assert.equal(
    environment.card.style.getPropertyValue("--v-motion-x"),
    "",
  );
});

test("globe render loop stops offscreen and while the document is hidden", () => {
  const environment = createEnvironment({ canvas2d: true });
  const cleanup = motion.init(environment.global);
  const globeObserver = environment.observers.find((observer) =>
    observer.observed.has(environment.hero),
  );

  assert.ok(globeObserver);
  assert.equal(environment.pendingAnimationFrames(), 1);

  globeObserver.intersect(environment.hero, false);
  assert.equal(environment.pendingAnimationFrames(), 0);

  globeObserver.intersect(environment.hero, true);
  assert.equal(environment.pendingAnimationFrames(), 1);

  environment.setVisibility("hidden");
  assert.equal(environment.pendingAnimationFrames(), 0);

  environment.setVisibility("visible");
  assert.equal(environment.pendingAnimationFrames(), 1);

  cleanup();
  assert.equal(environment.pendingAnimationFrames(), 0);
});

test("pending content becomes visible when reduced motion is enabled live", () => {
  const environment = createEnvironment();
  motion.init(environment.global);
  environment.reducedQuery.change(true);

  assert.equal(environment.root.dataset.vMotion, "static");
  assert.equal(environment.root.classList.contains("v-motion-enabled"), false);
  assert.equal(environment.section.classList.contains("is-visible"), true);
  assert.equal(environment.observers[0].disconnected, true);
});

test("missing IntersectionObserver reveals content immediately", () => {
  const environment = createEnvironment({
    finePointer: false,
    intersectionObserver: false,
  });
  const cleanup = motion.init(environment.global);

  assert.equal(environment.card.classList.contains("v-motion-reveal"), false);
  assert.equal(environment.section.classList.contains("is-visible"), true);
  assert.equal(environment.card.children.length, 0);
  cleanup();
});

test("mobile viewport skips scramble setup", () => {
  const environment = createEnvironment({ scrambleViewport: false });

  const cleanup = motion.init(environment.global);

  assert.equal(environment.root.dataset.vMotion, "ready");
  assert.equal(
    environment.queryCounts.get(motion.SELECTORS.scramble) || 0,
    0,
  );

  cleanup();
});

test("save-data preference keeps the system static", () => {
  const environment = createEnvironment({ saveData: true });
  motion.init(environment.global);

  assert.equal(environment.root.dataset.vMotion, "static");
});

test("initially visible sections are not staged into hidden reveal states", () => {
  const environment = createEnvironment({ sectionTop: 140, legacyTop: 160 });
  motion.init(environment.global);

  assert.equal(environment.section.classList.contains("v-motion-reveal"), false);
  assert.equal(
    environment.legacyCard.classList.contains("v-motion-reveal"),
    false,
  );
});

test("fallback viewport, preinit guard, and hidden spotlight branches stay safe", () => {
  const preinitialized = createEnvironment();
  preinitialized.root.dataset.vMotionInitialized = "true";
  const noopCleanup = motion.init(preinitialized.global);

  assert.doesNotThrow(noopCleanup);
  assert.equal(preinitialized.observers.length, 0);

  const environment = createEnvironment({ sectionTop: 760, legacyTop: 820 });
  const originalQuerySelector = environment.global.document.querySelector.bind(
    environment.global.document,
  );
  const originalQuerySelectorAll = environment.global.document.querySelectorAll.bind(
    environment.global.document,
  );

  environment.global.innerHeight = 0;
  environment.root.clientHeight = 640;
  environment.global.document.querySelector = (selector) =>
    selector === motion.SELECTORS.hero ? null : originalQuerySelector(selector);
  environment.global.document.querySelectorAll = (selector) => {
    if (selector === motion.SELECTORS.section) {
      return [{}, ...originalQuerySelectorAll(selector)];
    }

    return originalQuerySelectorAll(selector);
  };

  const cleanup = motion.init(environment.global);
  assert.equal(environment.hero.classList.contains("v-motion-hero"), false);
  assert.equal(environment.section.classList.contains("v-motion-reveal"), true);

  environment.setVisibility("hidden");
  environment.card.dispatch("pointermove", { clientX: 60, clientY: 80 });
  environment.card.dispatch("pointermove", { clientX: 90, clientY: 120 });
  environment.flushAnimationFrames();
  assert.equal(environment.card.style.getPropertyValue("--v-motion-x"), "");

  cleanup();
});
