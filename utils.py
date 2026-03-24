from flask import session, redirect, url_for, request
from functools import wraps

def login_required(f):
    """Декоратор перевірки авторизації користувача."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            # Зберігаємо поточний URL для перенаправлення після логіну
            return redirect(url_for('auth.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function
