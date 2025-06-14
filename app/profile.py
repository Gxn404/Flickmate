from flask import Blueprint, render_template, url_for, session, redirect, flash, request
from .db import init_db
from bson import ObjectId

bp = Blueprint("profile", __name__)

users = init_db("users")
movies = init_db("movies")
users_wishlist = init_db("users_watchlist")
reviews = init_db("users_reviews")

@bp.route('/profile')
def profile():
    user_id = session.get('user_id')

    if not user_id:
        flash("You gotta log in first!", "warning")
        return redirect(url_for('home.home'))

    login = True  # Already checked

    try:
        # 🔸 Find the user
        user = users.find_one({'_id': ObjectId(user_id)})
        if not user:
            flash("User not found!", "danger")
            return redirect(url_for('home.home'))

        # 🔸 Get all movie_ids from users_watchlist for this user
        watchlist_entries = list(users_wishlist.find({'user_id': ObjectId(user_id)}))
        movie_ids = [entry['movie_id'] for entry in watchlist_entries]

        # 🔸 Fetch full movie details
        user_watchlist_movies = list(movies.find({'_id': {'$in': movie_ids}}))

        # 🔸 Get recent reviews
        recent_reviews = list(reviews.find({'user_id': ObjectId(user_id)}).sort('created_at', -1).limit(5))

        # 🔸 Render profile with real movie data in watchlist
        return render_template(
            'app/profile.html',
            title='Profile',
            user=user,
            watchlist=user_watchlist_movies,
            recent_reviews=recent_reviews,
            login=login
        )

    except Exception as e:
        flash(f"Oops, something went wrong: {e}", "danger")
        return redirect(url_for('home.home'))


@bp.route("/profile/edit", methods=["POST"])
def edit_profile():
    if "user_id" not in session:
        return redirect(url_for("login"))
    user_id = ObjectId(session["user_id"])
    users.update_one(
        {"_id": user_id},
        {"$set": {
            "username": request.form["username"],
            "location": request.form["location"],
            "avatar_url": request.form["avatar_url"]
        }}
    )
    flash("Profile updated successfully!", "success")
    return redirect(url_for("profile.profile"))

