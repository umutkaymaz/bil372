from fastapi import FastAPI, HTTPException, Depends, Response, Cookie
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from fastapi import UploadFile, File
from sqlalchemy import create_engine, text
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from pydantic import BaseModel
from typing import Optional
import os
import shutil
import os
import secrets
from dotenv import load_dotenv
from fastapi.staticfiles import StaticFiles




load_dotenv()

IMAGES_DIR = "images"

DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_NAME = os.getenv("DB_NAME")
DB_PORT = os.getenv("DB_PORT")

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

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

app.mount("/images", StaticFiles(directory="images"), name="images")

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

class Comment(BaseModel):
    comment_content: str
    comment_date: str
    comment_ownerid: str
    comment_listingid: str

class ListingCreate(BaseModel):
    listing_name: str
    listing_price: float
    listing_condition: str
    listing_date: str
    listing_desc: Optional[str] = None
    listing_imagepath: Optional[str] = None
    genres: Optional[list[int]] = []   # genre_id listesi

class ListingUpdate(BaseModel):
    listing_name: str
    listing_price: float
    listing_condition: str
    listing_desc: Optional[str] = None
    genres: list[int]

class UserUpdate(BaseModel):
    user_name: str
    user_city: str
    user_restofaddress: str
    user_phonenumber: str
    new_password: Optional[str] = None



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

@app.put("/users/update/{user_id}")
def update_user_profile(
    user_id: str,
    updated_data: UserUpdate,
    access_token: Optional[str] = Cookie(None)
):
    # ---------------------------
    #  TOKEN DOĞRULAMA
    # ---------------------------
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
        token_user_id = payload.get("sub")

        if not token_user_id or str(token_user_id) != str(user_id):
            raise HTTPException(status_code=403, detail="You can only edit your own profile.")

    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    # ---------------------------
    #  SQL UPDATE QUERY HAZIRLAMA
    # ---------------------------

    update_fields = {
        "user_name": updated_data.user_name,
        "user_city": updated_data.user_city,
        "user_restofaddress": updated_data.user_restofaddress,
        "user_phonenumber": updated_data.user_phonenumber,
    }

    # Eğer yeni parola gönderilmişse hash'le ve ekle
    if updated_data.new_password:
        hashed = pwd_context.hash(updated_data.new_password)
        update_fields["user_passwordhashes"] = hashed

    # Dinamik SET kısmını oluştur
    set_clause = ", ".join([f"{key} = :{key}" for key in update_fields.keys()])

    sql = text(f"""
        UPDATE users_table
        SET {set_clause}
        WHERE user_id = :user_id
    """)

    update_fields["user_id"] = user_id

    # ---------------------------
    #  SQL ÇALIŞTIR
    # ---------------------------
    with engine.connect() as conn:
        conn.execute(sql, update_fields)
        conn.commit()

    return {"message": "Profile updated successfully"}

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
                SELECT c.comment_content, c.comment_date, c.comment_id, c.comment_ownerid, u.user_name
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

@app.delete("/listings/delete/{listing_id}")
def delete_listing(listing_id: int, access_token: Optional[str] = Cookie(None)):
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authorized")

    # Token decode
    try:
        payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    with engine.connect() as conn:
        # İlan var mı?
        listing = conn.execute(
            text("SELECT listing_ownerid FROM listings_table WHERE listing_id = :id"),
            {"id": listing_id}
        ).fetchone()

        if not listing:
            raise HTTPException(status_code=404, detail="Listing not found")

        # Sahibine ait mi?
        if listing[0] != user_id:
            raise HTTPException(status_code=403, detail="You cannot delete this listing")

        conn.execute(
            text("DELETE FROM listing_genres WHERE listing_id = :id"),
            {"id": listing_id}
        )

        # Önce yorumları sil (FK varsa gerekmez ama kesin çözüm)
        conn.execute(
            text("DELETE FROM comments_table WHERE comment_listingid = :id"),
            {"id": listing_id}
        )

        # Sonra ilanı sil
        conn.execute(
            text("DELETE FROM listings_table WHERE listing_id = :id"),
            {"id": listing_id}
        )

        conn.commit()

    return {"message": "Listing deleted successfully"}

