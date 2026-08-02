const dns = require("node:dns").promises
const crypto = require("node:crypto")
const net = require("node:net")

const MAX_REQUEST_BYTES = 16 * 1024
const MAX_HTML_BYTES = 2 * 1024 * 1024
const MAX_ALT_CHECK_BYTES = 64 * 1024
const FETCH_TIMEOUT_MS = 10_000
const PSI_TIMEOUT_MS = Number.parseInt(process.env.PSI_TIMEOUT_MS || "60000", 10)
const MAX_REDIRECTS = 3
const RATE_LIMIT = 10
const RATE_LIMIT_WINDOW_SECONDS = 60 * 60
const memoryRateLimits = new Map()

class HttpError extends Error {
  constructor(status, code, message, retryAfter = null) {
    super(message)
    this.status = status
    this.code = code
    this.retryAfter = retryAfter
  }
}

function writeJson(res, status, payload, headers = {}) {
  Object.entries(headers).forEach(([key, value]) => res.setHeader(key, value))
  res.statusCode = status
  res.setHeader("Content-Type", "application/json; charset=utf-8")
  res.end(JSON.stringify(payload))
}

function cleanHostname(hostname) {
  return String(hostname || "")
    .trim()
    .replace(/^\[/, "")
    .replace(/\]$/, "")
    .toLowerCase()
}

function parseIPv4(ip) {
  const parts = String(ip).split(".")
  if (parts.length !== 4) return null
  const nums = parts.map((part) => {
    if (!/^\d{1,3}$/.test(part)) return Number.NaN
    return Number(part)
  })
  if (nums.some((num) => !Number.isInteger(num) || num < 0 || num > 255)) return null
  return nums
}

function isPrivateIPv4(ip) {
  const parts = parseIPv4(ip)
  if (!parts) return false
  const [a, b] = parts
  return (
    a === 0 ||
    a === 10 ||
    a === 127 ||
    (a === 169 && b === 254) ||
    (a === 172 && b >= 16 && b <= 31) ||
    (a === 192 && b === 168) ||
    a >= 224
  )
}

function isPrivateIPv6(ip) {
  const value = String(ip).toLowerCase()
  if (value === "::" || value === "::1") return true
  if (value.startsWith("::ffff:")) {
    const mapped = value.replace("::ffff:", "")
    if (mapped.includes(".")) return isPrivateIPv4(mapped)
    return true
  }
  return (
    value.startsWith("fc") ||
    value.startsWith("fd") ||
    value.startsWith("fe8") ||
    value.startsWith("fe9") ||
    value.startsWith("fea") ||
    value.startsWith("feb") ||
    value.startsWith("ff") ||
    value.startsWith("2001:db8")
  )
}

function isBlockedIp(ip) {
  const kind = net.isIP(ip)
  if (kind === 4) return isPrivateIPv4(ip)
  if (kind === 6) return isPrivateIPv6(ip)
  return false
}

function validatePublicUrl(rawUrl) {
  let parsed
  try {
    parsed = new URL(String(rawUrl || "").trim())
  } catch (_error) {
    throw new HttpError(422, "invalid_url", "Geçerli bir URL girin.")
  }

  if (!["http:", "https:"].includes(parsed.protocol)) {
    throw new HttpError(422, "invalid_scheme", "Yalnızca http veya https URL'leri analiz edilebilir.")
  }

  parsed.hash = ""
  parsed.username = ""
  parsed.password = ""
  return parsed
}

async function assertPublicHostname(url) {
  const hostname = cleanHostname(url.hostname)
  if (!hostname || hostname === "localhost" || hostname.endsWith(".localhost")) {
    throw new HttpError(422, "blocked_host", "Bu host güvenlik nedeniyle analiz edilemez.")
  }

  if (net.isIP(hostname)) {
    if (isBlockedIp(hostname)) {
      throw new HttpError(422, "blocked_ip", "Özel veya yerel IP adresleri analiz edilemez.")
    }
    return
  }

  let records
  try {
    records = await dns.lookup(hostname, { all: true, verbatim: true })
  } catch (_error) {
    throw new HttpError(422, "dns_lookup_failed", "Alan adı çözümlenemedi.")
  }

  if (!records.length || records.some((record) => isBlockedIp(record.address))) {
    throw new HttpError(422, "blocked_resolved_ip", "Alan adı özel veya yerel bir IP adresine çözülüyor.")
  }
}

