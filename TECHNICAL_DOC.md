# Technical Documentation

This document explains the project in a simple way so a junior developer can understand how the app works, where the logic lives, and how the pieces connect.

## 1. Project Summary

This project is a Flask-based web application for selling mobile data bundles in Ghana.

It allows a customer to:
- view available data bundles
- choose a bundle
- enter email and phone number
- pay through Paystack
- have the order queued for delivery through InstantDataGH
- track the order later using the order reference

It also allows an admin to:
- log in
- view all orders on a dashboard
- manually mark an order as delivered or failed after checking the vendor dashboard

## 2. Main Business Flow

The system works in this order:

1. The customer selects a product from the public page.
2. The app creates an order and starts a Paystack payment.
3. Paystack confirms the payment.
4. The app queues the order for fulfillment.
5. A fulfillment worker sends the order to InstantDataGH.
6. The admin can manually confirm final delivery status if needed.

If you want a flow-only view, read:
- [ARCHITECTURE.md](/C:/Users/DELL/Desktop/payments_api/ARCHITECTURE.md)

## 3. Project Structure

### Core Files

- [app.py](/C:/Users/DELL/Desktop/payments_api/app.py)
Starts the Flask application, loads config, registers routes, and adds custom CLI commands.

- [config.py](/C:/Users/DELL/Desktop/payments_api/config.py)
Stores environment-based settings like database URL, Paystack keys, and vendor configuration.

- [extensions.py](/C:/Users/DELL/Desktop/payments_api/extensions.py)
Creates shared Flask extensions:
`db` for SQLAlchemy and `migrate` for Flask-Migrate.

### Data Layer

- [models.py](/C:/Users/DELL/Desktop/payments_api/models.py)
Defines the database tables used by the project.

### Routes

- [routes/payment.py](/C:/Users/DELL/Desktop/payments_api/routes/payment.py)
Contains the API routes, admin routes, and checkout/payment flow.

### Services

- [services/paystack.py](/C:/Users/DELL/Desktop/payments_api/services/paystack.py)
Handles Paystack transaction initialization and verification.

- [services/instantdatagh.py](/C:/Users/DELL/Desktop/payments_api/services/instantdatagh.py)
Handles sending data bundle purchase requests to InstantDataGH.

- [services/fulfillment.py](/C:/Users/DELL/Desktop/payments_api/services/fulfillment.py)
Handles fulfillment queueing, retries, and vendor submission.

- [services/product_seed.py](/C:/Users/DELL/Desktop/payments_api/services/product_seed.py)
Seeds default products into the database.

### Utilities

- [utils/security.py](/C:/Users/DELL/Desktop/payments_api/utils/security.py)
Verifies Paystack webhook signatures.

- [utils/decorators.py](/C:/Users/DELL/Desktop/payments_api/utils/decorators.py)
Contains the `admin_required` decorator for protecting admin routes.

### Templates

- [templates/index.html](/C:/Users/DELL/Desktop/payments_api/templates/index.html)
Public customer-facing storefront.

- [templates/dashboard.html](/C:/Users/DELL/Desktop/payments_api/templates/dashboard.html)
Admin dashboard.

- [templates/login.html](/C:/Users/DELL/Desktop/payments_api/templates/login.html)
Admin login page.

## 4. Database Models

### Product

Represents a data bundle a customer can buy.

Important fields:
- `name`
- `network`
- `data_amount`
- `retail_price`
- `is_active`

Example:
- `MTN 5GB`
- `24.00`

### Order

This is the main business record.

It stores:
- order reference
- customer email
- recipient phone number
- amount
- payment status
- fulfillment status
- vendor order ID

This is the most important table when tracking customer activity.

### PaymentTransaction

Stores payment activity related to an order.

Used mainly for:
- Paystack transaction reference
- payment response data
- payment status tracking

### FulfillmentJob

Represents a queued delivery task.

This is what the worker processes after payment has been confirmed.

### FulfillmentAttempt

Stores each attempt to send an order to InstantDataGH.

Useful for:
- debugging
- retry tracking
- vendor failure inspection

### Admin

Stores admin login accounts.

## 5. Statuses

There are two separate status groups in the app.

### Payment Status

This tells us what happened to the money.

Common values:
- `PENDING`
- `PAID`
- `FAILED`

### Fulfillment Status

This tells us what happened to the delivery.