@app.post("/listings/create")
def create_listing(listing: ListingCreate, access_token: Optional[str] = Cookie(None)):
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authorized")

    try:
        payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
        owner_id = payload.get("sub")
    except:
        raise HTTPException(status_code=401, detail="Invalid token")

    with engine.connect() as conn:
        conn.execute(
            text("""
                INSERT INTO listings_table (
                    listing_name, listing_price, listing_ownerid, 
                    listing_condition, listing_date, listing_desc, listing_imagepath
                )
                VALUES (
                    :name, :price, :owner, :cond, :date, :desc, :img
                )
            """),
            {
                "name": listing.listing_name,
                "price": listing.listing_price,
                "owner": owner_id,
                "cond": listing.listing_condition,
                "date": listing.listing_date,
                "desc": listing.listing_desc,
                "img": listing.listing_imagepath
            }
        )

        new_id = conn.execute(text("SELECT LAST_INSERT_ID()")).scalar()

        # ⭐ Genre eşleştirmelerini ekleyelim
        if listing.genres:
            for gid in listing.genres:
                conn.execute(
                    text("""
                        INSERT INTO listing_genres (listing_id, genre_id)
                        VALUES (:lid, :gid)
                    """),
                    {"lid": new_id, "gid": gid}
                )

        conn.commit()

    return {"message": "Listing created successfully", "listing_id": new_id}

@app.post("/listings/{listing_id}/upload_image")
def upload_listing_image(listing_id: int, file: UploadFile = File(...)):
    # Uzantıyı al
    filename = file.filename
    ext = filename.split(".")[-1].lower()

    # yalnızca belirli formatlara izin ver
    if ext not in ["jpg", "jpeg", "png", "webp"]:
        raise HTTPException(status_code=400, detail="Geçersiz dosya formatı. (jpg, jpeg, png, webp)")

    # Kaydedilecek nihai dosya adı
    save_path = f"{IMAGES_DIR}/{listing_id}.{ext}"

    # Dosyayı kaydet
    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # DB içindeki path'i güncelle
    with engine.connect() as conn:
        conn.execute(
            text("""
                UPDATE listings_table 
                SET listing_imagepath = :path 
                WHERE listing_id = :id
            """),
            {"path": f"/images/{listing_id}.{ext}", "id": listing_id}
        )
        conn.commit()

    return {"message": "Image uploaded.", "image_path": f"/images/{listing_id}.{ext}"}

