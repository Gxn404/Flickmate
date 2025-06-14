import json
from flask import Blueprint, Response, request, jsonify
from bson import ObjectId
from pymongo import DESCENDING, ASCENDING
from .db import init_db
from .utils import JSONEncoder, order_movie_fields, parse_cast_string, safe_cast_int

bp = Blueprint("movies", __name__, url_prefix= "/api")
movies = init_db("movies")


# 🎬 ROUTES

@bp.route('/search', methods=['GET'])
def get_movies():
    try:
        # Accept both 'title' and 'query' for frontend flexibility
        title = request.args.get('title') or request.args.get('query')
        genre = request.args.get('genres')
        year_from = safe_cast_int(request.args.get('year_from'))
        year_to = safe_cast_int(request.args.get('year_to'))
        imdb_min = request.args.get('imdbRating_min')
        imdb_max = request.args.get('imdbRating_max')
        director = request.args.get('director')
        actor = request.args.get('cast')
        sort_by = request.args.get('sort_by', 'popularity')
        order = request.args.get('order', 'asc')
        limit = safe_cast_int(request.args.get('limit'), 50)
        skip = safe_cast_int(request.args.get('skip'), 0)

        query = {}

        if title:
            query['title'] = {'$regex': title, '$options': 'i'}
        
         # Genres (accepts comma-separated list)
        if genre:
            genres = [g.strip() for g in genre.split(',') if g.strip()]
            if genres:
                query['$and'] = [
                    {'genres': {'$elemMatch': {'$regex': f'^{g}$', '$options': 'i'}}}
                    for g in genres
            ]

        if year_from or year_to:
            year_query = {}
            if year_from: year_query['$gte'] = year_from
            if year_to: year_query['$lte'] = year_to
            query['release_year'] = year_query

        if imdb_min or imdb_max:
            imdb_query = {}
            if imdb_min: imdb_query['$gte'] = float(imdb_min)
            if imdb_max: imdb_query['$lte'] = float(imdb_max)
            query['rating'] = imdb_query

        if director:
            query['director'] = {'$regex': director, '$options': 'i'}

        if actor:
            actors = [a.strip() for a in actor.split(',')]
            query['$or'] = [{'cast.name': {'$regex': a, '$options': 'i'}} for a in actors]

        # Sorting logic
        sort_fields = {
            'title': 'title',
            'year': 'release_year',
            'imdbrating': 'rating',
            'popularity': 'popularity',
            'date_added': 'date_added'
        }
        sort_field = sort_fields.get(sort_by.lower(), 'popularity')
        sort_order = ASCENDING if order.lower() == 'asc' else DESCENDING

        total_count = movies.count_documents(query)

        cursor = movies.find(query).sort(sort_field, sort_order).skip(skip).limit(limit)
        movie_list = [order_movie_fields(movie) for movie in cursor]

        return Response(json.dumps({
            'count': len(movie_list),
            'total': total_count,
            'data': movie_list,
            'skip': skip,
            'limit': limit
        }, cls=JSONEncoder, indent=2), mimetype='application/json')

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('movies/<movie_id>', methods=['GET'])
def get_movie(movie_id):
    try:
        movie = movies.find_one({'_id': ObjectId(movie_id)})
        if not movie:
            return Response(json.dumps({'error': 'Movie not found'}, cls=JSONEncoder), status=404, mimetype='application/json')

        return Response(json.dumps(order_movie_fields(movie), cls=JSONEncoder, indent=2), mimetype='application/json')
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('movies', methods=['POST'])
def add_movie():
    try:
        data = request.get_json()
        if not data or not data.get('title'):
            return jsonify({'error': 'Title is required'}), 400

        if isinstance(data.get('cast'), str):
            data['cast'] = parse_cast_string(data['cast'])

        result = movies.insert_one(data)
        return jsonify({'id': str(result.inserted_id), 'message': 'Movie added successfully'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('movies/<movie_id>', methods=['PUT'])
def update_movie(movie_id):
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid request data'}), 400

        if '_id' in data:
            data.pop('_id')

        if isinstance(data.get('cast'), str):
            data['cast'] = parse_cast_string(data['cast'])

        result = movies.update_one({'_id': ObjectId(movie_id)}, {'$set': data})
        if result.matched_count == 0:
            return jsonify({'error': 'Movie not found'}), 404

        return jsonify({'message': 'Movie updated successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('movies/<movie_id>', methods=['DELETE'])
def delete_movie(movie_id):
    try:
        result = movies.delete_one({'_id': ObjectId(movie_id)})
        if result.deleted_count == 0:
            return jsonify({'error': 'Movie not found'}), 404

        return jsonify({'message': 'Movie deleted successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('movies/trending', methods=['GET'])
def trending_movies():
    try:
        limit = safe_cast_int(request.args.get('limit'), 50)
        skip = safe_cast_int(request.args.get('skip'), 0)
        query = {'is_trending': True}
        total_count = movies.count_documents(query)
        cursor = movies.find(query).sort('popularity', DESCENDING).skip(skip).limit(limit)
        return Response(json.dumps({
            'count': total_count,
            'data': [order_movie_fields(movie) for movie in cursor],
            'skip': skip,
            'limit': limit
        }, cls=JSONEncoder, indent=2), mimetype='application/json')
    except Exception as e:
        return jsonify({'error': str(e)}), 500



@bp.route('movies/latest', methods=['GET'])
def latest_movies():
    try:
        limit = safe_cast_int(request.args.get('limit'), 50)
        skip = safe_cast_int(request.args.get('skip'), 0)
        query = {}
        total_count = movies.count_documents(query)
        cursor = movies.find(query).sort('released', DESCENDING).skip(skip).limit(limit)
        return Response(json.dumps({
            'count': total_count,
            'data': [order_movie_fields(movie) for movie in cursor],
            'skip': skip,
            'limit': limit
        }, cls=JSONEncoder, indent=2), mimetype='application/json')
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('movies/top_rated', methods=['GET'])
def top_rated_movies():
    try:
        limit = safe_cast_int(request.args.get('limit'), 50)
        skip = safe_cast_int(request.args.get('skip'), 0)
        query = {'is_top_rated': True}
        total_count = movies.count_documents(query)
        cursor = movies.find(query).sort('popularity', DESCENDING).skip(skip).limit(limit)
        return Response(json.dumps({
            'count': total_count,
            'data': [order_movie_fields(movie) for movie in cursor],
            'skip': skip,
            'limit': limit
        }, cls=JSONEncoder, indent=2), mimetype='application/json')
    except Exception as e:
        return jsonify({'error': str(e)}), 500
