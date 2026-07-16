!function (e) {
  const t = e.document;
  const STORAGE_KEY = "veridia-campaign-popup-seen";
  const WHATSAPP_NUMBER = "905055174654";
  const WHATSAPP_MESSAGE = "Merhaba Deniz, %50 indirim kampanyası hakkında bilgi almak istiyorum.";
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
#veridiaCampaignPopup{position:relative;width:100%;max-width:410px;background:var(--surface-1);border:1px solid var(--line-strong);border-radius:26px 26px 6px 26px;box-shadow:var(--shadow-strong);padding:1.9rem 1.6rem 1.6rem;text-align:left;transform:translateY(18px) scale(.97) rotate(-.4deg);transition:transform .35s ease;font-family:"DM Sans",sans-serif;color:var(--off-white);}
#veridiaCampaignOverlay.is-visible #veridiaCampaignPopup{transform:translateY(0) scale(1) rotate(0deg);}
#veridiaCampaignPopup .vcp-close{position:absolute;top:.85rem;right:.85rem;width:2.1rem;height:2.1rem;border:1px solid var(--line-soft);border-radius:50%;background:transparent;color:var(--off-white);font-size:1.1rem;line-height:1;cursor:pointer;display:flex;align-items:center;justify-content:center;}
#veridiaCampaignPopup .vcp-close:hover{background:var(--surface-strong);}
#veridiaCampaignPopup .vcp-who{display:flex;align-items:center;gap:.7rem;margin-bottom:1rem;}
#veridiaCampaignPopup .vcp-avatar{flex:none;width:2.75rem;height:2.75rem;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:1.05rem;color:var(--charcoal);background:linear-gradient(135deg,var(--gold-light),var(--emerald));}
#veridiaCampaignPopup .vcp-who-name{font-weight:700;font-size:.95rem;line-height:1.2;}
#veridiaCampaignPopup .vcp-who-meta{font-size:.78rem;color:var(--text-muted);}
#veridiaCampaignPopup .vcp-message{font-size:.97rem;line-height:1.6;color:var(--off-white);margin-bottom:1.3rem;}
#veridiaCampaignPopup .vcp-message s{color:var(--text-muted);}
#veridiaCampaignPopup .vcp-message strong{color:var(--gold-light);}
#veridiaCampaignPopup .btn-gold{display:block;width:100%;text-align:center;box-sizing:border-box;margin-bottom:.6rem;}
#veridiaCampaignPopup .vcp-fineprint{display:block;text-align:center;font-size:.74rem;color:var(--text-muted);margin-bottom:.5rem;}
#veridiaCampaignPopup .vcp-dismiss{display:block;margin:0 auto;background:none;border:none;color:var(--text-muted);font-size:.85rem;text-decoration:underline;cursor:pointer;padding:.25rem;}
@media (max-width:480px){#veridiaCampaignPopup{padding:1.7rem 1.3rem 1.4rem;}}
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
        <div class="vcp-who">
          <div class="vcp-avatar" aria-hidden="true">D</div>
          <div>
            <div class="vcp-who-name">Deniz · Veridia</div>
            <div class="vcp-who-meta">az önce</div>
          </div>
        </div>
        <p id="vcpTitle" class="vcp-message">Merhaba 👋 Bu ay yeni gelen markalara küçük bir jestimiz var: normalde <s>40.000 TL</s> olan web sitesi paketini <strong>20.000 TL'ye</strong> çekiyoruz. İster direkt merhaba deyin, ister aklınıza takılan bir şeyi sorun, ben bakarım.</p>
        <a class="btn-gold" href="${waHref}" data-whatsapp-message="${WHATSAPP_MESSAGE}" target="_blank" rel="noopener">WhatsApp'tan Yaz</a>
        <span class="vcp-fineprint">Bu ay için geçerli, kontenjan sınırlı</span>
        <button type="button" class="vcp-dismiss">Şimdilik geç</button>
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
