;(function (window) {
  const document = window.document
  const form = document.getElementById("analysisForm")
  const leadForm = document.getElementById("leadForm")
  const statusBox = document.getElementById("analysisStatus")
  const results = document.getElementById("analysisResults")
  const submitButton = document.getElementById("analysisSubmit")
  const formNote = document.getElementById("analysisFormNote")
  const leadMessage = document.getElementById("leadMessage")

  let latestReport = null

  const labels = {
    good: { icon: "✓", text: "İyi" },
    warning: { icon: "!", text: "Uyarı" },
    critical: { icon: "×", text: "Kritik" },
  }

  function normalizeUrl(value) {
    const trimmed = String(value || "").trim()
    if (!trimmed) return ""
    if (/^https?:\/\//i.test(trimmed)) return trimmed
    return `https://${trimmed}`
  }

  function setStatus(message, type) {
    statusBox.hidden = !message
    statusBox.textContent = message || ""
    statusBox.classList.toggle("is-error", type === "error")
  }

  function setLoading(isLoading) {
    document.body.classList.toggle("is-loading", isLoading)
    submitButton.disabled = isLoading
    submitButton.textContent = isLoading ? "Analiz Ediliyor" : "Analiz Et"
  }

  function escapeHtml(value) {
    return String(value || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;")
  }

  function scoreText(value) {
    return Number.isFinite(Number(value)) ? String(Math.round(Number(value))) : "0"
  }

  function metricValue(metric) {
    if (!metric) return "Alınamadı"
    if (metric.displayValue) return metric.displayValue
    if (Number.isFinite(metric.numericValue)) return `${Math.round(metric.numericValue)} ms`
    return "Alınamadı"
  }

  function renderMetrics(metrics) {
    const metricItems = [
      ["LCP", metricValue(metrics.lcp)],
      ["CLS", metricValue(metrics.cls)],
      [metrics.inp ? "INP" : "TBT", metricValue(metrics.inp || metrics.tbt)],
      ["Kaynak", "PageSpeed mobile"],
    ]
    document.getElementById("metricsStrip").innerHTML = metricItems
      .map(
        ([label, value]) => `
          <article class="metric-pill">
            <span>${escapeHtml(label)}</span>
            <strong>${escapeHtml(value)}</strong>
          </article>
        `
      )
      .join("")
  }

  function renderFindings(findings) {
    document.getElementById("findingsList").innerHTML = findings
      .map((finding) => {
        const label = labels[finding.status] || labels.warning
        return `
          <article class="finding-item" data-status="${escapeHtml(finding.status)}">
            <span class="finding-icon" aria-hidden="true">${label.icon}</span>
            <div>
              <div class="finding-meta">
                <span class="finding-category">${escapeHtml(finding.category)}</span>
                <span class="finding-status">${escapeHtml(label.text)}</span>
              </div>
              <h3>${escapeHtml(finding.title)}</h3>
              <p>${escapeHtml(finding.explanation)}</p>
              <p><strong>Nasıl düzeltilir:</strong> ${escapeHtml(finding.fix)}</p>
            </div>
          </article>
        `
      })
      .join("")
  }

  function renderResults(report) {
    latestReport = report
    const scores = report.scores || {}
    const categories = scores.categories || {}
    document.getElementById("overallScore").textContent = scoreText(scores.overall)
    document.getElementById("speedScore").textContent = scoreText(categories.speed)
    document.getElementById("technicalScore").textContent = scoreText(categories.technicalSeo)
    document.getElementById("contentScore").textContent = scoreText(categories.content)
    document.getElementById("mobileScore").textContent = scoreText(categories.mobile)
    document.getElementById("scoreUrl").textContent = report.finalUrl || report.analyzedUrl || "-"
    renderMetrics(report.metrics || {})
    renderFindings(report.findings || [])
    results.hidden = false
    results.scrollIntoView({ behavior: "smooth", block: "start" })

    if (typeof window.applyVeridiaConfigLinks === "function") {
      window.applyVeridiaConfigLinks(results)
    }
  }

  async function postJson(payload) {
    const response = await fetch("/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    })
    const body = await response.json().catch(() => ({}))
    if (!response.ok) {
      throw new Error(body.error?.message || "İstek tamamlanamadı.")
    }
    return body.data
  }

  form?.addEventListener("submit", async (event) => {
    event.preventDefault()
    const input = document.getElementById("analysisUrl")
    const url = normalizeUrl(input.value)
    if (!url) {
      formNote.textContent = "Analiz için bir URL girin."
      input.focus()
      return
    }

    input.value = url
    setLoading(true)
    setStatus("Sayfa alınıyor, PageSpeed mobil testi çalışıyor ve on-page sinyaller kontrol ediliyor.", "info")
    results.hidden = true
    leadMessage.textContent = ""

    try {
      const report = await postJson({ action: "analyze", url })
      setStatus(report.warnings?.length ? report.warnings.join(" ") : "Analiz tamamlandı.", "info")
      renderResults(report)
    } catch (error) {
      setStatus(error.message, "error")
    } finally {
      setLoading(false)
    }
  })

  leadForm?.addEventListener("submit", async (event) => {
    event.preventDefault()
    leadMessage.textContent = ""

    if (!latestReport) {
      leadMessage.textContent = "Önce bir site analizi oluşturun."
      return
    }

    const email = document.getElementById("leadEmail").value.trim()
    const phone = document.getElementById("leadPhone").value.trim()
    const consent = document.getElementById("leadConsent").checked

    if (!consent) {
      leadMessage.textContent = "PDF talebi için açık rıza kutusunu işaretlemeniz gerekir."
      return
    }

    try {
      await postJson({
        action: "lead",
        email,
        phone,
        consent,
        url: latestReport.analyzedUrl,
        reportId: latestReport.reportId,
      })
      leadForm.reset()
      leadMessage.textContent = "Talebiniz alındı. Ekibimiz raporu PDF olarak iletmek için sizinle iletişime geçecek."
    } catch (error) {
      leadMessage.textContent = error.message
    }
  })
})("undefined" !== typeof window ? window : globalThis)
