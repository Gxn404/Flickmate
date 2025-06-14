from flask import (
    Blueprint, render_template, redirect, request,
    session, flash, url_for, abort, json
)
from werkzeug.security import check_password_hash
from pymongo import MongoClient
from bson.objectid import ObjectId
import re 
from datetime import datetime, timedelta
from functools import wraps
from .utils import parse_cast_string

bp = Blueprint("admin", __name__, url_prefix='/admin')
bp.permanent_session_lifetime = timedelta(minutes=30)


# DB Setup
client = mongo.MongoClient("mongodb://mongo:DcqyilLRbvnZqQDrPpmfiVTynTxulnHJ@centerbeam.proxy.rlwy.net:30952/")
db = client["auth"]
users = db["users"]
movies = db["movies"]
reviews = db["reviews"]
logs = db["logs"]
watchlists = db["watchlists"]
feedback = db["feedback"]
admins = db["admin"]
settings = db["settings"]

# ============ Helpers ============

# Assuming you have `admins`, `logs` collection available from MongoDB setup

def is_admin_logged_in():
    return 'admin' in session

def admin_login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_admin_logged_in():
            flash("Access denied. Please login as admin.", "danger")
            return redirect(url_for('admin.admin_login'))
        return f(*args, **kwargs)
    return decorated_function

# ============ AUTH ============

@bp.route('/login', methods=['GET', 'POST'])
def admin_login():
    css_file = url_for("static", filename='css/auth.css')
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        ip_address = get_client_ip()

        if not email or not password:
            flash("Please fill all fields.", "danger")
            return redirect(url_for('admin.admin_login'))

        if not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            flash("Invalid email format.", "danger")
            return redirect(url_for('admin.admin_login'))

        admin = admins.find_one({'email': email})

        if admin and check_password_hash(admin['password_hash'], password):
            session.clear()
            session['admin_id'] = str(admin['_id'])
            session['admin'] = admin['username']
            session.permanent = True
            
            logs.insert_one({
                "user": admin['username'],
                "action": "Admin Login",
                "timestamp": datetime.utcnow(),
                "ip_address": ip_address
            })

            flash("Logged in successfully.", "success")
            return redirect(url_for('admin.admin_dashboard'))
        else:
            logs.insert_one({
                "user": email,
                "action": "Failed Login Attempt",
                "timestamp": datetime.utcnow(),
                "ip_address": ip_address
            })

            flash("Invalid email or password.", "danger")
            return redirect(url_for('admin.admin_login'))

    return render_template('admin/login.html', title='Admin Login', css_file=css_file)

@bp.route('/logout')
@admin_login_required
def admin_logout():
    logs.insert_one({
        "user": session.get('admin', 'Unknown'),
        "action": "Admin Logout",
        "timestamp": datetime.utcnow(),
        "ip_address": get_client_ip()
    })
    session.clear()
    flash("Logged out successfully.", "info")
    return redirect(url_for('admin.admin_login'))

# ============ BEFORE REQUEST ============

@bp.before_request
def restrict_to_admins():
    allowed_endpoints = ['admin.admin_login', 'static']
    if request.endpoint and (request.endpoint.startswith('admin.') or request.endpoint in allowed_endpoints):
        if request.endpoint != 'admin.admin_login' and not is_admin_logged_in():
            flash("Access denied. Please login as admin.", "danger")
            return redirect(url_for('admin.admin_login'))

# ============ ADMIN DASHBOARD ============

@bp.route('/dashboard')
@admin_login_required
def admin_dashboard():
    stats = {
        "monthly_revenue": 12345.67,
        "total_users": users.count_documents({}),
        "total_movies": movies.count_documents({}),
        "total_reviews": reviews.count_documents({}),
        "total_feedback": feedback.count_documents({})
    }

    chart = {
        'labels': ['Jan', 'Feb', 'Mar', 'Apr'],  # example labels
        'data': [10, 20, 30, 40]                 # example data points
    }
    recent_logs = list(logs.find().sort("timestamp", -1).limit(5))
    return render_template('admin/dashboard.html', title="Admin Dashboard", stats=stats, recent_logs=recent_logs, chart=chart)