async function readRequestJson(req) {
  if (req.body && typeof req.body === "object") return req.body
  if (typeof req.body === "string") return JSON.parse(req.body || "{}")

  let total = 0
  const chunks = []
  for await (const chunk of req) {
    total += chunk.length
    if (total > MAX_REQUEST_BYTES) {
      throw new HttpError(413, "request_too_large", "İstek gövdesi çok büyük.")
    }
    chunks.push(chunk)
  }

  const raw = Buffer.concat(chunks).toString("utf8")
  if (!raw.trim()) return {}
  try {
    return JSON.parse(raw)
  } catch (_error) {
    throw new HttpError(400, "invalid_json", "Geçerli JSON gönderin.")
  }
}

async function readLimitedText(response, maxBytes) {
  const reader = response.body?.getReader?.()
  if (!reader) {
    const text = await response.text()
    if (Buffer.byteLength(text, "utf8") > maxBytes) {
      throw new HttpError(413, "response_too_large", "Sayfa içeriği 2MB sınırını aşıyor.")
    }
    return text
  }

  let total = 0
  const chunks = []
  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    total += value.byteLength
    if (total > maxBytes) {
      reader.cancel().catch(() => {})
      throw new HttpError(413, "response_too_large", "Sayfa içeriği 2MB sınırını aşıyor.")
    }
    chunks.push(Buffer.from(value))
  }

  return Buffer.concat(chunks).toString("utf8")
}

