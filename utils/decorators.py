from functools import wraps
from flask import session, redirect
from models import Admin

def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        admin_id = session.get("admin")

        if not admin_id:
            return redirect("/api/login")

        admin = Admin.query.get(admin_id)

        if not admin:
            session.clear()
            return redirect("/api/login")

        return f(*args, **kwargs)

    return wrapper