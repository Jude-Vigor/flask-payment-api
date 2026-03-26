# extensions.py
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

try:
    from flask_migrate import Migrate
except ImportError:  # pragma: no cover
    class Migrate:  # type: ignore[override]
        def init_app(self, *args, **kwargs):
            return None


migrate = Migrate()
