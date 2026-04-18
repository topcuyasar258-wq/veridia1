const VERIDIA_CONFIG = Object.freeze({
  whatsapp: "905055174654",
  email: "hello@veridia.com.tr",
  siteUrl: "https://veridiareklam.com.tr",
  gaMeasurementId: "G-0972DPKMC7"
});
const WHATSAPP_NUMBER = VERIDIA_CONFIG.whatsapp;

(function initVeridiaConfig(root) {
  root.VERIDIA_CONFIG = VERIDIA_CONFIG;
  root.WHATSAPP_NUMBER = WHATSAPP_NUMBER;

  function buildVeridiaWhatsAppUrl(message = "") {
    const cleanPhone = String(WHATSAPP_NUMBER || "").replace(/\D/g, "");
    const encodedMessage = encodeURIComponent(String(message || ""));

    if (/^\d{10,15}$/.test(cleanPhone)) {
      return `https://wa.me/${cleanPhone}?text=${encodedMessage}`;
    }

    return `https://wa.me/?text=${encodedMessage}`;
  }

  function applyConfigLinks(scope) {
    if (!scope || typeof scope.querySelectorAll !== "function") {
      return;
    }

    scope.querySelectorAll("[data-whatsapp-message]").forEach((element) => {
      element.setAttribute("href", buildVeridiaWhatsAppUrl(element.dataset.whatsappMessage || ""));

      if (!element.hasAttribute("target")) {
        element.setAttribute("target", "_blank");
      }

      if (!element.hasAttribute("rel")) {
        element.setAttribute("rel", "noopener");
      }
    });
  }

  root.buildVeridiaWhatsAppUrl = buildVeridiaWhatsAppUrl;
  root.applyVeridiaConfigLinks = applyConfigLinks;

  if (typeof document !== "undefined") {
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", () => applyConfigLinks(document));
    } else {
      applyConfigLinks(document);
    }
  }
})(typeof window !== "undefined" ? window : globalThis);
