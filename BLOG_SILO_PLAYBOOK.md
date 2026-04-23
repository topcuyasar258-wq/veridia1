# Veridia Blog Silo Playbook

Bu dosya, Veridia blogunun SEO silo mimarisine uygun kalmasi icin temel editoryal kurallari tanimlar.

## Ana ilke

Her blog yazisi tek bir birincil hizmet yuzeyine baglanir. Yazinin amaci sadece trafik almak degil, kullaniciyi ayni silo icinde bir sonraki dogru sayfaya tasimaktir.

## Mevcut silolar

- `SEO`
  - `/seo/`
  - `/seo/teknik-seo-denetimi/`
  - `/seo/google-gorunurlugu/`
- `Reklam`
  - `/reklam/`
  - `/reklam/sosyal-medya-yonetimi/`
  - `/reklam/google-ads-yonetimi/`
  - `/reklam/meta-reklam-yonetimi/`
- `Yazilim`
  - `/yazilim/`
  - `/yazilim/web-sitesi-ve-donusum-yuzeyleri/`

## Yazi yazma kurallari

- Her yazi olusturulurken bir `service_slug` secilir.
- Ilk `%20` icinde ilgili hizmet sayfasina dogal bir baglamsal link verilir.
- Visible breadcrumb su mantikla kurulur:
  - `Ana Sayfa > Silo > Alt Hizmet > Yazi`
- Yazi sonundaki `Ilginizi Cekebilir` bolumu sadece:
  - ayni `service_slug` altindaki diger yazilar
  - ilgili hizmet sayfasi
  - gerekiyorsa ana silo sayfasi
  baglantilarini icerir.

## Anchor text kurallari

- `buraya tikla`, `detay`, `incele` gibi bos anchorlardan kacinin.
- Hedef sayfanin kelime grubunu kullanan acik anchorlar tercih edin.
- Ornek:
  - `Teknik SEO Denetimi`
  - `Google Gorunurlugu`
  - `Sosyal Medya Yonetimi`
  - `Google Ads Yonetimi`

## Blog index kurallari

- Blog kartlarindaki ikincil link generic CTA degil, ilgili hizmet sayfasina gitmelidir.
- `data-category` degeri silo mantigina gore secilir:
  - `seo`
  - `social`
  - `ads`
  - `web`

## Operasyon

Yeni yazi eklemek icin:

```bash
python3 yaziekle.py
```

Bu arac:

- yazi dosyasini olusturur,
- `content/site_graph.json` kaydini ekler,
- `blog.html` kartini ekler,
- hub sayfalarini ve `sitemap.xml` dosyasini yeniden uretir.
