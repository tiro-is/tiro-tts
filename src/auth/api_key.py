# Thanks to Coderwall https://coderwall.com/p/4qickw/require-an-api-key-for-a-route-in-flask-using-only-a-decorator)
# for this small Flask custom auth decorator tutorial.

from functools import wraps
from flask import request, abort, current_app

def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_app.config["AUTH_DISABLED"]:
            return f(*args, **kwargs)

        api_key: str = request.headers.get("authorization")
        if api_key and api_key == "secritkie":
            return f(*args, **kwargs)
        else:
            abort(401)
    return decorated_function
