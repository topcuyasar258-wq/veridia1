import assert from "node:assert/strict"
import test from "node:test"
import analyzeApi from "../api/analyze.js"

const { _internal } = analyzeApi

test("blocks local and private IP ranges", () => {
  for (const ip of ["127.0.0.1", "0.0.0.0", "10.0.0.4", "172.16.4.2", "172.31.255.1", "192.168.1.2", "169.254.169.254", "::1", "fc00::1", "fe80::1"]) {
    assert.equal(_internal.isBlockedIp(ip), true, ip)
  }
  assert.equal(_internal.isBlockedIp("8.8.8.8"), false)
})

test("accepts only http and https URLs", () => {
  assert.equal(_internal.validatePublicUrl("https://example.com/path#frag").toString(), "https://example.com/path")
  assert.throws(() => _internal.validatePublicUrl("file:///etc/passwd"), /Yalnızca http veya https/)
})

test("extracts on-page SEO signals from HTML", () => {
  const html = `
    <html>
      <head>
        <title>Örnek Site Analizi Başlığı Uzunluğu</title>
        <meta name="description" content="Bu açıklama arama sonucu için yeterli uzunlukta yazılmış örnek bir meta description metnidir ve kullanıcıya sayfanın değerini anlatır.">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link rel="canonical" href="https://example.com/">
        <meta property="og:title" content="Örnek">
        <meta property="og:image" content="https://example.com/og.jpg">
        <script type="application/ld+json">{"@context":"https://schema.org","@type":"Service"}</script>
      </head>
      <body>
        <h1>Örnek Başlık</h1>
        <img src="/a.jpg" alt="Açıklayıcı görsel">
        <img src="/b.jpg">
      </body>
    </html>
  `
  const result = _internal.analyzeHtml(html, "https://example.com/", { finalUrl: "https://example.com/" })
  assert.equal(result.title.exists, true)
  assert.equal(result.description.exists, true)
  assert.equal(result.h1.single, true)
  assert.equal(result.canonical.exists, true)
  assert.equal(result.viewport.exists, true)
  assert.equal(result.openGraph.hasTitle, true)
  assert.equal(result.openGraph.hasImage, true)
  assert.deepEqual(result.schema.types, ["Service"])
  assert.equal(result.images.altPercent, 50)
  assert.equal(result.robots.noindex, false)
  assert.equal(result.https.final, true)
})

test("requires consent before storing a lead", () => {
  assert.throws(
    () =>
      _internal.validateLead({
        email: "lead@example.com",
        phone: "+90 555 111 22 33",
        url: "https://example.com",
        consent: false,
      }),
    /Açık rıza/
  )
})
