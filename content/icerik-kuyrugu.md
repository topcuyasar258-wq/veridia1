# Icerik Kuyrugu — Guzellik Ekseni

Haftada bir gun oturup hazirlamak, 2-3 gunde bir yayina almak icin kuyruk.
Tamami guzellik/estetik/klinik ekseninde; diger dikeyler bilincli olarak
ertelendi.

## Bu kuyruk neye dayaniyor

Search Console, son 28 gun (2026-07-17 → 2026-08-13), Web aramasi:

| | Tik | Gosterim |
|---|---|---|
| Toplam | 41 | 690 |
| Marka ("veridia*") | 25 | 85 |
| **Marka disi (listelenen 50 sorgu)** | **0** | 290 |

Marka disi tek tik yok. Sebep dusuk TO degil, dusuk siralama: ticari
sorgularda 70-90. bandindayiz.

### Belirleyici bulgu

Guzellik ekseni sorgulari kumelere ayrildiginda net bir kalip cikiyor:

| Kume | Ozel sayfa | Pozisyon | Ornek sorgu (gosterim) |
|---|---|---|---|
| Genel guzellik pazarlama | var (hub) | 10-25 | guzellik pazarlamasi (29) |
| Guzellik merkezi SEO | var | 10-17 | guzellik merkezi seo (13) |
| Guzellik merkezi reklam | var | 17 | guzellik merkezi reklam calismalari (2) |
| Sosyal medya | **yok** | 36 | estetik merkezi sosyal medya yonetimi (3) |
| Klinik (genis) | kismen | 47-88 | klinik pazarlama (6) |
| Sac ekim | **yok** | 74 | sac ekim merkezi dijital pazarlama (8) |
| Web sitesi | **yok** | 91.5 | guzellik merkezi sitesi yaptirmak (4) |

**Ozel sayfasi olan kume 1-2. sayfada; olmayan kume gorunmuyor.**
Bu yuzden kuyruk once eksik kume sayfalarini kapatiyor, sonra mevcut
kumeleri derinlestiriyor.

`tests/test_seo_smoke.py` icindeki
`test_beauty_sector_page_marks_missing_service_pages_without_links` testi bu
mimarinin zaten planlandigini gosteriyor: guzellik altinda 4 hizmet sayfasi
ongorulmus, `seo` ve `google-ads` yapilmis, `web-tasarim` ve
`sosyal-medya-yonetimi` yapilmamis.

> **Uyari:** 41 tik / 690 gosterim kucuk ornek. Bunlar yon gosterir, kesin
> hukum degil. Arama hacmi verisi yok; hacim tahmini yazilmadi.

---

## 1. Hafta — Eksik kume sayfalarini kapat

En yuksek kaldirac burada. Bunlar **blog yazisi degil, hizmet sayfasi**;
`yaziekle.py` ile uretilmiyorlar (o arac sadece blog yazisi uretir).
`content/site_graph.json` icine `services` kaydi eklenip
`scripts/build_site_surfaces.py` calistirilarak uretilirler. Sayfalar
olusturulunca yukaridaki smoke testin guncellenmesi gerekir.

### 1.1 Guzellik Merkezi Web Sitesi (hizmet sayfasi)
- **URL:** `/sektorler/guzellik-merkezi-web-sitesi/`
- **Hedef sorgu:** `guzellik merkezi sitesi yaptirmak` — su an **pozisyon 91.5**
- **Neden once bu:** Satin alma niyeti en yuksek sorgu. Birisi acikca site
  yaptirmak istiyor ve bizi hic gormuyor.
- **Bolumler:** Randevu akisi olan site nasil kurulur → hizmet/fiyat sayfasi
  yapisi → oncesi-sonrasi galerisi ve yasal sinirlar → mobil hiz → paketler
- **Ic link:** hub `/sektorler/guzellik-merkezleri-icin-dijital-pazarlama/`,
  `/yazilim/web-sitesi-ve-donusum-yuzeyleri/`, mevcut yazi
  `Guzellik Merkezi Web Sitesi Nasil Olmali?`

