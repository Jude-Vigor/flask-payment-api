# app.py
from flask import Flask, app
from config import Config
from extensions import db
from routes.payment import payment_bp
from services.product_seed import seed_products

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    
    db.init_app(app)

    with app.app_context():
        db.create_all()
        seed_products()

    app.register_blueprint(payment_bp, url_prefix="/api")

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
