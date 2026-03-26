import json
from datetime import datetime, timedelta

from flask import current_app

from extensions import db
from models import FulfillmentAttempt, FulfillmentJob, Order
from services.instantdatagh import create_order as create_vendor_order

VALID_NETWORKS = {"MTN", "AirtelTigo", "Telecel"}


def _serialize(value):
    return json.dumps(value) if value is not None else None


def _retry_delay_minutes(attempt_number):
    delays = [1, 2, 5, 10, 15]
    index = min(max(attempt_number - 1, 0), len(delays) - 1)
    return delays[index]


def enqueue_fulfillment(order):
    job = order.fulfillment_job
    if job is None:
        job = FulfillmentJob(order=order)
        db.session.add(job)

    if job.status == "COMPLETED":
        return job

    job.status = "PENDING"
    job.locked_at = None
    job.last_error = None
    job.next_retry_at = datetime.utcnow()
    order.fulfillment_status = "QUEUED"
    return job


def _record_attempt(order, request_payload):
    attempt = FulfillmentAttempt(
        order=order,
        status="PENDING",
        request_payload=_serialize(request_payload),
    )
    db.session.add(attempt)
    db.session.flush()
    return attempt


def process_fulfillment_job(job):
    order = job.order
    if order is None:
        job.status = "FAILED"
        job.last_error = "Missing order for fulfillment job."
        return False

    if order.product.network not in VALID_NETWORKS:
        job.status = "FAILED"
        job.last_error = "Unsupported network configured for product."
        order.fulfillment_status = "FAILED"
        return False

    request_payload = {
        "network": order.product.network,
        "phone_number": order.phone_number,
        "data_amount": order.product.data_amount,
    }

    attempt = _record_attempt(order, request_payload)
    job.status = "PROCESSING"
    job.locked_at = datetime.utcnow()
    job.attempts += 1
    db.session.commit()

    try:
        _, response_payload = create_vendor_order(
            network=order.product.network,
            phone_number=order.phone_number,
            data_amount=order.product.data_amount,
        )
    except Exception as exc:
        attempt.status = "FAILED"
        attempt.error_message = str(exc)
        _mark_retry(job, order, str(exc), None)
        db.session.commit()
        current_app.logger.exception("Fulfillment request failed for order %s", order.reference)
        return False

    attempt.response_payload = _serialize(response_payload)
    job.last_response = _serialize(response_payload)

    if response_payload.get("status") == "success":
        vendor_data = response_payload.get("data") or {}
        attempt.status = "ACCEPTED"
        job.status = "COMPLETED"
        job.locked_at = None
        job.last_error = None
        order.fulfillment_status = "PROCESSING"
        order.vendor_order_id = vendor_data.get("order_id")
        order.vendor_status = vendor_data.get("status")
        order.vendor_response = _serialize(response_payload)
        order.fulfilled_at = datetime.utcnow()
        db.session.commit()
        return True

    attempt.status = "FAILED"
    attempt.error_message = response_payload.get("message", "Vendor fulfillment failed.")
    _mark_retry(job, order, attempt.error_message, response_payload)
    db.session.commit()
    return False


def _mark_retry(job, order, error_message, response_payload):
    job.locked_at = None
    job.last_error = error_message
    job.last_response = _serialize(response_payload)
    order.vendor_response = _serialize(response_payload) if response_payload is not None else order.vendor_response

    if job.attempts >= job.max_attempts:
        job.status = "FAILED"
        order.fulfillment_status = "FAILED"
        return

    job.status = "RETRYING"
    order.fulfillment_status = "RETRYING"
    delay_minutes = _retry_delay_minutes(job.attempts)
    job.next_retry_at = datetime.utcnow() + timedelta(minutes=delay_minutes)


def process_pending_fulfillment_jobs(limit=10):
    now = datetime.utcnow()
    jobs = (
        FulfillmentJob.query.join(Order)
        .filter(Order.payment_status == "PAID")
        .filter(FulfillmentJob.status.in_(["PENDING", "RETRYING"]))
        .filter(FulfillmentJob.next_retry_at <= now)
        .order_by(FulfillmentJob.next_retry_at.asc(), FulfillmentJob.id.asc())
        .limit(limit)
        .all()
    )

    results = {"processed": 0, "successful": 0, "failed": 0}

    for job in jobs:
        results["processed"] += 1
        if process_fulfillment_job(job):
            results["successful"] += 1
        else:
            results["failed"] += 1

    return results
