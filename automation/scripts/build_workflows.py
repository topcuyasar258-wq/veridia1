#!/usr/bin/env python3
from __future__ import annotations

import json
import textwrap
import uuid
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS_DIR = ROOT / "workflows"


def dedent(value: str) -> str:
    return textwrap.dedent(value).strip() + "\n"


def workflow_uuid(name: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"https://yankura.io/n8n/{name}"))


def node(
    workflow_name: str,
    name: str,
    node_type: str,
    position: tuple[int, int],
    parameters: dict,
    *,
    type_version: float | int = 1,
    extras: dict | None = None,
) -> dict:
    payload = {
        "parameters": parameters,
        "id": workflow_uuid(f"{workflow_name}:{name}"),
        "name": name,
        "type": node_type,
        "typeVersion": type_version,
        "position": list(position),
    }
    if extras:
        payload.update(extras)
    return payload


def connect(
    mapping: dict[str, dict[str, list[list[dict[str, object]]]]],
    source: str,
    target: str,
    *,
    output_index: int = 0,
    input_index: int = 0,
) -> None:
    source_bucket = mapping.setdefault(source, {"main": []})["main"]
    while len(source_bucket) <= output_index:
        source_bucket.append([])
    source_bucket[output_index].append(
        {
            "node": target,
            "type": "main",
            "index": input_index,
        }
    )


def workflow(name: str, nodes: list[dict], connections: dict[str, dict]) -> dict:
    return {
        "name": name,
        "nodes": nodes,
        "connections": connections,
        "pinData": {},
        "active": False,
        "settings": {
            "executionOrder": "v1",
        },
        "versionId": workflow_uuid(f"{name}:version"),
        "meta": {
            "instanceId": "yankura-automation",
            "templateCredsSetupCompleted": False,
        },
        "id": workflow_uuid(name),
        "tags": [],
    }


