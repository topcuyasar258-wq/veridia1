(() => {
  const primaryLinks = Object.freeze([
    Object.freeze({ href: "/", label: "Ana Sayfa" }),
    Object.freeze({ href: "/hizmetler/", label: "Hizmetlerimiz" }),
    Object.freeze({ href: "/sektorler/", label: "Sektörler" }),
    Object.freeze({ href: "/calismalarimiz.html", label: "Portfolyo" }),
    Object.freeze({ href: "/hakkimizda.html", label: "Hakkımızda" }),
    Object.freeze({ href: "/blog.html", label: "Blog" }),
  ]);
  const serviceLinks = Object.freeze([
    Object.freeze({ href: "/hizmetler/web-tasarim/", label: "Web Tasarım" }),
    Object.freeze({ href: "/hizmetler/seo-danismanligi/", label: "SEO Danışmanlığı" }),
    Object.freeze({ href: "/hizmetler/google-ads-yonetimi/", label: "Google Ads" }),
    Object.freeze({ href: "/hizmetler/sosyal-medya-yonetimi/", label: "Sosyal Medya" }),
  ]);
  const sectorLinks = Object.freeze([
    Object.freeze({ href: "/sektorler/guzellik-merkezleri-icin-dijital-pazarlama/", label: "Güzellik Salonları" }),
    Object.freeze({ href: "/sektorler/avukatlar-icin-dijital-pazarlama/", label: "Avukatlık" }),
    Object.freeze({ href: "/sektorler/estetik-klinikleri-icin-dijital-pazarlama/", label: "Estetik Klinikleri" }),
    Object.freeze({ href: "/sektorler/dis-klinikleri-icin-dijital-pazarlama/", label: "Diş Klinikleri" }),
    Object.freeze({ href: "/sektorler/kuaforler-icin-dijital-pazarlama/", label: "Kuaförler" }),
    Object.freeze({ href: "/sektorler/yerel-servis-isletmeleri-icin-dijital-pazarlama/", label: "Yerel Servis" }),
  ]);
  const serviceGroups = Object.freeze([
    Object.freeze({
      label: "Dijital Altyapı",
      links: Object.freeze([
        serviceLinks[0],
        Object.freeze({ href: "/yazilim/web-sitesi-ve-donusum-yuzeyleri/", label: "Dönüşüm Yüzeyleri" }),
      ]),
    }),
    Object.freeze({
      label: "Google Görünürlüğü",
      links: Object.freeze([
        serviceLinks[1],
        Object.freeze({ href: "/seo/teknik-seo-denetimi/", label: "Teknik SEO Denetimi" }),
        Object.freeze({ href: "/seo/google-gorunurlugu/", label: "Google Görünürlüğü" }),
      ]),
    }),
    Object.freeze({
      label: "Reklam ve Talep",
      links: Object.freeze([
        serviceLinks[2],
        serviceLinks[3],
        Object.freeze({ href: "/hizli-teklif.html", label: "Hızlı Teklif Akışı" }),
      ]),
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

  const currentPath = normalizePath(window.location.pathname);
  const nav = document.querySelector("#navbar, body > nav[aria-label='Ana Menü']");
  const existingList = nav?.querySelector(".nav-links");

  if (nav && existingList) {
    const listTag = existingList.tagName.toLowerCase();
    const linkMarkup = primaryLinks
      .map(({ href, label }) => {
        const isCurrent = normalizePath(href) === currentPath;
        const link = `<a href="${href}"${isCurrent ? ' aria-current="page"' : ""}>${label}</a>`;
        return listTag === "ul" ? `<li>${link}</li>` : link;
      })
      .join("");

    existingList.innerHTML = linkMarkup;

    if (!nav.querySelector(".revision-nav-cta")) {
      const cta = document.createElement("a");
      cta.className = "revision-nav-cta";
      cta.href = "https://wa.me/905055174654?text=Merhaba%20Veridia%2C%20projemi%20konu%C5%9Fmak%20istiyorum.";
      cta.setAttribute("data-whatsapp-message", "Merhaba Veridia, projemi konuşmak istiyorum.");
      cta.target = "_blank";
      cta.rel = "noopener";
      cta.textContent = "Proje Başlat";
      const actionSlot = nav.querySelector(".nav-mobile-right, .nav-actions");
      (actionSlot || nav).append(cta);
    }
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
        ${renderAccordion({ id: "revision-services", label: "Hizmetler", groups: serviceGroups })}
        ${renderAccordion({ id: "revision-sectors", label: "Sektörler", groups: [Object.freeze({ label: "Sektörler", links: sectorLinks, className: "revision-mobile-sector-group", labelMarkup: '<p class="revision-mobile-section-label">Sektörler</p>' })] })}
        <a class="revision-menu-link" href="/calismalarimiz.html" data-revision-close>Portfolyo</a>
        <a class="revision-menu-link" href="/hakkimizda.html" data-revision-close>Hakkımızda</a>
        <a class="revision-menu-link" href="/blog.html" data-revision-close>Blog</a>
      </div>

      <div class="revision-mobile-actions" aria-label="Hızlı aksiyonlar">
        <button class="revision-mobile-pill" type="button" data-theme-toggle>
          <span aria-hidden="true">☼</span>
          <span>Açık</span>
        </button>
        <a class="revision-mobile-pill" href="/iletisim.html" data-revision-close>İletişime Geç</a>
      </div>
    </div>
  `;

  const setMenuOpen = (isOpen) => {
    menu.classList.toggle("is-open", isOpen);
    menu.classList.toggle("open", isOpen);
    toggle?.classList.toggle("open", isOpen);
    document.body.classList.toggle("revision-menu-open", isOpen);
    document.body.style.overflow = isOpen ? "hidden" : "";
    menu.setAttribute("aria-hidden", String(!isOpen));
    toggle?.setAttribute("aria-expanded", String(isOpen));
    toggle?.setAttribute("aria-label", isOpen ? "Menüyü kapat" : "Menüyü aç");
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
    if (event.key === "Escape") setMenuOpen(false);
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
