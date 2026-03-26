# Payments API

Flask backend for selling data bundles with Paystack checkout and InstantDataGH fulfillment.

## Setup

Create and activate your virtual environment, then install dependencies:

```powershell
venv\Scripts\python -m pip install -r requirements.txt
```

Set your environment values in `.env`.

## Database Workflow

This project now uses Flask-Migrate and Alembic.

Apply migrations:

```powershell
venv\Scripts\flask --app app db upgrade
```

Create a new migration after model changes:

```powershell
venv\Scripts\flask --app app db migrate -m "Describe schema change"
venv\Scripts\flask --app app db upgrade
```

Seed starter products:

```powershell
venv\Scripts\flask --app app seed-products
```

## Running The App

Start the development server:

```powershell
venv\Scripts\flask --app app run --debug
```

## Fulfillment Worker

Paid orders are queued for fulfillment instead of being sent inline during webhook handling.

Process queued jobs manually:

```powershell
venv\Scripts\flask --app app process-fulfillment --limit 10
```

For local development, run that command periodically in another terminal while testing payments.

## Key Endpoints

- `GET /api/products`
- `POST /api/checkout`
- `GET /api/payments/verify`
- `POST /api/webhooks/paystack`
- `GET /api/orders/<reference>`


<!--  -->
A very practical routine
Use this order:

1. Activate or use your venv
2. Apply migrations
3. Start the server
4. Run the fulfillment worker separately when testing paid orders
Example:

venv\Scripts\flask --app app db upgrade
venv\Scripts\flask --app app run --debug
In another terminal:

venv\Scripts\flask --app app process-fulfillment --limit 10