COMMON_RUNTIME = dedent(
    """
    const crypto = require('crypto');

    function readEnv(name, defaultValue = undefined) {
      const value = process.env[name];
      if (value === undefined || value === null || value === '') {
        if (defaultValue !== undefined) {
          return defaultValue;
        }
        throw new Error(`Missing environment variable: ${name}`);
      }
      return value;
    }

    function optionalEnv(name, defaultValue = '') {
      const value = process.env[name];
      if (value === undefined || value === null || value === '') {
        return defaultValue;
      }
      return value;
    }

    async function httpJson(url, options = {}) {
      const response = await fetch(url, options);
      const text = await response.text();
      let payload = {};
      try {
        payload = text ? JSON.parse(text) : {};
      } catch {
        payload = { raw: text };
      }
      if (!response.ok) {
        throw new Error(`${options.method || 'GET'} ${url} failed (${response.status}): ${text.slice(0, 500)}`);
      }
      return payload;
    }

    async function httpBytes(url, options = {}) {
      const response = await fetch(url, options);
      const buffer = Buffer.from(await response.arrayBuffer());
      if (!response.ok) {
        throw new Error(`${options.method || 'GET'} ${url} failed (${response.status}): ${buffer.toString('utf-8').slice(0, 500)}`);
      }
      return buffer;
    }

    function slugify(value) {
      return String(value || '')
        .normalize('NFKD')
        .replace(/[^\\w\\s-]/g, '')
        .trim()
        .replace(/[\\s_-]+/g, '-')
        .replace(/^-+|-+$/g, '')
        .toLowerCase();
    }

    function toText(value) {
      if (value === undefined || value === null) {
        return '';
      }
      if (typeof value === 'string') {
        return value;
      }
      if (Array.isArray(value)) {
        return value.map((entry) => toText(entry)).filter(Boolean).join(' ');
      }
      if (typeof value === 'object') {
        return JSON.stringify(value);
      }
      return String(value);
    }

    function coalesce(...values) {
      for (const value of values) {
        if (value !== undefined && value !== null && String(value).trim() !== '') {
          return value;
        }
      }
      return '';
    }

    function extractEmail(value) {
      const match = toText(value).match(/[A-Z0-9._%+-]+@[A-Z0-9.-]+\\.[A-Z]{2,}/i);
      return match ? match[0].toLowerCase() : '';
    }

    function parseNumber(value, defaultValue = 0) {
      if (typeof value === 'number' && Number.isFinite(value)) {
        return value;
      }
      const match = toText(value).replace(/\\./g, '').replace(/,/g, '.').match(/-?\\d+(?:\\.\\d+)?/);
      return match ? Number(match[0]) : defaultValue;
    }

    function parseCurrency(value) {
      return Math.round(parseNumber(value, 0));
    }

    function formatCurrency(value) {
      return new Intl.NumberFormat('tr-TR', { style: 'currency', currency: 'TRY', maximumFractionDigits: 0 }).format(Number(value || 0));
    }

    function chunkRichText(value) {
      const text = toText(value).slice(0, 1900);
      if (!text) {
        return [];
      }
      return [
        {
          type: 'text',
          text: {
            content: text,
          },
        },
      ];
    }

    function notionTitle(value) {
      return {
        title: chunkRichText(value),
      };
    }

    function notionRichText(value) {
      return {
        rich_text: chunkRichText(value),
      };
    }

    function notionSelect(value) {
      const clean = toText(value).slice(0, 100);
      return clean ? { select: { name: clean } } : { select: null };
    }

    function notionStatus(value) {
      const clean = toText(value).slice(0, 100);
      return clean ? { status: { name: clean } } : { status: null };
    }

    function notionEmail(value) {
      const clean = extractEmail(value);
      return { email: clean || null };
    }

    function notionNumber(value) {
      const parsed = Number(value);
      return { number: Number.isFinite(parsed) ? parsed : null };
    }

    function notionUrl(value) {
      const clean = toText(value);
      return { url: clean || null };
    }

    function notionDate(value) {
      const clean = toText(value);
      return clean ? { date: { start: clean } } : { date: null };
    }

    function notionCheckbox(value) {
      return { checkbox: Boolean(value) };
    }

    async function notionRequest(path, method = 'GET', body = undefined) {
      const payload = await httpJson(`https://api.notion.com/v1${path}`, {
        method,
        headers: {
          Authorization: `Bearer ${readEnv('NOTION_API_KEY')}`,
          'Notion-Version': optionalEnv('NOTION_API_VERSION', '2022-06-28'),
          'Content-Type': 'application/json',
        },
        body: body === undefined ? undefined : JSON.stringify(body),
      });
      return payload;
    }

    async function notionCreatePage(databaseId, properties) {
      return notionRequest('/pages', 'POST', {
        parent: { database_id: databaseId },
        properties,
      });
    }

    async function notionUpdatePage(pageId, properties) {
      return notionRequest(`/pages/${pageId}`, 'PATCH', { properties });
    }

    async function notionGetPage(pageId) {
      return notionRequest(`/pages/${pageId}`);
    }

    async function notionQueryDatabase(databaseId, filter = undefined, sorts = undefined) {
      const body = { page_size: 100 };
      if (filter) {
        body.filter = filter;
      }
      if (sorts) {
        body.sorts = sorts;
      }
      const response = await notionRequest(`/databases/${databaseId}/query`, 'POST', body);
      return response.results || [];
    }

    function notionPropertyText(properties, name) {
      const prop = properties?.[name];
      if (!prop) {
        return '';
      }
      switch (prop.type) {
        case 'title':
          return (prop.title || []).map((entry) => entry.plain_text || entry.text?.content || '').join('');
        case 'rich_text':
          return (prop.rich_text || []).map((entry) => entry.plain_text || entry.text?.content || '').join('');
        case 'email':
          return prop.email || '';
        case 'phone_number':
          return prop.phone_number || '';
        case 'url':
          return prop.url || '';
        case 'number':
          return prop.number === null ? '' : String(prop.number);
        case 'select':
          return prop.select?.name || '';
        case 'status':
          return prop.status?.name || '';
        case 'multi_select':
          return (prop.multi_select || []).map((entry) => entry.name).join(', ');
        case 'date':
          return prop.date?.start || '';
        case 'checkbox':
          return prop.checkbox ? 'true' : 'false';
        default:
          return '';
      }
    }

    function parseJsonFromText(rawText) {
      const text = toText(rawText).trim();
      if (!text) {
        throw new Error('AI response was empty.');
      }
      try {
        return JSON.parse(text);
      } catch {
        const match = text.match(/(\\{[\\s\\S]*\\}|\\[[\\s\\S]*\\])/);
        if (match) {
          return JSON.parse(match[1]);
        }
        throw new Error(`Could not parse JSON from AI response: ${text.slice(0, 300)}`);
      }
    }

    async function callAiJson({ systemPrompt, userPrompt, maxTokens = 1400, temperature = 0.2 }) {
      const provider = optionalEnv('AI_PROVIDER', 'anthropic').toLowerCase();
      if (provider === 'openai') {
        const response = await httpJson('https://api.openai.com/v1/responses', {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${readEnv('OPENAI_API_KEY')}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            model: optionalEnv('OPENAI_MODEL', 'gpt-4.1-mini'),
            input: [
              { role: 'system', content: [{ type: 'input_text', text: systemPrompt }] },
              { role: 'user', content: [{ type: 'input_text', text: userPrompt }] },
            ],
            text: {
              format: {
                type: 'json_schema',
                name: 'yankura_response',
                schema: {
                  type: 'object',
                  additionalProperties: true,
                },
              },
            },
            max_output_tokens: maxTokens,
            temperature,
          }),
        });
        const outputText = response.output_text
          || (response.output || [])
            .flatMap((entry) => entry.content || [])
            .map((entry) => entry.text || '')
            .join('\\n');
        return parseJsonFromText(outputText);
      }

      const anthropicResponse = await httpJson('https://api.anthropic.com/v1/messages', {
        method: 'POST',
        headers: {
          'x-api-key': readEnv('ANTHROPIC_API_KEY'),
          'anthropic-version': optionalEnv('ANTHROPIC_VERSION', '2023-06-01'),
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          model: optionalEnv('ANTHROPIC_MODEL', 'claude-sonnet-4-20250514'),
          system: systemPrompt,
          max_tokens: maxTokens,
          temperature,
          messages: [
            {
              role: 'user',
              content: userPrompt,
            },
          ],
        }),
      });

      const text = (anthropicResponse.content || [])
        .filter((entry) => entry.type === 'text')
        .map((entry) => entry.text)
        .join('\\n');
      return parseJsonFromText(text);
    }

    async function sendEmail({ to, subject, html, attachments = [] }) {
      if (!to) {
        return { skipped: true };
      }
      const response = await httpJson('https://api.resend.com/emails', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${readEnv('RESEND_API_KEY')}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          from: readEnv('RESEND_FROM_EMAIL'),
          reply_to: optionalEnv('YANKURA_REPLY_TO', readEnv('RESEND_FROM_EMAIL')),
          to: [to],
          subject,
          html,
          attachments,
        }),
      });
      return response;
    }

    async function postSlack(text, webhookEnv = 'SLACK_WEBHOOK_URL') {
      const webhook = optionalEnv(webhookEnv);
      if (!webhook) {
        return { skipped: true };
      }
      const response = await fetch(webhook, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ text }),
      });
      if (!response.ok) {
        throw new Error(`Slack notification failed (${response.status})`);
      }
      return { ok: true };
    }

    function base64UrlEncode(input) {
      return Buffer.from(input).toString('base64').replace(/=/g, '').replace(/\\+/g, '-').replace(/\\//g, '_');
    }

    async function googleAccessToken(scopes) {
      const serviceEmail = readEnv('GOOGLE_SERVICE_ACCOUNT_EMAIL');
      const privateKey = readEnv('GOOGLE_SERVICE_ACCOUNT_PRIVATE_KEY').replace(/\\\\n/g, '\\n');
      const now = Math.floor(Date.now() / 1000);
      const payload = {
        iss: serviceEmail,
        scope: scopes.join(' '),
        aud: 'https://oauth2.googleapis.com/token',
        iat: now,
        exp: now + 3600,
      };
      const delegatedUser = optionalEnv('GOOGLE_DELEGATED_USER');
      if (delegatedUser) {
        payload.sub = delegatedUser;
      }
      const header = { alg: 'RS256', typ: 'JWT' };
      const unsignedJwt = `${base64UrlEncode(JSON.stringify(header))}.${base64UrlEncode(JSON.stringify(payload))}`;
      const signer = crypto.createSign('RSA-SHA256');
      signer.update(unsignedJwt);
      signer.end();
      const signature = signer.sign(privateKey).toString('base64').replace(/=/g, '').replace(/\\+/g, '-').replace(/\\//g, '_');
      const assertion = `${unsignedJwt}.${signature}`;
      const body = new URLSearchParams({
        grant_type: 'urn:ietf:params:oauth:grant-type:jwt-bearer',
        assertion,
      });
      const response = await httpJson('https://oauth2.googleapis.com/token', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: body.toString(),
      });
      return response.access_token;
    }

    async function googleJson(url, token, method = 'GET', body = undefined) {
      return httpJson(url, {
        method,
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: body === undefined ? undefined : JSON.stringify(body),
      });
    }

    async function googleCreateDoc(name, folderId, textContent) {
      const token = await googleAccessToken([
        'https://www.googleapis.com/auth/drive',
        'https://www.googleapis.com/auth/documents',
      ]);
      const file = await googleJson('https://www.googleapis.com/drive/v3/files?supportsAllDrives=true', token, 'POST', {
        name,
        mimeType: 'application/vnd.google-apps.document',
        parents: [folderId],
      });
      await googleJson(`https://docs.googleapis.com/v1/documents/${file.id}:batchUpdate`, token, 'POST', {
        requests: [
          {
            insertText: {
              location: { index: 1 },
              text: textContent,
            },
          },
        ],
      });
      const pdfBuffer = await httpBytes(
        `https://www.googleapis.com/drive/v3/files/${file.id}/export?mimeType=application/pdf&supportsAllDrives=true`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        },
      );
      return {
        id: file.id,
        url: `https://docs.google.com/document/d/${file.id}/edit`,
        pdfBase64: pdfBuffer.toString('base64'),
      };
    }

    async function googleCreateFolder(name, parentId) {
      const token = await googleAccessToken(['https://www.googleapis.com/auth/drive']);
      const folder = await googleJson('https://www.googleapis.com/drive/v3/files?supportsAllDrives=true', token, 'POST', {
        name,
        mimeType: 'application/vnd.google-apps.folder',
        parents: [parentId],
      });
      return {
        id: folder.id,
        url: `https://drive.google.com/drive/folders/${folder.id}`,
      };
    }

    async function googleSheetsAppend(spreadsheetId, range, rows) {
      const token = await googleAccessToken(['https://www.googleapis.com/auth/spreadsheets']);
      return googleJson(
        `https://sheets.googleapis.com/v4/spreadsheets/${spreadsheetId}/values/${encodeURIComponent(range)}:append?valueInputOption=USER_ENTERED`,
        token,
        'POST',
        {
          values: rows,
        },
      );
    }

    async function googleCopySlidesTemplate(templateId, name, folderId) {
      const token = await googleAccessToken([
        'https://www.googleapis.com/auth/drive',
        'https://www.googleapis.com/auth/presentations',
      ]);
      const copy = await googleJson(
        `https://www.googleapis.com/drive/v3/files/${templateId}/copy?supportsAllDrives=true`,
        token,
        'POST',
        {
          name,
          parents: [folderId],
        },
      );
      return {
        id: copy.id,
        token,
      };
    }

    async function googleSlidesReplaceText(presentationId, token, replacements) {
      const requests = replacements.map((entry) => ({
        replaceAllText: {
          containsText: {
            text: entry.placeholder,
            matchCase: true,
          },
          replaceText: entry.value,
        },
      }));
      await googleJson(
        `https://slides.googleapis.com/v1/presentations/${presentationId}:batchUpdate`,
        token,
        'POST',
        { requests },
      );
    }

    async function googleExportPdf(fileId, token) {
      return httpBytes(
        `https://www.googleapis.com/drive/v3/files/${fileId}/export?mimeType=application/pdf&supportsAllDrives=true`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        },
      );
    }

    function previousMonthRange() {
      const now = new Date();
      const start = new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth() - 1, 1));
      const end = new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), 0));
      const iso = (date) => date.toISOString().slice(0, 10);
      const label = start.toLocaleDateString('tr-TR', {
        year: 'numeric',
        month: 'long',
        timeZone: 'Europe/Istanbul',
      });
      return {
        since: iso(start),
        until: iso(end),
        label,
      };
    }

    function nextFiveWeekdays() {
      const dates = [];
      const cursor = new Date();
      cursor.setHours(0, 0, 0, 0);
      while (dates.length < 5) {
        cursor.setDate(cursor.getDate() + 1);
        const day = cursor.getDay();
        if (day !== 0 && day !== 6) {
          dates.push(new Date(cursor));
        }
      }
      return dates.map((date) => ({
        iso: date.toISOString().slice(0, 10),
        label: date.toLocaleDateString('tr-TR', {
          weekday: 'long',
          day: 'numeric',
          month: 'long',
          timeZone: 'Europe/Istanbul',
        }),
      }));
    }

    function serviceKeywordFallback(text) {
      const raw = toText(text).toLowerCase();
      if (/reklam|meta|facebook ads|tiktok ads|kampanya|roas|cpm|ctr/.test(raw)) {
        return 'reklam_kampanyasi';
      }
      if (/içerik|icerik|caption|reels|carousel|tasarım|brief/.test(raw)) {
        return 'icerik_uretimi';
      }
      if (/rapor|report|performans|ölçüm|olcum/.test(raw)) {
        return 'raporlama';
      }
      if (/sosyal medya|instagram yönetimi|instagram yonetimi|takvim|planlama/.test(raw)) {
        return 'sosyal_medya_yonetimi';
      }
      return 'diger';
    }
    """
)


def code_node(workflow_name: str, name: str, position: tuple[int, int], body: str) -> dict:
    return node(
        workflow_name,
        name,
        "n8n-nodes-base.code",
        position,
        {"jsCode": dedent(body)},
        type_version=2,
    )


def webhook_node(
    workflow_name: str,
    name: str,
    path: str,
    position: tuple[int, int],
    *,
    method: str = "POST",
) -> dict:
    return node(
        workflow_name,
        name,
        "n8n-nodes-base.webhook",
        position,
        {
            "httpMethod": method,
            "path": path,
            "responseMode": "onReceived",
            "options": {},
        },
        type_version=2,
        extras={"webhookId": workflow_uuid(f"{workflow_name}:{path}")},
    )


