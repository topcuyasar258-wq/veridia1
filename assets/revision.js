(() => {
  const primaryLinks = Object.freeze([
    Object.freeze({ href: "/", label: "Ana Sayfa" }),
    Object.freeze({ href: "/neler-yapiyoruz.html", label: "Hizmetlerimiz" }),
    Object.freeze({ href: "/calismalarimiz.html", label: "Portfolyo" }),
    Object.freeze({ href: "/hakkimizda.html", label: "Hakkımızda" }),
    Object.freeze({ href: "/blog.html", label: "Blog" }),
  ]);

  const normalizePath = (value) => {
    const path = value.split("#")[0].split("?")[0];
    return path === "/index.html" ? "/" : path;
  };

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
    <div class="revision-mobile-links">
      ${primaryLinks.map(({ href, label }) => `<a href="${href}" data-revision-close>${label}</a>`).join("")}
    </div>
    <p class="revision-mobile-meta">İstanbul · Türkiye — Dijital büyüme sistemleri</p>
  `;

  const setMenuOpen = (isOpen) => {
    menu.classList.toggle("is-open", isOpen);
    document.body.classList.toggle("revision-menu-open", isOpen);
    menu.setAttribute("aria-hidden", String(!isOpen));
    toggle?.setAttribute("aria-expanded", String(isOpen));
    toggle?.setAttribute("aria-label", isOpen ? "Menüyü kapat" : "Menüyü aç");
  };

  toggle?.setAttribute("aria-controls", menu.id);
  toggle?.addEventListener("click", () => {
    const isOpen = toggle.getAttribute("aria-expanded") === "true";
    setMenuOpen(!isOpen);
  });

  menu.addEventListener("click", (event) => {
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
