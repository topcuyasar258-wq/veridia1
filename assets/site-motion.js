(function registerSiteMotion(rootScope, factory) {
  "use strict";

  const api = factory();

  if (typeof module === "object" && module.exports) {
    module.exports = api;
  }

  if (rootScope && rootScope.document) {
    api.init(rootScope);
  }
})(
  typeof window !== "undefined" ? window : undefined,
  function createSiteMotion() {
    "use strict";

    const POLICY = Object.freeze({
      staggerStepMs: 70,
      staggerMaxMs: 350,
      observerThreshold: 0.08,
      observerRootMargin: "0px 0px -8% 0px",
      scrambleGlyphs: "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789@#$%&*+?",
      scrambleColumns: 9,
      scrambleColumnStepMs: 38,
      scrambleRowStepMs: 22,
      scrambleDelayMaxMs: 620,
      scrambleDurationMs: 420,
      scrambleGlyphSwapMs: 52,
      scrambleMaxCharacters: 140,
      globeDesktopPoints: 180,
      globeMobilePoints: 96,
      globeDesktopFrameMs: 1000 / 48,
      globeMobileFrameMs: 1000 / 30,
      globeMaxBackingWidth: 2400,
      globeMaxBackingHeight: 1600,
      globeMaxBackingPixels: 2400000,
    });

    const SELECTORS = Object.freeze({
      hero: [
        "#hero",
        ".silo-hero",
        ".work-hero",
        ".blog-header",
        ".article-hero",
        ".legal-hero",
        ".contact-hero",
        ".contact-hero-panel",
        ".hero-panel",
      ].join(", "),
      section: [
        "main > section",
        "main > article > section",
        "body > section",
      ].join(", "),
      card: [
        ".surface-card",
        ".resource-card",
        ".blog-card",
        ".related-card",
        ".signal-card",
        ".feature-card",
        ".result-card",
        ".blog-faq-card",
        ".sidebar-panel",
        ".info-panel",
        ".detail-card",
        ".step-card",
        ".case-note-card",
        ".case-story-card",
        ".fit-card",
        ".proof-card",
        ".choice-card",
        ".service-card",
        ".sector-card",
        ".team-card",
        ".portfolio-card",
        ".need-card",
        ".contact-card",
        ".comparison-card",
        ".summary-card",
        ".ledger-card",
        ".reference-service",
        ".reference-trust-logos > span",
      ].join(", "),
      cta: [
        ".btn-gold",
        ".btn-outline",
        ".primary-link",
        ".blog-footer-cta",
        ".mobile-menu-cta",
        ".nav-mobile-cta",
        ".final-cta a",
        ".cta-actions a",
        ".bridge-actions a",
        ".revision-nav-cta",
        ".btn-submit",
      ].join(", "),
      link: [
        ".surface-link",
        ".secondary-link",
        ".sector-link",
        ".p-link",
        ".home-portal-link",
      ].join(", "),
      scramble: "[data-v-scramble]",
    });

    function cappedStaggerDelay(index) {
      const numericIndex = Number(index);
      const safeIndex = Number.isFinite(numericIndex)
        ? Math.max(0, Math.floor(numericIndex))
        : 0;

      return Math.min(safeIndex * POLICY.staggerStepMs, POLICY.staggerMaxMs);
    }

    function scrambleDelay(index) {
      const numericIndex = Number(index);
      const safeIndex = Number.isFinite(numericIndex)
        ? Math.max(0, Math.floor(numericIndex))
        : 0;
      const column = safeIndex % POLICY.scrambleColumns;
      const row = Math.floor(safeIndex / POLICY.scrambleColumns);
      const scatteredDelay =
        column * POLICY.scrambleColumnStepMs +
        row * POLICY.scrambleRowStepMs;

      return Math.min(scatteredDelay, POLICY.scrambleDelayMaxMs);
    }

    function selectScrambleGlyph(character, progress, randomValue) {
      if (/\s/u.test(character) || Number(progress) >= 1) {
        return character;
      }

      const numericRandom = Number(randomValue);
      const safeRandom = Number.isFinite(numericRandom)
        ? Math.min(Math.max(numericRandom, 0), 0.999999)
        : 0;
      const glyphIndex = Math.floor(
        safeRandom * POLICY.scrambleGlyphs.length,
      );

      return POLICY.scrambleGlyphs[glyphIndex];
    }

    function createSpherePoints(count) {
      const numericCount = Number(count);
      const safeCount = Number.isFinite(numericCount)
        ? Math.max(0, Math.floor(numericCount))
        : 0;
      if (!safeCount) {
        return [];
      }

      const goldenAngle = Math.PI * (3 - Math.sqrt(5));
      return Array.from({ length: safeCount }, (_, index) => {
        const y =
          safeCount === 1 ? 0 : 1 - (index / (safeCount - 1)) * 2;
        const ringRadius = Math.sqrt(Math.max(0, 1 - y * y));
        const theta = goldenAngle * index;

        return {
          x: Math.cos(theta) * ringRadius,
          y,
          z: Math.sin(theta) * ringRadius,
        };
      });
    }

    function calculateCanvasBackingStore(width, height, pixelRatio) {
      const numericWidth = Number(width);
      const numericHeight = Number(height);
      if (
        !Number.isFinite(numericWidth) ||
        numericWidth <= 0 ||
        !Number.isFinite(numericHeight) ||
        numericHeight <= 0
      ) {
        return { height: 1, scale: 1, width: 1 };
      }

      const requestedScale = Number(pixelRatio);
      const safeScale =
        Number.isFinite(requestedScale) && requestedScale > 0
          ? requestedScale
          : 1;
      const pixelBudgetScale = Math.sqrt(
        POLICY.globeMaxBackingPixels / numericWidth / numericHeight,
      );
      const scale = Math.min(
        safeScale,
        POLICY.globeMaxBackingWidth / numericWidth,
        POLICY.globeMaxBackingHeight / numericHeight,
        pixelBudgetScale,
      );

      return {
        height: Math.max(1, Math.floor(numericHeight * scale)),
        scale,
        width: Math.max(1, Math.floor(numericWidth * scale)),
      };
    }

    function countScrambleCharacters(value) {
      if (typeof value !== "string") {
        return 0;
      }

      return Array.from(value).reduce(
        (count, character) => count + (/\s/u.test(character) ? 0 : 1),
        0,
      );
    }

    function shouldReduceMotion(mediaPreference, saveData) {
      const prefersReduced =
        typeof mediaPreference === "boolean"
          ? mediaPreference
          : Boolean(mediaPreference && mediaPreference.matches);

      return prefersReduced || Boolean(saveData);
    }

    function uniqueElements(elements) {
      return elements.filter(
        (element, index, collection) => collection.indexOf(element) === index,
      );
    }

    function isMotionCandidate(element) {
      if (!element || typeof element.matches !== "function") {
        return false;
      }

      const isUnavailable = Boolean(
        element.closest('[hidden], [aria-hidden="true"], dialog:not([open])'),
      );

      return !isUnavailable;
    }

    function addRevealClass(element, index) {
      element.classList.add("v-motion-reveal");
      element.style.setProperty(
        "--v-motion-delay",
        `${cappedStaggerDelay(index)}ms`,
      );
    }

    function readViewportHeight(global, document) {
      if (Number.isFinite(global.innerHeight) && global.innerHeight > 0) {
        return global.innerHeight;
      }

      const root = document && document.documentElement;
      return root && Number.isFinite(root.clientHeight) ? root.clientHeight : 0;
    }

    function isInitiallyVisible(element, viewportHeight) {
      if (
        !element ||
        typeof element.getBoundingClientRect !== "function" ||
        !viewportHeight
      ) {
        return false;
      }

      const bounds = element.getBoundingClientRect();
      const top = Number.isFinite(bounds.top) ? bounds.top : 0;
      const bottom = Number.isFinite(bounds.bottom) ? bounds.bottom : top;

      return top < viewportHeight * 0.88 && bottom > 0;
    }

    function createAmbientLayer(document, hero) {
      if (!hero) {
        return null;
      }

      const ambient = document.createElement("div");
      ambient.className = "v-motion-ambient";
      ambient.setAttribute("aria-hidden", "true");
      hero.classList.add("v-motion-hero");
      hero.appendChild(ambient);

      return ambient;
    }

    function createThreatGlobe(global, document, hero, finePointer) {
      if (!hero) {
        return null;
      }

      const canvas = document.createElement("canvas");
      canvas.className = "v-motion-globe";
      canvas.setAttribute("aria-hidden", "true");
      canvas.setAttribute("role", "presentation");

      if (typeof canvas.getContext !== "function") {
        return null;
      }

      const context = canvas.getContext("2d");
      if (!context) {
        return null;
      }

      hero.classList.add("v-motion-hero");
      hero.appendChild(canvas);

      const isMobile =
        Number.isFinite(global.innerWidth) && global.innerWidth < 768;
      const pointCount = isMobile
        ? POLICY.globeMobilePoints
        : POLICY.globeDesktopPoints;
      const frameInterval = isMobile
        ? POLICY.globeMobileFrameMs
        : POLICY.globeDesktopFrameMs;
      const points = createSpherePoints(pointCount);
      const edgeOffsets = isMobile ? [13] : [13, 21];
      const pointer = { x: 0, y: 0 };

      let animationFrame = 0;
      let canvasHeight = 0;
      let canvasWidth = 0;
      let destroyed = false;
      let isVisible = true;
      let lastFrameTime = 0;
      let visibilityObserver = null;

      const resizeCanvas = function resizeCanvas() {
        const bounds = hero.getBoundingClientRect();
        const widthCandidates = [
          bounds.width,
          hero.clientWidth,
          global.innerWidth,
          1,
        ];
        const heightCandidates = [
          bounds.height,
          hero.clientHeight,
          global.innerHeight,
          1,
        ];
        const measuredWidth = widthCandidates.find(
          (value) => Number.isFinite(value) && value > 0,
        );
        const measuredHeight = heightCandidates.find(
          (value) => Number.isFinite(value) && value > 0,
        );
        canvasWidth = Math.max(1, Math.round(measuredWidth));
        canvasHeight = Math.max(1, Math.round(measuredHeight));
        const maxDpr = isMobile ? 1 : 1.5;
        const pixelRatio = Math.min(
          Math.max(Number(global.devicePixelRatio) || 1, 1),
          maxDpr,
        );
        const backingStore = calculateCanvasBackingStore(
          canvasWidth,
          canvasHeight,
          pixelRatio,
        );

        canvas.width = backingStore.width;
        canvas.height = backingStore.height;
        canvas.style.width = `${canvasWidth}px`;
        canvas.style.height = `${canvasHeight}px`;
        context.setTransform(
          backingStore.scale,
          0,
          0,
          backingStore.scale,
          0,
          0,
        );
      };

      const handlePointerMove = function handlePointerMove(event) {
        const bounds = hero.getBoundingClientRect();
        if (!bounds.width || !bounds.height) {
          return;
        }

        pointer.x = Math.min(
          Math.max((event.clientX - bounds.left) / bounds.width - 0.5, -0.5),
          0.5,
        );
        pointer.y = Math.min(
          Math.max((event.clientY - bounds.top) / bounds.height - 0.5, -0.5),
          0.5,
        );
      };

      const handlePointerLeave = function handlePointerLeave() {
        pointer.x = 0;
        pointer.y = 0;
      };

      const drawGlobe = function drawGlobe(timestamp) {
        if (
          document.visibilityState !== "visible" ||
          !isVisible ||
          timestamp - lastFrameTime < frameInterval
        ) {
          return;
        }
        lastFrameTime = timestamp;

        context.clearRect(0, 0, canvasWidth, canvasHeight);
        const lightTheme =
          document.documentElement.getAttribute("data-theme") === "light";
        const storyState = hero.__vStoryState || {
          exit: 0,
          focus: 0,
          fracture: 0,
        };
        const storyApi = global.VeridiaStoryMotion;
        const initialCenterX = isMobile ? 0.68 : 0.73;
        const focusedCenterX =
          initialCenterX + (0.5 - initialCenterX) * storyState.focus;
        const centerX =
          canvasWidth * focusedCenterX + pointer.x * 18;
        const initialCenterY = isMobile ? 0.42 : 0.47;
        const centerY =
          canvasHeight *
            (initialCenterY + (0.48 - initialCenterY) * storyState.focus) +
          pointer.y * 14;
        const radius =
          Math.min(
            canvasWidth * (isMobile ? 0.43 : 0.29),
            canvasHeight * (isMobile ? 0.34 : 0.43),
          ) *
          (1 + storyState.focus * 0.1);
        const visibility = 1 - storyState.exit;
        const connectionVisibility =
          Math.pow(1 - storyState.fracture, 2) * visibility;
        const rotation = timestamp * 0.00012 + pointer.x * 0.16;
        const tilt = -0.18 + pointer.y * 0.08;
        const cosRotation = Math.cos(rotation);
        const sinRotation = Math.sin(rotation);
        const cosTilt = Math.cos(tilt);
        const sinTilt = Math.sin(tilt);
        const scanPosition = ((timestamp % 4600) / 4600) * 2 - 1;

        const projected = points.map((point, index) => {
          const storyPoint =
            storyState.fracture &&
            storyApi &&
            typeof storyApi.fractureSpherePoint === "function"
              ? storyApi.fractureSpherePoint(
                  point,
                  index,
                  storyState.fracture,
                )
              : point;
          const rotatedX =
            storyPoint.x * cosRotation + storyPoint.z * sinRotation;
          const rotatedZ =
            -storyPoint.x * sinRotation + storyPoint.z * cosRotation;
          const rotatedY = storyPoint.y * cosTilt - rotatedZ * sinTilt;
          const depthZ = storyPoint.y * sinTilt + rotatedZ * cosTilt;
          const depth = Math.min(Math.max((depthZ + 1) / 2, 0), 1);
          const perspective = 0.78 + depth * 0.26;
          const scanDistance = Math.abs(rotatedY - scanPosition);
          const scanStrength = Math.max(0, 1 - scanDistance / 0.13);

          return {
            depth,
            index,
            scanStrength,
            x: centerX + rotatedX * radius * perspective,
            y: centerY + rotatedY * radius,
          };
        });

        context.save();
        context.lineWidth = 0.7;
        projected.forEach((point, index) => {
          edgeOffsets.forEach((offset) => {
            const neighbor = projected[index + offset];
            if (!neighbor) {
              return;
            }

            const distance = Math.hypot(
              point.x - neighbor.x,
              point.y - neighbor.y,
            );
            if (distance > radius * 0.46) {
              return;
            }

            const alpha =
              (0.035 +
                ((point.depth + neighbor.depth) / 2) * 0.13 +
                Math.max(point.scanStrength, neighbor.scanStrength) * 0.24) *
              connectionVisibility;
            context.strokeStyle = lightTheme
              ? `rgba(32, 91, 69, ${alpha})`
              : `rgba(175, 224, 202, ${alpha})`;
            context.beginPath();
            context.moveTo(point.x, point.y);
            context.lineTo(neighbor.x, neighbor.y);
            context.stroke();
          });
        });

        projected
          .slice()
          .sort((left, right) => left.depth - right.depth)
          .forEach((point) => {
            const isSignal = (point.index * 37) % 97 < 3;
            const pulse =
              isSignal &&
              0.5 + Math.sin(timestamp * 0.004 + point.index) * 0.5;
            const size =
              0.75 +
              point.depth * 1.45 +
              point.scanStrength * 1.7 +
              (isSignal ? 1.2 + pulse : 0);
            const alpha =
              (0.16 +
                point.depth * 0.58 +
                point.scanStrength * 0.24) *
              visibility;

            context.fillStyle = isSignal
              ? `rgba(211, 176, 100, ${Math.min(1, alpha + 0.2)})`
              : lightTheme
                ? `rgba(35, 103, 77, ${alpha})`
                : `rgba(194, 236, 216, ${alpha})`;
            context.beginPath();
            context.arc(point.x, point.y, size, 0, Math.PI * 2);
            context.fill();

            if (isSignal) {
              context.strokeStyle =
                `rgba(211, 176, 100, ${(0.1 + pulse * 0.24) * visibility})`;
              context.lineWidth = 1;
              context.beginPath();
              context.arc(
                point.x,
                point.y,
                size + 4 + pulse * 5,
                0,
                Math.PI * 2,
              );
              context.stroke();
            }
          });

        const scanAlpha =
          (0.08 + (1 - Math.abs(scanPosition)) * 0.08) *
          connectionVisibility;
        context.strokeStyle = lightTheme
          ? `rgba(35, 103, 77, ${scanAlpha})`
          : `rgba(211, 176, 100, ${scanAlpha})`;
        context.lineWidth = 1;
        context.beginPath();
        context.ellipse(
          centerX,
          centerY + scanPosition * radius,
          radius * Math.sqrt(Math.max(0, 1 - scanPosition * scanPosition)),
          Math.max(3, radius * 0.055),
          0,
          0,
          Math.PI * 2,
        );
        context.stroke();
        context.restore();
      };

      const cancelQueuedRender = function cancelQueuedRender() {
        if (!animationFrame) {
          return;
        }

        global.cancelAnimationFrame(animationFrame);
        animationFrame = 0;
      };

      const shouldRender = function shouldRender() {
        return (
          !destroyed &&
          isVisible &&
          document.visibilityState === "visible"
        );
      };

      const queueRender = function queueRender() {
        if (!shouldRender() || animationFrame) {
          return;
        }

        animationFrame = global.requestAnimationFrame(render);
      };

      const render = function render(timestamp) {
        animationFrame = 0;
        if (!shouldRender()) {
          return;
        }

        drawGlobe(Number.isFinite(timestamp) ? timestamp : Date.now());
        queueRender();
      };

      const handleVisibilityChange = function handleVisibilityChange() {
        if (document.visibilityState === "visible") {
          queueRender();
          return;
        }

        cancelQueuedRender();
      };

      resizeCanvas();
      if (typeof global.addEventListener === "function") {
        global.addEventListener("resize", resizeCanvas, { passive: true });
      }
      if (finePointer) {
        hero.addEventListener("pointermove", handlePointerMove, {
          passive: true,
        });
        hero.addEventListener("pointerleave", handlePointerLeave, {
          passive: true,
        });
      }
      if ("IntersectionObserver" in global) {
        visibilityObserver = new global.IntersectionObserver(
          (entries) => {
            const entry = entries[0];
            isVisible = Boolean(entry && entry.isIntersecting);
            if (isVisible) {
              queueRender();
            } else {
              cancelQueuedRender();
            }
          },
          { rootMargin: "160px 0px" },
        );
        visibilityObserver.observe(hero);
      }
      document.addEventListener("visibilitychange", handleVisibilityChange);
      queueRender();

      return function removeThreatGlobe() {
        if (destroyed) {
          return;
        }
        destroyed = true;

        cancelQueuedRender();
        if (visibilityObserver) {
          visibilityObserver.disconnect();
          visibilityObserver = null;
        }
        if (typeof global.removeEventListener === "function") {
          global.removeEventListener("resize", resizeCanvas);
        }
        document.removeEventListener(
          "visibilitychange",
          handleVisibilityChange,
        );
        if (finePointer) {
          hero.removeEventListener("pointermove", handlePointerMove);
          hero.removeEventListener("pointerleave", handlePointerLeave);
        }
        canvas.remove();
      };
    }

    function prepareSpotlight(global, document, card) {
      const glow = document.createElement("span");
      glow.className = "v-motion-card-glow";
      glow.setAttribute("aria-hidden", "true");
      card.appendChild(glow);

      let pendingFrame = 0;
      let latestPoint = null;

      const paintSpotlight = function paintSpotlight() {
        pendingFrame = 0;
        if (!latestPoint || document.visibilityState !== "visible") {
          return;
        }

        const bounds = card.getBoundingClientRect();
        card.style.setProperty("--v-motion-x", `${latestPoint.x - bounds.left}px`);
        card.style.setProperty("--v-motion-y", `${latestPoint.y - bounds.top}px`);
      };

      const handlePointerMove = function handlePointerMove(event) {
        latestPoint = { x: event.clientX, y: event.clientY };
        if (pendingFrame) {
          return;
        }

        pendingFrame = global.requestAnimationFrame(paintSpotlight);
      };

      const handlePointerLeave = function handlePointerLeave() {
        latestPoint = null;
        if (pendingFrame) {
          global.cancelAnimationFrame(pendingFrame);
          pendingFrame = 0;
        }

        card.style.setProperty("--v-motion-x", "50%");
        card.style.setProperty("--v-motion-y", "50%");
      };

      card.addEventListener("pointermove", handlePointerMove, { passive: true });
      card.addEventListener("pointerleave", handlePointerLeave, {
        passive: true,
      });

      return function removeSpotlight() {
        handlePointerLeave();
        card.removeEventListener("pointermove", handlePointerMove);
        card.removeEventListener("pointerleave", handlePointerLeave);
        glow.remove();
      };
    }

    function collectScrambleTextNodes(target) {
      const textNodes = [];

      const visit = function visit(node) {
        Array.from(node.childNodes || []).forEach((child) => {
          if (child.nodeType === 3 && child.nodeValue) {
            textNodes.push(child);
            return;
          }

          if (
            child.nodeType === 1 &&
            !["SCRIPT", "STYLE", "NOSCRIPT"].includes(child.tagName)
          ) {
            visit(child);
          }
        });
      };

      visit(target);
      return textNodes;
    }

    function normalizedAccessibleText(target) {
      const renderedText =
        typeof target.innerText === "string" && target.innerText
          ? target.innerText
          : target.textContent || "";

      return renderedText.replace(/\s+/gu, " ").trim();
    }

    function createScrambleCharacter(document, character, index) {
      const wrapper = document.createElement("span");
      const measure = document.createElement("span");
      const glyph = document.createElement("span");

      wrapper.className = "v-scramble-char";
      wrapper.setAttribute("aria-hidden", "true");
      measure.className = "v-scramble-measure";
      measure.textContent = character;
      glyph.className = "v-scramble-glyph is-noise";
      glyph.textContent = selectScrambleGlyph(character, 0, Math.random());
      glyph.style.setProperty("--v-scramble-opacity", "0.18");
      glyph.style.setProperty("--v-scramble-lift", "0.24em");
      glyph.style.setProperty("--v-scramble-blur", "3px");
      glyph.style.setProperty("--v-scramble-scale", "0.94");
      wrapper.appendChild(measure);
      wrapper.appendChild(glyph);

      return {
        delay: scrambleDelay(index),
        glyph,
        lastSwapBucket: -1,
        original: character,
        wrapper,
      };
    }

    function prepareScramble(global, document, target) {
      const originalHtml = target.innerHTML;
      const originalAriaLabel = target.getAttribute("aria-label");
      const accessibleText = normalizedAccessibleText(target);
      const textNodes = collectScrambleTextNodes(target);
      const characters = [];
      const characterCount = textNodes.reduce(
        (count, textNode) =>
          count + countScrambleCharacters(textNode.nodeValue),
        0,
      );

      if (
        !characterCount ||
        characterCount > POLICY.scrambleMaxCharacters
      ) {
        return null;
      }

      textNodes.forEach((textNode) => {
        const fragment = document.createDocumentFragment();
        let word = null;

        Array.from(textNode.nodeValue).forEach((character) => {
          if (/\s/u.test(character)) {
            word = null;
            fragment.appendChild(document.createTextNode(character));
            return;
          }

          if (!word) {
            word = document.createElement("span");
            word.className = "v-scramble-word";
            word.setAttribute("aria-hidden", "true");
            fragment.appendChild(word);
          }

          const preparedCharacter = createScrambleCharacter(
            document,
            character,
            characters.length,
          );
          characters.push(preparedCharacter);
          word.appendChild(preparedCharacter.wrapper);
        });

        textNode.parentNode.replaceChild(fragment, textNode);
      });

      target.setAttribute("aria-label", accessibleText);
      target.classList.add("v-scramble-ready");
      target.dataset.vScrambleReady = "true";

      let animationFrame = 0;
      let hasStarted = false;
      let isComplete = false;

      const restoreOriginalDom = function restoreOriginalDom(completed) {
        if (animationFrame) {
          global.cancelAnimationFrame(animationFrame);
          animationFrame = 0;
        }

        target.innerHTML = originalHtml;
        target.classList.remove("v-scramble-ready", "is-scramble-running");
        target.classList.toggle("is-scramble-complete", Boolean(completed));
        delete target.dataset.vScrambleReady;
        if (originalAriaLabel === null) {
          target.removeAttribute("aria-label");
        } else {
          target.setAttribute("aria-label", originalAriaLabel);
        }
      };

      const settle = function settle() {
        restoreOriginalDom(true);
        isComplete = true;
      };

      const start = function start() {
        if (
          hasStarted ||
          isComplete ||
          typeof global.requestAnimationFrame !== "function"
        ) {
          if (typeof global.requestAnimationFrame !== "function") {
            settle();
          }
          return;
        }

        hasStarted = true;
        target.classList.add("is-scramble-running");
        let startedAt = null;

        const render = function render(timestamp) {
          if (document.visibilityState !== "visible") {
            startedAt = null;
            animationFrame = global.requestAnimationFrame(render);
            return;
          }

          const currentTime = Number.isFinite(timestamp) ? timestamp : Date.now();
          if (startedAt === null) {
            startedAt = currentTime;
          }

          const elapsed = Math.max(0, currentTime - startedAt);
          let pendingCharacters = 0;

          characters.forEach((character) => {
            const localElapsed = elapsed - character.delay;
            const progress = Math.min(
              Math.max(localElapsed / POLICY.scrambleDurationMs, 0),
              1,
            );

            if (progress >= 1) {
              if (!character.wrapper.classList.contains("is-settled")) {
                character.glyph.textContent = character.original;
                character.glyph.classList.remove("is-noise");
                character.glyph.classList.add("is-settled");
                character.wrapper.classList.add("is-settled");
              }
              character.glyph.style.setProperty("--v-scramble-opacity", "1");
              character.glyph.style.setProperty("--v-scramble-lift", "0em");
              character.glyph.style.setProperty("--v-scramble-blur", "0px");
              character.glyph.style.setProperty("--v-scramble-scale", "1");
              return;
            }

            pendingCharacters += 1;
            const swapBucket = Math.floor(
              Math.max(localElapsed, 0) / POLICY.scrambleGlyphSwapMs,
            );
            if (swapBucket !== character.lastSwapBucket) {
              character.lastSwapBucket = swapBucket;
              character.glyph.textContent = selectScrambleGlyph(
                character.original,
                progress,
                Math.random(),
              );
            }

            const opacity = 0.18 + progress * 0.82;
            const lift = (1 - progress) * 0.24;
            const blur = (1 - progress) * 3;
            const scale = 0.94 + progress * 0.06;
            character.glyph.style.setProperty(
              "--v-scramble-opacity",
              opacity.toFixed(3),
            );
            character.glyph.style.setProperty(
              "--v-scramble-lift",
              `${lift.toFixed(3)}em`,
            );
            character.glyph.style.setProperty(
              "--v-scramble-blur",
              `${blur.toFixed(2)}px`,
            );
            character.glyph.style.setProperty(
              "--v-scramble-scale",
              scale.toFixed(3),
            );
          });

          if (pendingCharacters) {
            animationFrame = global.requestAnimationFrame(render);
            return;
          }

          settle();
        };

        animationFrame = global.requestAnimationFrame(render);
      };

      const restore = function restore() {
        restoreOriginalDom(false);
      };

      return { restore, settle, start, target };
    }

    function init(global) {
      if (!global || !global.document) {
        return function noop() {};
      }

      const document = global.document;
      const root = document.documentElement;

      if (!root || root.dataset.vMotionInitialized === "true") {
        return function noop() {};
      }

      root.dataset.vMotionInitialized = "true";

      const supportsMatchMedia = typeof global.matchMedia === "function";
      const reducedMotionQuery = supportsMatchMedia
        ? global.matchMedia("(prefers-reduced-motion: reduce)")
        : { matches: true };
      const finePointerQuery = supportsMatchMedia
        ? global.matchMedia("(hover: hover) and (pointer: fine)")
        : { matches: false };
      const connection =
        global.navigator &&
        (global.navigator.connection ||
          global.navigator.mozConnection ||
          global.navigator.webkitConnection);
      const saveData = Boolean(connection && connection.saveData);
      const motionDisabled = shouldReduceMotion(reducedMotionQuery, saveData);

      const hero = document.querySelector(SELECTORS.hero);
      const viewportHeight = readViewportHeight(global, document);
      const trackedClasses = [
        "v-motion-hero",
        "v-motion-card",
        "v-motion-cta",
        "v-motion-link",
        "v-motion-reveal",
        "v-motion-passive",
        "is-visible",
      ];
      const trackedStyles = [
        "--v-motion-delay",
        "--v-motion-x",
        "--v-motion-y",
      ];
      const elementBaselines = new Map();
      const rememberElement = function rememberElement(element) {
        if (!element || elementBaselines.has(element)) {
          return;
        }

        elementBaselines.set(element, {
          classes: trackedClasses.map((className) => [
            className,
            element.classList.contains(className),
          ]),
          styles: trackedStyles.map((property) => [
            property,
            element.style.getPropertyValue(property),
          ]),
        });
      };
      const restoreElements = function restoreElements() {
        elementBaselines.forEach((baseline, element) => {
          baseline.classes.forEach(([className, wasPresent]) => {
            element.classList.toggle(className, wasPresent);
          });
          baseline.styles.forEach(([property, value]) => {
            if (value) {
              element.style.setProperty(property, value);
            } else {
              element.style.removeProperty(property);
            }
          });
        });
      };

      rememberElement(hero);

      const legacyReveals = Array.from(
        document.querySelectorAll(".reveal"),
      ).filter(
        (target) =>
          isMotionCandidate(target) &&
          !(
            target.parentElement &&
            target.parentElement.closest(".reveal")
          ) &&
          !isInitiallyVisible(target, viewportHeight),
      );
      legacyReveals.forEach(rememberElement);
      legacyReveals.forEach((target, index) =>
        addRevealClass(target, index % 5),
      );
      const passiveLegacyReveals = Array.from(
        document.querySelectorAll(".reveal .reveal"),
      );
      passiveLegacyReveals.forEach(rememberElement);
      passiveLegacyReveals.forEach((target) =>
        target.classList.add("v-motion-passive"),
      );

      const cards = Array.from(document.querySelectorAll(SELECTORS.card)).filter(
        (card) =>
          isMotionCandidate(card) &&
          !(hero && hero.contains(card)) &&
          !(
            card.parentElement &&
            card.parentElement.closest(".reveal")
          ),
      );
      cards.forEach(rememberElement);
      cards.forEach((card) => {
        card.classList.add("v-motion-card");
      });

      const sections = Array.from(
        document.querySelectorAll(SELECTORS.section),
      ).filter(
        (section) =>
          isMotionCandidate(section) &&
          section !== hero &&
          !(hero && hero.contains(section)) &&
          !section.matches(".reveal") &&
          !section.querySelector(".reveal") &&
          !isInitiallyVisible(section, viewportHeight),
      );
      sections.forEach(rememberElement);
      sections.forEach((section, index) => addRevealClass(section, index % 3));

      const revealTargets = uniqueElements([
        ...legacyReveals,
        ...sections,
      ]);
      const ctas = Array.from(document.querySelectorAll(SELECTORS.cta));
      const links = Array.from(document.querySelectorAll(SELECTORS.link));

      ctas.forEach(rememberElement);
      links.forEach(rememberElement);
      ctas.forEach((cta) => cta.classList.add("v-motion-cta"));
      links.forEach((link) => link.classList.add("v-motion-link"));

      const ambient = motionDisabled ? null : createAmbientLayer(document, hero);
      const removeThreatGlobe = motionDisabled
        ? null
        : createThreatGlobe(
            global,
            document,
            hero,
            finePointerQuery.matches,
          );
      const spotlightCleanups = !motionDisabled && finePointerQuery.matches
        ? cards.map((card) => prepareSpotlight(global, document, card))
        : [];
      const scrambleTargets = motionDisabled
        ? []
        : Array.from(document.querySelectorAll(SELECTORS.scramble))
            .filter(isMotionCandidate);
      const initialScrambleTargets = scrambleTargets.filter((target) =>
        isInitiallyVisible(target, viewportHeight),
      );
      const deferredScrambleTargets = scrambleTargets.filter(
        (target) => !initialScrambleTargets.includes(target),
      );
      const scrambleStates = [];
      const scrambleByTarget = new Map();
      const prepareScrambleTarget = function prepareScrambleTarget(target) {
        if (scrambleByTarget.has(target)) {
          return scrambleByTarget.get(target);
        }

        const state = prepareScramble(global, document, target);
        scrambleByTarget.set(target, state);
        if (state) {
          scrambleStates.push(state);
        }
        return state;
      };
      const initialScrambles = initialScrambleTargets
        .map(prepareScrambleTarget)
        .filter(Boolean);
      const observableTargets = uniqueElements([
        ...revealTargets,
        ...deferredScrambleTargets,
      ]);

      let observer = null;
      if (
        !motionDisabled &&
        "IntersectionObserver" in global &&
        observableTargets.length
      ) {
        observer = new global.IntersectionObserver(
          (entries) => {
            entries.forEach((entry) => {
              if (!entry.isIntersecting) {
                return;
              }

              if (revealTargets.includes(entry.target)) {
                entry.target.classList.add("is-visible");
              }
              const scrambleState = deferredScrambleTargets.includes(
                entry.target,
              )
                ? prepareScrambleTarget(entry.target)
                : null;
              if (scrambleState) {
                scrambleState.start();
              }
              observer.unobserve(entry.target);
            });
          },
          {
            rootMargin: POLICY.observerRootMargin,
            threshold: POLICY.observerThreshold,
          },
        );
        observableTargets.forEach((target) => observer.observe(target));
      } else {
        revealTargets.forEach((target) =>
          target.classList.add("is-visible"),
        );
      }

      if (motionDisabled) {
        root.dataset.vMotion = "static";
      } else {
        root.dataset.vMotion = "ready";
        root.classList.add("v-motion-enabled");
        initialScrambles.forEach((state) => state.start());
        if (!observer) {
          deferredScrambleTargets.forEach((target) => {
            const state = prepareScrambleTarget(target);
            if (state) {
              state.start();
            }
          });
        }
      }

      const handleVisibilityChange = function handleVisibilityChange() {
        root.classList.toggle(
          "v-motion-paused",
          document.visibilityState !== "visible",
        );
      };

      const makeStatic = function makeStatic() {
        root.dataset.vMotion = "static";
        root.classList.remove("v-motion-enabled", "v-motion-paused");
        revealTargets.forEach((target) =>
          target.classList.add("is-visible"),
        );
        scrambleStates.forEach((state) => state.settle());

        if (observer) {
          observer.disconnect();
          observer = null;
        }

        spotlightCleanups.forEach((cleanup) => cleanup());
        if (ambient) {
          ambient.remove();
        }
        if (removeThreatGlobe) {
          removeThreatGlobe();
        }
      };

      const handleReducedMotionChange = function handleReducedMotionChange(
        event,
      ) {
        if (shouldReduceMotion(event, saveData)) {
          makeStatic();
        }
      };
      const handleConnectionChange = function handleConnectionChange() {
        if (connection && connection.saveData) {
          makeStatic();
        }
      };

      document.addEventListener("visibilitychange", handleVisibilityChange);
      if (typeof reducedMotionQuery.addEventListener === "function") {
        reducedMotionQuery.addEventListener(
          "change",
          handleReducedMotionChange,
        );
      }
      if (
        connection &&
        typeof connection.addEventListener === "function"
      ) {
        connection.addEventListener("change", handleConnectionChange);
      }
      handleVisibilityChange();

      return function destroySiteMotion() {
        document.removeEventListener(
          "visibilitychange",
          handleVisibilityChange,
        );
        if (typeof reducedMotionQuery.removeEventListener === "function") {
          reducedMotionQuery.removeEventListener(
            "change",
            handleReducedMotionChange,
          );
        }
        if (
          connection &&
          typeof connection.removeEventListener === "function"
        ) {
          connection.removeEventListener(
            "change",
            handleConnectionChange,
          );
        }
        if (observer) {
          observer.disconnect();
          observer = null;
        }
        spotlightCleanups.forEach((cleanup) => cleanup());
        if (ambient && ambient.isConnected) {
          ambient.remove();
        }
        if (removeThreatGlobe) {
          removeThreatGlobe();
        }
        scrambleStates.forEach((state) => state.restore());
        root.classList.remove("v-motion-enabled", "v-motion-paused");
        restoreElements();
        delete root.dataset.vMotionInitialized;
        delete root.dataset.vMotion;
      };
    }

    return Object.freeze({
      POLICY,
      SELECTORS,
      calculateCanvasBackingStore,
      cappedStaggerDelay,
      countScrambleCharacters,
      createSpherePoints,
      scrambleDelay,
      selectScrambleGlyph,
      shouldReduceMotion,
      init,
    });
  },
);