### 1.2 Guzellik Merkezi Sosyal Medya Yonetimi (hizmet sayfasi)
- **URL:** `/sektorler/guzellik-merkezi-sosyal-medya-yonetimi/`
- **Hedef sorgu:** `estetik merkezi sosyal medya yonetimi` — **pozisyon 36**
- **Bolumler:** Icerik sistemi ve yayin ritmi → randevuya donen icerik tipleri
  → oncesi-sonrasi paylasim kurallari → is birligi/mikro influencer → olcum
- **Ic link:** hub, `/reklam/sosyal-medya-yonetimi/`, mevcut yazi
  `Guzellik Salonu Instagram'dan Musteri Nasil Bulur?`

### 1.3 Blog: Guzellik Merkezi Web Sitesi Maliyeti ve Kurulum Sureci
- **Slug:** `guzellik-merkezi-web-sitesi-maliyeti-ve-sureci`
- **Servis slug:** `web-sitesi-ve-donusum-yuzeyleri`
- **Gorevi:** 1.1'deki yeni hizmet sayfasini besleyen ilk spoke. Fiyat/surec
  sorgulari alt huniye yakin.
- **Bolumler:** Neye gore fiyatlanir → tek sayfa vs cok sayfa → randevu
  entegrasyonu maliyeti → sureye etki eden kalemler → hazir tema riskleri

---

## 2. Hafta — Guclu kumeleri 1. sayfaya tasi

Bu kumeler 10-17 bandinda; oradan ilk 5'e cikmak yeni kume acmaktan daha
ucuz.

### 2.1 Guzellik Merkezi SEO Denetimi: 12 Maddelik Kontrol Listesi
- **Slug:** `guzellik-merkezi-seo-denetimi-kontrol-listesi`
- **Servis slug:** `teknik-seo-denetimi`
- **Hedef kume:** `guzellik merkezi seo` (13 gosterim, poz 17.2),
  `seo guzellik` (poz 10), `podyum guzellik seo` (poz 11.3)
- **Gorevi:** `/sektorler/guzellik-merkezi-seo/` sayfasini besler ve ac kalan
  `teknik-seo-denetimi` silosunu guclendirir.
- **Bolumler:** Isletme profili → hizmet sayfasi yapisi → semt sayfalari →
  hiz → schema → yorum sinyali → ic linkleme

### 2.2 Guzellik Merkezi Fiyat Sayfasi Nasil Yazilir?
- **Slug:** `guzellik-merkezi-fiyat-sayfasi-nasil-yazilir`
- **Servis slug:** `web-sitesi-ve-donusum-yuzeyleri`
- **Gorevi:** Fiyat, guzellik sektorunde en yuksek niyetli aramalardan biri ve
  sitede hic islenmemis. 1.1 hizmet sayfasini da besler.
- **Bolumler:** Fiyat gosterilmeli mi → "baslangic fiyati" modeli → paket
  sunumu → rakip fiyat karsilastirmasi riski → fiyat sorusunu randevuya cevirme
- **Ic link:** mevcut `WhatsApp'ta Fiyat Sorusunu Randevuya Cevirme` yazisi

### 2.3 Estetik Klinigi Instagram Icerik Takvimi
- **Slug:** `estetik-klinigi-instagram-icerik-takvimi`
- **Servis slug:** `sosyal-medya-yonetimi`
- **Hedef kume:** `estetik merkezi sosyal medya yonetimi` (poz 36)
- **Gorevi:** 1.2 hizmet sayfasinin ikinci spoke'u.
- **Bolumler:** Haftalik sablon → icerik tipleri → oncesi-sonrasi kurallari →
  reels vs post → yorum/DM'den randevuya

---

## 3. Hafta — Klinik kumesi (poz 47-88)

Guzellik komsusu ama daha genis ve daha ticari terimler. Su an
`/sektorler/estetik-klinikleri-icin-dijital-pazarlama/` var fakat pozisyonu
58.7; destek icerigi yok.

### 3.1 Klinik Dijital Pazarlama: Estetik ve Medikal Klinikler Icin Sistem
- **Slug:** `klinik-dijital-pazarlama-sistemi`
- **Servis slug:** `google-gorunurlugu`
- **Hedef kume:** `klinik pazarlama` (6, poz 85.5), `klinik dijital pazarlama`
  (2, poz 51), `klinik medya reklam ajansi` (4, poz 88)
