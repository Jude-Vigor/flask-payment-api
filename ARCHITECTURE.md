# Architecture Overview

This document gives a high-level view of how the system works.

It is meant to answer:
- what talks to what
- where data flows
- which part is responsible for which job

## 1. Big Picture

This application has 5 main parts:

1. Customer frontend
2. Flask application
3. Database
4. Paystack
5. InstantDataGH

Simple view:

```text
Customer
   |
   v
Frontend UI (Flask templates)
   |
   v
Flask Routes
   |
   +--> Database
   |
   +--> Paystack
   |
   +--> Fulfillment Worker
           |
           v
      InstantDataGH
   |
   v
Admin Dashboard
```

## 2. Main System Components

### Customer Frontend

File:
- [templates/index.html](/C:/Users/DELL/Desktop/payments_api/templates/index.html)

Purpose:
- shows available products
- lets the customer choose a bundle
- collects email and recipient phone number
- starts checkout
- allows order tracking

This frontend talks to the backend through:
- `GET /api/products`
- `POST /api/checkout`
- `GET /api/orders/<reference>`

### Flask Application

Main files:
- [app.py](/C:/Users/DELL/Desktop/payments_api/app.py)
- [routes/payment.py](/C:/Users/DELL/Desktop/payments_api/routes/payment.py)

Purpose:
- serves HTML pages
- receives API requests
- validates input
- creates orders
- verifies payments
- queues fulfillment
- exposes admin functionality

This is the center of the system.

### Database

Main file:
- [models.py](/C:/Users/DELL/Desktop/payments_api/models.py)

Purpose:
- stores products
- stores orders
- stores payment records
- stores fulfillment jobs
- stores fulfillment attempts
- stores admin users

The database is the source of truth for the app.

### Paystack

Main file:
- [services/paystack.py](/C:/Users/DELL/Desktop/payments_api/services/paystack.py)

Purpose:
- initializes customer payment
- verifies payment
- sends webhook events back to the app

Paystack is only responsible for the money side.

### InstantDataGH

Main file:
- [services/instantdatagh.py](/C:/Users/DELL/Desktop/payments_api/services/instantdatagh.py)

Purpose:
- receives the data order request
- processes the data delivery request

InstantDataGH is responsible for the service-delivery side.

## 3. Request Flow Diagram

### Checkout and Payment Flow

```text
Customer opens homepage
   |
   v
Frontend requests product list
   |
   v
GET /api/products
   |
   v
Database returns active products
   |
   v
Customer selects product and submits checkout form
   |
   v
POST /api/checkout
   |
   +--> validate request
   +--> load product from DB
   +--> create Order
   +--> call Paystack initialize
   |
   v
Return Paystack authorization URL
   |
   v
Customer pays on Paystack
```

### Payment Confirmation Flow

```text
Paystack confirms payment
   |
   +--> GET /api/payments/verify
   |        or
   +--> POST /api/webhooks/paystack
   |
   v
Backend verifies payment
   |
   +--> mark order as PAID
   +--> create/update payment transaction
   +--> enqueue fulfillment job
   |
   v
Order is now ready for fulfillment
```

### Fulfillment Flow

```text
Fulfillment worker runs
   |
   v
Find paid orders with pending or retrying jobs
   |
   v
Call InstantDataGH
   |
   +--> if success:
   |       mark job completed
   |       set order fulfillment to PROCESSING
   |
   +--> if failure:
           record attempt
           retry later or mark FAILED
```

### Manual Admin Verification Flow

```text
Admin checks vendor dashboard
   |
   v
Admin opens internal dashboard
   |
   v
Admin clicks:
   - Mark Delivered
   - Mark Failed
   |
   v
Backend updates order fulfillment status
```

## 4. Responsibility Breakdown

### What the frontend is responsible for

- displaying products
- collecting customer inputs
- redirecting customer to Paystack
- showing order tracking results

### What the backend is responsible for

- validating inputs
- creating and managing orders
- deciding price from the database
- verifying payment
- queuing fulfillment
- handling admin actions

### What the database is responsible for

- storing persistent business data
- tracking order history
- storing job state and retry state

### What Paystack is responsible for

- collecting money
- confirming payment status

### What InstantDataGH is responsible for

- receiving the vendor order request
- handling the actual data delivery request

## 5. Important Design Decisions

### 1. Backend decides the price

The frontend only sends `product_id`.

The backend loads the product and uses its `retail_price`.

Why this is good:
- customer cannot tamper with price in the browser

### 2. Payment and fulfillment are separated

The system does not deliver immediately inside checkout.

Instead:
- payment succeeds first
- then fulfillment is queued

Why this is good:
- safer
- easier to retry
- easier to debug

### 3. Fulfillment uses a queue model

The app creates a `FulfillmentJob`.

The worker processes it later.

Why this is good:
- vendor delays do not block user requests
- retry logic becomes easier

### 4. Admin can manually reconcile vendor delivery

Since vendor confirmation is not fully automated yet, admin can mark final state manually.

Why this is useful:
- keeps operations practical
- gives control when vendor data is only available in dashboard form
- gives the admin a clear queue view through the internal dashboard

## 6. Current Status Lifecycle

### Payment lifecycle

```text
PENDING -> PAID
PENDING -> FAILED
```

### Fulfillment lifecycle

```text
PENDING -> QUEUED -> PROCESSING
PENDING -> QUEUED -> RETRYING -> PROCESSING
PENDING -> QUEUED -> FAILED
PROCESSING -> DELIVERED
PROCESSING -> FAILED
```

## 7. Files by Responsibility

### App bootstrap
- [app.py](/C:/Users/DELL/Desktop/payments_api/app.py)
- [config.py](/C:/Users/DELL/Desktop/payments_api/config.py)
- [extensions.py](/C:/Users/DELL/Desktop/payments_api/extensions.py)

### Core business flow
- [routes/payment.py](/C:/Users/DELL/Desktop/payments_api/routes/payment.py)
- [models.py](/C:/Users/DELL/Desktop/payments_api/models.py)

### Payment integration
- [services/paystack.py](/C:/Users/DELL/Desktop/payments_api/services/paystack.py)
- [utils/security.py](/C:/Users/DELL/Desktop/payments_api/utils/security.py)

### Fulfillment integration
- [services/instantdatagh.py](/C:/Users/DELL/Desktop/payments_api/services/instantdatagh.py)
- [services/fulfillment.py](/C:/Users/DELL/Desktop/payments_api/services/fulfillment.py)

### Admin/auth
- [utils/decorators.py](/C:/Users/DELL/Desktop/payments_api/utils/decorators.py)
- [templates/dashboard.html](/C:/Users/DELL/Desktop/payments_api/templates/dashboard.html)
- [templates/login.html](/C:/Users/DELL/Desktop/payments_api/templates/login.html)

### Customer UI
- [templates/index.html](/C:/Users/DELL/Desktop/payments_api/templates/index.html)

## 8. Practical Takeaway

If you want the shortest architecture summary, it is this:

```text
Customer chooses product
-> Flask creates order
-> Paystack handles payment
-> Flask verifies payment
-> Fulfillment job is queued
-> Worker sends order to InstantDataGH
-> Admin can manually confirm final delivery
```

That is the core architecture of the project.
