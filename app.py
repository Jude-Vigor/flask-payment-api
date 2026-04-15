import click
import time
from flask import Flask, render_template

from config import Config
from extensions import db, migrate
from models import FulfillmentJob, Product
from routes.payment import payment_bp
from services.fulfillment import process_pending_fulfillment_jobs
from services.product_seed import seed_products


def register_commands(app):
    @app.cli.command("seed-products")
    def seed_products_command():
        with app.app_context():
            seed_products()
        click.echo("Products seeded.")

    @app.cli.command("process-fulfillment")
    @click.option("--limit", default=10, show_default=True, type=int)
    def process_fulfillment_command(limit):
        with app.app_context():
            results = process_pending_fulfillment_jobs(limit=limit)
        click.echo(
            f"Processed {results['processed']} job(s): "
            f"{results['successful']} succeeded, {results['failed']} failed."
        )

    @app.cli.command("run-fulfillment-worker")
    @click.option("--limit", default=10, show_default=True, type=int)
    @click.option("--interval-seconds", default=10, show_default=True, type=int)
    def run_fulfillment_worker_command(limit, interval_seconds):
        click.echo(
            "Starting fulfillment worker. "
            f"Polling every {interval_seconds} second(s) with batch size {limit}."
        )

        try:
            while True:
                with app.app_context():
                    results = process_pending_fulfillment_jobs(limit=limit)

                if results["processed"] > 0:
                    click.echo(
                        f"Processed {results['processed']} job(s): "
                        f"{results['successful']} succeeded, {results['failed']} failed."
                    )

                time.sleep(interval_seconds)
        except KeyboardInterrupt:
            click.echo("Fulfillment worker stopped.")

    @app.cli.command("launch-check")
    def launch_check_command():
        required_env = [
            "SECRET_KEY",
            "PAYSTACK_SECRET_KEY",
            "BASE_URL",
            "INSTANTDATAGH_API_KEY",
            "INSTANTDATAGH_BASE_URL",
        ]
        missing = [key for key in required_env if not app.config.get(key)]

        with app.app_context():
            active_products = Product.query.filter_by(is_active=True).count()
            queued_jobs = (
                FulfillmentJob.query.filter(
                    FulfillmentJob.status.in_(["PENDING", "RETRYING"])
                ).count()
            )

        click.echo("Launch readiness")
        click.echo(f"- BASE_URL: {app.config.get('BASE_URL')}")
        click.echo(f"- Active products: {active_products}")
        click.echo(f"- Pending/retrying fulfillment jobs: {queued_jobs}")

        if missing:
            for key in missing:
                click.echo(f"- Missing env var: {key}", err=True)
            raise click.ClickException("Launch check failed.")

        if active_products == 0:
            raise click.ClickException("Launch check failed: no active products found.")

        click.echo("Launch check passed.")


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)

    with app.app_context():
        if app.config["AUTO_CREATE_TABLES"]:
            db.create_all()
            seed_products()

    app.register_blueprint(payment_bp, url_prefix="/api")

    @app.get("/")
    def home():
        return render_template("index.html")

    register_commands(app)

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
