(() => {
  const primaryLinks = Object.freeze([
    Object.freeze({ href: "/", label: "Ana Sayfa" }),
    Object.freeze({ label: "Hizmetler", menu: "services" }),
    Object.freeze({ label: "Sektörler", menu: "sectors" }),
    Object.freeze({ href: "/calismalarimiz", label: "Portfolyo" }),
    Object.freeze({ href: "/hakkimizda", label: "Hakkımızda" }),
    Object.freeze({ href: "/blog", label: "Blog" }),
  ]);
  const serviceLinks = Object.freeze([
    Object.freeze({ href: "/yazilim/web-sitesi-ve-donusum-yuzeyleri/", label: "Web Tasarım", description: "Dönüşüm odaklı web ve teklif yüzeyleri" }),
    Object.freeze({ href: "/seo/google-gorunurlugu/", label: "SEO Danışmanlığı", description: "Teknik temel ve sürdürülebilir görünürlük" }),
    Object.freeze({ href: "/reklam/google-ads-yonetimi/", label: "Google Ads", description: "Arama niyetini talebe dönüştüren kampanyalar" }),
    Object.freeze({ href: "/reklam/sosyal-medya-yonetimi/", label: "Sosyal Medya", description: "Planlı içerik ve topluluk yönetimi" }),
  ]);
  const sectorLinks = Object.freeze([
    Object.freeze({ href: "/sektorler/guzellik-merkezleri-icin-dijital-pazarlama/", label: "Güzellik Salonları", description: "Randevu ve yerel görünürlük sistemi" }),
    Object.freeze({ href: "/sektorler/avukatlar-icin-dijital-pazarlama/", label: "Avukatlık", description: "Güven odaklı dijital talep akışı" }),
    Object.freeze({ href: "/sektorler/estetik-klinikleri-icin-dijital-pazarlama/", label: "Estetik Klinikleri", description: "Danışan yolculuğu ve nitelikli talep" }),
    Object.freeze({ href: "/sektorler/dis-klinikleri-icin-dijital-pazarlama/", label: "Diş Klinikleri", description: "Tedavi aramasından randevuya" }),
    Object.freeze({ href: "/sektorler/kuaforler-icin-dijital-pazarlama/", label: "Kuaförler", description: "Yerel keşif ve rezervasyon akışı" }),
    Object.freeze({ href: "/sektorler/yerel-servis-isletmeleri-icin-dijital-pazarlama/", label: "Yerel Servis", description: "Yakındaki aramaları müşteriye dönüştürme" }),
  ]);
  const serviceGroups = Object.freeze([
    Object.freeze({
      label: "Dijital Altyapı",
      links: Object.freeze([
        serviceLinks[0],
        Object.freeze({ href: "/yazilim/web-sitesi-ve-donusum-yuzeyleri/", label: "Dönüşüm Yüzeyleri", description: "Landing page ve teklif akışı" }),
      ]),
    }),
    Object.freeze({
      label: "Google Görünürlüğü",
      links: Object.freeze([
        serviceLinks[1],
        Object.freeze({ href: "/seo/teknik-seo-denetimi/", label: "Teknik SEO Denetimi", description: "Kritik teknik sorunların önceliklendirilmesi" }),
        Object.freeze({ href: "/seo/google-gorunurlugu/", label: "Google Görünürlüğü", description: "Doğru aramalarda kalıcı görünürlük" }),
      ]),
    }),
    Object.freeze({
      label: "Reklam ve Talep",
      links: Object.freeze([
        serviceLinks[2],
        serviceLinks[3],
        Object.freeze({ href: "/hizli-teklif", label: "Hızlı Teklif Akışı", description: "İhtiyacınıza göre hızlı proje kapsamı" }),
      ]),
    }),
  ]);
  const megaMenus = Object.freeze([
    Object.freeze({
      id: "services",
      eyebrow: "Hizmetler",
      title: "Tek sistem, dört büyüme alanı.",
      description: "Web, SEO, reklam ve sosyal medyayı aynı müşteri kazanım hedefinde birleştiriyoruz.",
      groups: serviceGroups,
      spotlight: Object.freeze({
        href: "/hizmetler/",
        label: "Tüm hizmetleri incele",
        description: "Doğru başlangıç noktasını birlikte belirleyelim.",
      }),
    }),
    Object.freeze({
      id: "sectors",
      eyebrow: "Sektörler",
      title: "İş modelinize göre kurgulanan yaklaşım.",
      description: "Hazır kalıplar yerine, müşterinizin karar yolculuğuna göre çalışan bir sistem kuruyoruz.",
      groups: Object.freeze([
        Object.freeze({ label: "Uzmanlık Alanları", links: sectorLinks }),
      ]),
      spotlight: Object.freeze({
        href: "/sektorler/",
        label: "Tüm sektörleri keşfet",
        description: "Sektörünüze uygun sayfa ve talep akışını görün.",
      }),
    }),
  ]);

  const normalizePath = (value) => {
    const path = value.split("#")[0].split("?")[0];
    return path === "/index.html" ? "/" : path;
  };
  const renderSubLinks = (links) => links.map(({ href, label }) => `<li><a href="${href}" data-revision-close>${label}</a></li>`).join("");
  const renderAccordion = ({ id, label, groups }) => `
    <section class="revision-menu-section" data-revision-accordion>
      <button class="revision-menu-trigger" type="button" id="${id}-trigger" aria-expanded="false" aria-controls="${id}-panel" data-revision-accordion-trigger>
        <span>${label}</span>
        <span class="revision-menu-arrow" aria-hidden="true"></span>
      </button>
      <div class="revision-menu-panel" id="${id}-panel" role="region" aria-labelledby="${id}-trigger" hidden>
        ${groups
          .map(
            ({ label, links, className = "", labelMarkup = "" }) => `
              <div class="revision-menu-group${className ? ` ${className}` : ""}">
                ${labelMarkup || (label ? `<p class="revision-mobile-section-label">${label}</p>` : "")}
                <ul class="revision-menu-sublist">
                  ${renderSubLinks(links)}
                </ul>
              </div>
            `,
          )
          .join("")}
      </div>
    </section>
  `;
  const renderMegaLinks = (links) => links
    .map(({ href, label, description = "" }) => `
      <li>
        <a class="revision-mega-link" href="${href}" data-revision-mega-close>
          <span>${label}</span>
          ${description ? `<small>${description}</small>` : ""}
        </a>
      </li>
    `)
    .join("");
  const renderMegaMenu = ({ id, eyebrow, title, description, groups, spotlight }) => `
    <section class="revision-nav-mega" id="revision-${id}-mega" data-revision-mega="${id}" aria-label="${eyebrow} menüsü" hidden>
      <div class="revision-mega-shell">
        <header class="revision-mega-intro">
          <p>${eyebrow}</p>
          <h2>${title}</h2>
          <span>${description}</span>
        </header>
        <div class="revision-mega-grid">
          ${groups.map(({ label, links }) => `
            <div class="revision-mega-group">
              <p>${label}</p>
              <ul>${renderMegaLinks(links)}</ul>
            </div>
          `).join("")}
          <a class="revision-mega-spotlight" href="${spotlight.href}" data-revision-mega-close>
            <span class="revision-mega-spotlight-label">${spotlight.label}</span>
            <span>${spotlight.description}</span>
            <strong aria-hidden="true">↗</strong>
          </a>
        </div>
      </div>
    </section>
  `;

  const currentPath = normalizePath(window.location.pathname);
  const nav = document.querySelector("#navbar, body > nav[aria-label='Ana Menü']");
  const existingList = nav?.querySelector(".nav-links");
  const announcement = document.querySelector(".revision-announcement") || document.createElement("aside");
  const navOverlay = document.querySelector(".revision-nav-overlay") || document.createElement("button");

  if (nav && !announcement.isConnected) {
    announcement.className = "revision-announcement";
    announcement.setAttribute("aria-label", "Duyuru");
    announcement.innerHTML = `
      <a href="/hizli-teklif">
        <span class="revision-announcement-copy">Web, SEO ve reklamı tek müşteri kazanım sisteminde birleştirin.</span>
        <span class="revision-announcement-action">Ücretsiz mini analiz</span>
        <span aria-hidden="true">↗</span>
      </a>
    `;
    nav.before(announcement);
  }

  if (nav && !navOverlay.isConnected) {
    navOverlay.className = "revision-nav-overlay";
    navOverlay.type = "button";
    navOverlay.tabIndex = -1;
    navOverlay.setAttribute("aria-label", "Açık menüyü kapat");
    nav.after(navOverlay);
  }

  if (nav && existingList) {
    nav.setAttribute("aria-label", "Ana Menü");
    nav.querySelector(".nav-logo")?.setAttribute("aria-label", "Veridia Ana Sayfa");
    const listTag = existingList.tagName.toLowerCase();
    const linkMarkup = primaryLinks
      .map(({ href, label, menu: menuId }) => {
        if (menuId) {
          const trigger = `
            <button
              class="revision-nav-trigger"
              type="button"
              id="revision-${menuId}-trigger"
              aria-expanded="false"
              aria-haspopup="true"
              aria-controls="revision-${menuId}-mega"
              data-revision-mega-trigger="${menuId}"
            >
              <span>${label}</span>
              <span class="revision-nav-trigger-arrow" aria-hidden="true"></span>
            </button>
          `;
          return listTag === "ul" ? `<li class="revision-nav-item">${trigger}</li>` : trigger;
        }

        const isCurrent = normalizePath(href) === currentPath;
        const link = `<a href="${href}"${isCurrent ? ' aria-current="page"' : ""}>${label}</a>`;
        return listTag === "ul" ? `<li>${link}</li>` : link;
      })
      .join("");

    existingList.innerHTML = linkMarkup;

    let actionSlot = nav.querySelector(".nav-mobile-right, .nav-actions");
    if (!actionSlot) {
      actionSlot = document.createElement("div");
      actionSlot.className = "nav-actions";
      const menuToggle = nav.querySelector("[data-mobile-toggle], .hamburger");
      if (menuToggle) {
        nav.insertBefore(actionSlot, menuToggle);
        actionSlot.append(menuToggle);
      } else {
        nav.append(actionSlot);
      }
    }

    const appendBeforeMenu = (element) => {
      const menuToggle = actionSlot.querySelector("[data-mobile-toggle], .hamburger");
      if (menuToggle) {
        actionSlot.insertBefore(element, menuToggle);
      } else {
        actionSlot.append(element);
      }
    };

    if (!nav.querySelector(".revision-nav-theme")) {
      const themeButton = document.createElement("button");
      themeButton.className = "revision-nav-theme";
      themeButton.type = "button";
      themeButton.setAttribute("data-theme-toggle", "");
      themeButton.innerHTML = '<span class="theme-toggle-icon" data-theme-icon aria-hidden="true">🌙</span><span data-theme-label>Koyu</span>';
      appendBeforeMenu(themeButton);
    }

    if (!nav.querySelector(".revision-nav-cta")) {
      const cta = document.createElement("a");
      cta.className = "revision-nav-cta";
      cta.href = "https://wa.me/905055174654?text=Merhaba%20Veridia%2C%20projemi%20konu%C5%9Fmak%20istiyorum.";
      cta.setAttribute("data-whatsapp-message", "Merhaba Veridia, projemi konuşmak istiyorum.");
      cta.target = "_blank";
      cta.rel = "noopener";
      cta.textContent = "Proje Başlat";
      appendBeforeMenu(cta);
    }

    nav.insertAdjacentHTML("beforeend", megaMenus.map(renderMegaMenu).join(""));
  }

  const existingMenu = document.querySelector("#mobileMenu, .mobile-menu");
  const menu = existingMenu || document.createElement("div");
  const toggle = document.querySelector("[data-mobile-toggle], .hamburger");

  if (!existingMenu) {
    menu.id = "mobileMenu";
    menu.className = "mobile-menu";
    document.body.prepend(menu);
  }

  menu.classList.add("revision-mobile-menu");
  menu.setAttribute("aria-hidden", "true");
  menu.innerHTML = `
    <div class="revision-mobile-shell">
      <div class="revision-mobile-head">
        <a class="revision-mobile-brand" href="/" data-revision-close aria-label="Veridia Ana Sayfa">
          <span class="revision-mobile-mark" aria-hidden="true">V</span>
          <span>Veridia</span>
        </a>
        <button class="revision-menu-close" type="button" data-revision-close aria-label="Menüyü kapat"></button>
      </div>

      <div class="revision-mobile-links" aria-label="Mobil menü">
        ${renderAccordion({ id: "revision-mobile-services", label: "Hizmetler", groups: serviceGroups })}
        ${renderAccordion({ id: "revision-mobile-sectors", label: "Sektörler", groups: [Object.freeze({ label: "Sektörler", links: sectorLinks, className: "revision-mobile-sector-group", labelMarkup: '<p class="revision-mobile-section-label">Sektörler</p>' })] })}
        <a class="revision-menu-link" href="/calismalarimiz" data-revision-close>Portfolyo</a>
        <a class="revision-menu-link" href="/hakkimizda" data-revision-close>Hakkımızda</a>
        <a class="revision-menu-link" href="/blog" data-revision-close>Blog</a>
      </div>

      <div class="revision-mobile-actions" aria-label="Hızlı aksiyonlar">
        <button class="revision-mobile-pill" type="button" data-theme-toggle>
          <span aria-hidden="true">☼</span>
          <span>Açık</span>
        </button>
        <a class="revision-mobile-pill" href="/iletisim" data-revision-close>İletişime Geç</a>
      </div>
    </div>
  `;

  const megaTriggers = [...(nav?.querySelectorAll("[data-revision-mega-trigger]") || [])];
  const megaPanels = [...(nav?.querySelectorAll("[data-revision-mega]") || [])];
  let activeMegaTrigger = null;

  const setMegaMenu = (menuId) => {
    megaTriggers.forEach((trigger) => {
      const isActive = trigger.dataset.revisionMegaTrigger === menuId;
      trigger.setAttribute("aria-expanded", String(isActive));
      trigger.closest(".revision-nav-item")?.classList.toggle("is-active", isActive);
      if (isActive) activeMegaTrigger = trigger;
    });

    megaPanels.forEach((panel) => {
      const isActive = panel.dataset.revisionMega === menuId;
      if (isActive) {
        panel.hidden = false;
      } else {
        panel.hidden = true;
      }
      panel.classList.toggle("is-open", isActive);
    });

    const isOpen = Boolean(menuId);
    nav?.classList.toggle("has-open-mega", isOpen);
    navOverlay.classList.toggle("is-open", isOpen);
    navOverlay.setAttribute("aria-hidden", String(!isOpen));
    if (!isOpen) activeMegaTrigger = null;
  };

  megaTriggers.forEach((trigger) => {
    trigger.addEventListener("click", (event) => {
      event.preventDefault();
      const menuId = trigger.dataset.revisionMegaTrigger;
      const nextMenu = trigger.getAttribute("aria-expanded") === "true" ? null : menuId;
      setMegaMenu(nextMenu);
    });

    trigger.addEventListener("pointerenter", (event) => {
      if (event.pointerType === "touch" || window.matchMedia("(max-width: 1000px)").matches) return;
      setMegaMenu(trigger.dataset.revisionMegaTrigger);
    });
  });

  nav?.addEventListener("pointerleave", (event) => {
    if (event.pointerType === "touch" || window.matchMedia("(max-width: 1000px)").matches) return;
    setMegaMenu(null);
  });

  nav?.addEventListener("focusout", (event) => {
    if (event.relatedTarget && nav.contains(event.relatedTarget)) return;
    setMegaMenu(null);
  });

  nav?.addEventListener("click", (event) => {
    if (event.target.closest("[data-revision-mega-close]")) setMegaMenu(null);
  });

  navOverlay.addEventListener("click", () => setMegaMenu(null));
  window.addEventListener("resize", () => {
    if (window.matchMedia("(max-width: 1000px)").matches) setMegaMenu(null);
  }, { passive: true });
  setMegaMenu(null);

  let previousFocus = null;

  const setMenuOpen = (isOpen) => {
    const wasOpen = menu.classList.contains("is-open");
    if (isOpen && !wasOpen) previousFocus = document.activeElement;
    if (isOpen) setMegaMenu(null);

    menu.classList.toggle("is-open", isOpen);
    menu.classList.toggle("open", isOpen);
    toggle?.classList.toggle("open", isOpen);
    document.body.classList.toggle("revision-menu-open", isOpen);
    document.body.style.overflow = isOpen ? "hidden" : "";
    menu.setAttribute("aria-hidden", String(!isOpen));
    toggle?.setAttribute("aria-expanded", String(isOpen));
    toggle?.setAttribute("aria-label", isOpen ? "Menüyü kapat" : "Menüyü aç");

    if (isOpen) {
      window.requestAnimationFrame(() => {
        menu.querySelector(".revision-menu-close")?.focus({ preventScroll: true });
      });
    } else if (wasOpen) {
      previousFocus?.focus({ preventScroll: true });
      previousFocus = null;
    }
  };

  toggle?.setAttribute("aria-controls", menu.id);
  setMenuOpen(false);

  toggle?.addEventListener("click", (event) => {
    event.preventDefault();
    event.stopPropagation();
    const isOpen = toggle.getAttribute("aria-expanded") === "true";
    setMenuOpen(!isOpen);
  });

  menu.addEventListener("click", (event) => {
    const trigger = event.target.closest("[data-revision-accordion-trigger]");
    if (trigger) {
      const item = trigger.closest("[data-revision-accordion]");
      const panel = item?.querySelector(".revision-menu-panel");
      const isExpanded = trigger.getAttribute("aria-expanded") === "true";
      trigger.setAttribute("aria-expanded", String(!isExpanded));
      item?.classList.toggle("is-expanded", !isExpanded);
      if (panel) panel.hidden = isExpanded;
      return;
    }
    if (event.target.closest("[data-revision-close]")) setMenuOpen(false);
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && nav?.classList.contains("has-open-mega")) {
      const triggerToRestore = activeMegaTrigger;
      setMegaMenu(null);
      triggerToRestore?.focus({ preventScroll: true });
      return;
    }

    if (!menu.classList.contains("is-open")) return;

    if (event.key === "Escape") {
      setMenuOpen(false);
      return;
    }

    if (event.key === "Tab") {
      const focusableElements = [...menu.querySelectorAll('a[href], button:not([disabled]), [tabindex]:not([tabindex="-1"])')]
        .filter((element) => element.getClientRects().length > 0);
      const firstElement = focusableElements[0];
      const lastElement = focusableElements.at(-1);

      if (event.shiftKey && document.activeElement === firstElement) {
        event.preventDefault();
        lastElement?.focus();
      } else if (!event.shiftKey && document.activeElement === lastElement) {
        event.preventDefault();
        firstElement?.focus();
      }
    }
  });

  const updateHeader = () => nav?.classList.toggle("is-scrolled", window.scrollY > 24);
  updateHeader();
  window.addEventListener("scroll", updateHeader, { passive: true });

  const revealElements = [...document.querySelectorAll(".reveal")];
  if ("IntersectionObserver" in window) {
    const observer = new IntersectionObserver(
      (entries, activeObserver) => {
        entries
          .filter(({ isIntersecting }) => isIntersecting)
          .forEach(({ target }) => {
            target.classList.add("is-visible");
            activeObserver.unobserve(target);
          });
      },
      { threshold: 0.12 },
    );
    revealElements.forEach((element) => observer.observe(element));
  } else {
    revealElements.forEach((element) => element.classList.add("is-visible"));
  }
})();