@app.put("/listings/{listing_id}/update")
def update_listing(listing_id: int, data: ListingUpdate, access_token: Optional[str] = Cookie(None)):
    if not access_token:
        raise HTTPException(status_code=401)

    payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
    user_id = payload.get("sub")

    with engine.connect() as conn:
        owner = conn.execute(
            text("SELECT listing_ownerid FROM listings_table WHERE listing_id = :id"),
            {"id": listing_id}
        ).fetchone()

        if not owner or owner[0] != user_id:
            raise HTTPException(status_code=403, detail="Yetkin yok")

        conn.execute(
            text("""
                UPDATE listings_table
                SET 
                    listing_name = :name,
                    listing_price = :price,
                    listing_condition = :cond,
                    listing_desc = :desc
                WHERE listing_id = :id
            """),
            {
                "id": listing_id,
                "name": data.listing_name,
                "price": data.listing_price,
                "cond": data.listing_condition,
                "desc": data.listing_desc
            }
        )

        # Genre güncelle
        conn.execute(
            text("DELETE FROM listing_genres WHERE listing_id = :id"),
            {"id": listing_id}
        )

        for gid in data.genres:
            conn.execute(
                text("INSERT INTO listing_genres (listing_id, genre_id) VALUES (:lid, :gid)"),
                {"lid": listing_id, "gid": gid}
            )

        conn.commit()

    return {"message": "Listing updated"}

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
                    c.*,
                    u.user_name
                FROM comments_table c
                JOIN users_table u 
                ON u.user_id = c.comment_ownerid
                WHERE c.comment_listingid = :id
            """),
            {"id": listing_id}
        )

    return [dict(row._mapping) for row in result]

@app.post("/comments/post_comment")
def post_comment(comment: Comment):
    with engine.connect() as conn:
        conn.execute(
            text("""
                INSERT INTO comments_table (
                    comment_content, 
                    comment_date, 
                    comment_ownerid, 
                    comment_listingid
                ) VALUES (
                    :content, 
                    :date, 
                    :owner, 
                    :listing
                );
            """),
            {
                "content": comment.comment_content,
                "date": comment.comment_date,       # YYYY-MM-DD formatı
                "owner": comment.comment_ownerid,
                "listing": comment.comment_listingid
            }
        )
        conn.commit()

@app.delete("/comments/delete_comment/{comment_id}")
def delete_comment(comment_id: int, access_token: Optional[str] = Cookie(None)):
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authorized")

    try:
        payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    with engine.connect() as conn:
        # Yorumu çek
        comment = conn.execute(
            text("""
                SELECT comment_ownerid 
                FROM comments_table 
                WHERE comment_id = :cid
            """),
            {"cid": comment_id}
        ).fetchone()

        if not comment:
            raise HTTPException(status_code=404, detail="Comment not found")

        # Sadece sahibi silebilir
        if comment[0] != user_id:
            raise HTTPException(status_code=403, detail="You cannot delete this comment")

        # Sil
        conn.execute(
            text("DELETE FROM comments_table WHERE comment_id = :cid"),
            {"cid": comment_id}
        )
        conn.commit()

    return {"message": "Comment deleted successfully"}

@app.put("/comments/update/{comment_id}")
def update_comment(comment_id: int, updated: Comment, access_token: Optional[str] = Cookie(None)):
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authorized")

    # Token decode
    try:
        payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    with engine.connect() as conn:
        # Yorum var mı?
        comment = conn.execute(
            text("SELECT comment_ownerid FROM comments_table WHERE comment_id = :id"),
            {"id": comment_id}
        ).fetchone()

        if not comment:
            raise HTTPException(status_code=404, detail="Comment not found")

        # Sahibi mi?
        if comment[0] != user_id:
            raise HTTPException(status_code=403, detail="You cannot update this comment")

        # Yorum güncelle
        conn.execute(
            text("""
                UPDATE comments_table
                SET comment_content = :content
                WHERE comment_id = :id
            """),
            {"content": updated.comment_content, "id": comment_id}
        )
        conn.commit()

    return {"message": "Comment updated successfully"}



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
    name: str = None,
    city: str = None,
    min_price: float = None,
    max_price: float = None,
    genre: str = None,
    sort_by: str = None,
    sort_order: str = None
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

    if name:
        query += f' AND l.listing_name LIKE "%{name}%"'
        params["name"] = name

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

    if sort_by and sort_order:
        if sort_by == "name":
            query += " ORDER BY l.listing_name"

        elif sort_by == "price":
            query += " ORDER BY l.listing_price"
        
        if sort_order == "asc":
            query += " ASC"
        
        elif sort_order == "desc":
            query += " DESC"


    print("\nQUERY:\n")
    print(query)

    with engine.connect() as conn:
        result = conn.execute(text(query), params)

    return [dict(row._mapping) for row in result]

# -----------------------------
# GENRES
# -----------------------------

@app.get("/genres")
def get_all_genres():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT genre_id, genre_name FROM genres"))
        return [dict(row._mapping) for row in result]