def schedule_trigger_node(workflow_name: str, name: str, expression: str, position: tuple[int, int]) -> dict:
    return node(
        workflow_name,
        name,
        "n8n-nodes-base.scheduleTrigger",
        position,
        {
            "rule": {
                "interval": [
                    {
                        "field": "cronExpression",
                        "expression": expression,
                    }
                ]
            }
        },
        type_version=1.2,
    )


def switch_node(
    workflow_name: str,
    name: str,
    value_expression: str,
    rules: list[str],
    position: tuple[int, int],
    *,
    fallback_output: int,
) -> dict:
    return node(
        workflow_name,
        name,
        "n8n-nodes-base.switch",
        position,
        {
            "dataType": "string",
            "value1": value_expression,
            "rules": {
                "rules": [
                    {
                        "operation": "equal",
                        "value2": rule,
                    }
                    for rule in rules
                ]
            },
            "fallbackOutput": fallback_output,
        },
        type_version=1,
    )


def email_imap_node(workflow_name: str, name: str, position: tuple[int, int]) -> dict:
    return node(
        workflow_name,
        name,
        "n8n-nodes-base.emailReadImap",
        position,
        {
            "downloadAttachments": False,
            "options": {},
        },
        type_version=2,
    )


def error_trigger_node(workflow_name: str, name: str, position: tuple[int, int]) -> dict:
    return node(
        workflow_name,
        name,
        "n8n-nodes-base.errorTrigger",
        position,
        {},
        type_version=1,
    )


def build_workflow_01() -> dict:
    wf = "01_Lead_Capture_Classification"
    nodes: list[dict] = [
        webhook_node(wf, "Lead Form Webhook", "yankura/lead-intake", (60, 140)),
        webhook_node(wf, "Instagram DM Webhook", "yankura/instagram-dm", (60, 300)),
        webhook_node(wf, "WhatsApp Webhook", "yankura/whatsapp-inbound", (60, 460)),
        email_imap_node(wf, "Gmail IMAP Trigger", (60, 620)),
        code_node(
            wf,
            "Normalize Intake",
            (320, 340),
            f"""
            {COMMON_RUNTIME}
            function extractBudgetText(text) {{
              const match = toText(text).match(/(\\d{{1,3}}(?:[.,]\\d{{3}})*(?:\\s*[-–]\\s*\\d{{1,3}}(?:[.,]\\d{{3}})*)?)\\s*(tl|try)/i);
              return match ? match[0] : '';
            }}

            const results = items.map((item) => {{
              const raw = item.json || {{}};
              const body = raw.body && typeof raw.body === 'object' ? raw.body : raw;
              const headers = raw.headers || {{}};
              const emailText = [raw.subject, raw.textPlain, raw.textHtml].filter(Boolean).join('\\n');
              const source = coalesce(
                body.source,
                headers['x-yankura-source'],
                headers['x-manychat-subscriber-id'] ? 'instagram_dm' : '',
                headers['x-twilio-signature'] ? 'whatsapp' : '',
                raw.from ? 'email' : '',
                'web_form',
              );
              const requestText = coalesce(body.request, body.talep, body.message, body.notes, body.text, emailText);
              const requestedService = coalesce(body.service, body.requestedService, body.hizmet, serviceKeywordFallback(requestText));
              const name = coalesce(body.name, body.fullName, body.isim, raw.from?.value?.[0]?.name, body.company, 'Yeni Lead');
              const email = extractEmail(coalesce(body.email, raw.from?.value?.[0]?.address, raw.from?.text));
              const phone = coalesce(body.phone, body.telefon, body.whatsapp, body.mobile);
              const company = coalesce(body.company, body.companyName, body.brandName, body.marka, '');
              const sector = coalesce(body.sector, body.sektor, 'Belirtilmedi');
              const budgetRaw = coalesce(body.budget, body.butce, extractBudgetText(requestText), 'Belirtilmedi');
              const leadId = `lead-${{slugify(company || name || email || 'yankura')}}-${{Date.now()}}`;
              return {{
                json: {{
                  leadId,
                  source,
                  name,
                  email,
                  phone,
                  company,
                  sector,
                  budgetRaw,
                  budgetValue: parseCurrency(budgetRaw),
                  requestedServiceRaw: requestedService,
                  requestText,
                  receivedAt: new Date().toISOString(),
                }},
              }};
            }});

            return results;
            """,
        ),
        code_node(
            wf,
            "Classify Lead",
            (560, 340),
            f"""
            {COMMON_RUNTIME}
            const output = [];
            for (const item of items) {{
              const fallbackCategory = serviceKeywordFallback(`${{item.json.requestText}} ${{item.json.requestedServiceRaw}}`);
              let classification = {{
                category: fallbackCategory,
                rationale: 'Anahtar kelime fallback kurali ile siniflandirildi.',
                confidence: 0.58,
                urgency: 'normal',
              }};

              try {{
                classification = await callAiJson({{
                  systemPrompt: 'Sen Yankura icin lead siniflandirma asistani sin. Sadece gecerli JSON don.',
                  userPrompt: `
                  Asagidaki lead verisini incele ve yalnizca su kategorilerden birini sec:
                  [sosyal_medya_yonetimi, reklam_kampanyasi, icerik_uretimi, raporlama, diger]

                  Lead:
                  ${{JSON.stringify(item.json, null, 2)}}

                  Donus JSON seklinde olmali:
                  {{
                    "category": "...",
                    "rationale": "...",
                    "confidence": 0.0,
                    "urgency": "dusuk|normal|yuksek"
                  }}
                  `,
                }});
              }} catch (error) {{
                classification.aiError = error.message;
              }}

              output.push({{
                json: {{
                  ...item.json,
                  serviceCategory: classification.category || fallbackCategory,
                  classificationReason: classification.rationale || '',
                  classificationConfidence: classification.confidence || 0,
                  urgency: classification.urgency || 'normal',
                  aiFallbackUsed: Boolean(classification.aiError),
                }},
              }});
            }}

            return output;
            """,
        ),
        code_node(
            wf,
            "Create Notion Lead",
            (800, 340),
            f"""
            {COMMON_RUNTIME}
            const response = [];
            for (const item of items) {{
              const page = await notionCreatePage(readEnv('NOTION_LEADS_DATABASE_ID'), {{
                Name: notionTitle(item.json.company || item.json.name || item.json.leadId),
                Email: notionEmail(item.json.email),
                Phone: notionRichText(item.json.phone),
                Company: notionRichText(item.json.company || item.json.name),
                Sector: notionSelect(item.json.sector),
                Source: notionSelect(item.json.source),
                Category: notionSelect(item.json.serviceCategory),
                'Lead Status': notionStatus('Lead'),
                'Lead ID': notionRichText(item.json.leadId),
                'Requested Service': notionRichText(item.json.requestedServiceRaw),
                Request: notionRichText(item.json.requestText),
                'Budget Label': notionRichText(item.json.budgetRaw),
                'Budget Value': notionNumber(item.json.budgetValue),
                'Classification Note': notionRichText(item.json.classificationReason),
                'Created At': notionDate(item.json.receivedAt),
              }});

              response.push({{
                json: {{
                  ...item.json,
                  notionLeadPageId: page.id,
                  notionLeadUrl: page.url,
                }},
              }});
            }}

            return response;
            """,
        ),
        switch_node(
            wf,
            "Switch Category",
            "={{$json.serviceCategory}}",
            [
                "sosyal_medya_yonetimi",
                "reklam_kampanyasi",
                "icerik_uretimi",
                "raporlama",
            ],
            (1040, 340),
            fallback_output=4,
        ),
        code_node(
            wf,
            "Route Social Media",
            (1280, 80),
            f"""
            {COMMON_RUNTIME}
            for (const item of items) {{
              await httpJson(`${{readEnv('INTERNAL_WEBHOOK_BASE_URL', 'http://n8n-main:5678')}}/webhook/yankura/proposal/generate`, {{
                method: 'POST',
                headers: {{ 'Content-Type': 'application/json' }},
                body: JSON.stringify({{
                  ...item.json,
                  proposalTrack: 'social_media',
                  packageFrame: 'Sosyal medya yonetimi odakli teklif',
                }}),
              }});
            }}
            return items;
            """,
        ),
        code_node(
            wf,
            "Route Ad Campaigns",
            (1280, 220),
            f"""
            {COMMON_RUNTIME}
            for (const item of items) {{
              await httpJson(`${{readEnv('INTERNAL_WEBHOOK_BASE_URL', 'http://n8n-main:5678')}}/webhook/yankura/proposal/generate`, {{
                method: 'POST',
                headers: {{ 'Content-Type': 'application/json' }},
                body: JSON.stringify({{
                  ...item.json,
                  proposalTrack: 'ads',
                  packageFrame: 'Meta ve TikTok reklam yonetimi odakli teklif',
                }}),
              }});
            }}
            return items;
            """,
        ),
        code_node(
            wf,
            "Route Content Production",
            (1280, 360),
            f"""
            {COMMON_RUNTIME}
            for (const item of items) {{
              await httpJson(`${{readEnv('INTERNAL_WEBHOOK_BASE_URL', 'http://n8n-main:5678')}}/webhook/yankura/proposal/generate`, {{
                method: 'POST',
                headers: {{ 'Content-Type': 'application/json' }},
                body: JSON.stringify({{
                  ...item.json,
                  proposalTrack: 'content',
                  packageFrame: 'Icerik uretimi ve takvim odakli teklif',
                }}),
              }});
            }}
            return items;
            """,
        ),
        code_node(
            wf,
            "Route Reporting",
            (1280, 500),
            f"""
            {COMMON_RUNTIME}
            for (const item of items) {{
              await httpJson(`${{readEnv('INTERNAL_WEBHOOK_BASE_URL', 'http://n8n-main:5678')}}/webhook/yankura/proposal/generate`, {{
                method: 'POST',
                headers: {{ 'Content-Type': 'application/json' }},
                body: JSON.stringify({{
                  ...item.json,
                  proposalTrack: 'reporting',
                  packageFrame: 'Raporlama ve optimizasyon odakli teklif',
                }}),
              }});
            }}
            return items;
            """,
        ),
        code_node(
            wf,
            "Route Manual Review",
            (1280, 640),
            f"""
            {COMMON_RUNTIME}
            for (const item of items) {{
              await postSlack(
                `Yeni manuel inceleme lead'i\\nKaynak: ${{item.json.source}}\\nAd: ${{item.json.name}}\\nSirket: ${{item.json.company || '-'}}\\nTalep: ${{item.json.requestText}}`,
                'SLACK_WEBHOOK_URL',
              );
            }}
            return items;
            """,
        ),
        code_node(
            wf,
            "Send Ack Email",
            (1530, 340),
            f"""
            {COMMON_RUNTIME}
            const results = [];
            for (const item of items) {{
              if (item.json.email) {{
                await sendEmail({{
                  to: item.json.email,
                  subject: 'Talebinizi aldik | Yankura',
                  html: `
                    <div style="font-family:Arial,sans-serif;line-height:1.6">
                      <p>Merhaba ${{item.json.name.split(' ')[0]}},</p>
                      <p>Mesajiniz bize ulasti. Yankura ekibi olarak talebinizi inceledik ve size uygun akis icin sistemi calistirdik.</p>
                      <p><strong>Talep kategorisi:</strong> ${{item.json.serviceCategory}}</p>
                      <p>Kisa sure icinde teklifinizi paylasacagiz. Bu sirada eklemek istediginiz bir detay varsa bu maile direkt yanit verebilirsiniz.</p>
                      <p>Sevgiler,<br>Yankura</p>
                    </div>
                  `,
                }});
              }}
              results.push(item);
            }}
            return results;
            """,
        ),
    ]

    connections: dict[str, dict] = {}
    for trigger_name in [
        "Lead Form Webhook",
        "Instagram DM Webhook",
        "WhatsApp Webhook",
        "Gmail IMAP Trigger",
    ]:
        connect(connections, trigger_name, "Normalize Intake")
    connect(connections, "Normalize Intake", "Classify Lead")
    connect(connections, "Classify Lead", "Create Notion Lead")
    connect(connections, "Create Notion Lead", "Switch Category")
    connect(connections, "Switch Category", "Route Social Media", output_index=0)
    connect(connections, "Switch Category", "Route Ad Campaigns", output_index=1)
    connect(connections, "Switch Category", "Route Content Production", output_index=2)
    connect(connections, "Switch Category", "Route Reporting", output_index=3)
    connect(connections, "Switch Category", "Route Manual Review", output_index=4)
    for route_name in [
        "Route Social Media",
        "Route Ad Campaigns",
        "Route Content Production",
        "Route Reporting",
        "Route Manual Review",
    ]:
        connect(connections, route_name, "Send Ack Email")
    return workflow("Yankura | 01 Lead Capture & Classification", nodes, connections)


