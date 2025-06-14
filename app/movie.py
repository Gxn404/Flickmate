from flask import Blueprint, render_template, url_for, session, redirect, flash
from .db import init_db
from bson import ObjectId
import logging

bp = Blueprint("movie", __name__)

users = init_db("users")
movies = init_db("movies")
users_wishlist = init_db("users_watchlist")
reviews = init_db("users_reviews")




@bp.route('/details/<name>')
def details(name):

    try:
        movie = movies.find_one({"_id": ObjectId(name)})
    except:
        movie = None


    if not movie:
        flash("Movie not found.", "danger")
        return redirect(url_for('home.home'))  # Or any fallback route you want

    return render_template('app/details.html', name=name, movie=movie)


@bp.route('/search')
def search():
    user_id = session.get('user_id')
    user = users.find_one({'_id': ObjectId(user_id)})
    if not user_id:
        flash("You gotta log in first!", "warning")
        return redirect(url_for('login.login'))  # temporarily redirect home

    if not user_id:
        login = False
    else:
        login = True
    return render_template('app/search.html',title='Discover',login = login, user=user)

@bp.route('/genres')
def genre():
    user_id = session.get('user_id')
    user = users.find_one({'_id': ObjectId(user_id)})
    if not user_id:
        flash("You gotta log in first!", "warning")
        return redirect(url_for('login.login'))  # temporarily redirect home

    if not user_id:
        login = False
    else:
        login = True
    return render_template('app/genre.html',title='Genre',login = login, user=user)