# ============ USERS ============

@bp.route('/users')
@admin_login_required
def admin_users():
    all_users_cursor = users.find({'joined_date': {'$exists': True}})
    user_list = []

    for user in all_users_cursor:
        joined = user.get('joined_date', 'N/A')

        if isinstance(joined, str):
            try:
                user['joined'] = datetime.strptime(joined, '%Y-%m-%dT%H:%M:%S.%f').strftime('%Y-%m-%d')

            except ValueError:
                user['joined'] = 'Invalid Date Format'
        elif isinstance(joined, datetime):
            user['joined'] = joined.strftime('%Y-%m-%d')
        else:
            user['joined'] = 'N/A'

        user_list.append(user)

    return render_template(
        'admin/users.html',
        users=user_list,
        title="Manage Users",
        datetime=datetime,
        request=request
    )

# ============ MOVIES (MAIN, FEATURED, TRENDING) ============

def extract_release_year(released_str):
    if not released_str:
        return None
    date_formats = [
        "%d %b %Y",     # e.g., 25 Apr 2025
        "%Y-%m-%d",     # e.g., 2025-05-25
        "%d-%m-%Y",     # e.g., 25-04-2025
        "%Y/%m/%d",     # e.g., 2025/05/25
        "%d %B %Y",     # e.g., 18 October 2024 ← NEWLY ADDED
    ]
    for fmt in date_formats:
        try:
            return datetime.strptime(released_str.strip(), fmt).year
        except ValueError:
            continue
    return None


@bp.route('/movies', methods=['GET', 'POST'])
@admin_login_required
def admin_movies():
    tab = request.args.get('tab', 'all')
    search = request.args.get('search', '').strip()

    # Base query for search (title, genre, director)
    query_base = {}
    if search:
        query_base = {
            "$or": [
                {"title": {"$regex": search, "$options": "i"}},
                {"genre": {"$regex": search, "$options": "i"}},
                {"director": {"$regex": search, "$options": "i"}}
            ]
        }

    # Grab movies by tab using separate collections for featured & trending
    movies_all = list(movies.find(query_base))
    movies_featured = list(movies.find({**query_base, "is_popular": True}))
    movies_trending = list(movies.find({**query_base, "is_trending": True}))

    # Bulk POST actions (delete, toggle featured/trending)
    if request.method == 'POST':
        action = request.form.get('action')
        selected_ids = request.form.getlist('selected_movies')
        try:
            object_ids = [ObjectId(_id) for _id in selected_ids]
        except Exception:
            flash("Invalid movie IDs selected.", "danger")
            return redirect(url_for('admin.admin_movies', tab=tab, search=search))

        if action == 'delete':
            res = movies.delete_many({'_id': {'$in': object_ids}})
            flash(f"Deleted {res.deleted_count} movie(s).", "success")

        elif action == 'toggle_featured':
            for oid in object_ids:
                movie = movies.find_one({'_id': oid})
                if movie:
                    new_status = not movie.get('is_popular', False)
                    movies.update_one({'_id': oid}, {'$set': {'is_popular': new_status}})
                    # Sync featured collection
                    if new_status:
                        movies.update_one({'_id': oid}, {'$set': movie}, upsert=True)
                    else:
                        movies.delete_one({'_id': oid})
            flash("Toggled featured status for selected movies.", "success")

        elif action == 'toggle_trending':
            for oid in object_ids:
                movie = movies.find_one({'_id': oid})
                if movie:
                    new_status = not movie.get('is_trending', False)
                    movies.update_one({'_id': oid}, {'$set': {'is_trending': new_status}})
                    # Sync trending collection
                    if new_status:
                        movies.update_one({'_id': oid}, {'$set': movie}, upsert=True)
                    else:
                        movies.delete_one({'_id': oid})
            flash("Toggled trending status for selected movies.", "success")

        else:
            flash("Unknown action.", "warning")

        return redirect(url_for('admin.admin_movies', tab=tab, search=search))

    return render_template(
        'admin/movies.html',
        title="Manage Movies",
        active_tab=tab,
        movies_all=movies_all,
        movies_featured=movies_featured,
        movies_trending=movies_trending,
        search=search,
        request=request
    )