def build_workflow_02() -> dict:
    wf = "02_Proposal_Generation"
    nodes = [
        webhook_node(wf, "Proposal Webhook", "yankura/proposal/generate", (80, 260)),
        code_node(
            wf,
            "Normalize Proposal Input",
            (320, 260),
            f"""
            {COMMON_RUNTIME}
            const pricingByTrack = {{
              social_media: {{ starter: 18000, growth: 32000, pro: 54000 }},
              ads: {{ starter: 22000, growth: 38000, pro: 65000 }},
              content: {{ starter: 15000, growth: 28000, pro: 46000 }},
              reporting: {{ starter: 12000, growth: 22000, pro: 36000 }},
            }};

            return items.map((item) => {{
              const track = coalesce(item.json.proposalTrack, item.json.serviceCategory, 'social_media');
              const defaults = pricingByTrack[track] || pricingByTrack.social_media;
              return {{
                json: {{
                  ...item.json,
                  proposalTrack: track,
                  pricingGuide: defaults,
                }},
              }};
            }});
            """,
        ),
        code_node(
            wf,
            "Generate Proposal Content",
            (580, 260),
            f"""
            {COMMON_RUNTIME}
            const results = [];
            for (const item of items) {{
              const guide = item.json.pricingGuide;
              const proposal = await callAiJson({{
                systemPrompt: 'Sen Yankura ajansinin teklif yazarisin. Turkce, profesyonel ama sicak bir tonda yalnizca JSON dondur.',
                userPrompt: `
                Sen Yankura ajansinin teklif yazarisin. Asagidaki musteri icin Turkce, profesyonel ama sicak bir teklif metni olustur.

                Musteri: ${{item.json.name}}
                Sirket / Marka: ${{item.json.company || item.json.name}}
                Sektor: ${{item.json.sector}}
                Istek: ${{item.json.requestText}}
                Butce: ${{item.json.budgetRaw}}
                Kategori: ${{item.json.serviceCategory}}

                Fiyat rehberi:
                Starter taban: ${{guide.starter}} TL
                Growth taban: ${{guide.growth}} TL
                Pro taban: ${{guide.pro}} TL

                JSON seklinde don:
                {{
                  "emailSubject": "...",
                  "opening": "...",
                  "packages": [
                    {{
                      "name": "Starter",
                      "priceRange": "...",
                      "duration": "...",
                      "services": ["..."],
                      "bestFor": "..."
                    }},
                    {{
                      "name": "Growth",
                      "priceRange": "...",
                      "duration": "...",
                      "services": ["..."],
                      "bestFor": "..."
                    }},
                    {{
                      "name": "Pro",
                      "priceRange": "...",
                      "duration": "...",
                      "services": ["..."],
                      "bestFor": "..."
                    }}
                  ],
                  "whyYankura": "...",
                  "cta": "..."
                }}
                `,
              }});

              results.push({{
                json: {{
                  ...item.json,
                  proposal,
                }},
              }});
            }}
            return results;
            """,
        ),
        code_node(
            wf,
            "Create Doc And Approval Links",
            (860, 260),
            f"""
            {COMMON_RUNTIME}
            const results = [];
            for (const item of items) {{
              const approvalToken = crypto.randomUUID();
              const proposal = item.json.proposal;
              const proposalText = [
                `YANKURA TEKLIFI`,
                ``,
                `Musteri: ${{item.json.company || item.json.name}}`,
                `Sektor: ${{item.json.sector}}`,
                `Talep: ${{item.json.requestText}}`,
                ``,
                proposal.opening,
                ``,
                ...proposal.packages.flatMap((pkg) => [
                  `## ${{pkg.name}}`,
                  `Fiyat: ${{pkg.priceRange}}`,
                  `Sure: ${{pkg.duration}}`,
                  `Kimler icin: ${{pkg.bestFor}}`,
                  `Hizmetler:`,
                  ...pkg.services.map((entry) => `- ${{entry}}`),
                  ``,
                ]),
                `Neden Yankura?`,
                proposal.whyYankura,
                ``,
                `Kapanis`,
                proposal.cta,
              ].join('\\n');

              const docName = `${{item.json.company || item.json.name}} - Yankura Teklif - ${{new Date().toISOString().slice(0, 10)}}`;
              const doc = await googleCreateDoc(docName, readEnv('GOOGLE_DRIVE_PROPOSALS_FOLDER_ID'), proposalText);
              const publicBase = readEnv('PUBLIC_WEBHOOK_BASE_URL');
              const approvalLinks = Object.fromEntries(
                proposal.packages.map((pkg) => [
                  pkg.name,
                  `${{publicBase}}/webhook/yankura/proposal-approval?leadPageId=${{encodeURIComponent(item.json.notionLeadPageId)}}&approvalToken=${{encodeURIComponent(approvalToken)}}&selectedPackage=${{encodeURIComponent(pkg.name)}}`,
                ]),
              );

              await notionUpdatePage(item.json.notionLeadPageId, {{
                'Lead Status': notionStatus('Proposal Sent'),
                'Proposal Url': notionUrl(doc.url),
                'Approval Token': notionRichText(approvalToken),
              }});

              results.push({{
                json: {{
                  ...item.json,
                  approvalToken,
                  approvalLinks,
                  proposalDocUrl: doc.url,
                  proposalPdfBase64: doc.pdfBase64,
                  proposalPdfName: `${{slugify(item.json.company || item.json.name || item.json.leadId)}}-yankura-teklif.pdf`,
                }},
              }});
            }}
            return results;
            """,
        ),
        code_node(
            wf,
            "Send Proposal Email",
            (1140, 180),
            f"""
            {COMMON_RUNTIME}
            const results = [];
            for (const item of items) {{
              const proposal = item.json.proposal;
              const cards = proposal.packages.map((pkg) => `
                <div style="border:1px solid #e5e7eb;border-radius:14px;padding:18px;margin-bottom:14px">
                  <h3 style="margin:0 0 10px 0">${{pkg.name}}</h3>
                  <p style="margin:0 0 6px 0"><strong>Fiyat:</strong> ${{pkg.priceRange}}</p>
                  <p style="margin:0 0 6px 0"><strong>Sure:</strong> ${{pkg.duration}}</p>
                  <p style="margin:0 0 10px 0"><strong>Kimler icin:</strong> ${{pkg.bestFor}}</p>
                  <ul style="padding-left:18px;margin:0 0 14px 0">
                    ${{pkg.services.map((service) => `<li>${{service}}</li>`).join('')}}
                  </ul>
                  <a href="${{item.json.approvalLinks[pkg.name]}}" style="display:inline-block;background:#111827;color:#fff;padding:10px 14px;border-radius:10px;text-decoration:none">Bu paketi onayla</a>
                </div>
              `).join('');

              await sendEmail({{
                to: item.json.email,
                subject: proposal.emailSubject || 'Yankura teklifiniz hazir',
                html: `
                  <div style="font-family:Arial,sans-serif;line-height:1.7;color:#111827">
                    <p>Merhaba ${{item.json.name.split(' ')[0]}},</p>
                    <p>${{proposal.opening}}</p>
                    ${{cards}}
                    <p><strong>Neden Yankura?</strong><br>${{proposal.whyYankura}}</p>
                    <p>${{proposal.cta}}</p>
                    <p>Teklif dokumaninizi da PDF olarak ekte paylastik. Sorulariniz olursa bu maile cevap verebilirsiniz.</p>
                  </div>
                `,
                attachments: [
                  {{
                    filename: item.json.proposalPdfName,
                    content: item.json.proposalPdfBase64,
                  }},
                ],
              }});
              results.push(item);
            }}
            return results;
            """,
        ),
        code_node(
            wf,
            "Notify Slack New Proposal",
            (1140, 340),
            f"""
            {COMMON_RUNTIME}
            for (const item of items) {{
              await postSlack(
                `Yeni teklif hazirlandi\\nMusteri: ${{item.json.company || item.json.name}}\\nKategori: ${{item.json.serviceCategory}}\\nDokuman: ${{item.json.proposalDocUrl}}`,
                'SLACK_WEBHOOK_NEW_PROPOSAL',
              );
            }}
            return items;
            """,
        ),
    ]

    connections: dict[str, dict] = {}
    connect(connections, "Proposal Webhook", "Normalize Proposal Input")
    connect(connections, "Normalize Proposal Input", "Generate Proposal Content")
    connect(connections, "Generate Proposal Content", "Create Doc And Approval Links")
    connect(connections, "Create Doc And Approval Links", "Send Proposal Email")
    connect(connections, "Create Doc And Approval Links", "Notify Slack New Proposal")
    return workflow("Yankura | 02 Proposal Generation", nodes, connections)


