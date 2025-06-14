from datetime import datetime
from collections import OrderedDict
import json
from bson import ObjectId
import re

MOVIE_KEYS_ORDER = [
    "_id", "title", "description", "poster_url", "backdrop_path", "trailer_url",
    "release_year","released", "duration_mins", "genres", "languages", "director", "writers",
    "cast", "production_companies", "country", "age_rating", "rating", "num_reviews",
    "streaming", "is_featured", "is_trending", "is_top_rated", "added_by", 
    "date_added", "updated_at",
]


# 🔹 Cast string parser: "Actor:Role | ..." ➜ [{"name": ..., "role": ...}, ...]
def parse_cast_string(cast_str):
    if not cast_str:
        return []
    cast_list = []
    for item in cast_str.split('|'):
        parts = item.strip().split(':', 1)
        if len(parts) == 2:
            name, role = parts
            cast_list.append({'name': name.strip(), 'role': role.strip()})
    return cast_list

# 🔹 JSON encoder for ObjectId and datetime
class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        if isinstance(o, datetime):
            return o.isoformat()
        return super().default(o)

def order_movie_fields(movie):
    ordered = OrderedDict()
    for key in MOVIE_KEYS_ORDER:
        val = movie.get(key)
        if isinstance(val, datetime):
            val = val.isoformat()
        ordered[key] = val
    return ordered

def safe_cast_int(val, default=None):
    try:
        return int(val)
    except (ValueError, TypeError):
        return default
    
def is_pass_strong(password):
    return (
        len(password) >=8 and len(password) <= 15 and
        re.search(r'[A-Z]', password) and
        re.search(r'[a-z]', password) and
        re.search(r'\d', password) and
        re.search(r'[!@#$%^&*(),.?\":{}|<>]', password)
    )