@bp.route('/movie/<movie_id>', methods=['GET', 'POST'])
@admin_login_required
def admin_movie_detail(movie_id):
    movie = movies.find_one({'_id': ObjectId(movie_id)})
    if not movie:
        flash("Movie not found", "danger")
        return redirect(url_for('admin.admin_movies'))

    if request.method == 'POST':
        # Example: update movie details (title, overview, etc.)
        title = request.form.get('title', '').strip()
        overview = request.form.get('overview', '').strip()
        poster_url = request.form.get('poster_url', '').strip()
        release_date = request.form.get('release_date', '').strip()
        rating = request.form.get('rating', '0').strip()

        try:
            rating_val = float(rating)
        except ValueError:
            rating_val = 0.0

        update_data = {
            'title': title,
            'overview': overview,
            'poster_url': poster_url,
            'release_date': release_date,
            'rating': rating_val,
            'is_popular': 'is_popular' in request.form,
            'is_trending': 'is_trending' in request.form
        }

        movies.update_one({'_id': ObjectId(movie_id)}, {'$set': update_data})
        flash("Movie updated successfully.", "success")
        return redirect(url_for('admin.admin_movie_detail', movie_id=movie_id))

    return render_template('admin/movie_detail.html', movie=movie, title=movie.get('title', 'Movie Details'))

