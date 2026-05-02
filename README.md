# TrustLens AI

A Render-ready Flask SaaS MVP that audits public websites for trust, conversion risk, UX clarity, security signals, missing legal pages, pricing clarity, and visitor red flags.

## Local run

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python app.py
```

Open: http://127.0.0.1:5000

Default admin is created from env vars:

```env
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=StrongPassword123!
```

## Render settings

Build Command:

```bash
pip install -r requirements.txt
```

Start Command:

```bash
gunicorn wsgi:app --bind 0.0.0.0:$PORT --log-level info --access-logfile - --error-logfile -
```

Environment variables:

```env
SECRET_KEY=long-random-secret
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=StrongPassword123!
APP_NAME=TrustLens AI
FLASK_ENV=production
ALLOWED_SCAN_TIMEOUT=10
FREE_PLAN_LIMIT=3
```

Recommended: create Render PostgreSQL and add `DATABASE_URL`. The app also works with SQLite for quick MVP tests.

## Health check

`/healthz`

## Notes

The audit engine is defensive and non-invasive. It only fetches the public HTML page and checks visible trust/conversion/security indicators.
