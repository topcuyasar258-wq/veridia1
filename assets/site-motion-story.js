(function registerScrollStory(rootScope, factory) {
  "use strict";

  const api = factory();

  if (typeof module === "object" && module.exports) {
    module.exports = api;
  }

  if (rootScope && rootScope.document) {
    rootScope.VeridiaStoryMotion = api;
    const boot = function bootScrollStory() {
      api.init(rootScope);
    };

    if (rootScope.document.readyState === "loading") {
      rootScope.document.addEventListener("DOMContentLoaded", boot, {
        once: true,
      });
    } else {
      boot();
    }
  }
})(
  typeof window !== "undefined" ? window : undefined,
  function createScrollStoryModule() {
    "use strict";

    const STORY_SCENES = Object.freeze([
      Object.freeze({
        eyebrow: "01 — Görünürlük",
        title: "Doğru müşterinin karşısına çıkın.",
        copy:
          "SEO ve reklam, markanızı talebin oluştuğu anda görünür kılar.",
      }),
      Object.freeze({
        eyebrow: "02 — Dönüşüm",
        title: "İlgiyi müşteriye dönüştürün.",
        copy:
          "Net mesaj, güçlü web deneyimi ve doğru teklif akışı birlikte çalışır.",
      }),
    ]);

    function clampUnit(value) {
      const numericValue = Number(value);
      if (!Number.isFinite(numericValue)) {
        return 0;
      }

      return Math.min(Math.max(numericValue, 0), 1);
    }

    function smoothStep(start, end, value) {
      if (!Number.isFinite(start) || !Number.isFinite(end) || end <= start) {
        return clampUnit(value);
      }

      const progress = clampUnit((Number(value) - start) / (end - start));
      return progress * progress * (3 - 2 * progress);
    }

    function sceneEnvelope(progress, enterStart, enterEnd, exitStart, exitEnd) {
      const entrance = smoothStep(enterStart, enterEnd, progress);
      const exit = 1 - smoothStep(exitStart, exitEnd, progress);
      return clampUnit(entrance * exit);
    }

    function calculateStickyProgress(
      sectionTop,
      sectionHeight,
      viewportHeight,
      stickyTop,
    ) {
      const numericTop = Number(sectionTop);
      const numericHeight = Number(sectionHeight);
      const numericViewport = Number(viewportHeight);
      const numericStickyTop = Number(stickyTop);
      if (
        !Number.isFinite(numericTop) ||
        !Number.isFinite(numericHeight) ||
        !Number.isFinite(numericViewport) ||
        !Number.isFinite(numericStickyTop)
      ) {
        return 0;
      }

      const travel = numericHeight - numericViewport;
      if (travel <= 0) {
        return 0;
      }

      return clampUnit((numericStickyTop - numericTop) / travel);
    }

    function resolveStoryTimeline(value) {
      const progress = clampUnit(value);
      const focus = smoothStep(0.12, 0.38, progress);
      const fracture = smoothStep(0.82, 0.98, progress);
      const exit = smoothStep(0.9, 1, progress);
      const introOpacity = 1 - smoothStep(0.12, 0.26, progress);
      const firstSceneOpacity = sceneEnvelope(
        progress,
        0.2,
        0.34,
        0.54,
        0.64,
      );
      const secondSceneOpacity = sceneEnvelope(
        progress,
        0.56,
        0.68,
        0.84,
        0.98,
      );
      const activeScene =
        progress >= 0.98
          ? -1
          : progress < 0.25
            ? 0
            : progress < 0.62
              ? 1
              : 2;

      return Object.freeze({
        activeScene,
        exit,
        focus,
        fracture,
        opacities: Object.freeze([
          clampUnit(introOpacity),
          firstSceneOpacity,
          secondSceneOpacity,
        ]),
        progress,
      });
    }

    function deterministicUnit(index, salt) {
      const numericIndex = Number.isFinite(Number(index))
        ? Math.floor(Number(index))
        : 0;
      const value =
        Math.sin((numericIndex + 1) * 12.9898 + salt * 78.233) * 43758.5453;
      return value - Math.floor(value);
    }

    function fractureSpherePoint(point, index, amount) {
      const source = point || {};
      const x = Number.isFinite(Number(source.x)) ? Number(source.x) : 0;
      const y = Number.isFinite(Number(source.y)) ? Number(source.y) : 0;
      const z = Number.isFinite(Number(source.z)) ? Number(source.z) : 0;
      const fracture = clampUnit(amount);
      if (!fracture) {
        return { x, y, z };
      }

      const length = Math.hypot(x, y, z);
      const angle = deterministicUnit(index, 1) * Math.PI * 2;
      const radial =
        length > 0
          ? { x: x / length, y: y / length, z: z / length }
          : { x: Math.cos(angle), y: Math.sin(angle), z: 0 };
      const tangent = {
        x: Math.cos(angle) * 0.34,
        y: (deterministicUnit(index, 2) - 0.5) * 0.5,
        z: Math.sin(angle) * 0.34,
      };
      const distance =
        fracture *
        fracture *
        (0.58 + deterministicUnit(index, 3) * 0.72);

      return {
        x: x + (radial.x + tangent.x) * distance,
        y: y + (radial.y + tangent.y) * distance,
        z: z + (radial.z + tangent.z) * distance,
      };
    }

    function createScene(document, scene, index) {
      const section = document.createElement("section");
      const eyebrow = document.createElement("p");
      const title = document.createElement("h2");
      const copy = document.createElement("p");

      section.className = "v-scroll-scene";
      section.dataset.vStoryScene = String(index + 1);
      section.setAttribute("aria-hidden", "true");
      section.tabIndex = -1;
      eyebrow.className = "v-scroll-scene-eyebrow";
      eyebrow.textContent = scene.eyebrow;
      title.id = `v-story-scene-title-${index + 1}`;
      title.textContent = scene.title;
      section.setAttribute("aria-labelledby", title.id);
      copy.className = "v-scroll-scene-copy";
      copy.textContent = scene.copy;
      section.appendChild(eyebrow);
      section.appendChild(title);
      section.appendChild(copy);

      return section;
    }

    function createStaticStory(document, hero) {
      const parent = hero && hero.parentNode;
      if (!parent) {
        return function noop() {};
      }

      const section = document.createElement("section");
      const heading = document.createElement("h2");
      const grid = document.createElement("div");

      section.className = "v-story-static";
      section.setAttribute("aria-labelledby", "v-story-static-title");
      heading.id = "v-story-static-title";
      heading.textContent = "Görünürlükten dönüşüme";
      grid.className = "v-story-static-grid";
      STORY_SCENES.forEach((scene, index) => {
        const article = document.createElement("article");
        const eyebrow = document.createElement("p");
        const title = document.createElement("h2");
        const copy = document.createElement("p");

        article.dataset.vStaticStoryScene = String(index + 1);
        article.tabIndex = -1;
        eyebrow.textContent = scene.eyebrow;
        title.textContent = scene.title;
        copy.textContent = scene.copy;
        article.appendChild(eyebrow);
        article.appendChild(title);
        article.appendChild(copy);
        grid.appendChild(article);
      });
      section.appendChild(heading);
      section.appendChild(grid);
      parent.insertBefore(section, hero.nextSibling);

      return function removeStaticStory() {
        section.remove();
      };
    }

    function focusElementWithoutScroll(element) {
      if (!element || typeof element.focus !== "function") {
        return;
      }
      try {
        element.focus({ preventScroll: true });
      } catch (_error) {
        element.focus();
      }
    }

    function createScrollStory(global, document, hero) {
      const heroContent = hero && hero.querySelector(".hero-content");
      const parent = hero && hero.parentNode;
      if (!hero || !heroContent || !parent) {
        return null;
      }

      const track = document.createElement("div");
      const copyLayer = document.createElement("div");
      const cue = document.createElement("div");
      const cueLabel = document.createElement("span");
      const cueLine = document.createElement("i");
      const indexList = document.createElement("ol");
      const scenes = STORY_SCENES.map((scene, index) =>
        createScene(document, scene, index),
      );
      const markers = [0, 1, 2].map((index) => {
        const marker = document.createElement("li");
        marker.textContent = String(index).padStart(2, "0");
        indexList.appendChild(marker);
        return marker;
      });
      const originalHeroAria = heroContent.getAttribute("aria-hidden");
      const originalHeroInert = heroContent.hasAttribute("inert");
      const originalScene = hero.getAttribute("data-v-story-scene");
      const originalFracture = hero.getAttribute("data-v-fracture");
      const focusAttributeRestorations = new Map();
      const originalStyleValues = new Map(
        [
          "--v-story-progress",
          "--v-story-focus",
          "--v-story-fracture",
          "--v-story-exit",
          "--v-story-intro-opacity",
          "--v-story-intro-shift",
          "--v-story-cue-opacity",
        ].map((property) => [
          property,
          hero.style.getPropertyValue(property),
        ]),
      );

      track.className = "v-scroll-track";
      track.dataset.vScrollStory = "true";
      copyLayer.className = "v-scroll-copy";
      cue.className = "v-scroll-cue";
      cue.setAttribute("aria-hidden", "true");
      cueLabel.textContent = "Kaydır";
      cueLine.setAttribute("aria-hidden", "true");
      cue.appendChild(cueLabel);
      cue.appendChild(cueLine);
      indexList.className = "v-scroll-index";
      indexList.setAttribute("aria-hidden", "true");
      scenes.forEach((scene) => copyLayer.appendChild(scene));

      parent.insertBefore(track, hero);
      track.appendChild(hero);
      hero.appendChild(copyLayer);
      hero.appendChild(cue);
      hero.appendChild(indexList);
      hero.classList.add("v-scroll-story");

      let animationFrame = 0;
      let destroyed = false;
      let isNearViewport = true;
      let lastProgress = null;
      let needsMeasure = false;
      let stickyTop = 0;
      let storyObserver = null;
      let trackHeight = 0;
      let trackStart = 0;
      let viewportHeight = 0;

      const restoreAttribute = function restoreAttribute(
        element,
        name,
        originalValue,
      ) {
        if (originalValue === null) {
          element.removeAttribute(name);
        } else {
          element.setAttribute(name, originalValue);
        }
      };

      const prepareFocusTarget = function prepareFocusTarget(element) {
        if (!element) {
          return null;
        }
        if (!focusAttributeRestorations.has(element)) {
          focusAttributeRestorations.set(
            element,
            element.getAttribute("tabindex"),
          );
        }
        element.tabIndex = -1;
        return element;
      };

      const focusWithoutScroll = function focusWithoutScroll(element) {
        if (!element) {
          return;
        }
        const target =
          element.tabIndex < 0 && !element.hasAttribute("tabindex")
            ? prepareFocusTarget(element)
            : element;
        if (target) {
          focusElementWithoutScroll(target);
        }
      };

      const applyState = function applyState(state) {
        const focusedElement = document.activeElement;
        const focusWasInIntro =
          focusedElement && heroContent.contains(focusedElement);
        const focusedScene = scenes.find((scene) =>
          focusedElement ? scene.contains(focusedElement) : false,
        );

        hero.__vStoryState = state;
        hero.dataset.vStoryScene = String(state.activeScene);
        hero.dataset.vFracture = state.fracture.toFixed(3);
        hero.style.setProperty("--v-story-progress", state.progress.toFixed(4));
        hero.style.setProperty("--v-story-focus", state.focus.toFixed(4));
        hero.style.setProperty(
          "--v-story-fracture",
          state.fracture.toFixed(4),
        );
        hero.style.setProperty("--v-story-exit", state.exit.toFixed(4));
        hero.style.setProperty(
          "--v-story-intro-opacity",
          state.opacities[0].toFixed(4),
        );
        hero.style.setProperty(
          "--v-story-intro-shift",
          `${(-state.focus * 1.75).toFixed(3)}rem`,
        );
        hero.style.setProperty(
          "--v-story-cue-opacity",
          (1 - state.focus).toFixed(4),
        );

        scenes.forEach((scene, index) => {
          const isActive = state.activeScene === index + 1;
          scene.setAttribute("aria-hidden", String(!isActive));
          scene.style.setProperty(
            "--v-story-scene-opacity",
            state.opacities[index + 1].toFixed(4),
          );
          scene.style.setProperty(
            "--v-story-scene-shift",
            `${((1 - state.opacities[index + 1]) * 2).toFixed(3)}rem`,
          );
          scene.style.setProperty(
            "--v-story-scene-scale",
            (0.975 + state.opacities[index + 1] * 0.025).toFixed(4),
          );
        });

        const introIsActive = state.activeScene === 0;
        heroContent.setAttribute("aria-hidden", String(!introIsActive));
        heroContent.inert = !introIsActive;
        markers.forEach((marker, index) => {
          marker.classList.toggle("is-active", state.activeScene === index);
        });

        if (focusWasInIntro && state.activeScene !== 0) {
          focusWithoutScroll(
            state.activeScene > 0
              ? scenes[state.activeScene - 1]
              : document.querySelector("#reference-trust-title"),
          );
        } else if (focusedScene) {
          if (state.activeScene === 0) {
            focusWithoutScroll(heroContent.querySelector(".hero-cta a"));
          } else if (state.activeScene === -1) {
            focusWithoutScroll(
              document.querySelector("#reference-trust-title"),
            );
          } else if (focusedScene !== scenes[state.activeScene - 1]) {
            focusWithoutScroll(scenes[state.activeScene - 1]);
          }
        }
      };

      const currentScrollY = function currentScrollY() {
        if (Number.isFinite(global.scrollY)) {
          return global.scrollY;
        }
        return Number.isFinite(global.pageYOffset) ? global.pageYOffset : 0;
      };

      const measure = function measureStory() {
        const trackBounds = track.getBoundingClientRect();
        const heroBounds = hero.getBoundingClientRect();
        const computedHero = global.getComputedStyle(hero);
        const measuredStickyTop = Number.parseFloat(computedHero.top);

        stickyTop = Number.isFinite(measuredStickyTop)
          ? measuredStickyTop
          : 0;
        trackHeight =
          Number.isFinite(track.offsetHeight) && track.offsetHeight > 0
            ? track.offsetHeight
            : trackBounds.height;
        viewportHeight =
          Number.isFinite(heroBounds.height) && heroBounds.height > 0
            ? heroBounds.height
            : Math.max(1, Number(global.innerHeight) || 1);
        trackStart = currentScrollY() + trackBounds.top;
      };

      const update = function updateStory() {
        animationFrame = 0;
        if (
          destroyed ||
          !isNearViewport ||
          document.visibilityState !== "visible"
        ) {
          return;
        }

        if (needsMeasure) {
          measure();
          needsMeasure = false;
          lastProgress = null;
        }
        const sectionTop = trackStart - currentScrollY();
        const progress = calculateStickyProgress(
          sectionTop,
          trackHeight,
          viewportHeight,
          stickyTop,
        );
        if (
          lastProgress !== null &&
          Math.abs(progress - lastProgress) < 0.0001
        ) {
          return;
        }
        lastProgress = progress;
        applyState(resolveStoryTimeline(progress));
      };

      const queueUpdate = function queueStoryUpdate() {
        if (
          destroyed ||
          animationFrame ||
          !isNearViewport ||
          document.visibilityState !== "visible"
        ) {
          return;
        }

        animationFrame = global.requestAnimationFrame(update);
      };

      const requestMeasure = function requestStoryMeasure() {
        needsMeasure = true;
        queueUpdate();
      };

      const handleVisibilityChange = function handleVisibilityChange() {
        if (document.visibilityState === "visible") {
          requestMeasure();
          return;
        }

        if (animationFrame) {
          global.cancelAnimationFrame(animationFrame);
          animationFrame = 0;
        }
      };

      if (typeof global.IntersectionObserver === "function") {
        storyObserver = new global.IntersectionObserver(
          (entries) => {
            const entry = entries[0];
            isNearViewport = Boolean(entry && entry.isIntersecting);
            if (isNearViewport) {
              requestMeasure();
            } else if (animationFrame) {
              global.cancelAnimationFrame(animationFrame);
              animationFrame = 0;
            }
          },
          { rootMargin: "100% 0px" },
        );
        storyObserver.observe(track);
      }

      global.addEventListener("scroll", queueUpdate, { passive: true });
      global.addEventListener("resize", requestMeasure, { passive: true });
      global.addEventListener("load", requestMeasure, { once: true });
      document.addEventListener("visibilitychange", handleVisibilityChange);
      measure();
      const initialState = resolveStoryTimeline(0);
      lastProgress = initialState.progress;
      applyState(initialState);
      queueUpdate();

      return function removeScrollStory() {
        if (destroyed) {
          return;
        }
        destroyed = true;

        if (animationFrame) {
          global.cancelAnimationFrame(animationFrame);
          animationFrame = 0;
        }
        if (storyObserver) {
          storyObserver.disconnect();
          storyObserver = null;
        }
        global.removeEventListener("scroll", queueUpdate);
        global.removeEventListener("resize", requestMeasure);
        global.removeEventListener("load", requestMeasure);
        document.removeEventListener(
          "visibilitychange",
          handleVisibilityChange,
        );

        copyLayer.remove();
        cue.remove();
        indexList.remove();
        parent.insertBefore(hero, track);
        track.remove();
        hero.classList.remove("v-scroll-story");
        delete hero.__vStoryState;
        restoreAttribute(hero, "data-v-story-scene", originalScene);
        restoreAttribute(hero, "data-v-fracture", originalFracture);
        restoreAttribute(
          heroContent,
          "aria-hidden",
          originalHeroAria,
        );
        heroContent.inert = originalHeroInert;
        if (!originalHeroInert) {
          heroContent.removeAttribute("inert");
        }
        focusAttributeRestorations.forEach((value, element) => {
          restoreAttribute(element, "tabindex", value);
        });
        originalStyleValues.forEach((value, property) => {
          if (value) {
            hero.style.setProperty(property, value);
          } else {
            hero.style.removeProperty(property);
          }
        });
      };
    }

    function init(global) {
      if (!global || !global.document) {
        return function noop() {};
      }

      const document = global.document;
      const root = document.documentElement;
      const hero = document.querySelector("body.reference-home-page #hero");
      if (
        !root ||
        !hero ||
        root.dataset.vStoryInitialized === "true"
      ) {
        return function noop() {};
      }

      root.dataset.vStoryInitialized = "true";
      const reducedMotionQuery =
        typeof global.matchMedia === "function"
          ? global.matchMedia("(prefers-reduced-motion: reduce)")
          : { matches: true };
      const compactViewportQuery =
        typeof global.matchMedia === "function"
          ? global.matchMedia(
              "(max-height: 520px) and (orientation: landscape)",
            )
          : { matches: false };
      const connection =
        global.navigator &&
        (global.navigator.connection ||
          global.navigator.mozConnection ||
          global.navigator.webkitConnection);
      const saveData = Boolean(connection && connection.saveData);
      if (
        reducedMotionQuery.matches ||
        compactViewportQuery.matches ||
        saveData
      ) {
        const removeStaticStory = createStaticStory(document, hero);
        root.dataset.vStory = "static";
        return function destroyStaticStoryState() {
          removeStaticStory();
          delete root.dataset.vStoryInitialized;
          delete root.dataset.vStory;
        };
      }

      const removeStory = createScrollStory(global, document, hero);
      if (!removeStory) {
        delete root.dataset.vStoryInitialized;
        return function noop() {};
      }
      root.dataset.vStory = "ready";

      let destroyed = false;
      let removeStaticStory = null;
      let storyIsActive = true;
      const mediaQueries = [reducedMotionQuery, compactViewportQuery];
      const destroy = function destroyStory() {
        if (destroyed) {
          return;
        }
        destroyed = true;
        if (storyIsActive) {
          removeStory();
          storyIsActive = false;
        }
        if (removeStaticStory) {
          removeStaticStory();
        }
        mediaQueries.forEach((query) => {
          if (typeof query.removeEventListener === "function") {
            query.removeEventListener("change", handleStaticPreference);
          }
        });
        if (
          connection &&
          typeof connection.removeEventListener === "function"
        ) {
          connection.removeEventListener(
            "change",
            handleConnectionChange,
          );
        }
        delete root.dataset.vStoryInitialized;
        delete root.dataset.vStory;
      };
      const enterStaticMode = function enterStaticStoryMode() {
        if (destroyed || !storyIsActive) {
          return;
        }
        const focusedElement = document.activeElement;
        const focusWasInHero =
          focusedElement && hero.contains(focusedElement);
        const focusedScene =
          focusedElement &&
          typeof focusedElement.closest === "function"
            ? focusedElement.closest(
                ".v-scroll-scene[data-v-story-scene]",
              )
            : null;
        const focusedSceneIndex = focusedScene
          ? focusedScene.dataset.vStoryScene
          : null;

        removeStory();
        storyIsActive = false;
        removeStaticStory = createStaticStory(document, hero);
        root.dataset.vStory = "static";
        if (focusedSceneIndex) {
          focusElementWithoutScroll(
            document.querySelector(
              `[data-v-static-story-scene="${focusedSceneIndex}"]`,
            ),
          );
        } else if (
          focusWasInHero &&
          focusedElement &&
          focusedElement.isConnected
        ) {
          focusElementWithoutScroll(focusedElement);
        }
      };
      const handleStaticPreference = function handleStaticPreference(event) {
        if (event.matches) {
          enterStaticMode();
        }
      };
      const handleConnectionChange = function handleConnectionChange() {
        if (connection && connection.saveData) {
          enterStaticMode();
        }
      };

      mediaQueries.forEach((query) => {
        if (typeof query.addEventListener === "function") {
          query.addEventListener("change", handleStaticPreference);
        }
      });
      if (
        connection &&
        typeof connection.addEventListener === "function"
      ) {
        connection.addEventListener("change", handleConnectionChange);
      }
      return destroy;
    }

    return Object.freeze({
      STORY_SCENES,
      calculateStickyProgress,
      createScrollStory,
      createStaticStory,
      fractureSpherePoint,
      init,
      resolveStoryTimeline,
    });
  },
);
