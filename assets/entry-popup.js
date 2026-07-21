;(function (window) {
  const document = window.document
  const STORAGE_KEY = 'veridia-campaign-popup-seen'
  const SHOW_DELAY_MS = 1400
  const WHATSAPP_NUMBER = (window.VERIDIA_CONFIG && window.VERIDIA_CONFIG.whatsapp) || '905055174654'
  const WHATSAPP_MESSAGE =
    'Merhaba Veridia, web sitesi kampanyası için ücretsiz ön görüşme almak istiyorum.'

  function alreadySeen() {
    try {
      return window.sessionStorage.getItem(STORAGE_KEY) === '1'
    } catch (err) {
      return false
    }
  }

  function markSeen() {
    try {
      window.sessionStorage.setItem(STORAGE_KEY, '1')
    } catch (err) {
      // sessionStorage kapalıysa popup yalnızca bir sonraki ziyarette tekrar görünebilir.
    }
  }

  function buildWhatsAppUrl(message) {
    if (typeof window.buildVeridiaWhatsAppUrl === 'function') {
      return window.buildVeridiaWhatsAppUrl(message)
    }

    const number = String(WHATSAPP_NUMBER || '').replace(/\D/g, '')
    const encodedMessage = encodeURIComponent(String(message || ''))
    return /^\d{10,15}$/.test(number)
      ? `https://wa.me/${number}?text=${encodedMessage}`
      : `https://wa.me/?text=${encodedMessage}`
  }

  function injectStyles() {
    if (document.getElementById('veridia-campaign-popup-styles')) return

    const style = document.createElement('style')
    style.id = 'veridia-campaign-popup-styles'
    style.textContent = `
#veridiaCampaignOverlay{position:fixed;inset:0;z-index:10000;display:flex;align-items:center;justify-content:center;padding:1.25rem;background:rgba(6,10,9,.62);backdrop-filter:blur(8px) saturate(1.04);opacity:0;transition:opacity .28s ease;}
#veridiaCampaignOverlay.is-visible{opacity:1;}
#veridiaCampaignOverlay.is-closing{opacity:0;}
#veridiaCampaignPopup{position:relative;width:min(100%,500px);max-height:min(92svh,680px);overflow:auto;border:1px solid rgba(93,159,131,.34);border-radius:18px;background:radial-gradient(circle at 14% 0,rgba(93,159,131,.2),transparent 32%),linear-gradient(150deg,rgba(18,31,27,.98),rgba(9,16,14,.98));box-shadow:0 30px 88px rgba(0,0,0,.46),inset 0 1px rgba(255,255,255,.05);color:var(--off-white,#f4f1ea);font-family:"DM Sans",sans-serif;padding:1.75rem;transform:translateY(16px) scale(.98);transition:transform .28s ease;}
#veridiaCampaignPopup:focus{outline:none;}
#veridiaCampaignOverlay.is-visible #veridiaCampaignPopup{transform:translateY(0) scale(1);}
#veridiaCampaignPopup .vcp-close{position:absolute;top:1rem;right:1rem;width:2.5rem;height:2.5rem;border:1px solid rgba(255,255,255,.12);border-radius:999px;background:rgba(255,255,255,.04);color:var(--off-white,#f4f1ea);font-size:1.2rem;line-height:1;cursor:pointer;display:flex;align-items:center;justify-content:center;transition:background .18s,border-color .18s,transform .18s;}
#veridiaCampaignPopup .vcp-close:hover{background:rgba(255,255,255,.09);border-color:rgba(93,159,131,.45);transform:rotate(4deg);}
#veridiaCampaignPopup .vcp-eyebrow{display:inline-flex;align-items:center;gap:.5rem;max-width:calc(100% - 3.2rem);border:1px solid rgba(93,159,131,.42);border-radius:999px;background:rgba(93,159,131,.12);color:#91c9aa;font-size:.68rem;font-weight:800;letter-spacing:.13em;text-transform:uppercase;padding:.48rem .78rem;margin-bottom:1rem;}
#veridiaCampaignPopup h2{max-width:14ch;margin:0 0 .65rem;color:var(--off-white,#f4f1ea);font-family:"Cormorant Garamond",serif;font-size:clamp(1.9rem,6vw,2.65rem);font-weight:600;line-height:1;letter-spacing:0;}
#veridiaCampaignPopup .vcp-copy{max-width:32rem;margin:0 0 .9rem;color:var(--text-muted,#96a59d);font-size:.96rem;line-height:1.55;}
#veridiaCampaignPopup .vcp-offer{display:grid;grid-template-columns:1fr auto;gap:1rem;align-items:end;border-block:1px solid rgba(93,159,131,.2);padding:.9rem 0;margin:0 0 .9rem;}
#veridiaCampaignPopup .vcp-offer small{display:block;color:var(--text-muted,#96a59d);font-size:.78rem;line-height:1.35;}
#veridiaCampaignPopup .vcp-offer strong{display:block;margin-top:.25rem;color:#91c9aa;font-size:1.28rem;line-height:1.2;}
#veridiaCampaignPopup .vcp-price-old{color:rgba(244,241,234,.56);font-size:.95rem;text-decoration:line-through;text-align:right;white-space:nowrap;}
#veridiaCampaignPopup .vcp-points{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:.5rem;margin:0 0 1rem;}
#veridiaCampaignPopup .vcp-point{border:1px solid rgba(255,255,255,.08);border-radius:8px;background:rgba(255,255,255,.035);padding:.66rem .64rem;}
#veridiaCampaignPopup .vcp-point strong{display:block;color:var(--off-white,#f4f1ea);font-size:.84rem;line-height:1.25;}
#veridiaCampaignPopup .vcp-point span{display:block;margin-top:.22rem;color:var(--text-muted,#96a59d);font-size:.72rem;line-height:1.35;}
#veridiaCampaignPopup .vcp-actions{display:grid;gap:.72rem;}
#veridiaCampaignPopup .vcp-primary{display:flex;align-items:center;justify-content:center;width:100%;min-height:3.35rem;border:1px solid rgba(244,241,234,.18);background:linear-gradient(135deg,#9bb18b,#6f8d70);color:#08120f;text-align:center;text-decoration:none;text-transform:uppercase;letter-spacing:.12em;font-size:.8rem;font-weight:900;padding:1rem 1.15rem;box-shadow:0 18px 42px rgba(93,159,131,.2);transition:transform .18s,filter .18s;}
#veridiaCampaignPopup .vcp-primary:hover{filter:brightness(1.05);transform:translateY(-1px);}
#veridiaCampaignPopup .vcp-secondary{border:0;background:transparent;color:var(--text-muted,#96a59d);font-size:.86rem;text-decoration:underline;text-underline-offset:4px;cursor:pointer;padding:.35rem;}
#veridiaCampaignPopup .vcp-secondary:hover{color:var(--off-white,#f4f1ea);}
#veridiaCampaignPopup .vcp-note{margin:.75rem 0 0;color:rgba(244,241,234,.54);font-size:.74rem;line-height:1.4;text-align:center;}
[data-theme="light"] #veridiaCampaignOverlay{background:rgba(16,36,29,.24);backdrop-filter:blur(8px) saturate(1.02);}
[data-theme="light"] #veridiaCampaignPopup{border-color:rgba(31,75,54,.18);background:radial-gradient(circle at 14% 0,rgba(45,106,79,.09),transparent 34%),linear-gradient(150deg,rgba(255,255,255,.98),rgba(247,250,247,.96));box-shadow:0 30px 88px rgba(31,75,54,.16),inset 0 1px rgba(255,255,255,.78);color:#10241d;}
[data-theme="light"] #veridiaCampaignPopup .vcp-close{border-color:rgba(31,75,54,.16);background:rgba(45,106,79,.06);color:#10241d;}
[data-theme="light"] #veridiaCampaignPopup .vcp-close:hover{background:rgba(45,106,79,.1);border-color:rgba(45,106,79,.34);}
[data-theme="light"] #veridiaCampaignPopup .vcp-eyebrow{border-color:rgba(45,106,79,.28);background:rgba(45,106,79,.08);color:#245f45;}
[data-theme="light"] #veridiaCampaignPopup h2,[data-theme="light"] #veridiaCampaignPopup .vcp-point strong{color:#10241d;}
[data-theme="light"] #veridiaCampaignPopup .vcp-copy,[data-theme="light"] #veridiaCampaignPopup .vcp-offer small,[data-theme="light"] #veridiaCampaignPopup .vcp-point span{color:#50645b;}
[data-theme="light"] #veridiaCampaignPopup .vcp-offer{border-block-color:rgba(31,75,54,.16);}
[data-theme="light"] #veridiaCampaignPopup .vcp-offer strong{color:#245f45;}
[data-theme="light"] #veridiaCampaignPopup .vcp-price-old{color:rgba(16,36,29,.48);}
[data-theme="light"] #veridiaCampaignPopup .vcp-point{border-color:rgba(31,75,54,.14);background:rgba(255,255,255,.72);}
[data-theme="light"] #veridiaCampaignPopup .vcp-primary{border-color:rgba(36,95,69,.32);background:linear-gradient(135deg,#245f45,#347a58);color:#fff;box-shadow:0 18px 42px rgba(45,106,79,.2);}
[data-theme="light"] #veridiaCampaignPopup .vcp-secondary{color:#50645b;}
[data-theme="light"] #veridiaCampaignPopup .vcp-secondary:hover{color:#10241d;}
[data-theme="light"] #veridiaCampaignPopup .vcp-note{color:rgba(16,36,29,.58);}
@media (max-width:560px){#veridiaCampaignOverlay{align-items:flex-end;padding:.85rem;}#veridiaCampaignPopup{width:100%;border-radius:16px;padding:1.35rem 1.05rem 1.05rem;}#veridiaCampaignPopup .vcp-close{top:.72rem;right:.72rem;width:2.35rem;height:2.35rem;}#veridiaCampaignPopup .vcp-eyebrow{margin-bottom:.75rem;font-size:.62rem;letter-spacing:.1em;}#veridiaCampaignPopup h2{max-width:15ch;font-size:clamp(1.85rem,9vw,2.25rem);line-height:1.02;}#veridiaCampaignPopup .vcp-copy{font-size:.9rem;line-height:1.48;margin-bottom:.75rem;}#veridiaCampaignPopup .vcp-offer{grid-template-columns:1fr;gap:.35rem;padding:.72rem 0;margin-bottom:.72rem;}#veridiaCampaignPopup .vcp-offer strong{font-size:1.08rem;}#veridiaCampaignPopup .vcp-price-old{text-align:left;font-size:.86rem;}#veridiaCampaignPopup .vcp-points{grid-template-columns:1fr;gap:.35rem;margin-bottom:.8rem;}#veridiaCampaignPopup .vcp-point{padding:.5rem .62rem;}#veridiaCampaignPopup .vcp-point span{display:none;}#veridiaCampaignPopup .vcp-primary{min-height:3rem;font-size:.7rem;letter-spacing:.08em;padding:.82rem 1rem;}#veridiaCampaignPopup .vcp-secondary{font-size:.82rem;padding:.2rem;}#veridiaCampaignPopup .vcp-note{display:none;}}
@media (prefers-reduced-motion:reduce){#veridiaCampaignOverlay,#veridiaCampaignPopup,#veridiaCampaignPopup .vcp-close,#veridiaCampaignPopup .vcp-primary{transition:none!important;transform:none!important;}}
`
    document.head.appendChild(style)
  }

  function buildPopup() {
    const overlay = document.createElement('div')
    overlay.id = 'veridiaCampaignOverlay'
    overlay.setAttribute('aria-hidden', 'true')

    const waHref = buildWhatsAppUrl(WHATSAPP_MESSAGE)
    overlay.innerHTML = `
      <div id="veridiaCampaignPopup" role="dialog" aria-modal="true" aria-labelledby="vcpTitle" aria-describedby="vcpDescription" tabindex="-1">
        <button type="button" class="vcp-close" aria-label="Kampanya penceresini kapat">&times;</button>
        <span class="vcp-eyebrow">Bu ay web sitesi başlangıcı</span>
        <h2 id="vcpTitle">Web Siteniz Teklif Getirsin</h2>
        <p id="vcpDescription" class="vcp-copy">Bu ay web sitesi sprintine indirimli başlayın; mobil hız, Google altyapısı ve WhatsApp/form akışı tek planda netleşsin.</p>
        <div class="vcp-offer">
          <div>
            <small>Başlangıç teklifi</small>
            <strong>20.000 TL'den başlayan web sitesi sprinti</strong>
          </div>
          <span class="vcp-price-old">40.000 TL paket değeri</span>
        </div>
        <div class="vcp-points" aria-label="Kampanya kapsamı">
          <div class="vcp-point"><strong>Net mesaj</strong><span>İlk ekranda anlaşılır teklif dili</span></div>
          <div class="vcp-point"><strong>Mobil hız</strong><span>Telefondan kolay iletişim akışı</span></div>
          <div class="vcp-point"><strong>CTA kurgusu</strong><span>WhatsApp, form ve teklif yönlendirmesi</span></div>
        </div>
        <div class="vcp-actions">
          <a class="vcp-primary" href="${waHref}" data-whatsapp-message="${WHATSAPP_MESSAGE}" target="_blank" rel="noopener">Ücretsiz Ön Görüşme Al</a>
          <button type="button" class="vcp-secondary">Şimdilik kapat</button>
        </div>
        <p class="vcp-note">Ön görüşmede sitenizin hangi noktada müşteri kaybettiğini birlikte netleştiririz.</p>
      </div>
    `
    return overlay
  }

  function showPopup() {
    if (alreadySeen() || !document.body) return

    injectStyles()
    const overlay = buildPopup()
    const previousOverflow = document.body.style.overflow
    const previousFocus = document.activeElement
    document.body.appendChild(overlay)
    document.body.style.overflow = 'hidden'

    const popup = overlay.querySelector('#veridiaCampaignPopup')
    const closeButton = overlay.querySelector('.vcp-close')
    const dismissButton = overlay.querySelector('.vcp-secondary')
    const primaryButton = overlay.querySelector('.vcp-primary')

    function restoreFocus() {
      if (previousFocus && typeof previousFocus.focus === 'function') {
        previousFocus.focus({ preventScroll: true })
      }
    }

    function close() {
      markSeen()
      overlay.classList.add('is-closing')
      overlay.classList.remove('is-visible')
      overlay.setAttribute('aria-hidden', 'true')
      document.body.style.overflow = previousOverflow
      document.removeEventListener('keydown', onKeydown)
      overlay.addEventListener(
        'transitionend',
        () => {
          overlay.remove()
          restoreFocus()
        },
        { once: true }
      )
      setTimeout(() => {
        if (overlay.isConnected) {
          overlay.remove()
          restoreFocus()
        }
      }, 420)
    }

    function onKeydown(event) {
      if (event.key === 'Escape') {
        event.preventDefault()
        close()
        return
      }

      if (event.key !== 'Tab') return
      const focusable = [...overlay.querySelectorAll('a[href],button:not([disabled])')]
      if (!focusable.length) return
      const first = focusable[0]
      const last = focusable[focusable.length - 1]

      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault()
        last.focus()
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault()
        first.focus()
      }
    }

    overlay.addEventListener('click', (event) => {
      if (event.target === overlay) close()
    })
    closeButton.addEventListener('click', close)
    dismissButton.addEventListener('click', close)
    primaryButton.addEventListener('click', markSeen)
    document.addEventListener('keydown', onKeydown)

    window.requestAnimationFrame(() => {
      overlay.classList.add('is-visible')
      overlay.setAttribute('aria-hidden', 'false')
      popup.focus({ preventScroll: true })
    })
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => setTimeout(showPopup, SHOW_DELAY_MS))
  } else {
    setTimeout(showPopup, SHOW_DELAY_MS)
  }
})(typeof window !== 'undefined' ? window : globalThis)
