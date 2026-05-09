# Concurrency Safe Payout Engine

A minimal payout engine for Indian merchants collecting international payments.
Handles balance tracking, payout requests, concurrency, idempotency, and 
background processing.

## Stack

- Backend: Django + DRF + PostgreSQL
- Background jobs: Celery + Redis + django-celery-beat
- Frontend: React + Vite + Tailwind CSS

## Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL (running on port 5432 or 5433)
- Redis (running on port 6379)

## Setup

### 1. Clone and install backend dependencies

```bash
git clone <your-repo-url>
cd playto-payout
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure database

Create a PostgreSQL database named `playto_db`.

Edit `config/settings/local.py` with your DB credentials:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'playto_db',
        'USER': 'postgres',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

### 3. Run migrations

```bash
python manage.py migrate
```

### 4. Seed test data

```bash
# Creates 2 merchants with bank accounts and credit history
python manage.py shell < seed.py
```

This seeds:
- Ravi Designs — ₹1000 + ₹500 credits
- Priya Studio — ₹750 credit

### 5. Register Celery beat task

```bash
python manage.py shell
```
```python
from django_celery_beat.models import PeriodicTask, IntervalSchedule
import json

schedule, _ = IntervalSchedule.objects.get_or_create(
    every=30, period=IntervalSchedule.SECONDS
)
PeriodicTask.objects.get_or_create(
    name='Retry stuck payouts every 30s',
    defaults={
        'interval': schedule,
        'task': 'apps.payouts.tasks.retry_stuck_payouts',
        'args': json.dumps([]),
    }
)
exit()
```

### 6. Setup frontend

```bash
cd frontend
npm install
```

## Running

Open 4 terminals from project root, activate venv in each backend terminal:

| Terminal | Directory | Command |
|---|---|---|
| T1 | `playto-payout/` | `python manage.py runserver` |
| T2 | `playto-payout/` | `celery -A config worker --loglevel=info -P solo` |
| T3 | `playto-payout/` | `celery -A config beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler` |
| T4 | `playto-payout/frontend/` | `npm run dev` |

- Backend API: http://localhost:8000
- Frontend dashboard: http://localhost:5173

## API Reference

### Balance

GET /api/v1/merchants/balance/

### Ledger entries

GET /api/v1/merchants/ledger/

### Create payout

POST /api/v1/payouts/
Headers:
Idempotency-Key: <uuid>
Content-Type: application/json
Body:
{ "amount_paise": 5000, "bank_account_id": 1 }

### Payout history

GET /api/v1/payouts/list/

## Running Tests

```bash
python manage.py test apps.tests
```

Two tests:
- `test_concurrency.py` — two simultaneous 60-rupee requests against 100-rupee balance, exactly one succeeds
- `test_idempotency.py` — same idempotency key twice creates only one payout

## Key Design Decisions

**Balance is never stored.** It is derived from ledger entries on every read
using DB-level aggregation. The invariant `SUM(credits+releases) - SUM(debits+holds) = balance`
is structurally guaranteed.

**Concurrency is handled at the DB layer.** `SELECT FOR UPDATE` on the merchant
row serializes concurrent payout requests. Python-level locking would fail
across multiple workers.

**Payout lifecycle:** `hold → release → debit` (success) or `hold → release` (failure).
Fund release is atomic with state transition inside a single `transaction.atomic()`.

See `EXPLAINER.md` for detailed answers to each technical constraint.