@bp.route('/movies/add', methods=['GET', 'POST'])
@admin_login_required
def admin_add_movie():
    if request.method == 'POST':
        form_data = request.form
        json_input = form_data.get('json_data', '').strip()

        # Try to parse JSON input if it's provided
        if json_input:
            try:
                data = json.loads(json_input)
            except json.JSONDecodeError:
                flash("Invalid JSON format", "danger")
                return redirect(url_for('admin.admin_add_movie'))
        else:
            # Construct data dict from form fields
            data = {
                "title": form_data.get('title', '').strip(),
                "description": form_data.get('description', '').strip(),
                "poster_url": form_data.get('poster_url', '').strip(),
                "backdrop_path": form_data.get('backdrop_path', '').strip(),
                "trailer_url": form_data.get('trailer_url', '').strip(),
                "released": form_data.get('released', '').strip(),
                "duration_mins": form_data.get('duration_mins', '').strip(),
                "genres": form_data.get('genres', '').strip(),
                "languages": form_data.get('languages', '').strip(),
                "director": form_data.get('director', '').strip(),
                "writers": form_data.get('writers', '').strip(),
                "cast": form_data.get('cast', '').strip(),
                "production_companies": form_data.get('production_companies', '').strip(),
                "country": form_data.get('country', '').strip(),
                "age_rating": form_data.get('age_rating', '').strip(),
                "rating": form_data.get('rating', '0').strip(),
                "num_reviews": form_data.get('num_reviews', '0').strip(),
                "streaming": form_data.get('streaming', '').strip(),
                "is_popular": 'is_popular' in form_data,
                "is_trending": 'is_trending' in form_data,
                "is_top_rated": 'is_top_rated' in form_data
            }

        # Validation
        title = data.get('title', '').strip()
        if not title:
            flash("Title is required", "danger")
            return redirect(url_for('admin.admin_add_movie'))

        try:
            rating_val = float(data.get('rating', 0))
        except ValueError:
            rating_val = 0.0

        released_str = data.get('released', '').strip()
        released_val = released_str  # Store original string if needed
        release_year_val = extract_release_year(released_str)


        try:
            duration_val = int(data.get('duration_mins')) if data.get('duration_mins') else None
        except ValueError:
            duration_val = None

        try:
            num_reviews_val = int(data.get('num_reviews')) if data.get('num_reviews') else 0
        except ValueError:
            num_reviews_val = 0

        # Fields that could be lists
        genres_list = (
            data['genres'] if isinstance(data.get('genres'), list)
            else [g.strip() for g in data.get('genres', '').split(',') if g.strip()]
        )
        languages_list = (
            data['languages'] if isinstance(data.get('languages'), list)
            else [l.strip() for l in data.get('languages', '').split(',') if l.strip()]
        )
        writers_list = (
            data['writers'] if isinstance(data.get('writers'), list)
            else [w.strip() for w in data.get('writers', '').split(',') if w.strip()]
        )
        production_companies_list = (
            data['production_companies'] if isinstance(data.get('production_companies'), list)
            else [p.strip() for p in data.get('production_companies', '').split(',') if p.strip()]
        )
        streaming_list = (
            data['streaming'] if isinstance(data.get('streaming'), list)
            else [s.strip() for s in data.get('streaming', '').split(',') if s.strip()]
        )

        # Cast processing
        cast_list = []
        if isinstance(data.get('cast'), list):
            cast_list = data.get('cast')
        elif isinstance(data.get('cast'), str):
            entries = [c.strip() for c in data['cast'].split('|') if c.strip()]
            for entry in entries:
                if ':' in entry:
                    name, role = entry.split(':', 1)
                    cast_list.append({"name": name.strip(), "role": role.strip()})

        # Duplication check
        existing_movie = movies.find_one({"title": {"$regex": f"^{title}$", "$options": "i"}})
        if existing_movie:
            flash(f"A movie with the title '{title}' already exists.", "warning")
            return redirect(url_for('admin.admin_movies'))

        new_movie = {
            "title": title,
            "description": data.get("description", ""),
            "poster_url": data.get("poster_url", ""),
            "backdrop_path": data.get("backdrop_path", ""),
            "trailer_url": data.get("trailer_url", ""),
            "release_year": release_year_val,
            "released": released_val,
            "duration_mins": duration_val,
            "genres": genres_list,
            "languages": languages_list,
            "director": data.get("director", ""),
            "writers": writers_list,
            "cast": cast_list,
            "production_companies": production_companies_list,
            "country": data.get("country", ""),
            "age_rating": data.get("age_rating", ""),
            "rating": rating_val,
            "num_reviews": num_reviews_val,
            "streaming": streaming_list,
            "is_popular": data.get("is_popular", False),
            "is_trending": data.get("is_trending", False),
            "is_top_rated": data.get("is_top_rated", False),
            "added_by": session['admin'],
            "date_added": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }

        movies.insert_one(new_movie)
        flash(f"Added new movie '{title}'", 'success')
        return redirect(url_for('admin.admin_add_movie'))

    return render_template('admin/add_movie.html', title="Add Movie")


