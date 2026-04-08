# Yankura

Bu proje tek sayfalik bir site ve yerel bir Python sunucusu ile birlikte calisir.

## Instagram analizini calistirma

1. Bir Apify hesabi olustur.
2. Apify tokenini al.
3. `.env.example` dosyasini `.env` olarak kopyala.
4. `.env` icindeki `APIFY_TOKEN` alanina kendi tokenini yaz.
5. Terminalde proje klasorunde su komutu calistir:

```bash
python3 server.py
```

6. Bilgisayarda tarayicida `http://127.0.0.1:8000/index.html` adresini ac.

## Mobilde acma

1. Bilgisayar ve telefonu ayni Wi-Fi agina bagla.
2. Sunucuyu calistir:

```bash
python3 server.py
```

3. Bilgisayarin yerel IP adresini ogren.
4. Telefonda `http://BILGISAYAR_IP:8000/index.html` adresini ac.

Ornek:

```text
http://192.168.1.8:8000/index.html
```

Not: Sunucu yerel aga acik olsun diye `HOST=0.0.0.0` ile calisir. Sadece bu davranisi degistirmek istersen `.env` dosyasina `HOST=127.0.0.1` yazabilirsin.

## Opsiyonel ortam degiskenleri

```bash
APIFY_ACTOR=apify~instagram-profile-scraper
APIFY_TIMEOUT_SECS=120
APIFY_MEMORY_MB=256
APIFY_INPUT_FIELD=usernames
PORT=8000
HOST=0.0.0.0
```

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
