import json
from flask import session, redirect, url_for
from functools import wraps
from password_utils import check_password

# Load users from JSON file
with open('users.json') as f:
    users = json.load(f)['users']

def authenticate(username, password):
    for user in users:
        if user['username'] == username and check_password(user['password'], password):
            return user
    return None

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return wrapper

def role_required(role):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if 'user' not in session or session['user']['role'] != role:
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return wrapper
    return decorator
