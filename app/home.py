from flask import Blueprint, render_template, url_for, session, redirect, flash, logging
from .db import init_db
from bson import ObjectId

bp = Blueprint("home", __name__)

users = init_db("users")
movies = init_db("movies")
users_wishlist = init_db("users_watchlist")
reviews = init_db("users_reviews")

@bp.route('/')
def home():
    user_id = session.get('user_id')
    user = users.find_one({'_id': ObjectId(user_id)})
    if not user_id:
        flash("You gotta log in first!", "warning")
        return redirect(url_for('login.login'))

    if not user_id:
        login = False
    else:
        login = True

    style = url_for('static', filename='css/main.css')
    return render_template('app/home.html', title='Home', css_file= style, login = login, user=user)

@bp.route('/<path:anything>')
def fallback(anything):
    return render_template('app/404.html', title='Page Not Found'), 404