def build_workflow_03() -> dict:
    wf = "03_Content_Calendar"
    nodes = [
        webhook_node(wf, "Content Calendar Webhook", "yankura/content/calendar/generate", (80, 140)),
        schedule_trigger_node(wf, "Weekly Content Trigger", "0 10 * * 1", (80, 340)),
        code_node(
            wf,
            "Load Client Context",
            (340, 240),
            f"""
            {COMMON_RUNTIME}
            const results = [];
            const explicitLeadId = items[0]?.json?.leadPageId || items[0]?.json?.notionLeadPageId || '';
            const pages = explicitLeadId
              ? [await notionGetPage(explicitLeadId)]
              : await notionQueryDatabase(
                  readEnv('NOTION_LEADS_DATABASE_ID'),
                  {{
                    property: 'Lead Status',
                    status: {{ equals: 'Active' }},
                  }},
                );

            for (const page of pages) {{
              const properties = page.properties || {{}};
              results.push({{
                json: {{
                  notionLeadPageId: page.id,
                  clientName: notionPropertyText(properties, 'Company') || notionPropertyText(properties, 'Name'),
                  email: notionPropertyText(properties, 'Email'),
                  sector: notionPropertyText(properties, 'Sector') || 'Belirtilmedi',
                  targetAudience: notionPropertyText(properties, 'Target Audience') || 'KOBI karar vericileri ve son kullanici karmasi',
                  brandVoice: notionPropertyText(properties, 'Brand Voice') || 'Net, sicak ve guven veren',
                  avoidTopics: notionPropertyText(properties, 'Avoid Topics') || 'Siyasi kutuplasma ve markayla uyumsuz mizah',
                }},
              }});
            }}

            return results;
            """,
        ),
        code_node(
            wf,
            "Generate Weekly Calendar",
            (620, 240),
            f"""
            {COMMON_RUNTIME}
            const results = [];
            for (const item of items) {{
              const dates = nextFiveWeekdays();
              const calendar = await callAiJson({{
                systemPrompt: 'Sen Yankura icin sosyal medya icerik stratejisti sin. Turkce, uygulanabilir ve yalnizca JSON dondur.',
                userPrompt: `
                Turkiye pazari icin ${{item.json.sector}} sektorunde faaliyet gosteren ${{item.json.clientName}} markasi icin bu haftanin 5 gunluk Instagram icerik takvimini olustur.
                Hedef kitle: ${{item.json.targetAudience}}
                Marka sesi: ${{item.json.brandVoice}}
                Kacinilacak konular: ${{item.json.avoidTopics}}
                Tarihler:
                ${{dates.map((entry) => `- ${{entry.label}} (${{entry.iso}})`).join('\\n')}}

                JSON seklinde don:
                {{
                  "weeklySummary": "...",
                  "entries": [
                    {{
                      "date": "YYYY-MM-DD",
                      "topic": "...",
                      "format": "reels|carousel|gonderi",
                      "caption": "...",
                      "hashtags": ["...", "..."],
                      "creativeBrief": "..."
                    }}
                  ]
                }}
                `,
              }});

              results.push({{
                json: {{
                  ...item.json,
                  calendar,
                }},
              }});
            }}
            return results;
            """,
        ),
        code_node(
            wf,
            "Persist Calendar To Notion",
            (900, 240),
            f"""
            {COMMON_RUNTIME}
            const results = [];
            for (const item of items) {{
              const createdPages = [];
              for (const entry of item.json.calendar.entries || []) {{
                const page = await notionCreatePage(readEnv('NOTION_CONTENT_CALENDAR_DATABASE_ID'), {{
                  Name: notionTitle(`${{item.json.clientName}} | ${{entry.topic}}`),
                  Client: notionRichText(item.json.clientName),
                  Date: notionDate(entry.date),
                  Topic: notionRichText(entry.topic),
                  Format: notionSelect(entry.format),
                  Caption: notionRichText(entry.caption),
                  Hashtags: notionRichText((entry.hashtags || []).join(' ')),
                  'Creative Brief': notionRichText(entry.creativeBrief),
                  Status: notionStatus('Pending Approval'),
                }});
                createdPages.push(page.url);
              }}

              results.push({{
                json: {{
                  ...item.json,
                  contentCalendarEntryUrls: createdPages,
                }},
              }});
            }}
            return results;
            """,
        ),
        code_node(
            wf,
            "Send Slack Weekly Summary",
            (1180, 140),
            f"""
            {COMMON_RUNTIME}
            for (const item of items) {{
              const lines = (item.json.calendar.entries || []).map((entry) => `- ${{entry.date}} | ${{entry.format}} | ${{entry.topic}}`);
              await postSlack(
                `Haftalik icerik takvimi hazir\\nMusteri: ${{item.json.clientName}}\\nOzet: ${{item.json.calendar.weeklySummary}}\\n${{lines.join('\\n')}}`,
                'SLACK_WEBHOOK_CONTENT',
              );
            }}
            return items;
            """,
        ),
        code_node(
            wf,
            "Send Approval Email",
            (1180, 340),
            f"""
            {COMMON_RUNTIME}
            for (const item of items) {{
              await sendEmail({{
                to: item.json.email,
                subject: `${{item.json.clientName}} icin haftalik icerik takvimi hazir`,
                html: `
                  <div style="font-family:Arial,sans-serif;line-height:1.7">
                    <p>Merhaba,</p>
                    <p>Bu haftanin Yankura icerik takvimi hazir. Kisa ozet:</p>
                    <p>${{item.json.calendar.weeklySummary}}</p>
                    <ul>
                      ${{(item.json.calendar.entries || []).map((entry) => `<li><strong>${{entry.date}}</strong> - ${{entry.format}} - ${{entry.topic}}</li>`).join('')}}
                    </ul>
                    <p>Takvimi Notion uzerinden incelemek icin ekibimiz sizinle paylasilan icerik tablosunu kullanabilir. Detay isterseniz bu maile donus yapmaniz yeterli.</p>
                    <p>Sevgiler,<br>Yankura</p>
                  </div>
                `,
              }});
            }}
            return items;
            """,
        ),
    ]

    connections: dict[str, dict] = {}
    connect(connections, "Content Calendar Webhook", "Load Client Context")
    connect(connections, "Weekly Content Trigger", "Load Client Context")
    connect(connections, "Load Client Context", "Generate Weekly Calendar")
    connect(connections, "Generate Weekly Calendar", "Persist Calendar To Notion")
    connect(connections, "Persist Calendar To Notion", "Send Slack Weekly Summary")
    connect(connections, "Persist Calendar To Notion", "Send Approval Email")
    return workflow("Yankura | 03 Content Calendar & Captions", nodes, connections)


