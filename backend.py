from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware  # BUNU EKLE
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_NAME = os.getenv("DB_NAME")

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}"

engine = create_engine(DATABASE_URL, echo=True)
app = FastAPI()

# CORS AYARI - BUNU EKLE
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Tüm originlere izin ver
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Geri kalan kodların...

# -----------------------------
# USERS
# -----------------------------
@app.get("/users")
def get_users():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM users_table"))
        users = [dict(row._mapping) for row in result]
    return users


@app.get("/users/{user_id}")
def get_user(user_id: str):
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT * FROM users_table WHERE user_id = :uid"),
            {"uid": user_id}
        ).fetchone()

    if not result:
        raise HTTPException(status_code=404, detail="User not found")

    return dict(result._mapping)

# -----------------------------
# LISTINGS
# -----------------------------
@app.get("/listings")
def get_all_listings():
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT 
                l.*, u.user_name, u.user_city 
            FROM listings_table l
            JOIN users_table u 
            ON l.listing_ownerid = u.user_id
        """))

        listings = [dict(row._mapping) for row in result]

    return listings


@app.get("/listings/{listing_id}")
def get_listing(listing_id: int):
    with engine.connect() as conn:
        listing = conn.execute(
            text("SELECT * FROM listings_table WHERE listing_id = :id"),
            {"id": listing_id}
        ).fetchone()

        if not listing:
            raise HTTPException(status_code=404, detail="Listing not found")

        genres = conn.execute(
            text("""
                SELECT g.genre_name FROM genres g
                JOIN listing_genres lg ON g.genre_id = lg.genre_id
                WHERE lg.listing_id = :id
            """),
            {"id": listing_id}
        )

        comments = conn.execute(
            text("""
                SELECT c.comment_content, c.comment_date, u.user_name
                FROM comments_table c
                JOIN users_table u ON c.comment_ownerid = u.user_id
                WHERE c.comment_listingid = :id
            """),
            {"id": listing_id}
        )

    return {
        **dict(listing._mapping),
        "genres": [g[0] for g in genres],
        "comments": [dict(row._mapping) for row in comments]
    }

# -----------------------------
# SEARCH / FILTER
# -----------------------------
@app.get("/search")
def search_listings(keyword: str = ""):
    with engine.connect() as conn:
        result = conn.execute(
            text("""
                SELECT l.*, u.user_name, u.user_city
                FROM listings_table l
                JOIN users_table u ON l.listing_ownerid = u.user_id
                WHERE l.listing_name LIKE :key
            """),
            {"key": f"%{keyword}%"}
        )

    return [dict(row._mapping) for row in result]

# -----------------------------
# COMMENTS
# -----------------------------
@app.get("/comments/{listing_id}")
def get_comments(listing_id: int):
    with engine.connect() as conn:
        result = conn.execute(
            text("""
                SELECT 
                    c.comment_content,
                    c.comment_date,
                    u.user_name
                FROM comments_table c
                JOIN users_table u 
                ON u.user_id = c.comment_ownerid
                WHERE c.comment_listingid = :id
            """),
            {"id": listing_id}
        )

    return [dict(row._mapping) for row in result]

# -----------------------------
# VIEW - user_listing_genre_view
# -----------------------------
@app.get("/view/user_listing_genre")
def get_view():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM user_listing_genre_view"))

    return [dict(row._mapping) for row in result]

# -----------------------------
# FILTERING
# -----------------------------

@app.get("/filters/listings")
def filter_listings(
    city: str = None,
    min_price: float = None,
    max_price: float = None,
    genre: str = None
):
    query = """
        SELECT DISTINCT l.*, u.user_name, u.user_city
        FROM listings_table l
        JOIN users_table u ON l.listing_ownerid = u.user_id
        LEFT JOIN listing_genres lg ON l.listing_id = lg.listing_id
        LEFT JOIN genres g ON lg.genre_id = g.genre_id
        WHERE 1=1
    """

    params = {}

    if city:
        query += " AND u.user_city = :city"
        params["city"] = city

    if min_price:
        query += " AND l.listing_price >= :min_price"
        params["min_price"] = min_price

    if max_price:
        query += " AND l.listing_price <= :max_price"
        params["max_price"] = max_price

    if genre:
        query += " AND g.genre_name = :genre"
        params["genre"] = genre

    with engine.connect() as conn:
        result = conn.execute(text(query), params)

    return [dict(row._mapping) for row in result]

