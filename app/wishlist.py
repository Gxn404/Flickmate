from flask import Blueprint, render_template, url_for, session, redirect, flash, request, jsonify
from .db import init_db
from bson import ObjectId

bp = Blueprint("wishlist", __name__)

# Database collections
users = init_db("users")
movies = init_db("movies")
users_wishlist = init_db("users_watchlist")
reviews = init_db("users_reviews")

# 🎯 Render Wishlist Page
@bp.route('/wishlist')
def wishlist():
    user_id = session.get('user_id')
    if not user_id:
        flash("You gotta log in first!", "warning")
        return redirect(url_for('login.login'))

    try:
        user_oid = ObjectId(user_id)
    except:
        flash("Invalid user ID!", "danger")
        return redirect(url_for('login.login'))

    user = users.find_one({'_id': user_oid})
    wishlist_entries = list(users_wishlist.find({'user_id': user_oid}))
    movie_ids = [entry['movie_id'] for entry in wishlist_entries]

    wishlist_movies = list(movies.find({'_id': {'$in': movie_ids}})) if movie_ids else []

    return render_template(
        'app/wishlist.html',
        title='Wishlist',
        wishlist=wishlist_movies,
        user=user,
        login=True
    )

# 💖 Toggle Wishlist Entry
@bp.route('/wishlist/toggle/<movie_id>', methods=['POST'])
def toggle_wishlist(movie_id):
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'error': 'Login required'}), 401

    try:
        user_oid = ObjectId(user_id)
        movie_oid = ObjectId(movie_id)
    except:
        return jsonify({'success': False, 'error': 'Invalid ID format'}), 400

    if not movies.find_one({'_id': movie_oid}):
        return jsonify({'success': False, 'error': 'Movie not found'}), 404

    existing = users_wishlist.find_one({
        'user_id': user_oid,
        'movie_id': movie_oid
    })

    if existing:
        users_wishlist.delete_one({'_id': existing['_id']})
        return jsonify({'success': True, 'action': 'removed'})
    else:
        users_wishlist.insert_one({
            'user_id': user_oid,
            'movie_id': movie_oid
        })
        return jsonify({'success': True, 'action': 'added'})

# ✅ Check Wishlist Status (for 1 item only)
@bp.route('/wishlist/status/<movie_id>', methods=['GET'])
def wishlist_status(movie_id):
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'in_wishlist': False}), 200

    try:
        movie_oid = ObjectId(movie_id)
        user_oid = ObjectId(user_id)
    except:
        return jsonify({'in_wishlist': False}), 400

    in_wishlist = users_wishlist.find_one({
        'user_id': user_oid,
        'movie_id': movie_oid
    }) is not None

    return jsonify({'in_wishlist': in_wishlist}), 200
