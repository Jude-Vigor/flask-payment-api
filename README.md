# Payments API

Flask application for selling mobile data bundles with:
- Paystack for payments
- InstantDataGH for bundle fulfillment
- an admin dashboard for monitoring and manual reconciliation

## What This Project Does

The app allows a customer to:
- open a public storefront
- choose a data bundle
- enter email and recipient phone number
- pay through Paystack
- track order status later

The app allows an admin to:
- log in
- view orders
- see payment and fulfillment status
- manually mark orders as delivered or failed

## Main Flow

1. Customer selects a bundle.
2. The app creates an order.
3. Paystack handles payment.
4. Payment is verified by callback or webhook.
5. A fulfillment job is queued.
6. A worker sends the request to InstantDataGH.
7. Admin can manually confirm final delivery if needed.

## Project Docs

- [TECHNICAL_DOC.md](/C:/Users/DELL/Desktop/payments_api/TECHNICAL_DOC.md)
Junior-friendly technical explanation of the project.

- [ARCHITECTURE.md](/C:/Users/DELL/Desktop/payments_api/ARCHITECTURE.md)
High-level architecture and flow overview.

## Setup

Install dependencies:

```powershell
venv\Scripts\python -m pip install -r requirements.txt
```

Add your environment variables in `.env`.

Important values:
- `SECRET_KEY`
- `DATABASE_URL` or default SQLite
- `PAYSTACK_SECRET_KEY`
- `BASE_URL`
- `INSTANTDATAGH_API_KEY`
- `INSTANTDATAGH_BASE_URL`
- `AUTO_CREATE_TABLES`

## Database Commands

Apply migrations:

```powershell
venv\Scripts\flask --app app db upgrade
```

Create a new migration after changing models:

```powershell
venv\Scripts\flask --app app db migrate -m "Describe schema change"
venv\Scripts\flask --app app db upgrade
```

Seed starter products:

```powershell
venv\Scripts\flask --app app seed-products
```

## Run the App

Start the development server:

```powershell
venv\Scripts\flask --app app run --debug
```

Open in browser:

```text
http://127.0.0.1:5000/
```

## Fulfillment Worker

Paid orders are not sent to the vendor inline during checkout verification.
They are queued first.

Process queued fulfillment jobs:

```powershell
venv\Scripts\flask --app app process-fulfillment --limit 10
```

For local testing, run that command in another terminal while the app is running.

## Key Routes

### Public

- `GET /`
- `GET /api/products`
- `POST /api/checkout`
- `GET /api/payments/verify`
- `GET /api/orders/<reference>`

### Admin

- `GET /api/login`
- `GET /api/dashboard`
- `GET /api/payments`
- `GET /api/fulfillment-jobs`
- `POST /api/orders/<reference>/mark-delivered`
- `POST /api/orders/<reference>/mark-failed`

## Quick Dev Routine

Use this order:

1. Install dependencies if needed
2. Apply migrations
3. Start the app
4. Run the fulfillment worker if testing paid orders

Commands:

```powershell
venv\Scripts\flask --app app db upgrade
venv\Scripts\flask --app app run --debug
```

In another terminal:

```powershell
venv\Scripts\flask --app app process-fulfillment --limit 10
```

## Notes

- Prices come from the backend database, not the browser.
- Payment and fulfillment are intentionally separated.
- Final delivery confirmation is currently supported through admin manual verification.
