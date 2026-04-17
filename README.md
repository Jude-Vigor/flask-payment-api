# Commerce fufilment API

Production-style Flask backend for digital product checkout, payment verification, and post-payment fulfillment processing.

## Overview

This repository implements a backend for digital service delivery. The application exposes a public checkout flow, persists products, orders, and payment records in a relational database, verifies Paystack payments via callback and webhook, and processes post-payment fulfillment in a separate worker loop with retry scheduling. In production, it is configured to run against PostgreSQL.

The project is currently deployed on Railway. The repository also includes process examples for a traditional VPS deployment using Gunicorn, systemd, and Nginx.

## Key Features

- Database-backed product catalog, orders, payment transactions, fulfillment jobs, and fulfillment attempts
- Server-side pricing: checkout accepts `product_id`; price is resolved from the database
- Paystack transaction initialization and verification
- Paystack webhook signature validation using HMAC SHA-512
- Decoupled fulfillment pipeline: payment confirmation queues work for a background worker
- Retry-based fulfillment processing with escalating retry delays
- Order tracking endpoint for customer-side status lookup
- Admin session login, dashboard view, payment filtering, and manual reconciliation actions
- Flask CLI commands for migrations, product seeding, worker execution, and launch-readiness checks

## Tech Stack

- Python
- Flask
- Flask-SQLAlchemy
- Flask-Migrate / Alembic
- SQLAlchemy
- Requests
- PostgreSQL in production via `DATABASE_URL`, with SQLite fallback for local development
- Gunicorn for WSGI serving
- Railway for current deployment

## Architecture / Request Flow

Core components:

- Public storefront served from Flask templates
- API routes for checkout, verification, order tracking, and admin operations
- Relational database for business state
- Paystack for payment collection and confirmation
- Dedicated fulfillment integration behind a service layer
- Background fulfillment worker driven by CLI

Request flow:

```text
Customer selects product
-> POST /api/checkout
-> backend creates Order and PaymentTransaction
-> backend initializes Paystack transaction
-> customer completes payment on Paystack
-> Paystack callback or webhook confirms payment
-> backend marks order PAID and queues FulfillmentJob
-> worker polls due jobs
-> worker submits order for fulfillment
-> backend records attempt history and updates fulfillment state
-> admin can manually mark delivered/failed when operational review is needed
```

Status model:

- Payment: `PENDING` -> `PAID` or `FAILED`
- Fulfillment: `PENDING` -> `QUEUED` -> `PROCESSING` / `RETRYING` -> `DELIVERED` or `FAILED`

## API Endpoints

### Public

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/` | Customer storefront |
| `GET` | `/api/products` | List active products |
| `POST` | `/api/checkout` | Create order and initialize Paystack checkout |
| `GET` | `/api/payments/verify` | Verify Paystack payment and queue fulfillment |
| `POST` | `/api/webhooks/paystack` | Receive Paystack webhook events |
| `GET` | `/api/orders/<reference>` | Retrieve order status by reference |

### Admin

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` / `POST` | `/api/login` | Admin login |
| `GET` | `/api/logout` | Clear admin session |
| `GET` | `/api/dashboard` | Admin dashboard |
| `GET` | `/api/payments` | Filterable payment/order listing |
| `GET` | `/api/fulfillment-jobs` | Queue visibility and retry status |
| `POST` | `/api/orders/<reference>/mark-delivered` | Manual delivery reconciliation |
| `POST` | `/api/orders/<reference>/mark-failed` | Manual failure reconciliation |

## Running Locally

### 1. Install dependencies

Windows:

```powershell
py -m venv venv
venv\Scripts\python -m pip install -r requirements.txt
```

macOS / Linux:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Create `.env`

Use the environment template below and set real credentials for Paystack and the fulfillment provider.

### 3. Apply database migrations

Windows:

```powershell
venv\Scripts\flask --app app db upgrade
```

macOS / Linux:

```bash
flask --app app db upgrade
```

### 4. Seed products

Windows:

```powershell
venv\Scripts\flask --app app seed-products
```

macOS / Linux:

```bash
flask --app app seed-products
```

### 5. Run the web app

Windows:

```powershell
venv\Scripts\flask --app app run --debug
```

macOS / Linux:

```bash
flask --app app run --debug
```

### 6. Run the fulfillment worker

Single-pass processing:

Windows:

```powershell
venv\Scripts\flask --app app process-fulfillment --limit 10
```

macOS / Linux:

```bash
flask --app app process-fulfillment --limit 10
```

Continuous worker loop:

```bash
flask --app app run-fulfillment-worker --interval-seconds 10 --limit 10
```

### 7. Run a launch check

```bash
flask --app app launch-check
```

Local default URL:

```text
http://127.0.0.1:5000/
```

## Environment Variables

The application loads configuration from `.env` via `python-dotenv`.

```env
SECRET_KEY=replace-with-a-long-random-secret
DATABASE_URL=sqlite:///app.db
PAYSTACK_SECRET_KEY=sk_test_or_live_key
BASE_URL=http://127.0.0.1:5000
INSTANTDATAGH_API_KEY=your_vendor_api_key
INSTANTDATAGH_BASE_URL=your_vendor_base_url
AUTO_CREATE_TABLES=true
```

Notes:

- `SECRET_KEY`, `PAYSTACK_SECRET_KEY`, and `BASE_URL` are required at startup.
- `DATABASE_URL` defaults to SQLite locally; PostgreSQL URLs are normalized to the SQLAlchemy `psycopg` driver.
- `INSTANTDATAGH_BASE_URL` defaults to `https://instantdatagh.com/api.php`.
- `AUTO_CREATE_TABLES=true` enables `db.create_all()` on startup; migrations are still included and should be preferred for managed environments.

## Deployment

Current runtime target:

- Railway

Operational shape:

- Web process serving `app:app`
- Separate worker process running `flask --app app run-fulfillment-worker --interval-seconds 10 --limit 10`

The repository also includes example deployment assets for a VPS-style setup:

- `deploy/systemd/payments-api-web.service`
- `deploy/systemd/payments-api-worker.service`
- `deploy/nginx/payments-api.conf.example`

Typical production commands:

```bash
gunicorn --bind 127.0.0.1:8000 app:app
flask --app app run-fulfillment-worker --interval-seconds 10 --limit 10
```

Paystack should be configured with:

- Callback URL: `/api/payments/verify`
- Webhook URL: `/api/webhooks/paystack`

## Reliability / Security Notes

- Prices are resolved server-side from the `Product` table rather than trusting client-submitted amounts.
- Payment confirmation is handled through both user return verification and Paystack webhooks.
- Webhook requests are validated with the `x-paystack-signature` header.
- Fulfillment is intentionally separated from checkout to avoid blocking user requests on vendor latency.
- Fulfillment attempts are persisted, with retry delays of 1, 2, 5, 10, and 15 minutes and a default max of 5 attempts.
- One fulfillment job is maintained per order, which helps constrain duplicate queue creation when payment confirmation is received more than once.
- Admin access is session-based and password verification uses Werkzeug hash checking.
- Manual admin reconciliation exists for final operational control when vendor-side completion needs review.

## Future Improvements

- Replace the polling CLI worker with a managed queue system and dedicated job broker
- Add automated admin bootstrapping and stronger authentication controls
- Add request rate limiting, CSRF protection for admin actions, and structured audit logging
- Expand test coverage around webhook replay scenarios, retry behavior, and external API failure handling
- Add vendor-side delivery confirmation callbacks if supported by the fulfillment provider