- **Bolumler:** Klinik ile guzellik merkezi farki → hasta yolculugu → kanal
  dagilimi → mevzuat sinirlari → olcum
- **Not:** Kanibalizasyon riski — mevcut guzellik hub'i ile ortusmemesi icin
  "klinik" cercevesinde kalmali, "guzellik merkezi" terimini hedeflememeli.

### 3.2 Klinikler Icin Donusum Odakli Reklam Yapisi
- **Slug:** `klinikler-icin-donusum-odakli-reklam-yapisi`
- **Servis slug:** `google-ads-yonetimi`
- **Hedef sorgu:** `klinik donusum odakli reklam` (poz 47.5)
- **Bolumler:** Kampanya mimarisi → landing uyumu → form vs arama → negatif
  kelimeler → olcum
- **Ic link:** mevcut `Guzellik Merkezi Google Ads Negatif Anahtar Kelime Listesi`

### 3.3 Guzellik Merkezi Yorum Yonetimi ve Kotu Yorum Cevaplama
- **Slug:** `guzellik-merkezi-yorum-yonetimi`
- **Servis slug:** `google-gorunurlugu`
- **Gorevi:** Yorum sinyali yerel siralamanin dogrudan girdisi; sitede hic
  islenmemis. E-E-A-T tarafini da guclendirir.
- **Bolumler:** Yorum toplama ritmi → kotu yoruma cevap sablonu → sahte yorum
  bildirimi → yorumu sayfaya tasima → schema

---

## 4. Hafta — Komsu dikeyler ve semt serisi

### 4.1 Sac Ekim Merkezi Dijital Pazarlama
- **Slug:** `sac-ekim-merkezi-dijital-pazarlama`
- **Servis slug:** `google-gorunurlugu`
- **Hedef sorgu:** `sac ekim merkezi dijital pazarlama` — 8 gosterim, poz 73.8
- **Neden:** Gorunmeyen kumeler icinde en yuksek gosterime sahip olani; guzellik
  ekseninin dogal komsusu, yurt disi hasta boyutu ile yuksek musteri degeri.
- **Bolumler:** Yurt disi hasta akisi → dil/lokalizasyon → oncesi-sonrasi
  mevzuati → fiyat seffafligi → yorum

### 4.2 Cilt Bakimi Merkezi Icin Dijital Pazarlama
- **Slug:** `cilt-bakimi-merkezi-dijital-pazarlama`
- **Servis slug:** `sosyal-medya-yonetimi`
- **Hedef sorgu:** `cilt bakimi pazarlamasi` (poz 27)
- **Bolumler:** Tekrar eden seans modeli → abonelik/paket → icerik ekseni →
  sezonluk kampanya

### 4.3 Sisli ve Besiktas'ta Guzellik Merkezi Nasil One Cikar?
- **Slug:** `sislide-besiktasta-guzellik-merkezi-nasil-one-cikar`
- **Servis slug:** `google-gorunurlugu`
- **Gorevi:** Mevcut `Kadikoy'de Guzellik Merkezi Nasil One Cikar?` yazisinin
  serisi. Semt bazli sayfalar yerel aramada tekrarlanabilir ve birikimli.
- **Bolumler:** Semt rekabet profili → isletme profili semt sinyalleri →
  semt sayfasi yapisi → yerel is birligi
- **Not:** Kadikoy yazisinin performansi olcuye alinip seri devam ettirilmeli;
  calismiyorsa semt serisi durdurulmali.

---

## Kuyruk bittikten sonra beklenen

- Guzellik ekseninde **kume sayfasi olmayan** tek bir ticari sorgu kalmaz
- `teknik-seo-denetimi` silosu 1 → 2, `sosyal-medya-yonetimi` 2 → 4 yaziya cikar
- Klinik kumesi ilk destek icerigini alir

## Yeniden olcum

4 hafta sonra Search Console'dan ayni 28 gunluk raporu al ve su iki sayiya bak:

1. **Marka disi tik** — su an 0. Ilk hedef bunu pozitife cevirmek.
2. Yukaridaki tablodaki kumelerin ortalama pozisyonu.

Marka disi tik hala 0 ise sorun icerik miktari degildir; o noktada strateji
(hedef segment, rekabet seviyesi) yeniden degerlendirilmeli.
