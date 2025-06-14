from flask import Blueprint, session, jsonify
from bson import ObjectId
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np
from datetime import datetime
from .db import init_db

bp = Blueprint("recommendation", __name__, url_prefix="/api/movies")

# 🔌 MongoDB Collections
users = init_db("users")
movies = init_db("movies")
users_wishlist = init_db("users_watchlist")


# 🎯 Serializer
def serialize_movie(movie):
    return {
        "_id": str(movie.get("_id")),
        "title": movie.get("title"),
        "genres": movie.get("genres", []),
        "rating": movie.get("rating", 0),
        "features": movie.get("features", []),
        "poster_url": movie.get("poster_url", ""),
        "year": movie.get("year", ""),
        "description": movie.get("description", "")
    }

def serialize_movies(movie_list):
    return [serialize_movie(m) for m in movie_list]


# 🧠 Wishlist-Based Recommender with Recency Boost
def recommend_movies(base_movies, all_movies, top_n=6):
    base_vectors = [np.array(m.get("features", [])) for m in base_movies if m.get("features")]
    if not base_vectors:
        return all_movies[:top_n]  # fallback if no features

    base_matrix = np.stack(base_vectors)
    current_year = datetime.now().year

    recommendations = []
    for movie in all_movies:
        target_vec = np.array(movie.get("features", []))
        if target_vec.size == 0:
            continue

        # 💡 Mean similarity
        similarities = cosine_similarity([target_vec], base_matrix)[0]
        avg_sim = np.mean(similarities)

        # 🔥 Recency Boost (boost newer movies slightly)
        year = movie.get("year")
        try:
            year = int(year)
            recency_boost = 1 + max(0, (year - 2015)) * 0.02
        except:
            recency_boost = 1.0

        final_score = avg_sim * recency_boost
        recommendations.append((movie, final_score))

    # 🥇 Sorted by score descending
    recommendations.sort(key=lambda x: x[1], reverse=True)
    return [m for m, _ in recommendations[:top_n]]


# 📍 Route 1: Personalized Recommendations
@bp.route("/recommendations")
def recommend_for_user():
    user_id = session.get("user_id")
    all_movies = list(movies.find({}))

    if not user_id:
        return jsonify({"data": serialize_movies(all_movies[:10])})

    try:
        user_oid = ObjectId(user_id)
        wishlist_entries = list(users_wishlist.find({"user_id": user_oid}))
        wishlist_ids = [w["movie_id"] for w in wishlist_entries]
        wishlist_movies = list(movies.find({"_id": {"$in": wishlist_ids}}))

        # ❌ Filter out wishlist movies from candidates
        candidates = [m for m in all_movies if m["_id"] not in wishlist_ids]

        if wishlist_movies:
            recommended = recommend_movies(wishlist_movies, candidates, top_n=10)
        else:
            recommended = candidates[:10]

        return jsonify({"data": serialize_movies(recommended)})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# 📍 Route 2: Similar Movies (by plot + genre)
@bp.route("/recommendations/<movie_id>")
def recommend_similar_movies(movie_id):
    try:
        all_docs = list(movies.find({}))
        base_movie = next((m for m in all_docs if str(m["_id"]) == movie_id), None)

        if not base_movie:
            return jsonify({"error": "Movie not found"}), 404

        def get_features(movie):
            genres = " ".join(movie.get("genres", []))
            desc = movie.get("description", "")
            return f"{genres} {genres} {desc}"

        feature_texts = [get_features(m) for m in all_docs]
        vectorizer = TfidfVectorizer(stop_words="english")
        tfidf_matrix = vectorizer.fit_transform(feature_texts)

        base_index = all_docs.index(base_movie)
        scores = cosine_similarity(tfidf_matrix[base_index], tfidf_matrix).flatten()

        top_indices = scores.argsort()[::-1][1:11]
        similar = [serialize_movie(all_docs[i]) for i in top_indices]

        return jsonify({"related": similar})

    except Exception as e:
        return jsonify({"error": str(e)}), 500
