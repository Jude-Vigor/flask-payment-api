import click
from flask import Flask

from config import Config
from extensions import db, migrate
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
    register_commands(app)

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