def build_workflow_04() -> dict:
    wf = "04_Monthly_Report"
    nodes = [
        schedule_trigger_node(wf, "Monthly Report Trigger", "0 9 1 * *", (80, 240)),
        code_node(
            wf,
            "Load Active Ad Clients",
            (320, 240),
            f"""
            {COMMON_RUNTIME}
            const pages = await notionQueryDatabase(readEnv('NOTION_LEADS_DATABASE_ID'), {{
              and: [
                {{
                  property: 'Lead Status',
                  status: {{ equals: 'Active' }},
                }},
                {{
                  property: 'Meta Ad Account ID',
                  rich_text: {{ is_not_empty: true }},
                }},
              ],
            }});

            return pages.map((page) => {{
              const properties = page.properties || {{}};
              return {{
                json: {{
                  notionLeadPageId: page.id,
                  clientName: notionPropertyText(properties, 'Company') || notionPropertyText(properties, 'Name'),
                  email: notionPropertyText(properties, 'Email'),
                  metaAdAccountId: notionPropertyText(properties, 'Meta Ad Account ID'),
                }},
              }};
            }});
            """,
        ),
        code_node(
            wf,
            "Fetch Meta Metrics",
            (600, 240),
            f"""
            {COMMON_RUNTIME}
            const range = previousMonthRange();
            const results = [];
            for (const item of items) {{
              const fields = [
                'campaign_name',
                'reach',
                'impressions',
                'clicks',
                'spend',
                'cpm',
                'ctr',
                'purchase_roas',
              ].join(',');
              const query = new URLSearchParams({{
                fields,
                level: 'campaign',
                limit: '50',
                time_range: JSON.stringify({{ since: range.since, until: range.until }}),
                access_token: readEnv('META_ACCESS_TOKEN'),
              }});
              const url = `https://graph.facebook.com/${{optionalEnv('META_GRAPH_API_VERSION', 'v23.0')}}/act_${{item.json.metaAdAccountId}}/insights?${{query.toString()}}`;
              const response = await httpJson(url);
              const campaigns = response.data || [];
              const totals = campaigns.reduce((acc, campaign) => {{
                acc.reach += parseNumber(campaign.reach);
                acc.impressions += parseNumber(campaign.impressions);
                acc.clicks += parseNumber(campaign.clicks);
                acc.spend += parseNumber(campaign.spend);
                acc.cpm += parseNumber(campaign.cpm);
                acc.ctr += parseNumber(campaign.ctr);
                const roasValue = Array.isArray(campaign.purchase_roas) ? parseNumber(campaign.purchase_roas[0]?.value) : parseNumber(campaign.purchase_roas);
                acc.roas += roasValue;
                return acc;
              }}, {{ reach: 0, impressions: 0, clicks: 0, spend: 0, cpm: 0, ctr: 0, roas: 0 }});
              const topCampaign = [...campaigns].sort((left, right) => {{
                const leftScore = parseNumber(Array.isArray(left.purchase_roas) ? left.purchase_roas[0]?.value : left.purchase_roas) + parseNumber(left.ctr);
                const rightScore = parseNumber(Array.isArray(right.purchase_roas) ? right.purchase_roas[0]?.value : right.purchase_roas) + parseNumber(right.ctr);
                return rightScore - leftScore;
              }})[0] || null;

              results.push({{
                json: {{
                  ...item.json,
                  reportRange: range,
                  metaCampaigns: campaigns,
                  metaTotals: totals,
                  topCampaign,
                }},
              }});
            }}
            return results;
            """,
        ),
        code_node(
            wf,
            "Append Google Sheets Row",
            (880, 240),
            f"""
            {COMMON_RUNTIME}
            const results = [];
            for (const item of items) {{
              await googleSheetsAppend(
                readEnv('GOOGLE_SHEETS_REPORTING_SPREADSHEET_ID'),
                optionalEnv('GOOGLE_SHEETS_REPORTING_RANGE', 'Raw!A:I'),
                [[
                  item.json.clientName,
                  item.json.reportRange.label,
                  item.json.metaTotals.reach,
                  item.json.metaTotals.impressions,
                  item.json.metaTotals.clicks,
                  item.json.metaTotals.spend,
                  item.json.metaTotals.roas,
                  item.json.metaTotals.cpm,
                  item.json.metaTotals.ctr,
                ]],
              );
              results.push(item);
            }}
            return results;
            """,
        ),
        code_node(
            wf,
            "Generate Report Narrative",
            (1160, 240),
            f"""
            {COMMON_RUNTIME}
            const results = [];
            for (const item of items) {{
              const narrative = await callAiJson({{
                systemPrompt: 'Sen Yankura icin aylik reklam performans raporu yazan bir stratejistsin. Turkce, profesyonel ve anlasilir bir dille yalnizca JSON dondur.',
                userPrompt: `
                Asagidaki Meta reklam performans verilerini analiz et ve musteriye sunulacak Turkce rapor narratifi yaz.

                Veriler:
                ${{JSON.stringify({{
                  range: item.json.reportRange,
                  totals: item.json.metaTotals,
                  topCampaign: item.json.topCampaign,
                  campaigns: item.json.metaCampaigns,
                }}, null, 2)}}

                JSON:
                {{
                  "overviewParagraphs": ["...", "..."],
                  "topPerformer": "...",
                  "recommendations": ["...", "...", "..."],
                  "watchMetrics": ["...", "..."]
                }}
                `,
              }});

              results.push({{
                json: {{
                  ...item.json,
                  narrative,
                }},
              }});
            }}
            return results;
            """,
        ),
        code_node(
            wf,
            "Build Slides Deck And Log",
            (1440, 240),
            f"""
            {COMMON_RUNTIME}
            const results = [];
            for (const item of items) {{
              const deckName = `${{item.json.clientName}} - Yankura Aylik Rapor - ${{item.json.reportRange.label}}`;
              const copy = await googleCopySlidesTemplate(
                readEnv('GOOGLE_SLIDES_TEMPLATE_ID'),
                deckName,
                readEnv('GOOGLE_DRIVE_REPORTS_FOLDER_ID'),
              );

              await googleSlidesReplaceText(copy.id, copy.token, [
                {{ placeholder: '{{CLIENT_NAME}}', value: item.json.clientName }},
                {{ placeholder: '{{REPORT_MONTH}}', value: item.json.reportRange.label }},
                {{ placeholder: '{{OVERVIEW_1}}', value: item.json.narrative.overviewParagraphs?.[0] || '' }},
                {{ placeholder: '{{OVERVIEW_2}}', value: item.json.narrative.overviewParagraphs?.[1] || '' }},
                {{ placeholder: '{{TOP_PERFORMER}}', value: item.json.narrative.topPerformer || '' }},
                {{ placeholder: '{{RECOMMENDATION_1}}', value: item.json.narrative.recommendations?.[0] || '' }},
                {{ placeholder: '{{RECOMMENDATION_2}}', value: item.json.narrative.recommendations?.[1] || '' }},
                {{ placeholder: '{{RECOMMENDATION_3}}', value: item.json.narrative.recommendations?.[2] || '' }},
                {{ placeholder: '{{METRICS}}', value: `Reach: ${{item.json.metaTotals.reach}} | Impressions: ${{item.json.metaTotals.impressions}} | Clicks: ${{item.json.metaTotals.clicks}} | Spend: ${{formatCurrency(item.json.metaTotals.spend)}} | ROAS: ${{item.json.metaTotals.roas.toFixed(2)}} | CPM: ${{item.json.metaTotals.cpm.toFixed(2)}} | CTR: ${{item.json.metaTotals.ctr.toFixed(2)}}` }},
              ]);

              const pdfBuffer = await googleExportPdf(copy.id, copy.token);
              const reportPage = await notionCreatePage(readEnv('NOTION_REPORTS_DATABASE_ID'), {{
                Name: notionTitle(`${{item.json.clientName}} | ${{item.json.reportRange.label}}`),
                Client: notionRichText(item.json.clientName),
                'Report Month': notionRichText(item.json.reportRange.label),
                Reach: notionNumber(item.json.metaTotals.reach),
                Impressions: notionNumber(item.json.metaTotals.impressions),
                Clicks: notionNumber(item.json.metaTotals.clicks),
                Spend: notionNumber(item.json.metaTotals.spend),
                ROAS: notionNumber(item.json.metaTotals.roas),
                CPM: notionNumber(item.json.metaTotals.cpm),
                CTR: notionNumber(item.json.metaTotals.ctr),
                'Report Url': notionUrl(`https://docs.google.com/presentation/d/${{copy.id}}/edit`),
              }});

              results.push({{
                json: {{
                  ...item.json,
                  reportDeckUrl: `https://docs.google.com/presentation/d/${{copy.id}}/edit`,
                  reportPdfBase64: pdfBuffer.toString('base64'),
                  reportPdfName: `${{slugify(item.json.clientName)}}-${{slugify(item.json.reportRange.label)}}-rapor.pdf`,
                  notionReportUrl: reportPage.url,
                }},
              }});
            }}
            return results;
            """,
        ),
        code_node(
            wf,
            "Send Monthly Report Email",
            (1720, 180),
            f"""
            {COMMON_RUNTIME}
            for (const item of items) {{
              await sendEmail({{
                to: item.json.email,
                subject: `${{item.json.clientName}} | ${{item.json.reportRange.label}} reklam raporu hazir`,
                html: `
                  <div style="font-family:Arial,sans-serif;line-height:1.7">
                    <p>Merhaba,</p>
                    <p>${{item.json.reportRange.label}} donemine ait performans raporunuz hazir.</p>
                    <p><strong>Genel degerlendirme</strong></p>
                    <p>${{item.json.narrative.overviewParagraphs?.[0] || ''}}</p>
                    <p>${{item.json.narrative.overviewParagraphs?.[1] || ''}}</p>
                    <p><strong>En iyi performansli reklam</strong><br>${{item.json.narrative.topPerformer || ''}}</p>
                    <ul>${{(item.json.narrative.recommendations || []).map((entry) => `<li>${{entry}}</li>`).join('')}}</ul>
                    <p>Sunum linki: <a href="${{item.json.reportDeckUrl}}">${{item.json.reportDeckUrl}}</a></p>
                  </div>
                `,
                attachments: [
                  {{
                    filename: item.json.reportPdfName,
                    content: item.json.reportPdfBase64,
                  }},
                ],
              }});
            }}
            return items;
            """,
        ),
    ]

    connections: dict[str, dict] = {}
    connect(connections, "Monthly Report Trigger", "Load Active Ad Clients")
    connect(connections, "Load Active Ad Clients", "Fetch Meta Metrics")
    connect(connections, "Fetch Meta Metrics", "Append Google Sheets Row")
    connect(connections, "Append Google Sheets Row", "Generate Report Narrative")
    connect(connections, "Generate Report Narrative", "Build Slides Deck And Log")
    connect(connections, "Build Slides Deck And Log", "Send Monthly Report Email")
    return workflow("Yankura | 04 Monthly Performance Report", nodes, connections)


