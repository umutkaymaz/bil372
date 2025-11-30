from fastapi import FastAPI, HTTPException, Depends, Response, Cookie
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from sqlalchemy import create_engine, text
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from pydantic import BaseModel
from typing import Optional
import os
import secrets
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_NAME = os.getenv("DB_NAME")

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}"

engine = create_engine(DATABASE_URL, echo=True)
app = FastAPI()

# CORS AYARI
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080",
        "http://127.0.0.1:8080",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Güvenlik ayarları
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

security = HTTPBearer()

# Request modelleri
class UserRegister(BaseModel):
    user_id: str
    user_name: str
    user_city: str
    user_restofaddress: str
    user_phonenumber: str
    password: str

class UserLogin(BaseModel):
    user_id: str
    password: str

# Yardımcı fonksiyonlar
def hash_password(password: str) -> str:
    return pwd_context.hash(password[:72])

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password[:72], hashed_password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# -----------------------------
# AUTH ENDPOINTS
# -----------------------------
@app.post("/register")
def register_user(user: UserRegister):
    with engine.connect() as conn:
        # Kullanıcı zaten var mı kontrol et
        existing = conn.execute(
            text("SELECT user_id FROM users_table WHERE user_id = :uid"),
            {"uid": user.user_id}
        ).fetchone()
        
        if existing:
            raise HTTPException(status_code=400, detail="User ID already exists")
        
        # Telefon numarası zaten var mı kontrol et
        existing_phone = conn.execute(
            text("SELECT user_id FROM users_table WHERE user_phonenumber = :phone"),
            {"phone": user.user_phonenumber}
        ).fetchone()
        
        if existing_phone:
            raise HTTPException(status_code=400, detail="Phone number already registered")
        
        # Şifreyi hashle ve kullanıcıyı ekle
        hashed_pwd = hash_password(user.password)
        conn.execute(
            text("""
                INSERT INTO users_table 
                (user_id, user_name, user_city, user_restofaddress, 
                 user_phonenumber, user_passwordhashes)
                VALUES (:uid, :name, :city, :addr, :phone, :pwd)
            """),
            {
                "uid": user.user_id,
                "name": user.user_name,
                "city": user.user_city,
                "addr": user.user_restofaddress,
                "phone": user.user_phonenumber,
                "pwd": hashed_pwd
            }
        )
        conn.commit()
    
    return {"message": "User registered successfully", "user_id": user.user_id}

@app.post("/login")
def login_user(user: UserLogin, response: Response):
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT user_passwordhashes FROM users_table WHERE user_id = :uid"),
            {"uid": user.user_id}
        ).fetchone()
        
        if not result:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        if not verify_password(user.password, result[0]):
            raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Token oluştur
    access_token = create_access_token(data={"sub": user.user_id})
    
    print(f"DEBUG LOGIN: Setting cookie with token: {access_token[:20]}...")
    
    # Cookie olarak ayarla
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=1800,
        path="/"
    )
    
    return {"message": "Login successful", "user_id": user.user_id}

@app.post("/logout")
def logout_user(response: Response):
    response.delete_cookie(key="access_token", path="/")
    return {"message": "Logout successful"}

@app.get("/me")
def get_current_user_info(access_token: Optional[str] = Cookie(None)):
    print(f"DEBUG: Received access_token cookie: {access_token}")
    
    if not access_token:
        raise HTTPException(status_code=401, detail="No access token in cookie")
    
    try:
        payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT user_id, user_name, user_city, user_restofaddress, user_phonenumber 
                    FROM users_table 
                    WHERE user_id = :uid
                """),
                {"uid": user_id}
            ).fetchone()
            
            if not result:
                raise HTTPException(status_code=404, detail="User not found")
            
            return dict(result._mapping)
    except JWTError as e:
        print(f"JWT Error: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")

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
                l.*, u.*
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
            text("""
                 SELECT l.*, u.*
                 FROM listings_table as l
                 JOIN users_table as u
                 ON l.listing_ownerid = u.user_id 
                 WHERE listing_id = :id
                 """),
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
                SELECT l.*, u.*
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
        SELECT DISTINCT l.*, u.*
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