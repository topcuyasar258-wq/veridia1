# Yankura Automation Stack

Bu klasor, Yankura icin self-hosted n8n + AI otomasyon katmanini tutar. Mevcut landing ve `server.py` akisini bozmaz; ayrica import edilebilir workflow JSON dosyalari, ornek istemci formlari ve Docker stack'i saglar.

## Kurulum

1. `automation/.env.example` dosyasini `automation/.env` olarak kopyala.
2. Notion, Google, Resend, Slack, Meta ve Apify degiskenlerini doldur.
3. Workflow JSON'larini yeniden uret:

```bash
python3 automation/scripts/build_workflows.py
```

4. n8n stack'ini kaldir:

```bash
docker compose --env-file automation/.env -f automation/docker-compose.yml up -d
```

5. Workflow'lari import et:

```bash
bash automation/scripts/import_workflows.sh
```

6. n8n arayuzu: `http://localhost:5678`
7. Ornek form sayfalari:
   - `http://127.0.0.1:8000/automation/forms/lead-intake.html`
   - `http://127.0.0.1:8000/automation/forms/onboarding-form.html`

## Workflow listesi

- `automation/workflows/01-lead-capture-and-classification.json`
- `automation/workflows/02-proposal-generation.json`
- `automation/workflows/03-content-calendar.json`
- `automation/workflows/04-monthly-report.json`
- `automation/workflows/05-competitor-analysis.json`
- `automation/workflows/06-onboarding.json`
- `automation/workflows/07-error-handler.json`

## Webhook path'leri

- `POST /webhook/yankura/lead-intake`
- `POST /webhook/yankura/instagram-dm`
- `POST /webhook/yankura/whatsapp-inbound`
- `POST /webhook/yankura/proposal/generate`
- `POST /webhook/yankura/content/calendar/generate`
- `POST /webhook/yankura/competitor-analysis`
- `POST /webhook/yankura/slash/competitor-analysis`
- `GET /webhook/yankura/proposal-approval`
- `POST /webhook/yankura/onboarding-form`

## Notlar

- Workflow'lar, n8n credential objeleri yerine env tabanli HTTP entegrasyonlari kullanir. Bu nedenle `automation/.env` sozlesmesi kritik.
- Gmail IMAP trigger'i `Workflow 01` icinde vardir; Gmail/IMAP credential baglantisini n8n arayuzunden yapman gerekir.
- Error handler import edildikten sonra n8n UI icinden ana workflow'lara manuel atanmalidir.
- Ayrintili veri modeli ve placeholder sozlesmeleri icin `automation/docs/architecture.md` dosyasina bak.
