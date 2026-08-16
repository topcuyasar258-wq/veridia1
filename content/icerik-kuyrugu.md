# Içerik Kuyrugu

Haftada bir gun oturup yazilari hazirlamak, 2-3 gunde bir yayina almak icin
hazirlanmis kuyruk. Her madde `yaziekle.py`'ye dogrudan girilebilecek sekilde
yazildi.

## Bu kuyruk nasil secildi

Site uzerindeki **icerik bosluklarina** gore. Iki somut bulgu:

1. **13 sektor sayfasinin 9'unu besleyen hic blog yazisi yok.** Sektor
   sayfalari para sayfasi; onlara ic link gonderen destek icerigi olmadan tek
   baslarina duruyorlar. Mevcut 19 yazinin buyuk cogunlugu guzellik merkezi
   konusunda yogunlasmis.
2. **Iki hizmet silosu ac kalmis:** `teknik-seo-denetimi` (1 yazi) ve
   `meta-reklam-yonetimi` (1 yazi). Digerlerinde 2-7 yazi var.

Kuyruk bu iki boslugu kapatacak sekilde siralandi.

> **Not:** Bu siralama site yapisi analizine dayaniyor, canli arama hacmi
> verisine degil. Elimde dogrulanmis anahtar kelime hacmi yok; sayilar
> uydurmamak icin hacim tahmini yazmadim. Search Console veya bir kelime
> aracina erisim acilirsa siralama gercek veriyle yeniden onceliklendirilebilir.

## Kullanim

Her yazi icin:

```bash
python3 yaziekle.py
```

Sorulara asagidaki tablodaki `Baslik`, `Ozet`, `Slug` ve `Servis slug` degerlerini gir.
Arac; dosyayi, `vercel.json` yonlendirmelerini, `blog.html` kartini, JSON-LD'yi
ve `sitemap.xml`'i kendisi hallediyor. Sonrasinda:

```bash
python3 -m unittest tests.test_seo_routing tests.test_seo_smoke
```

---

## 1. Hafta — Dis ve estetik klinikleri

### 1.1 Dis Klinigi Google'da Nasil Hasta Bulur?
- **Slug:** `dis-klinigi-googlede-nasil-hasta-bulur`
- **Servis slug:** `google-gorunurlugu`
- **Besledigi sayfa:** `/sektorler/dis-klinikleri-icin-dijital-pazarlama/`
- **Arama niyeti:** Klinik sahibi, hasta akisini artirmanin yolunu ariyor. Ticari arastirma.
- **Bolumler:** Hastanin arama yolculugu (sikayet -> tedavi adi -> klinik secimi) → Google Isletme Profili kurulumu → tedavi bazli sayfa yapisi → yorum toplama ritmi → olcum
- **Ic link plani:** Intro'da `/seo/google-gorunurlugu/`; kapanista sektor sayfasi + `Google Haritalar'da Guzellik Merkezi Nasil Ust Siraya Cikar?`

### 1.2 Dis Klinigi Randevu Sayfasi Nasil Olmali?
- **Slug:** `dis-klinigi-randevu-sayfasi-nasil-olmali`
- **Servis slug:** `web-sitesi-ve-donusum-yuzeyleri`
- **Besledigi sayfa:** `/sektorler/dis-klinikleri-icin-dijital-pazarlama/`
- **Arama niyeti:** Sitesi olan ama randevu almayan klinik. Cozum odakli.
- **Bolumler:** Randevu formunda kac alan olmali → tedavi secimi UX'i → WhatsApp vs form → mobil davranis → guven unsurlari (hekim profili, belgeler)
- **Ic link plani:** `/yazilim/web-sitesi-ve-donusum-yuzeyleri/`; kapanista `Guzellik Merkezi Randevu No-Show Sorunu` ve `WhatsApp'ta Fiyat Sorusunu Randevuya Cevirme`

### 1.3 Estetik Klinikleri Icin Onay Alan Google Ads Yapisi
- **Slug:** `estetik-klinikleri-icin-onay-alan-google-ads-yapisi`
- **Servis slug:** `google-ads-yonetimi`
- **Besledigi sayfa:** `/sektorler/estetik-klinikleri-icin-dijital-pazarlama/`
- **Arama niyeti:** Reklami reddedilen/kisitlanan klinik. Sorun cozme, yuksek aciliyet.
- **Bolumler:** Saglik reklamlarinda kisitli kategoriler → izin gerektiren ifadeler → landing page uyumu → oncesi/sonrasi gorsel kurali → red durumunda itiraz akisi
- **Ic link plani:** `/reklam/google-ads-yonetimi/`; kapanista `Guzellik ve Estetik Reklamlari Meta'da Neden Reddedilir?` (Meta tarafinin Google karsiligi — guclu cift)