async function fetchWithGuards(startUrl, options = {}) {
  let current = validatePublicUrl(startUrl)
  const maxBytes = options.maxBytes || MAX_HTML_BYTES
  const method = options.method || "GET"
  const visited = []

  for (let redirectCount = 0; redirectCount <= MAX_REDIRECTS; redirectCount += 1) {
    await assertPublicHostname(current)
    visited.push(current.toString())

    const controller = new AbortController()
    const timeout = setTimeout(() => controller.abort(), FETCH_TIMEOUT_MS)
    let response
    try {
      response = await fetch(current.toString(), {
        method,
        redirect: "manual",
        signal: controller.signal,
        headers: {
          "User-Agent": "VeridiaSiteAnalizi/1.0 (+https://www.veridiareklam.com.tr/araclar/site-analizi/)",
          Accept: "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        },
      })
    } catch (error) {
      if (error.name === "AbortError") {
        throw new HttpError(504, "fetch_timeout", "Hedef sayfa 10 saniye içinde yanıt vermedi.")
      }
      throw new HttpError(502, "fetch_failed", "Hedef sayfa alınamadı.")
    } finally {
      clearTimeout(timeout)
    }

    if ([301, 302, 303, 307, 308].includes(response.status)) {
      const location = response.headers.get("location")
      if (!location) {
        throw new HttpError(502, "redirect_without_location", "Hedef sayfa geçersiz bir yönlendirme döndürdü.")
      }
      if (redirectCount === MAX_REDIRECTS) {
        throw new HttpError(508, "too_many_redirects", "Hedef sayfa 3 yönlendirmeden fazla yönlendiriyor.")
      }
      current = validatePublicUrl(new URL(location, current).toString())
      continue
    }

    const text = method === "HEAD" ? "" : await readLimitedText(response, maxBytes)
    return {
      finalUrl: current.toString(),
      status: response.status,
      contentType: response.headers.get("content-type") || "",
      html: text,
      redirects: visited.length - 1,
      redirectChain: visited,
    }
  }

  throw new HttpError(508, "too_many_redirects", "Hedef sayfa 3 yönlendirmeden fazla yönlendiriyor.")
}

function redisConfig() {
  const url = process.env.UPSTASH_REDIS_REST_URL || process.env.KV_REST_API_URL
  const token = process.env.UPSTASH_REDIS_REST_TOKEN || process.env.KV_REST_API_TOKEN
  return url && token ? { url: url.replace(/\/$/, ""), token } : null
}

function enforceMemoryRateLimit(key) {
  const now = Date.now()
  const windowMs = RATE_LIMIT_WINDOW_SECONDS * 1000
  const active = (memoryRateLimits.get(key) || []).filter((timestamp) => now - timestamp < windowMs)
  if (active.length >= RATE_LIMIT) {
    const retryAfter = Math.max(60, Math.ceil((windowMs - (now - active[0])) / 1000))
    throw new HttpError(429, "rate_limit_exceeded", "Saatlik analiz limitine ulaşıldı.", retryAfter)
  }
  active.push(now)
  memoryRateLimits.set(key, active)
  return {
    limit: RATE_LIMIT,
    remaining: Math.max(0, RATE_LIMIT - active.length),
    resetSeconds: RATE_LIMIT_WINDOW_SECONDS,
  }
}

async function redisCommand(command, ...args) {
  const config = redisConfig()
  if (!config) {
    throw new HttpError(
      503,
      "rate_limit_store_missing",
      "Rate limit için Upstash Redis veya Vercel KV yapılandırılmalı."
    )
  }

  const response = await fetch(config.url, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${config.token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify([command, ...args]),
  })
  const payload = await response.json().catch(() => ({}))
  if (!response.ok || payload.error) {
    throw new HttpError(503, "rate_limit_store_failed", "Rate limit deposuna ulaşılamadı.")
  }
  return payload.result
}

function clientIp(req) {
  const forwarded = req.headers["x-forwarded-for"]
  const raw = Array.isArray(forwarded) ? forwarded[0] : forwarded
  return String(raw || req.socket?.remoteAddress || "unknown")
    .split(",")[0]
    .trim()
}

function rateKeyForIp(ip) {
  const salt = process.env.RATE_LIMIT_SALT || "veridia-site-analysis"
  const hash = crypto.createHash("sha256").update(`${salt}:${ip}`).digest("hex")
  return `site-analysis:rate:${hash}`
}

async function enforceRateLimit(req) {
  const key = rateKeyForIp(clientIp(req))
  if (!redisConfig()) return enforceMemoryRateLimit(key)
  const count = Number(await redisCommand("INCR", key))
  if (count === 1) await redisCommand("EXPIRE", key, RATE_LIMIT_WINDOW_SECONDS)
  if (count > RATE_LIMIT) {
    const ttl = Math.max(60, Number(await redisCommand("TTL", key)) || RATE_LIMIT_WINDOW_SECONDS)
    throw new HttpError(429, "rate_limit_exceeded", "Saatlik analiz limitine ulaşıldı.", ttl)
  }
  return {
    limit: RATE_LIMIT,
    remaining: Math.max(0, RATE_LIMIT - count),
    resetSeconds: Number(await redisCommand("TTL", key)) || RATE_LIMIT_WINDOW_SECONDS,
  }
}

function decodeHtml(value) {
  const named = { amp: "&", lt: "<", gt: ">", quot: '"', apos: "'", nbsp: " " }
  return String(value || "")
    .replace(/<[^>]+>/g, " ")
    .replace(/&(#x?[0-9a-f]+|[a-z]+);/gi, (match, entity) => {
      const lower = entity.toLowerCase()
      if (named[lower]) return named[lower]
      if (lower.startsWith("#x")) return String.fromCodePoint(Number.parseInt(lower.slice(2), 16))
      if (lower.startsWith("#")) return String.fromCodePoint(Number.parseInt(lower.slice(1), 10))
      return match
    })
    .replace(/\s+/g, " ")
    .trim()
}

function parseAttributes(tag) {
  const attrs = {}
  const pattern = /([a-zA-Z_:][-a-zA-Z0-9_:.]*)\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s"'>=]+))/g
  let match
  while ((match = pattern.exec(tag))) {
    attrs[match[1].toLowerCase()] = decodeHtml(match[2] || match[3] || match[4] || "")
  }
  return attrs
}

function tagsByName(html, name) {
  const pattern = new RegExp(`<${name}\\b[^>]*>`, "gi")
  return html.match(pattern) || []
}

function metaContent(html, key, value) {
  const wanted = String(value).toLowerCase()
  for (const tag of tagsByName(html, "meta")) {
    const attrs = parseAttributes(tag)
    if (String(attrs[key] || "").toLowerCase() === wanted) return attrs.content || ""
  }
  return ""
}

function linkAttrsByRel(html, relName) {
  const wanted = String(relName).toLowerCase()
  return tagsByName(html, "link")
    .map(parseAttributes)
    .filter((attrs) =>
      String(attrs.rel || "")
        .toLowerCase()
        .split(/\s+/)
        .includes(wanted)
    )
}

function collectJsonLdTypes(html) {
  const blocks = [...html.matchAll(/<script\b[^>]*type=["']application\/ld\+json["'][^>]*>([\s\S]*?)<\/script>/gi)]
  const types = new Set()

  function visit(value) {
    if (Array.isArray(value)) {
      value.forEach(visit)
      return
    }
    if (!value || typeof value !== "object") return
    const type = value["@type"]
    if (typeof type === "string") types.add(type)
    if (Array.isArray(type)) type.forEach((item) => typeof item === "string" && types.add(item))
    Object.values(value).forEach(visit)
  }

  blocks.forEach((block) => {
    try {
      visit(JSON.parse(block[1]))
    } catch (_error) {
      types.add("Geçersiz JSON-LD")
    }
  })

  return [...types]
}

function analyzeHtml(html, requestedUrl, fetchMeta = {}) {
  const title = decodeHtml((html.match(/<title\b[^>]*>([\s\S]*?)<\/title>/i) || [])[1] || "")
  const description = decodeHtml(metaContent(html, "name", "description"))
  const robots = metaContent(html, "name", "robots")
  const h1Count = (html.match(/<h1\b[^>]*>/gi) || []).length
  const canonical = linkAttrsByRel(html, "canonical")[0]?.href || ""
  const viewport = metaContent(html, "name", "viewport")
  const ogTitle = metaContent(html, "property", "og:title")
  const ogImage = metaContent(html, "property", "og:image")
  const schemaTypes = collectJsonLdTypes(html)
  const hreflangs = linkAttrsByRel(html, "alternate")
    .filter((attrs) => attrs.hreflang)
    .map((attrs) => attrs.hreflang)
  const imgTags = tagsByName(html, "img").map(parseAttributes)
  const imagesWithAlt = imgTags.filter((attrs) => String(attrs.alt || "").trim()).length
  const altPercent = imgTags.length ? Math.round((imagesWithAlt / imgTags.length) * 100) : 100
  const requested = validatePublicUrl(requestedUrl)
  const final = validatePublicUrl(fetchMeta.finalUrl || requestedUrl)

  return {
    title: { exists: Boolean(title), value: title, length: title.length, inRange: title.length >= 30 && title.length <= 60 },
    description: {
      exists: Boolean(description),
      value: description,
      length: description.length,
      inRange: description.length >= 120 && description.length <= 160,
    },
    h1: { count: h1Count, single: h1Count === 1 },
    canonical: { exists: Boolean(canonical), href: canonical },
    viewport: { exists: Boolean(viewport), value: viewport },
    openGraph: { hasTitle: Boolean(ogTitle), hasImage: Boolean(ogImage) },
    schema: { exists: schemaTypes.length > 0, types: schemaTypes },
    images: { total: imgTags.length, withAlt: imagesWithAlt, altPercent },
    robots: { value: robots, noindex: /\bnoindex\b/i.test(robots) },
    hreflang: { exists: hreflangs.length > 0, values: hreflangs },
    https: { requested: requested.protocol === "https:", final: final.protocol === "https:" },
    redirect: { finalUrl: final.toString(), redirects: fetchMeta.redirects || 0 },
  }
}

async function checkWwwConsistency(url) {
  const parsed = validatePublicUrl(url)
  const host = parsed.hostname
  const alternateHost = host.startsWith("www.") ? host.slice(4) : `www.${host}`
  if (net.isIP(cleanHostname(host))) {
    return { checked: false, consistent: null, note: "IP adreslerinde www kontrolü uygulanmaz." }
  }

  const alternate = new URL(parsed.toString())
  alternate.hostname = alternateHost

  try {
    const original = await fetchWithGuards(parsed.toString(), { method: "HEAD", maxBytes: MAX_ALT_CHECK_BYTES })
    const alternateResult = await fetchWithGuards(alternate.toString(), { method: "HEAD", maxBytes: MAX_ALT_CHECK_BYTES })
    const originalFinalHost = validatePublicUrl(original.finalUrl).hostname.replace(/^www\./, "")
    const alternateFinalHost = validatePublicUrl(alternateResult.finalUrl).hostname.replace(/^www\./, "")
    return {
      checked: true,
      consistent: originalFinalHost === alternateFinalHost,
      primaryFinalUrl: original.finalUrl,
      alternateFinalUrl: alternateResult.finalUrl,
    }
  } catch (_error) {
    return { checked: false, consistent: null, note: "Alternatif www/non-www sürümü doğrulanamadı." }
  }
}

function scoreFromCategory(category) {
  return typeof category?.score === "number" ? Math.round(category.score * 100) : null
}

function auditMetric(audits, id) {
  const audit = audits?.[id]
  if (!audit) return null
  return {
    id,
    numericValue: typeof audit.numericValue === "number" ? audit.numericValue : null,
    displayValue: audit.displayValue || "",
    score: typeof audit.score === "number" ? audit.score : null,
  }
}

function extractPsi(psi) {
  const lhr = psi?.lighthouseResult || {}
  const categories = lhr.categories || {}
  const audits = lhr.audits || {}
  const inp = auditMetric(audits, "interaction-to-next-paint")
  const tbt = auditMetric(audits, "total-blocking-time")

  return {
    scores: {
      performance: scoreFromCategory(categories.performance),
      accessibility: scoreFromCategory(categories.accessibility),
      bestPractices: scoreFromCategory(categories["best-practices"]),
      seo: scoreFromCategory(categories.seo),
    },
    metrics: {
      lcp: auditMetric(audits, "largest-contentful-paint"),
      cls: auditMetric(audits, "cumulative-layout-shift"),
      inp: inp || null,
      tbt: inp ? null : tbt,
    },
  }
}

async function fetchPsi(url) {
  const endpoint = new URL("https://www.googleapis.com/pagespeedonline/v5/runPagespeed")
  endpoint.searchParams.set("url", url)
  endpoint.searchParams.set("strategy", "mobile")
  endpoint.searchParams.set("category", "performance")
  endpoint.searchParams.append("category", "accessibility")
  endpoint.searchParams.append("category", "best-practices")
  endpoint.searchParams.append("category", "seo")
  if (process.env.PSI_API_KEY) endpoint.searchParams.set("key", process.env.PSI_API_KEY)

  const controller = new AbortController()
  const timeout = setTimeout(() => controller.abort(), PSI_TIMEOUT_MS)
  try {
    const response = await fetch(endpoint.toString(), { signal: controller.signal })
    const payload = await response.json().catch(() => ({}))
    if (!response.ok) {
      throw new HttpError(502, "psi_failed", payload.error?.message || "PageSpeed Insights yanıtı alınamadı.")
    }
    return extractPsi(payload)
  } finally {
    clearTimeout(timeout)
  }
}

function statusFromScore(score, warn = 80, critical = 50) {
  if (score === null || score === undefined) return "warning"
  if (score < critical) return "critical"
  if (score < warn) return "warning"
  return "good"
}

function addFinding(findings, status, category, title, explanation, fix) {
  findings.push({ status, category, title, explanation, fix })
}

function buildFindings(onPage, psi, www) {
  const findings = []
  const scores = psi.scores
  const metrics = psi.metrics

  addFinding(
    findings,
    statusFromScore(scores.performance),
    "Hız",
    "Mobil performans skoru",
    scores.performance === null ? "PageSpeed performans skoru alınamadı." : `Mobil performans skoru ${scores.performance}/100.`,
    "Kritik CSS, görsel boyutları, kullanılmayan JavaScript ve cache ayarlarını birlikte optimize edin."
  )

  if (metrics.lcp?.numericValue) {
    const lcpSeconds = metrics.lcp.numericValue / 1000
    addFinding(
      findings,
      lcpSeconds > 4 ? "critical" : lcpSeconds > 2.5 ? "warning" : "good",
      "Hız",
      "Largest Contentful Paint",
      `Ana içerik ${metrics.lcp.displayValue || `${lcpSeconds.toFixed(1)} sn`} içinde yükleniyor.`,
      "Hero görselini sıkıştırın, kritik CSS'i öne alın ve render engelleyici kaynakları azaltın."
    )
  }

  if (metrics.cls?.numericValue !== null && metrics.cls?.numericValue !== undefined) {
    const cls = metrics.cls.numericValue
    addFinding(
      findings,
      cls > 0.25 ? "critical" : cls > 0.1 ? "warning" : "good",
      "Mobil",
      "CLS stabilitesi",
      `Sayfa kayma skoru ${metrics.cls.displayValue || cls.toFixed(3)}.`,
      "Görsellere boyut verin, geç yüklenen banner alanlarını sabitleyin ve font değişimlerini kontrol edin."
    )
  }

  const responsiveness = metrics.inp || metrics.tbt
  if (responsiveness?.numericValue !== null && responsiveness?.numericValue !== undefined) {
    const isInp = responsiveness.id === "interaction-to-next-paint"
    const value = responsiveness.numericValue
    addFinding(
      findings,
      isInp ? (value > 500 ? "critical" : value > 200 ? "warning" : "good") : value > 600 ? "critical" : value > 200 ? "warning" : "good",
      "Mobil",
      isInp ? "INP etkileşim gecikmesi" : "TBT etkileşim engeli",
      `${isInp ? "INP" : "TBT"} değeri ${responsiveness.displayValue || `${Math.round(value)} ms`}.`,
      "Uzun JavaScript görevlerini bölün, üçüncü taraf scriptleri geciktirin ve ana thread yükünü azaltın."
    )
  }

  addFinding(
    findings,
    onPage.title.exists ? (onPage.title.inRange ? "good" : "warning") : "critical",
    "İçerik",
    "Title etiketi",
    onPage.title.exists
      ? `Title uzunluğu ${onPage.title.length} karakter.`
      : "Sayfada title etiketi bulunamadı.",
    "Title metnini ana hizmet vaadiyle yazın ve 30-60 karakter aralığında tutun."
  )

  addFinding(
    findings,
    onPage.description.exists ? (onPage.description.inRange ? "good" : "warning") : "critical",
    "İçerik",
    "Meta description",
    onPage.description.exists
      ? `Meta description uzunluğu ${onPage.description.length} karakter.`
      : "Meta description bulunamadı.",
    "Açıklamayı arama sonucunda tıklama niyeti oluşturacak şekilde 120-160 karakter aralığında yazın."
  )

  addFinding(
    findings,
    onPage.h1.single ? "good" : "critical",
    "İçerik",
    "H1 yapısı",
    onPage.h1.single ? "Sayfada tek bir H1 bulunuyor." : `Sayfada ${onPage.h1.count} adet H1 bulundu.`,
    "Sayfada yalnızca bir ana H1 bırakın; alt başlıkları H2/H3 yapısına taşıyın."
  )

  addFinding(
    findings,
    onPage.canonical.exists ? "good" : "warning",
    "Teknik SEO",
    "Canonical etiketi",
    onPage.canonical.exists ? "Canonical etiketi mevcut." : "Canonical etiketi bulunamadı.",
    "Kanonik URL'yi sayfanın tercih edilen indexlenebilir adresine işaret edecek şekilde ekleyin."
  )

  addFinding(
    findings,
    onPage.viewport.exists ? "good" : "critical",
    "Mobil",
    "Viewport meta",
    onPage.viewport.exists ? "Mobil viewport meta etiketi mevcut." : "Mobil viewport meta etiketi bulunamadı.",
    "Head alanına width=device-width ve initial-scale=1 içeren viewport meta etiketi ekleyin."
  )

  addFinding(
    findings,
    onPage.openGraph.hasTitle && onPage.openGraph.hasImage ? "good" : "warning",
    "İçerik",
    "Open Graph",
    onPage.openGraph.hasTitle && onPage.openGraph.hasImage
      ? "og:title ve og:image mevcut."
      : "og:title veya og:image eksik.",
    "Sosyal paylaşım görünümü için og:title, og:description ve og:image alanlarını tamamlayın."
  )

  addFinding(
    findings,
    onPage.schema.exists ? "good" : "warning",
    "Teknik SEO",
    "JSON-LD schema",
    onPage.schema.exists ? `Schema tipleri: ${onPage.schema.types.join(", ")}.` : "JSON-LD schema bulunamadı.",
    "Sayfa türüne göre Organization, Service, FAQPage, Article veya Product gibi uygun schema ekleyin."
  )

  addFinding(
    findings,
    onPage.images.altPercent < 50 ? "critical" : onPage.images.altPercent < 80 ? "warning" : "good",
    "İçerik",
    "Görsel alt metinleri",
    `${onPage.images.total} görselin %${onPage.images.altPercent} kadarında alt metni var.`,
    "Anlam taşıyan her görsele kısa, açıklayıcı ve sayfa bağlamına uygun alt metni ekleyin."
  )

  addFinding(
    findings,
    onPage.robots.noindex ? "critical" : "good",
    "Teknik SEO",
    "Robots noindex",
    onPage.robots.noindex ? "Robots meta etiketi noindex içeriyor." : "Robots meta noindex sinyali yok.",
    "Indexlenmesi gereken sayfalarda noindex yönergesini kaldırın."
  )

  addFinding(
    findings,
    onPage.https.final ? "good" : "critical",
    "Teknik SEO",
    "HTTPS kullanımı",
    onPage.https.final ? "Final URL HTTPS üzerinden açılıyor." : "Final URL HTTPS kullanmıyor.",
    "SSL sertifikasını etkinleştirin ve HTTP trafiğini HTTPS adresine yönlendirin."
  )

  if (www.checked) {
    addFinding(
      findings,
      www.consistent ? "good" : "warning",
      "Teknik SEO",
      "www/non-www tutarlılığı",
      www.consistent ? "www ve non-www sürümleri aynı ana hosta yönleniyor." : "www ve non-www sürümleri farklı final adreslere gidiyor.",
      "Tek tercih edilen hostu belirleyip diğer sürümü 301 ile kanonik hosta yönlendirin."
    )
  } else {
    addFinding(findings, "warning", "Teknik SEO", "www/non-www kontrolü", www.note, "DNS ve yönlendirme ayarlarını canlı host üzerinde doğrulayın.")
  }

  if (onPage.hreflang.exists) {
    addFinding(
      findings,
      "good",
      "Teknik SEO",
      "Hreflang",
      `Hreflang değerleri raporlandı: ${onPage.hreflang.values.join(", ")}.`,
      "Çok dilli sayfalarda hreflang karşılıklılığını ve canonical uyumunu ayrıca kontrol edin."
    )
  }

  addFinding(
    findings,
    statusFromScore(scores.accessibility, 85, 60),
    "Mobil",
    "Accessibility skoru",
    scores.accessibility === null ? "Accessibility skoru alınamadı." : `Accessibility skoru ${scores.accessibility}/100.`,
    "Kontrast, form label, buton adı ve klavye odağı sorunlarını Lighthouse önerileriyle düzeltin."
  )

  addFinding(
    findings,
    statusFromScore(scores.bestPractices, 85, 60),
    "Teknik SEO",
    "Best practices skoru",
    scores.bestPractices === null ? "Best practices skoru alınamadı." : `Best practices skoru ${scores.bestPractices}/100.`,
    "Güvenli kaynak kullanımı, konsol hataları ve modern tarayıcı pratiklerini temizleyin."
  )

  addFinding(
    findings,
    statusFromScore(scores.seo, 85, 60),
    "Teknik SEO",
    "PageSpeed SEO skoru",
    scores.seo === null ? "PageSpeed SEO skoru alınamadı." : `PageSpeed SEO skoru ${scores.seo}/100.`,
    "Lighthouse SEO önerilerini on-page kontrollerle birlikte önceliklendirin."
  )

  const order = { critical: 0, warning: 1, good: 2 }
  return findings.sort((a, b) => order[a.status] - order[b.status])
}

function boolScore(items) {
  const values = items.map(Boolean)
  return Math.round((values.filter(Boolean).length / values.length) * 100)
}

function average(values) {
  const clean = values.filter((value) => typeof value === "number")
  if (!clean.length) return 0
  return Math.round(clean.reduce((sum, value) => sum + value, 0) / clean.length)
}

function buildScores(onPage, psi, www) {
  const speed = psi.scores.performance ?? average([psi.metrics.lcp?.score && psi.metrics.lcp.score * 100])
  const technicalSeo = average([
    boolScore([onPage.canonical.exists, !onPage.robots.noindex, onPage.https.final, onPage.schema.exists]),
    psi.scores.seo,
    psi.scores.bestPractices,
    www.consistent === null ? null : www.consistent ? 100 : 60,
  ])
  const content = boolScore([
    onPage.title.exists && onPage.title.inRange,
    onPage.description.exists && onPage.description.inRange,
    onPage.h1.single,
    onPage.openGraph.hasTitle && onPage.openGraph.hasImage,
    onPage.images.altPercent >= 80,
  ])
  const mobile = average([
    boolScore([onPage.viewport.exists]),
    psi.scores.accessibility,
    psi.metrics.cls?.score === null || psi.metrics.cls?.score === undefined ? null : Math.round(psi.metrics.cls.score * 100),
    (psi.metrics.inp || psi.metrics.tbt)?.score === null || (psi.metrics.inp || psi.metrics.tbt)?.score === undefined
      ? null
      : Math.round((psi.metrics.inp || psi.metrics.tbt).score * 100),
  ])
  const overall = Math.round(speed * 0.35 + technicalSeo * 0.25 + content * 0.25 + mobile * 0.15)

  return {
    overall,
    categories: {
      speed,
      technicalSeo,
      content,
      mobile,
    },
  }
}

async function runAnalysis(url) {
  const validated = validatePublicUrl(url)
  await assertPublicHostname(validated)

  const [page, psiResult] = await Promise.allSettled([fetchWithGuards(validated.toString()), fetchPsi(validated.toString())])
  if (page.status === "rejected") throw page.reason

  const onPage = analyzeHtml(page.value.html, validated.toString(), page.value)
  const www = await checkWwwConsistency(validated.toString())
  const psi =
    psiResult.status === "fulfilled"
      ? psiResult.value
      : {
          scores: { performance: null, accessibility: null, bestPractices: null, seo: null },
          metrics: { lcp: null, cls: null, inp: null, tbt: null },
        }
  const findings = buildFindings(onPage, psi, www)
  const scores = buildScores(onPage, psi, www)

  return {
    analyzedUrl: validated.toString(),
    finalUrl: page.value.finalUrl,
    statusCode: page.value.status,
    generatedAt: new Date().toISOString(),
    scores,
    metrics: psi.metrics,
    psiScores: psi.scores,
    onPage,
    findings,
    warnings: psiResult.status === "rejected" ? ["PageSpeed Insights ölçümü alınamadı; on-page analiz tamamlandı."] : [],
    reportId: crypto.randomUUID(),
  }
}

function validateLead(body) {
  const email = String(body.email || "").trim().toLowerCase()
  const phone = String(body.phone || "").trim()
  const consent = body.consent === true
  const url = validatePublicUrl(body.url || "")
  if (!consent) throw new HttpError(422, "consent_required", "Açık rıza olmadan kayıt oluşturulamaz.")
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    throw new HttpError(422, "invalid_email", "Geçerli bir e-posta adresi girin.")
  }
  if (!/^[+()\d\s-]{10,24}$/.test(phone)) {
    throw new HttpError(422, "invalid_phone", "Geçerli bir telefon numarası girin.")
  }
  return { email, phone, url: url.toString(), reportId: String(body.reportId || ""), consent }
}

async function storeLead(body) {
  const lead = validateLead(body)
  const record = {
    ...lead,
    consentText: "Site Analizi PDF gönderimi ve iletişim için açık rıza verildi.",
    consentVersion: "2026-07-23",
    createdAt: new Date().toISOString(),
  }
  await redisCommand("RPUSH", "site-analysis:leads", JSON.stringify(record))
  await redisCommand("LTRIM", "site-analysis:leads", -1000, -1)
  return { saved: true }
}

async function handler(req, res) {
  if (req.method !== "POST") {
    res.setHeader("Allow", "POST")
    return writeJson(res, 405, { error: { code: "method_not_allowed", message: "Yalnızca POST desteklenir." } })
  }

  try {
    const body = await readRequestJson(req)
    const action = body.action === "lead" ? "lead" : "analyze"

    if (action === "lead") {
      validateLead(body)
      const limit = await enforceRateLimit(req)
      await storeLead(body)
      return writeJson(res, 200, { data: { saved: true }, meta: { rateLimit: limit } })
    }

    const targetUrl = validatePublicUrl(body.url).toString()
    const limit = await enforceRateLimit(req)
    const result = await runAnalysis(targetUrl)
    return writeJson(res, 200, { data: result, meta: { rateLimit: limit } })
  } catch (error) {
    const status = error instanceof HttpError ? error.status : 500
    const code = error instanceof HttpError ? error.code : "internal_error"
    const message = error instanceof HttpError ? error.message : "Analiz sırasında beklenmeyen bir hata oluştu."
    const headers = error.code === "rate_limit_exceeded" ? { "Retry-After": String(error.retryAfter || 3600) } : {}
    return writeJson(res, status, { error: { code, message } }, headers)
  }
}

module.exports = handler
module.exports._internal = {
  analyzeHtml,
  buildFindings,
  buildScores,
  cleanHostname,
  isBlockedIp,
  rateKeyForIp,
  validateLead,
  validatePublicUrl,
}