@bp.route('/movies/edit/<movie_id>', methods=['GET', 'POST'])
@admin_login_required
def edit_movie(movie_id):
    try:
        movie = movies.find_one({"_id": ObjectId(movie_id)})
        if not movie:
            flash("Movie not found!", "danger")
            return redirect(url_for('admin.admin_movies'))

        if request.method == 'POST':
            import json

            def get_str(data, field):
                return str(data.get(field, '') or '').strip()

            def get_list(data, field):
                raw = get_str(data, field)
                return [x.strip() for x in raw.split(',')] if raw else []

            def get_cast_list(data):
                cast_raw = get_str(data, 'cast')
                cast_list = []
                if cast_raw:
                    for entry in cast_raw.split('|'):
                        parts = entry.strip().split(':')
                        if len(parts) == 2:
                            name, role = parts[0].strip(), parts[1].strip()
                            cast_list.append({"name": name, "role": role})
                return cast_list

            def get_int(data, field, default=0):
                try:
                    return int(data.get(field, default))
                except (ValueError, TypeError):
                    return default

            def get_float(data, field, default=0.0):
                try:
                    return float(data.get(field, default))
                except (ValueError, TypeError):
                    return default

            # ---- JSON Mode ----
            if request.form.get('json_data'):
                try:
                    data = json.loads(request.form['json_data'])
                except Exception as e:
                    flash(f"Invalid JSON: {e}", "danger")
                    return render_template('admin/edit_movie.html', movie=movie)

                # Required check
                if not get_str(data, 'title'):
                    flash("Title is required in JSON.", "danger")
                    return render_template('admin/edit_movie.html', movie=movie)

                movie_data = {}

                # Only update fields that exist in the JSON payload
                if 'title' in data: movie_data['title'] = get_str(data, 'title')
                if 'description' in data: movie_data['description'] = get_str(data, 'description')
                if 'poster_url' in data: movie_data['poster_url'] = get_str(data, 'poster_url')
                if 'backdrop_path' in data: movie_data['backdrop_path'] = get_str(data, 'backdrop_path')
                if 'trailer_url' in data: movie_data['trailer_url'] = get_str(data, 'trailer_url')
                if 'released' in data:
                    released = get_str(data, 'released')
                    movie_data['released'] = released
                    movie_data['release_year'] = extract_release_year(released)
                if 'duration_mins' in data: movie_data['duration_mins'] = get_int(data, 'duration_mins')
                if 'genres' in data: movie_data['genres'] = get_list(data, 'genres')
                if 'languages' in data: movie_data['languages'] = get_list(data, 'languages')
                if 'director' in data: movie_data['director'] = get_str(data, 'director')
                if 'writers' in data: movie_data['writers'] = get_list(data, 'writers')
                if 'production_companies' in data: movie_data['production_companies'] = get_list(data, 'production_companies')
                if 'country' in data: movie_data['country'] = get_str(data, 'country')
                if 'age_rating' in data: movie_data['age_rating'] = get_str(data, 'age_rating')
                if 'rating' in data: movie_data['rating'] = get_float(data, 'rating')
                if 'num_reviews' in data: movie_data['num_reviews'] = get_int(data, 'num_reviews')
                if 'streaming' in data: movie_data['streaming'] = get_list(data, 'streaming')
                if 'cast' in data: movie_data['cast'] = get_cast_list(data)

                # Boolean flags (only set if explicitly included)
                if 'is_popular' in data: movie_data['is_popular'] = bool(data.get('is_popular'))
                if 'is_trending' in data: movie_data['is_trending'] = bool(data.get('is_trending'))
                if 'is_top_rated' in data: movie_data['is_top_rated'] = bool(data.get('is_top_rated'))
                
                # Always update timestamp
                movie_data['updated_at'] = datetime.utcnow()

            # ---- FORM Mode ----
            else:
                form = request.form

                if not get_str(form, 'title'):
                    flash("Title is required.", "danger")
                    return render_template('admin/edit_movie.html', movie=movie)

                movie_data = {
                    "title": get_str(form, 'title'),
                    "description": get_str(form, 'description'),
                    "poster_url": get_str(form, 'poster_url'),
                    "backdrop_path": get_str(form, 'backdrop_path'),
                    "trailer_url": get_str(form, 'trailer_url'),
                    "released": get_str(form, 'released'),
                    "release_year": extract_release_year(get_str(form, 'released')),
                    "duration_mins": get_int(form, 'duration_mins'),
                    "genres": get_list(form, 'genres'),
                    "languages": get_list(form, 'languages'),
                    "director": get_str(form, 'director'),
                    "writers": get_list(form, 'writers'),
                    "production_companies": get_list(form, 'production_companies'),
                    "country": get_str(form, 'country'),
                    "age_rating": get_str(form, 'age_rating'),
                    "rating": get_float(form, 'rating'),
                    "num_reviews": get_int(form, 'num_reviews'),
                    "streaming": get_list(form, 'streaming'),
                    "cast": get_cast_list(form),
                    "is_popular": 'is_popular' in form,
                    "is_trending": 'is_trending' in form,
                    "is_top_rated": 'is_top_rated' in form,
                    "updated_at": datetime.utcnow()
                }

            # Perform DB Update
            movies.update_one({"_id": ObjectId(movie_id)}, {"$set": movie_data})

            flash("Movie updated successfully!", "success")
            return redirect(url_for('admin.admin_movies'))

        return render_template('admin/edit_movie.html', movie=movie)

    except Exception as e:
        flash(f"Error: {e}", "danger")
        return redirect(url_for('admin.admin_movies'))