---

## 2. Hafta — Kuafor, restoran, yerel servis

### 2.1 Kuafor Salonu Google Haritalar'da Nasil One Cikar?
- **Slug:** `kuafor-salonu-google-haritalarda-nasil-one-cikar`
- **Servis slug:** `google-gorunurlugu`
- **Besledigi sayfa:** `/sektorler/kuaforler-icin-dijital-pazarlama/`
- **Arama niyeti:** Mahalle rekabetinde gorunmek isteyen salon. Yerel SEO.
- **Bolumler:** Salon kategorisi secimi → hizmet listesi ve fiyat gorunurlugu → foto stratejisi → yorum cevaplama → yogun saat yonetimi
- **Ic link plani:** `/seo/google-gorunurlugu/`; kapanista `Kadikoy'de Guzellik Merkezi Nasil One Cikar?` (semt bazli lokal SEO mantigi ayni)

### 2.2 Restoran Google Isletme Profili: Rezervasyon Getiren Kurulum
- **Slug:** `restoran-google-isletme-profili-rezervasyon-kurulumu`
- **Servis slug:** `google-gorunurlugu`
- **Besledigi sayfa:** `/sektorler/kafe-restoran-dijital-pazarlama/`
- **Arama niyeti:** "yakinimda restoran" trafigini masaya cevirmek isteyen isletme.
- **Bolumler:** Menu ve fiyat alanlari → rezervasyon linki → foto guncelleme ritmi → yorum yonetimi → ozel gun/kampanya postlari
- **Ic link plani:** `/seo/google-gorunurlugu/`; kapanista sektor sayfasi

### 2.3 Yerel Servis Isletmesi Icin Acil Arama Alan Web Sitesi
- **Slug:** `yerel-servis-isletmesi-icin-acil-arama-alan-web-sitesi`
- **Servis slug:** `web-sitesi-ve-donusum-yuzeyleri`
- **Besledigi sayfa:** `/sektorler/yerel-servis-isletmeleri-icin-dijital-pazarlama/`
- **Arama niyeti:** Tesisatci, elektrikci, cilingir gibi acil hizmet veren isletme.
- **Bolumler:** Telefon CTA'sinin konumu → hizmet bolgesi sayfalari → 7/24 sinyali → fiyat beklentisi yonetimi → mobil hiz
- **Ic link plani:** `/yazilim/web-sitesi-ve-donusum-yuzeyleri/`; kapanista `Hizmet Sitelerinde CTA Nasil Olmali?` ve `Web Sitesi Yavassa Musteri Neden Kacar?`

---

## 3. Hafta — Ac kalan silolari besle

### 3.1 Core Web Vitals 2026: INP Nedir, Nasil Duzeltilir?
- **Slug:** `core-web-vitals-inp-nedir-nasil-duzeltilir`
- **Servis slug:** `teknik-seo-denetimi`  ← **ac silo**
- **Besledigi sayfa:** `/seo/teknik-seo-denetimi/`
- **Arama niyeti:** Site sahibi/gelistirici, PageSpeed uyarisi almis. Bilgi + cozum.
- **Bolumler:** INP'nin FID'in yerini almasi → iyi/kotu esikler → en sik 5 sebep (agir JS, uzun task, layout thrash, ucuncu parti script, gorsel) → olcum (CrUX alan verisi vs lab) → duzeltme sirasi
- **Ic link plani:** `/seo/teknik-seo-denetimi/`; kapanista `Teknik SEO ve Web Performansi` ve `Web Sitesi Yavassa Musteri Neden Kacar?`
- **Not:** Bu silo tek yaziyla ayakta; hizmet sayfasinin otoritesi icin oncelikli.

### 3.2 Moda E-Ticarette Urun Sayfasi SEO'su
- **Slug:** `moda-e-ticarette-urun-sayfasi-seosu`
- **Servis slug:** `teknik-seo-denetimi`  ← **ac silo**
- **Besledigi sayfa:** `/sektorler/moda-e-ticaret-dijital-pazarlama/`
- **Arama niyeti:** E-ticaret sahibi, urun sayfalari siralanmiyor.
- **Bolumler:** Urun schema (fiyat, stok, yorum) → varyant/renk URL yapisi ve kopya icerik riski → gorsel optimizasyonu ve alt metin → kategori-urun ic linkleme → tukenen urun yonetimi
- **Ic link plani:** `/seo/teknik-seo-denetimi/`; kapanista sektor sayfasi