Common values:
- `PENDING`
- `QUEUED`
- `PROCESSING`
- `RETRYING`
- `DELIVERED`
- `FAILED`

### Important Note

Payment success and delivery success are not the same thing.

Example:
- an order can be `PAID`
- but fulfillment can still be `FAILED`

## 6. Request Flow

### Checkout Flow

The customer selects a product and submits:

```json
{
  "email": "buyer@example.com",
  "phone_number": "0501234567",
  "product_id": 1
}
```

The backend then:
1. validates the request
2. loads the selected product from the database
3. creates an `Order`
4. initializes Paystack payment
5. returns a Paystack authorization URL

Important rule:
The frontend does not control price.
The backend reads the amount from the product in the database.

### Payment Confirmation Flow

Payment can be confirmed in two ways:

1. `GET /api/payments/verify`
2. `POST /api/webhooks/paystack`

After successful verification:
- the order is marked `PAID`
- a fulfillment job is queued

### Fulfillment Flow

The worker processes queued fulfillment jobs.

The worker:
1. selects due jobs for paid orders
2. calls InstantDataGH
3. records a fulfillment attempt
4. updates order status
5. retries failed attempts with delay

Retry delays are:
- 1 minute
- 2 minutes
- 5 minutes
- 10 minutes
- 15 minutes

## 7. API Endpoints

### Public Endpoints

- `GET /`
Shows the customer-facing storefront.

- `GET /api/products`
Returns active products.

- `POST /api/checkout`
Creates an order and starts Paystack payment.

- `GET /api/payments/verify`
Verifies payment and queues fulfillment.

- `POST /api/webhooks/paystack`
Receives Paystack webhook events.

- `GET /api/orders/<reference>`
Returns one order for tracking.

### Admin Endpoints

- `GET /api/login`
Shows admin login page.

- `POST /api/login`
Authenticates the admin.

- `GET /api/dashboard`
Shows the admin dashboard.

- `GET /api/payments`
Returns order data for the dashboard.

- `POST /api/orders/<reference>/mark-delivered`
Admin manually marks an order as delivered.

- `POST /api/orders/<reference>/mark-failed`
Admin manually marks an order as failed.

## 8. Frontend Pages

### Public Page

[templates/index.html](/C:/Users/DELL/Desktop/payments_api/templates/index.html)

This page:
- loads products from `/api/products`
- allows the customer to select a bundle
- sends checkout requests to `/api/checkout`
- allows order tracking using `/api/orders/<reference>`

### Admin Dashboard

[templates/dashboard.html](/C:/Users/DELL/Desktop/payments_api/templates/dashboard.html)

This page:
- shows revenue
- lists orders
- shows payment status
- shows fulfillment status
- gives manual admin actions

### Login Page

[templates/login.html](/C:/Users/DELL/Desktop/payments_api/templates/login.html)

Simple admin login form.

## 9. Environment Variables

The app depends on values from `.env`.

Important ones:

- `SECRET_KEY`
Used by Flask sessions.

- `DATABASE_URL`
Database connection string.

- `PAYSTACK_SECRET_KEY`
Used for Paystack API requests.

- `BASE_URL`
Used when generating the Paystack callback URL.

- `INSTANTDATAGH_API_KEY`
Used for vendor API authentication.

- `INSTANTDATAGH_BASE_URL`
Vendor base URL.

- `AUTO_CREATE_TABLES`
Controls whether tables are auto-created in local development.

## 10. Running the Project

Apply database migrations:

```powershell
venv\Scripts\flask --app app db upgrade
```

Seed starter products:

```powershell
venv\Scripts\flask --app app seed-products
```

Run the app:

```powershell
venv\Scripts\flask --app app run --debug
```

Run the fulfillment worker:

```powershell
venv\Scripts\flask --app app process-fulfillment --limit 10
```

## 11. Development Mental Model

The app can be understood in 4 layers:

### 1. Presentation Layer
This is what the user sees.

Examples:
- storefront
- admin dashboard
- login page

### 2. Route Layer
This receives HTTP requests and returns responses.

Example:
- [routes/payment.py](/C:/Users/DELL/Desktop/payments_api/routes/payment.py)

### 3. Service Layer
This contains business logic and external integrations.

Examples:
- Paystack service
- InstantDataGH service
- fulfillment service

