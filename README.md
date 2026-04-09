# Yankura

Bu proje tek sayfalik bir site ve yerel bir Python sunucusu ile birlikte calisir.

## Instagram analizini calistirma

1. Bir Apify hesabi olustur.
2. Apify tokenini al.
3. `.env.example` dosyasini `.env` olarak kopyala.
4. `.env` icindeki `APIFY_TOKEN` alanina kendi tokenini yaz.
5. Endpoint'i yeniden acmak istiyorsan `.env` icine `INSTAGRAM_ANALYSIS_ENABLED=1` ekle.
6. Domain veya farkli bir cihaz uzerinden eriseceksen `ALLOWED_ORIGINS` satirini kendi origin'lerinle guncelle.
7. Terminalde proje klasorunde su komutu calistir:

```bash
python3 server.py
```

8. Bilgisayarda tarayicida `http://127.0.0.1:8000/` adresini ac.

## Mobilde acma

1. Bilgisayar ve telefonu ayni Wi-Fi agina bagla.
2. Sunucuyu calistir:

```bash
python3 server.py
```

3. Bilgisayarin yerel IP adresini ogren.
4. Telefonda `http://BILGISAYAR_IP:8000/` adresini ac.

Ornek:

```text
http://192.168.1.8:8000/
```

Not: Guvenlik icin varsayilan `HOST=127.0.0.1` olarak gelir. Telefonda veya yerel agda acman gerekiyorsa `.env` icine bilincli sekilde `HOST=0.0.0.0` yaz ve `ALLOWED_ORIGINS` listesine kullandigin origin'i ekle.

## Opsiyonel ortam degiskenleri

```bash
APIFY_ACTOR=apify~instagram-profile-scraper
APIFY_TIMEOUT_SECS=120
APIFY_MEMORY_MB=256
APIFY_INPUT_FIELD=usernames
APIFY_ALLOW_INSECURE_SSL=0
INSTAGRAM_ANALYSIS_ENABLED=0
MAX_REQUEST_BODY_BYTES=4096
RATE_LIMIT_WINDOW_SECS=300
RATE_LIMIT_MAX_REQUESTS=5
MAX_PROXY_IMAGE_BYTES=5242880
ALLOWED_ORIGINS=http://127.0.0.1:8000,http://localhost:8000,https://veridia.com.tr,https://www.veridia.com.tr
TRUSTED_PROXY_IPS=
PORT=8000
HOST=127.0.0.1
SITE_URL=https://veridia.com.tr
```

`SITE_URL`, blog yazisi olusturma aracinin canonical, Open Graph ve sitemap adreslerini dogru domain ile uretmesi icin kullanilir.
`TRUSTED_PROXY_IPS`, sunucu bir reverse proxy arkasinda calisiyorsa rate limit icin hangi proxy IP'lerinin `Forwarded` veya `X-Forwarded-For` header'larina guvenilecegini belirler. Bos birakilirsa sadece dogrudan baglanan istemci IP'si kullanilir.

## Kaynaklar

- Apify actor sync dataset endpoint: https://docs.apify.com/api/v2/act-run-sync-get-dataset-items-post
- Actor API ornegi: https://apify.com/datadoping/instagram-profile-scraper/api

## n8n otomasyon katmani

Repo icine, ajans operasyonlari icin ayri bir `automation/` klasoru eklendi. Bu klasor icinde:

- self-hosted n8n Docker stack'i,
- import edilebilir workflow JSON dosyalari,
- ornek lead / onboarding formlari,
- entegrasyon mimarisi ve Notion veri sozlesmeleri

yer alir.

Baslangic noktasi:

```bash
python3 automation/scripts/build_workflows.py
docker compose --env-file automation/.env -f automation/docker-compose.yml up -d
bash automation/scripts/import_workflows.sh
```

Detaylar icin `automation/README.md` dosyasina bak.
