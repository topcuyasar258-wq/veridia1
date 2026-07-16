!function (e) {
  const t = e.document;
  const STORAGE_KEY = "veridia-campaign-popup-seen";
  const WHATSAPP_NUMBER = "905055174654";
  const WHATSAPP_MESSAGE = "Merhaba Veridia, %50 indirim kampanyasından yararlanmak istiyorum.";
  const SHOW_DELAY_MS = 1200;

  function alreadySeen() {
    try {
      return e.sessionStorage.getItem(STORAGE_KEY) === "1";
    } catch (err) {
      return false;
    }
  }

  function markSeen() {
    try {
      e.sessionStorage.setItem(STORAGE_KEY, "1");
    } catch (err) {
      /* sessionStorage unavailable (private mode, etc.) — popup will just show again next time */
    }
  }

  function injectStyles() {
    if (t.getElementById("veridia-campaign-popup-styles")) return;
    const style = t.createElement("style");
    style.id = "veridia-campaign-popup-styles";
    style.textContent = `
#veridiaCampaignOverlay{position:fixed;inset:0;z-index:10000;display:flex;align-items:center;justify-content:center;padding:1.25rem;background:rgba(10,15,13,.72);backdrop-filter:blur(6px);opacity:0;transition:opacity .35s ease;}
#veridiaCampaignOverlay.is-visible{opacity:1;}
#veridiaCampaignOverlay.is-closing{opacity:0;}
#veridiaCampaignPopup{position:relative;width:100%;max-width:430px;background:var(--surface-1);border:1px solid var(--line-strong);border-radius:20px;box-shadow:var(--shadow-strong);padding:2.25rem 1.75rem 1.75rem;text-align:center;transform:translateY(18px) scale(.97);transition:transform .35s ease;font-family:"DM Sans",sans-serif;color:var(--off-white);}
#veridiaCampaignOverlay.is-visible #veridiaCampaignPopup{transform:translateY(0) scale(1);}
#veridiaCampaignPopup .vcp-close{position:absolute;top:.85rem;right:.85rem;width:2.1rem;height:2.1rem;border:1px solid var(--line-soft);border-radius:50%;background:transparent;color:var(--off-white);font-size:1.1rem;line-height:1;cursor:pointer;display:flex;align-items:center;justify-content:center;}
#veridiaCampaignPopup .vcp-close:hover{background:var(--surface-strong);}
#veridiaCampaignPopup .vcp-badge{display:inline-block;padding:.35rem .9rem;border-radius:999px;background:rgba(45,106,79,.16);border:1px solid var(--line-strong);color:var(--gold-light);font-size:.72rem;font-weight:700;letter-spacing:.08em;text-transform:uppercase;margin-bottom:1rem;}
#veridiaCampaignPopup h2{font-size:1.5rem;line-height:1.25;margin-bottom:.65rem;}
#veridiaCampaignPopup p{font-size:.95rem;line-height:1.55;color:var(--text-muted);margin-bottom:1.1rem;}
#veridiaCampaignPopup .vcp-price{display:flex;align-items:baseline;justify-content:center;gap:.6rem;margin-bottom:1.4rem;}
#veridiaCampaignPopup .vcp-price-old{font-size:1.05rem;color:var(--text-muted);text-decoration:line-through;}
#veridiaCampaignPopup .vcp-price-new{font-size:1.6rem;font-weight:700;color:var(--gold-light);}
#veridiaCampaignPopup .btn-gold{display:block;width:100%;text-align:center;box-sizing:border-box;margin-bottom:.75rem;}
#veridiaCampaignPopup .vcp-dismiss{background:none;border:none;color:var(--text-muted);font-size:.85rem;text-decoration:underline;cursor:pointer;padding:.25rem;}
@media (max-width:480px){#veridiaCampaignPopup{padding:2rem 1.35rem 1.5rem;}#veridiaCampaignPopup h2{font-size:1.3rem;}}
`;
    t.head.appendChild(style);
  }

  function buildPopup() {
    const overlay = t.createElement("div");
    overlay.id = "veridiaCampaignOverlay";
    overlay.setAttribute("aria-hidden", "true");

    const waHref =
      "https://wa.me/" + WHATSAPP_NUMBER + "?text=" + encodeURIComponent(WHATSAPP_MESSAGE);

    overlay.innerHTML = `
      <div id="veridiaCampaignPopup" role="dialog" aria-modal="true" aria-labelledby="vcpTitle">
        <button type="button" class="vcp-close" aria-label="Kapat">&times;</button>
        <span class="vcp-badge">Sınırlı Süre Kampanyası</span>
        <h2 id="vcpTitle">Web Sitenizde %50 İndirim</h2>
        <p>Dönüşüm odaklı, mobilde hızlı çalışan profesyonel web sitesi paketlerinde bu ay geçerli kampanya fiyatlarıyla başlayın.</p>
        <div class="vcp-price">
          <span class="vcp-price-old">40.000 TL</span>
          <span class="vcp-price-new">20.000 TL'den başlayan</span>
        </div>
        <a class="btn-gold" href="${waHref}" data-whatsapp-message="${WHATSAPP_MESSAGE}" target="_blank" rel="noopener">Kampanyadan Yararlan</a>
        <button type="button" class="vcp-dismiss">Şimdi değil</button>
      </div>
    `;
    return overlay;
  }

  function showPopup() {
    if (alreadySeen()) return;
    injectStyles();
    const overlay = buildPopup();
    t.body.appendChild(overlay);

    const previousOverflow = t.body.style.overflow;
    t.body.style.overflow = "hidden";

    function close() {
      markSeen();
      overlay.classList.add("is-closing");
      overlay.classList.remove("is-visible");
      t.body.style.overflow = previousOverflow;
      overlay.addEventListener(
        "transitionend",
        () => overlay.remove(),
        { once: true }
      );
      setTimeout(() => overlay.isConnected && overlay.remove(), 500);
    }

    overlay.addEventListener("click", (ev) => {
      if (ev.target === overlay) close();
    });
    overlay.querySelector(".vcp-close").addEventListener("click", close);
    overlay.querySelector(".vcp-dismiss").addEventListener("click", close);
    overlay.querySelector(".btn-gold").addEventListener("click", () => markSeen());
    t.addEventListener("keydown", function onKey(ev) {
      if (ev.key === "Escape") {
        close();
        t.removeEventListener("keydown", onKey);
      }
    });

    requestAnimationFrame(() => {
      overlay.classList.add("is-visible");
      overlay.querySelector(".vcp-close").focus();
    });
  }

  if (t.readyState === "loading") {
    t.addEventListener("DOMContentLoaded", () => setTimeout(showPopup, SHOW_DELAY_MS));
  } else {
    setTimeout(showPopup, SHOW_DELAY_MS);
  }
}(typeof window !== "undefined" ? window : globalThis);