def build_workflow_05() -> dict:
    wf = "05_Competitor_Analysis"
    nodes = [
        webhook_node(wf, "Competitor Webhook", "yankura/competitor-analysis", (80, 140)),
        webhook_node(wf, "Slack Slash Webhook", "yankura/slash/competitor-analysis", (80, 340)),
        code_node(
            wf,
            "Normalize Competitor Input",
            (340, 240),
            f"""
            {COMMON_RUNTIME}
            const payloads = [];
            for (const item of items) {{
              const raw = item.json || {{}};
              const body = raw.body && typeof raw.body === 'object' ? raw.body : raw;
              const accountText = coalesce(body.competitors, body.accounts, body.text, body.rakipler);
              const competitors = toText(accountText)
                .split(/[\\s,\\n]+/)
                .map((entry) => entry.trim().replace(/^@/, ''))
                .filter(Boolean);
              payloads.push({{
                json: {{
                  requesterName: coalesce(body.name, body.requesterName, 'Yankura Team'),
                  requesterEmail: extractEmail(body.email),
                  clientName: coalesce(body.clientName, body.brand, body.marka, 'Yankura Musterisi'),
                  competitors,
                  notes: coalesce(body.notes, body.context),
                }},
              }});
            }}
            return payloads;
            """,
        ),
        code_node(
            wf,
            "Fetch Public Competitor Posts",
            (620, 240),
            f"""
            {COMMON_RUNTIME}
            const results = [];
            for (const item of items) {{
              const actor = readEnv('COMPETITOR_APIFY_ACTOR');
              const inputField = optionalEnv('COMPETITOR_APIFY_INPUT_FIELD', 'usernames');
              const payload = {{
                [inputField]: item.json.competitors,
                resultsLimit: 30,
              }};
              const data = await httpJson(
                `https://api.apify.com/v2/acts/${{actor}}/run-sync-get-dataset-items?token=${{readEnv('APIFY_TOKEN')}}`,
                {{
                  method: 'POST',
                  headers: {{ 'Content-Type': 'application/json' }},
                  body: JSON.stringify(payload),
                }},
              );
              const itemsList = Array.isArray(data) ? data : data.items || [];
              const posts = [];
              for (const profile of itemsList) {{
                const latestPosts = profile.latestPosts || profile.posts || profile.latestIgtvVideos || [];
                for (const post of latestPosts) {{
                  const timestamp = new Date(coalesce(post.timestamp, post.latestComments?.[0]?.timestamp, post.inputUrlCreatedAt, Date.now()));
                  const daysDiff = (Date.now() - timestamp.getTime()) / 86400000;
                  if (daysDiff > 30) {{
                    continue;
                  }}
                  const likes = parseNumber(coalesce(post.likesCount, post.likes, post.likeCount));
                  const comments = parseNumber(coalesce(post.commentsCount, post.comments, post.commentCount));
                  const views = parseNumber(coalesce(post.videoViewCount, post.videoPlayCount, post.videoViewCounts));
                  posts.push({{
                    account: profile.username || profile.userName || profile.ownerUsername,
                    caption: toText(post.caption || post.alt || ''),
                    type: coalesce(post.type, post.displayResourceType, post.productType, 'post'),
                    likes,
                    comments,
                    views,
                    engagement: likes + comments + views,
                    hashtags: (toText(post.caption || '').match(/#\\w+/g) || []).slice(0, 20),
                    takenAt: timestamp.toISOString(),
                  }});
                }}
              }}
              posts.sort((left, right) => right.engagement - left.engagement);
              results.push({{
                json: {{
                  ...item.json,
                  topPosts: posts.slice(0, 10),
                }},
              }});
            }}
            return results;
            """,
        ),
        code_node(
            wf,
            "Generate Analysis Summary",
            (900, 240),
            f"""
            {COMMON_RUNTIME}
            const output = [];
            for (const item of items) {{
              const analysis = await callAiJson({{
                systemPrompt: 'Sen Yankura icin rakip analizi yapan stratejistsin. Turkce, aksiyon odakli ve yalnizca JSON dondur.',
                userPrompt: `
                Bu rakip Instagram verilerini analiz et:
                ${{JSON.stringify(item.json.topPosts, null, 2)}}

                JSON don:
                {{
                  "formats": ["..."],
                  "winningTopics": ["..."],
                  "hashtagStrategy": ["..."],
                  "timingAndFrequency": ["..."],
                  "opportunityAreas": ["...", "...", "..."],
                  "summary": "..."
                }}
                `,
              }});

              output.push({{
                json: {{
                  ...item.json,
                  analysis,
                }},
              }});
            }}
            return output;
            """,
        ),
        code_node(
            wf,
            "Save Analysis To Notion",
            (1180, 240),
            f"""
            {COMMON_RUNTIME}
            const results = [];
            for (const item of items) {{
              const page = await notionCreatePage(readEnv('NOTION_COMPETITOR_ANALYSIS_DATABASE_ID'), {{
                Name: notionTitle(`${{item.json.clientName}} | Rakip Analizi`),
                Client: notionRichText(item.json.clientName),
                Competitors: notionRichText(item.json.competitors.join(', ')),
                Summary: notionRichText(item.json.analysis.summary),
                Formats: notionRichText((item.json.analysis.formats || []).join(' | ')),
                Topics: notionRichText((item.json.analysis.winningTopics || []).join(' | ')),
                Opportunities: notionRichText((item.json.analysis.opportunityAreas || []).join(' | ')),
                'Created At': notionDate(new Date().toISOString()),
              }});
              results.push({{
                json: {{
                  ...item.json,
                  notionAnalysisUrl: page.url,
                }},
              }});
            }}
            return results;
            """,
        ),
        code_node(
            wf,
            "Notify Slack Teams",
            (1460, 240),
            f"""
            {COMMON_RUNTIME}
            for (const item of items) {{
              await postSlack(
                `Rakip analizi hazir\\nMusteri: ${{item.json.clientName}}\\nRakipler: ${{item.json.competitors.join(', ')}}\\nOzet: ${{item.json.analysis.summary}}\\nNotion: ${{item.json.notionAnalysisUrl}}`,
                'SLACK_WEBHOOK_STRATEGY',
              );
            }}
            return items;
            """,
        ),
    ]

    connections: dict[str, dict] = {}
    connect(connections, "Competitor Webhook", "Normalize Competitor Input")
    connect(connections, "Slack Slash Webhook", "Normalize Competitor Input")
    connect(connections, "Normalize Competitor Input", "Fetch Public Competitor Posts")
    connect(connections, "Fetch Public Competitor Posts", "Generate Analysis Summary")
    connect(connections, "Generate Analysis Summary", "Save Analysis To Notion")
    connect(connections, "Save Analysis To Notion", "Notify Slack Teams")
    return workflow("Yankura | 05 Competitor Analysis", nodes, connections)


