# 🎬 Movie Recommendation API

A RESTful Flask API to manage and query movie data, complete with advanced filters, sorting, pagination, and field ordering.

---

## 🚀 Features

- 📥 Add, update, delete movies
- 🔍 Search by title, genre, director, actors, and more
- 🎯 Filter by year, IMDb rating range, etc.
- 📈 Sort by title, year, or IMDb rating
- 📚 Pagination with limit/skip
- 🔄 Consistent field order using `OrderedDict`

---

## 🛠️ Tech Stack

- **Python + Flask**
- **MongoDB** (via `pymongo`)
- **JSON REST API**

---

## 📦 Installation

```bash
git clone https://github.com/your-username/movie-api.git
cd movie-api
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
⚙️ Configuration
Edit your app/db.py to point to your MongoDB instance:

python
Copy
Edit
from pymongo import MongoClient

def init_db(collection_name):
    client = MongoClient("mongodb://localhost:27017/")
    db = client["movie_db"]
    return db[collection_name]
▶️ Running the API
bash
Copy
Edit
flask run
Base URL: http://localhost:5000/api/movies

📚 API Endpoints
🔍 GET /api/movies
Query all or filtered movies.

Query Parameters:

Param	Type	Description
title	string	Regex search for title
genre	string	Comma-separated list of genres
year_from	int	Filter movies released from this year
year_to	int	Filter movies released up to this year
imdbRating_min	float	Minimum IMDb rating
imdbRating_max	float	Maximum IMDb rating
director	string	Regex search on director name
actor	string	Search inside the Actors array
sort_by	string	title, year, imdbRating
order	string	asc or desc
limit	int	Default: 50
skip	int	For pagination

📄 GET /api/movies/<movie_id>
Returns a single movie by MongoDB ObjectId.

➕ POST /api/movies
Add a new movie.

Body Example:

json
Copy
Edit
{
  "Title": "The Matrix",
  "Year": "1999",
  "Genre": ["Action", "Sci-Fi"],
  "Director": "Lana Wachowski, Lilly Wachowski",
  ...
}
✏️ PUT /api/movies/<movie_id>
Update an existing movie.

Body: Partial or full movie object (excluding _id).

❌ DELETE /api/movies/<movie_id>
Deletes the movie with that ID.

🧪 Testing
You can test with:

Postman

curl

Swagger docs (optional if added)

A frontend 😎

🧠 To-Do / Future Plans
 Add JWT auth for user-based access

 User ratings & reviews

 Swagger or ReDoc documentation

 Upload poster image support

 Advanced full-text search

💬 Example cURL
bash
Copy
Edit
curl "http://localhost:5000/api/movies?genre=Action&year_from=2000&sort_by=imdbRating&order=desc"
👨‍💻 Author
Built by Gagan 💻🧠 — student, dev, and creative mastermind behind this awesome project.

📜 License
MIT License. Use it, build on it, break it, remix it — just give credit.

yaml
Copy
Edit

---

Let me know if you want me to generate a `requirements.txt` for this, or create a seed script to dump in 20+ sample movies from IMDb-style data!
