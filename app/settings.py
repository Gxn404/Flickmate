from flask import Blueprint, render_template, url_for, session, redirect, flash
from .db import init_db
from bson import ObjectId

bp = Blueprint("settings", __name__)

users = init_db("users")
movies = init_db("movies")
users_wishlist = init_db("users_watchlist")
reviews = init_db("users_reviews")

@bp.route('/settings')
def setttings():
    user_id = session.get('user_id')
    user = users.find_one({'_id': ObjectId(user_id)})
    if not user_id:
        flash("You gotta log in first!", "warning")
        return redirect(url_for('login.login')) 

    if not user_id:
        login = False
    else:
        login = True
    return render_template('app/settings.html',title='Settings',login = login, user=user)