@bp.route('/movies/view/<movie_id>')
def view_movie(movie_id):
    try:
        movie = movies.find_one({"_id": ObjectId(movie_id)})
        if not movie:
            abort(404, description="Movie not found")
        return render_template('admin/view_movie.html', movie=movie)
    except Exception as e:
        abort(500, description=str(e))

@bp.route('/movies/delete/<movie_id>', methods=['POST', 'GET'])
@admin_login_required
def admin_delete_movie(movie_id):
    try:
        movie = movies.find_one({"_id": ObjectId(movie_id)})
        if not movie:
            flash("Movie not found or already deleted!", "warning")
            return redirect(url_for('admin.admin_movies'))

        movies.delete_one({"_id": ObjectId(movie_id)})

        # Optional: Log the deletion with IP
        logs.insert_one({
            "user": session.get("admin", "Unknown Admin"),
            "action": f"Deleted movie: {movie.get('title', 'Unknown Title')}",
            "timestamp": datetime.utcnow(),
            "ip_address": request.remote_addr
        })

        flash("Movie deleted successfully.", "success")
    except Exception as e:
        flash(f"An error occurred: {e}", "danger")

    return redirect(url_for('admin.admin_movies'))
# ============ REVIEWS ============

@bp.route('/reviews')
@admin_login_required
def admin_reviews():
    all_reviews = list(reviews.find())
    return render_template('admin/reviews.html', reviews=all_reviews, title="Manage Reviews")

# ============ REPORTS ============

@bp.route('/reports')
@admin_login_required
def admin_reports():
    return "Comming soon! This feature is under development."

# ============ LOGS ============

@bp.route('/logs')
@admin_login_required
def admin_logs():
    search = request.args.get('search', '').strip()
    query = {}

    if search:
        regex = Regex(search, 'i')  # Case-insensitive search
        query = {
            "$or": [
                {"user": regex},
                {"action": regex},
                {"timestamp": {"$regex": search}},  # fallback for date strings if stored as strings
            ]
        }

    all_logs = list(logs.find(query).sort("timestamp", -1))
    return render_template('admin/logs.html', logs=all_logs, title="System Logs")

def get_client_ip():
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    return request.remote_addr

# ============ FEEDBACK ============

@bp.route('/feedback')
@admin_login_required
def admin_feedback():
    all_feedback = list(feedback.find())
    return render_template('admin/feedback.html', feedback=all_feedback, title="User Feedback")

# ============ SETTINGS ============

@bp.route('/settings', methods=['GET', 'POST'])
@admin_login_required
def admin_settings():
    current_settings = settings.find_one() or {}

    if request.method == 'POST':
        theme = request.form.get("theme")
        if theme not in ['dark', 'light']:
            flash("Invalid theme selected.", "danger")
            return redirect(url_for('admin.admin_settings'))

        settings.update_one({}, {'$set': {'theme': theme}}, upsert=True)
        flash("Settings updated successfully.", "success")
        return redirect(url_for('admin.admin_settings'))

    return render_template('admin/settings.html', settings=current_settings, title="Settings")

# ============ ADMINS / ROLES ============

@bp.route('/roles')
@admin_login_required
def admin_roles():
    all_admins = list(admins.find())
    return render_template('admin/roles.html', admins=all_admins, title="Admin Roles")
