from click.testing import CliRunner

from app import create_app
from extensions import db
from models import FulfillmentJob, Order


def login_as_admin(client, admin_user):
    return client.post(
        "/api/login",
        data={"email": admin_user.email, "password": "password123"},
        follow_redirects=False,
    )


def test_home_page_loads(client):
    response = client.get("/")

    assert response.status_code == 200
    assert "Checkout" in response.get_data(as_text=True)


def test_dashboard_redirects_when_not_logged_in(client):
    response = client.get("/api/dashboard", follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/api/login")


def test_login_redirects_to_dashboard_when_credentials_are_valid(client, admin_user):
    response = login_as_admin(client, admin_user)

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/api/dashboard")


def test_login_returns_invalid_credentials_for_bad_password(client, admin_user):
    response = client.post(
        "/api/login",
        data={"email": admin_user.email, "password": "wrong-password"},
    )

    assert response.status_code == 200
    assert response.get_data(as_text=True) == "Invalid credentials"


def test_get_payments_requires_admin_session(client, paid_order):
    response = client.get("/api/payments", follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/api/login")


def test_get_payments_returns_orders_for_logged_in_admin(client, admin_user, paid_order):
    login_as_admin(client, admin_user)

    response = client.get("/api/payments")

    assert response.status_code == 200
    payload = response.get_json()
    assert len(payload) == 1
    assert payload[0]["reference"] == paid_order.reference
    assert payload[0]["status"] == "PAID"


def test_get_fulfillment_jobs_returns_jobs_for_logged_in_admin(client, admin_user, paid_order, app):
    with app.app_context():
        job = FulfillmentJob(order_id=paid_order.id, status="PENDING")
        db.session.add(job)
        db.session.commit()

    login_as_admin(client, admin_user)

    response = client.get("/api/fulfillment-jobs")

    assert response.status_code == 200
    payload = response.get_json()
    assert len(payload) == 1
    assert payload[0]["order"]["reference"] == paid_order.reference
    assert payload[0]["status"] == "PENDING"


def test_logout_clears_session_and_redirects(client, admin_user):
    login_as_admin(client, admin_user)

    response = client.get("/api/logout", follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/api/login")


def test_launch_check_passes_when_config_and_products_are_present(app, product):
    runner = app.test_cli_runner()

    result = runner.invoke(args=["launch-check"])

    assert result.exit_code == 0
    assert "Launch check passed." in result.output


def test_process_fulfillment_command_prints_summary(app, monkeypatch):
    def fake_process_pending_fulfillment_jobs(limit):
        return {"processed": 2, "successful": 1, "failed": 1}

    monkeypatch.setattr("app.process_pending_fulfillment_jobs", fake_process_pending_fulfillment_jobs)
    runner = app.test_cli_runner()

    result = runner.invoke(args=["process-fulfillment", "--limit", "5"])

    assert result.exit_code == 0
    assert "Processed 2 job(s): 1 succeeded, 1 failed." in result.output


def test_seed_products_command_prints_success(app, monkeypatch):
    def fake_seed_products():
        return None

    monkeypatch.setattr("app.seed_products", fake_seed_products)
    runner = app.test_cli_runner()

    result = runner.invoke(args=["seed-products"])

    assert result.exit_code == 0
    assert "Products seeded." in result.output


def test_run_fulfillment_worker_stops_cleanly(app, monkeypatch):
    calls = {"count": 0}

    def fake_process_pending_fulfillment_jobs(limit):
        calls["count"] += 1
        return {"processed": 1, "successful": 1, "failed": 0}

    def stop_worker(_seconds):
        raise KeyboardInterrupt()

    monkeypatch.setattr("app.process_pending_fulfillment_jobs", fake_process_pending_fulfillment_jobs)
    monkeypatch.setattr("app.time.sleep", stop_worker)
    runner = app.test_cli_runner()

    result = runner.invoke(args=["run-fulfillment-worker", "--limit", "3", "--interval-seconds", "1"])

    assert result.exit_code == 0
    assert "Starting fulfillment worker." in result.output
    assert "Processed 1 job(s): 1 succeeded, 0 failed." in result.output
    assert "Fulfillment worker stopped." in result.output
    assert calls["count"] == 1