### 3.3 Moda Markalari Icin Meta Reklam Yapisi
- **Slug:** `moda-markalari-icin-meta-reklam-yapisi`
- **Servis slug:** `meta-reklam-yonetimi`  ← **ac silo**
- **Besledigi sayfa:** `/sektorler/moda-e-ticaret-dijital-pazarlama/`
- **Arama niyeti:** Meta'da reklam veren ama ROAS tutturamayan marka.
- **Bolumler:** Katalog kurulumu → kampanya mimarisi (prospecting / retargeting) → kreatif rotasyonu → koleksiyon lansmani takvimi → olcum ve iOS sonrasi atribusyon
- **Ic link plani:** `/reklam/meta-reklam-yonetimi/`; kapanista sektor sayfasi

---

## 4. Hafta — Avukat, B2B, yasam/ev

### 4.1 Avukat Web Sitesinde Reklam Kurallarina Uyum
- **Slug:** `avukat-web-sitesinde-reklam-kurallarina-uyum`
- **Servis slug:** `web-sitesi-ve-donusum-yuzeyleri`
- **Besledigi sayfa:** `/sektorler/avukatlar-icin-dijital-pazarlama/`
- **Arama niyeti:** Site yaptirmak isteyen ama baro kurallarindan cekinen avukat. Yuksek niyet, dusuk rekabet.
- **Bolumler:** Meslek kurallarinin site diline etkisi → izin verilen/verilmeyen ifadeler → uzmanlik alani sayfalari nasil yazilir → iletisim ve on gorusme akisi → icerik uretiminde sinirlar
- **Ic link plani:** `/yazilim/web-sitesi-ve-donusum-yuzeyleri/`; kapanista `Avukatlar Icin Google Reklamlari`
- **Not:** Hukuki mevzuat iddiasi iceriyor; yayindan once guncel baro/TBB duzenlemesi teyit edilmeli.

### 4.2 B2B Teknoloji Sitesinde Demo Talebi Nasil Artirilir?
- **Slug:** `b2b-teknoloji-sitesinde-demo-talebi-nasil-artirilir`
- **Servis slug:** `web-sitesi-ve-donusum-yuzeyleri`
- **Besledigi sayfa:** `/sektorler/teknoloji-b2b-dijital-pazarlama/`
- **Arama niyeti:** SaaS/teknoloji firmasi, trafik var donusum yok.
- **Bolumler:** Demo formu vs kendin dene → alan sayisi ve nitelendirme dengesi → sosyal kanit yerlesimi → fiyat sayfasi olmamasi sorunu → satis ekibine devir
- **Ic link plani:** `/yazilim/web-sitesi-ve-donusum-yuzeyleri/`; kapanista `B2B Pazarlamada Donusum Hunisi`

### 4.3 Ev ve Yasam Markalari Icin Instagram Icerik Sistemi
- **Slug:** `ev-yasam-markalari-icin-instagram-icerik-sistemi`
- **Servis slug:** `sosyal-medya-yonetimi`
- **Besledigi sayfa:** `/sektorler/yasam-ev-markalari-dijital-pazarlama/`
- **Arama niyeti:** Dekorasyon/ev markasi, gorsel agirlikli satis kanali kurmak istiyor.
- **Bolumler:** Atmosfer vs urun cekimi dengesi → koleksiyon anlatimi → kaydedilme/paylasilma metrigi → magaza etiketleme → uretici isbirligi
- **Ic link plani:** `/reklam/sosyal-medya-yonetimi/`; kapanista `Instagram Algoritmasi 2026`

---

## Kuyruk bittikten sonra

Bu 12 yazi yayinlandiginda:
- 9 sektor sayfasinin tamami en az bir destek yazisiyla beslenmis olur
- `teknik-seo-denetimi` 1 -> 3, `meta-reklam-yonetimi` 1 -> 2 yaziya cikar

Sonraki tur icin oncelik onerisi: her sektor sayfasini 3 yaziya tamamlamak
(hub-and-spoke icin saglikli taban) ve o noktada gercek arama verisiyle
yeniden onceliklendirmek.
