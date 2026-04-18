# Deployment Guide

## Production Shape

The application is currently deployed on Railway with PostgreSQL as the production database.

The live web service starts by applying database migrations and then serves the Flask app with Gunicorn:

```bash
flask --app app db upgrade && gunicorn --bind 0.0.0.0:$PORT app:app
```

The fulfillment workflow is designed to run separately from the checkout request path. For environments where a second process is available, the worker can run independently to process queued fulfillment jobs:

```bash
flask --app app run-fulfillment-worker --interval-seconds 10 --limit 10
```

The customer flow stays the same:

1. checkout creates an order
2. Paystack handles payment
3. payment verification or webhook marks the order paid
4. fulfillment is queued
5. the worker submits the order for downstream fulfillment

## Required Environment Variables

Set these on the deployment target before starting the application:

- `SECRET_KEY`
- `DATABASE_URL` or the default SQLite path
- `PAYSTACK_SECRET_KEY`
- `BASE_URL`
- `INSTANTDATAGH_API_KEY`
- `INSTANTDATAGH_BASE_URL`
- `AUTO_CREATE_TABLES`

`BASE_URL` must be the public HTTPS domain used by customers and configured in Paystack.
When deploying outside Railway, keep the `.env` file in the project root so the Flask app and Gunicorn process can load it through `python-dotenv`.

## Railway Deployment

Railway web start command:

```bash
flask --app app db upgrade && gunicorn --bind 0.0.0.0:$PORT app:app
```

This setup ensures:

- schema migrations run on deploy/startup
- the web application is served by Gunicorn
- production traffic is routed through Railway using the injected `PORT`

If you run a separate worker service, use:

```bash
flask --app app run-fulfillment-worker --interval-seconds 10 --limit 10
```

## VPS / Traditional Server Setup

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
7. Confirm the order shows a stored downstream fulfillment response and a `vendor_order_id` if one is returned.
8. Confirm the order appears in `/api/dashboard` and the queue status appears in `/api/fulfillment-jobs`.

## Included Examples

- `deploy/systemd/payments-api-web.service`
- `deploy/systemd/payments-api-worker.service`
- `deploy/nginx/payments-api.conf.example`

Adjust usernames, paths, and domain names before using them on the server.
