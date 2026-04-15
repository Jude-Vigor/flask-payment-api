# Deployment Guide

## Production Shape

This project is designed to run as two separate processes on one VPS:

- a web process for the Flask app
- a worker process for queued fulfillment jobs

The customer flow stays the same:

1. checkout creates an order
2. Paystack handles payment
3. payment verification or webhook marks the order paid
4. fulfillment is queued
5. the worker submits the order to InstantDataGH

## Required Environment Variables

Set these on the server before starting either process:

- `SECRET_KEY`
- `DATABASE_URL` or the default SQLite path
- `PAYSTACK_SECRET_KEY`
- `BASE_URL`
- `INSTANTDATAGH_API_KEY`
- `INSTANTDATAGH_BASE_URL`
- `AUTO_CREATE_TABLES`

`BASE_URL` must be the public HTTPS domain used by customers and configured in Paystack.
Keep the `.env` file in the project root so the Flask app and Gunicorn process can load it through `python-dotenv`.

## First-Time Server Setup

Install production dependencies:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements-prod.txt
```

Run database setup:

```bash
flask --app app db upgrade
flask --app app seed-products
flask --app app launch-check
```

## Start Commands

Run the web process with Gunicorn:

```bash
gunicorn --bind 127.0.0.1:8000 app:app
```

Run the worker process in a second service:

```bash
flask --app app run-fulfillment-worker --interval-seconds 10 --limit 10
```

## Paystack Configuration

Update Paystack to use the live domain:

- callback URL path: `/api/payments/verify`
- webhook URL path: `/api/webhooks/paystack`

The webhook is what keeps payment confirmation reliable even if the customer closes the browser after paying.

## Live Validation Checklist

1. Open the homepage and confirm products load.
2. Submit checkout with a valid Ghana-format number such as `0XXXXXXXXX`.
3. Complete one real Paystack payment.
4. Confirm the order becomes `PAID`.
5. Confirm a fulfillment job is created or updated.
6. Confirm the worker logs that it processed the job.
7. Confirm the order shows a stored vendor response and a `vendor_order_id` if InstantDataGH returns one.
8. Confirm the order appears in `/api/dashboard` and the queue status appears in `/api/fulfillment-jobs`.

## Included Examples

- `deploy/systemd/payments-api-web.service`
- `deploy/systemd/payments-api-worker.service`
- `deploy/nginx/payments-api.conf.example`

Adjust usernames, paths, and domain names before using them on the server.
