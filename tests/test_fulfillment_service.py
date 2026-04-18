from datetime import datetime, timedelta

from extensions import db
from models import FulfillmentJob, Order
from services.fulfillment import process_fulfillment_job, process_pending_fulfillment_jobs


def test_process_fulfillment_job_marks_success(app, paid_order, monkeypatch):
    with app.app_context():
        job = FulfillmentJob(order_id=paid_order.id, status="PENDING")
        db.session.add(job)
        db.session.commit()

    def fake_create_vendor_order(network, phone_number, data_amount):
        return {}, {"status": "success", "data": {"order_id": "VENDOR-123", "status": "accepted"}}

    monkeypatch.setattr("services.fulfillment.create_vendor_order", fake_create_vendor_order)

    with app.app_context():
        job = FulfillmentJob.query.filter_by(order_id=paid_order.id).first()
        result = process_fulfillment_job(job)
        order = db.session.get(Order, paid_order.id)

        assert result is True
        assert job.status == "COMPLETED"
        assert order.fulfillment_status == "PROCESSING"
        assert order.vendor_order_id == "VENDOR-123"
        assert len(order.fulfillment_attempts) == 1
        assert order.fulfillment_attempts[0].status == "ACCEPTED"


def test_process_fulfillment_job_retries_after_exception(app, paid_order, monkeypatch):
    with app.app_context():
        job = FulfillmentJob(order_id=paid_order.id, status="PENDING")
        db.session.add(job)
        db.session.commit()

    def fake_create_vendor_order(network, phone_number, data_amount):
        raise RuntimeError("Vendor timeout")

    monkeypatch.setattr("services.fulfillment.create_vendor_order", fake_create_vendor_order)

    with app.app_context():
        job = FulfillmentJob.query.filter_by(order_id=paid_order.id).first()
        result = process_fulfillment_job(job)
        order = db.session.get(Order, paid_order.id)

        assert result is False
        assert job.status == "RETRYING"
        assert job.attempts == 1
        assert job.last_error == "Vendor timeout"
        assert job.next_retry_at > datetime.utcnow()
        assert order.fulfillment_status == "RETRYING"
        assert len(order.fulfillment_attempts) == 1
        assert order.fulfillment_attempts[0].status == "FAILED"


def test_process_pending_fulfillment_jobs_returns_summary(app, paid_order, monkeypatch):
    with app.app_context():
        job = FulfillmentJob(
            order_id=paid_order.id,
            status="PENDING",
            next_retry_at=datetime.utcnow() - timedelta(minutes=1),
        )
        db.session.add(job)
        db.session.commit()

    def fake_create_vendor_order(network, phone_number, data_amount):
        return {}, {"status": "success", "data": {"order_id": "VENDOR-456", "status": "accepted"}}

    monkeypatch.setattr("services.fulfillment.create_vendor_order", fake_create_vendor_order)

    with app.app_context():
        results = process_pending_fulfillment_jobs(limit=10)

        assert results == {"processed": 1, "successful": 1, "failed": 0}
