(function initWorkPages(root) {
  const doc = root.document;
  const prefersReducedMotion = root.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const revealNodes = Array.from(doc.querySelectorAll(".reveal"));

  if (prefersReducedMotion) {
    revealNodes.forEach((node) => node.classList.add("visible"));
  } else if ("IntersectionObserver" in root) {
    const revealObserver = new IntersectionObserver((entries, observer) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) {
          return;
        }

        entry.target.classList.add("visible");
        observer.unobserve(entry.target);
      });
    }, {
      threshold: 0.16
    });

    revealNodes.forEach((node) => revealObserver.observe(node));
  } else {
    revealNodes.forEach((node) => node.classList.add("visible"));
  }

  const anchorLinks = Array.from(doc.querySelectorAll(".page-anchor-nav a[href^=\"#\"]"));
  const sectionTargets = anchorLinks
    .map((link) => doc.querySelector(link.getAttribute("href")))
    .filter(Boolean);

  if (anchorLinks.length && sectionTargets.length && "IntersectionObserver" in root) {
    const activateLink = (id) => {
      anchorLinks.forEach((link) => {
        const isActive = link.getAttribute("href") === `#${id}`;
        link.setAttribute("aria-current", String(isActive));
      });
    };

    const sectionObserver = new IntersectionObserver((entries) => {
      const visibleEntry = entries
        .filter((entry) => entry.isIntersecting)
        .sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];

      if (visibleEntry?.target?.id) {
        activateLink(visibleEntry.target.id);
      }
    }, {
      rootMargin: "-25% 0px -55% 0px",
      threshold: [0.1, 0.32, 0.54]
    });

    sectionTargets.forEach((section) => sectionObserver.observe(section));

    if (sectionTargets[0]?.id) {
      activateLink(sectionTargets[0].id);
    }
  }
})(typeof window !== "undefined" ? window : globalThis);