### 4. Data Layer
This contains database models and relationships.

Example:
- [models.py](/C:/Users/DELL/Desktop/payments_api/models.py)

## 12. Common Developer Tasks

### Add a new product

There are two simple ways:
- add it manually in the database
- add it to [product_seed.py](/C:/Users/DELL/Desktop/payments_api/services/product_seed.py) if it is a default starter product

### Change a bundle price

Update the `retail_price` in the `Product` record.

Important:
Do not let the frontend choose the price.
The backend should remain the source of truth.

### Change checkout validation

Edit:
- [routes/payment.py](/C:/Users/DELL/Desktop/payments_api/routes/payment.py)

Look for:
- `_validate_checkout_payload`

### Change Paystack logic

Edit:
- [services/paystack.py](/C:/Users/DELL/Desktop/payments_api/services/paystack.py)

### Change vendor delivery logic

Edit:
- [services/instantdatagh.py](/C:/Users/DELL/Desktop/payments_api/services/instantdatagh.py)
- [services/fulfillment.py](/C:/Users/DELL/Desktop/payments_api/services/fulfillment.py)

### Change the public frontend

Edit:
- [templates/index.html](/C:/Users/DELL/Desktop/payments_api/templates/index.html)

### Change the admin dashboard

Edit:
- [templates/dashboard.html](/C:/Users/DELL/Desktop/payments_api/templates/dashboard.html)

### Add a new database column

Steps:
1. Update [models.py](/C:/Users/DELL/Desktop/payments_api/models.py)
2. Generate a migration
3. Apply the migration

Commands:

```powershell
venv\Scripts\flask --app app db migrate -m "Describe schema change"
venv\Scripts\flask --app app db upgrade
```

## 13. Troubleshooting

### The app does not start

Check:
- virtual environment is active
- dependencies are installed
- `.env` exists
- required environment variables are present

### Products are not showing on the homepage

Check:
- database has products
- `Product.is_active` is `True`
- `/api/products` returns data

If needed, seed products:

```powershell
venv\Scripts\flask --app app seed-products
```

### Payment is successful but delivery does not happen

Check:
- order has `payment_status = PAID`
- fulfillment job exists
- worker was run

Run:

```powershell
venv\Scripts\flask --app app process-fulfillment --limit 10
```

### Webhook is failing

Check:
- `PAYSTACK_SECRET_KEY` is correct
- request signature matches what [utils/security.py](/C:/Users/DELL/Desktop/payments_api/utils/security.py) expects
- your public `BASE_URL` is correct

### Admin dashboard redirects to login

Check:
- admin session exists
- admin record still exists in database

### Migration command fails

Check:
- Flask-Migrate is installed
- database is reachable
- migration files are not broken

Use:

```powershell
venv\Scripts\flask --app app db heads
venv\Scripts\flask --app app db current
```

## 14. Glossary

### Product
A bundle the customer can buy.

### Order
A customer purchase record.

### Payment Transaction
A payment-provider record tied to an order.

### Fulfillment
The process of sending the purchased data to the customer.

### Fulfillment Job
A queued task waiting to be processed by the worker.

### Fulfillment Attempt
One try to submit the order to the vendor.

### Webhook
A server-to-server callback sent automatically by another service.

### Migration
A tracked database schema change.

### Vendor
In this project, the external data provider: InstantDataGH.

## 15. Good Engineering Decisions Already Present

These are strong parts of the codebase:

- product pricing comes from the backend, not the browser
- payment and fulfillment are separated
- webhook signatures are verified
- fulfillment uses retries
- admin routes are protected
- the codebase is split into sensible folders
- database migrations are used

## 16. Current Limitations

These are areas to improve later:

- final vendor delivery confirmation is still partly manual
- admin authentication is basic
- product seeding does not sync updates to existing rows
- worker processing is manual unless automated externally

## 17. Practical Summary

This application is a small data resale platform.

Main idea:
- products are stored in the database
- customer pays through Paystack
- paid orders are queued for fulfillment
- vendor submission happens through InstantDataGH
- admin can manually verify final delivery status

If you understand:
- `Product`
- `Order`
- `payment_status`
- `fulfillment_status`
- Paystack verification
- fulfillment queue

then you understand the heart of the project.

For a quick start guide, use:
- [README.md](/C:/Users/DELL/Desktop/payments_api/README.md)