def build_workflow_06() -> dict:
    wf = "06_Onboarding"
    nodes = [
        webhook_node(wf, "Proposal Approval Webhook", "yankura/proposal-approval", (80, 120), method="GET"),
        webhook_node(wf, "Onboarding Form Webhook", "yankura/onboarding-form", (80, 360)),
        code_node(
            wf,
            "Normalize Onboarding Event",
            (340, 240),
            f"""
            {COMMON_RUNTIME}
            return items.map((item) => {{
              const raw = item.json || {{}};
              const body = raw.body && typeof raw.body === 'object' ? raw.body : raw;
              const query = raw.query || {{}};
              const isApproval = Boolean(query.approvalToken || body.approvalToken || query.selectedPackage);
              return {{
                json: {{
                  mode: isApproval ? 'approval' : 'onboarding',
                  leadPageId: coalesce(query.leadPageId, body.leadPageId, body.notionLeadPageId),
                  approvalToken: coalesce(query.approvalToken, body.approvalToken),
                  selectedPackage: coalesce(query.selectedPackage, body.selectedPackage),
                  brandName: coalesce(body.brandName, body.company, body.clientName),
                  website: coalesce(body.website, body.site),
                  targetAudience: coalesce(body.targetAudience, body.hedefKitle),
                  brandVoice: coalesce(body.brandVoice, body.markaSesi),
                  avoidTopics: coalesce(body.avoidTopics, body.kacinilanlar),
                  primaryGoal: coalesce(body.primaryGoal, body.hedef),
                  email: extractEmail(body.email),
                }},
              }};
            }});
            """,
        ),
        switch_node(
            wf,
            "Switch Onboarding Mode",
            "={{$json.mode}}",
            ["approval", "onboarding"],
            (620, 240),
            fallback_output=2,
        ),
        code_node(
            wf,
            "Process Approval",
            (900, 120),
            f"""
            {COMMON_RUNTIME}
            for (const item of items) {{
              const page = await notionGetPage(item.json.leadPageId);
              const savedToken = notionPropertyText(page.properties || {{}}, 'Approval Token');
              if (savedToken && savedToken !== item.json.approvalToken) {{
                throw new Error('Approval token dogrulanamadi.');
              }}
              const email = notionPropertyText(page.properties || {{}}, 'Email');
              const company = notionPropertyText(page.properties || {{}}, 'Company') || notionPropertyText(page.properties || {{}}, 'Name');
              await notionUpdatePage(item.json.leadPageId, {{
                'Lead Status': notionStatus('Active'),
                'Selected Package': notionSelect(item.json.selectedPackage || 'Starter'),
              }});
              const onboardingUrl = `${{readEnv('STATIC_SITE_BASE_URL')}}/automation/forms/onboarding-form.html?leadPageId=${{encodeURIComponent(item.json.leadPageId)}}&approvalToken=${{encodeURIComponent(item.json.approvalToken)}}&brandName=${{encodeURIComponent(company)}}&email=${{encodeURIComponent(email)}}`;
              await sendEmail({{
                to: email,
                subject: 'Hos geldiniz! Onboarding formunuz hazir',
                html: `
                  <div style="font-family:Arial,sans-serif;line-height:1.7">
                    <p>Merhaba,</p>
                    <p>Teklif onayiniz sisteme dustu. Simdi proje kurulumuna geciyoruz.</p>
                    <p>Asagidaki onboarding formunu doldurdugunuzda ekip brief, klasorleme ve ilk icerik planini otomatik baslatacak:</p>
                    <p><a href="${{onboardingUrl}}">${{onboardingUrl}}</a></p>
                    <p>Sevgiler,<br>Yankura</p>
                  </div>
                `,
              }});
            }}
            return items;
            """,
        ),
        code_node(
            wf,
            "Complete Onboarding",
            (900, 340),
            f"""
            {COMMON_RUNTIME}
            const results = [];
            for (const item of items) {{
              const leadPage = await notionGetPage(item.json.leadPageId);
              const savedToken = notionPropertyText(leadPage.properties || {{}}, 'Approval Token');
              if (savedToken && savedToken !== item.json.approvalToken) {{
                throw new Error('Onboarding token dogrulanamadi.');
              }}
              const clientName = item.json.brandName || notionPropertyText(leadPage.properties || {{}}, 'Company') || notionPropertyText(leadPage.properties || {{}}, 'Name');
              const email = item.json.email || notionPropertyText(leadPage.properties || {{}}, 'Email');

              const briefPage = await notionCreatePage(readEnv('NOTION_BRIEFS_DATABASE_ID'), {{
                Name: notionTitle(`${{clientName}} | Marka Briefi`),
                Client: notionRichText(clientName),
                Website: notionUrl(item.json.website),
                'Target Audience': notionRichText(item.json.targetAudience),
                'Brand Voice': notionRichText(item.json.brandVoice),
                'Avoid Topics': notionRichText(item.json.avoidTopics),
                'Primary Goal': notionRichText(item.json.primaryGoal),
              }});

              const rootFolder = await googleCreateFolder(clientName, readEnv('GOOGLE_DRIVE_CLIENTS_ROOT_FOLDER_ID'));
              await googleCreateFolder('Creatives', rootFolder.id);
              await googleCreateFolder('Reports', rootFolder.id);
              await googleCreateFolder('Strategy', rootFolder.id);

              await notionUpdatePage(item.json.leadPageId, {{
                'Lead Status': notionStatus('Active'),
                'Drive Folder Url': notionUrl(rootFolder.url),
                'Brief Url': notionUrl(briefPage.url),
                'Target Audience': notionRichText(item.json.targetAudience),
                'Brand Voice': notionRichText(item.json.brandVoice),
                'Avoid Topics': notionRichText(item.json.avoidTopics),
              }});

              await httpJson(`${{readEnv('INTERNAL_WEBHOOK_BASE_URL', 'http://n8n-main:5678')}}/webhook/yankura/content/calendar/generate`, {{
                method: 'POST',
                headers: {{ 'Content-Type': 'application/json' }},
                body: JSON.stringify({{
                  leadPageId: item.json.leadPageId,
                }}),
              }});

              await sendEmail({{
                to: email,
                subject: 'Yankura onboarding tamamlandi',
                html: `
                  <div style="font-family:Arial,sans-serif;line-height:1.7">
                    <p>Merhaba,</p>
                    <p>Onboarding bilgileriniz alindi. Artık proje kurulumunuz tamamlandi ve ekip ilk icerik takvimini olusturuyor.</p>
                    <p><strong>Klasor:</strong> <a href="${{rootFolder.url}}">${{rootFolder.url}}</a></p>
                    <p><strong>Brief sayfasi:</strong> <a href="${{briefPage.url}}">${{briefPage.url}}</a></p>
                    <p>Check-list:</p>
                    <ul>
                      <li>Marka varliklari klasore yuklenecek</li>
                      <li>Ilk icerik takvimi onaya cikacak</li>
                      <li>Reklam hesap erisimleri ekip tarafindan kontrol edilecek</li>
                    </ul>
                  </div>
                `,
              }});

              await postSlack(
                `Yeni musteri basladi!\\nMusteri: ${{clientName}}\\nDrive: ${{rootFolder.url}}\\nBrief: ${{briefPage.url}}`,
                'SLACK_WEBHOOK_OPERATIONS',
              );

              results.push({{
                json: {{
                  ...item.json,
                  briefUrl: briefPage.url,
                  driveFolderUrl: rootFolder.url,
                }},
              }});
            }}
            return results;
            """,
        ),
        code_node(
            wf,
            "Unhandled Event",
            (900, 560),
            """
            return items;
            """,
        ),
    ]

    connections: dict[str, dict] = {}
    connect(connections, "Proposal Approval Webhook", "Normalize Onboarding Event")
    connect(connections, "Onboarding Form Webhook", "Normalize Onboarding Event")
    connect(connections, "Normalize Onboarding Event", "Switch Onboarding Mode")
    connect(connections, "Switch Onboarding Mode", "Process Approval", output_index=0)
    connect(connections, "Switch Onboarding Mode", "Complete Onboarding", output_index=1)
    connect(connections, "Switch Onboarding Mode", "Unhandled Event", output_index=2)
    return workflow("Yankura | 06 Onboarding Automation", nodes, connections)


def build_workflow_07() -> dict:
    wf = "07_Error_Handler"
    nodes = [
        error_trigger_node(wf, "Error Trigger", (80, 220)),
        code_node(
            wf,
            "Notify Ops",
            (340, 220),
            f"""
            {COMMON_RUNTIME}
            for (const item of items) {{
              const execution = item.json.execution || {{}};
              const workflowName = execution.workflowData?.name || execution.workflowData?.id || 'Bilinmeyen workflow';
              const lastNode = execution.lastNodeExecuted || 'Bilinmeyen node';
              const errorMessage = execution.error?.message || item.json.error?.message || 'Mesaj yok';
              await postSlack(
                `n8n hata alarmi\\nWorkflow: ${{workflowName}}\\nNode: ${{lastNode}}\\nHata: ${{errorMessage}}`,
                'SLACK_WEBHOOK_ALERTS',
              );
            }}
            return items;
            """,
        ),
    ]
    connections: dict[str, dict] = {}
    connect(connections, "Error Trigger", "Notify Ops")
    return workflow("Yankura | 07 Error Handler", nodes, connections)


def main() -> None:
    WORKFLOWS_DIR.mkdir(parents=True, exist_ok=True)
    workflows = {
        "01-lead-capture-and-classification.json": build_workflow_01(),
        "02-proposal-generation.json": build_workflow_02(),
        "03-content-calendar.json": build_workflow_03(),
        "04-monthly-report.json": build_workflow_04(),
        "05-competitor-analysis.json": build_workflow_05(),
        "06-onboarding.json": build_workflow_06(),
        "07-error-handler.json": build_workflow_07(),
    }
    for filename, data in workflows.items():
      (WORKFLOWS_DIR / filename).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
      print(f"generated {filename}")


if __name__ == "__main__":
    main()
