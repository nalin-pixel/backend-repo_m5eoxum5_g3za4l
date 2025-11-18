import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import User, Media, Review, SCHEMAS

app = FastAPI(title="Cine+Play API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class MediaCreate(Media):
    pass


class ReviewCreate(Review):
    pass


@app.get("/")
def read_root():
    return {"message": "Cine+Play backend running"}


@app.get("/test")
def test_database():
    """Test endpoint to check database connectivity and list collections"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = db.name if hasattr(db, 'name') else "❌ Unknown"
            response["connection_status"] = "Connected"
            try:
                response["collections"] = db.list_collection_names()[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️ Connected but Error: {str(e)[:80]}"
        else:
            response["database"] = "⚠️ Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:80]}"

    return response


# ----- Users -----
@app.post("/users", response_model=dict)
def create_user(user: User):
    user_id = create_document("user", user)
    return {"id": user_id}


@app.get("/users", response_model=List[dict])
def list_users(limit: int = 50):
    docs = get_documents("user", limit=min(limit, 100))
    for d in docs:
        d["id"] = str(d.pop("_id"))
    return docs


# ----- Media (movies & games) -----
@app.post("/media", response_model=dict)
def create_media(media: MediaCreate):
    media_id = create_document("media", media)
    return {"id": media_id}


@app.get("/media", response_model=List[dict])
def list_media(type: Optional[str] = None, q: Optional[str] = None, limit: int = 50):
    filt = {}
    if type in {"movie", "game"}:
        filt["type"] = type
    if q:
        # Basic case-insensitive contains using regex
        filt["title"] = {"$regex": q, "$options": "i"}
    docs = get_documents("media", filter_dict=filt, limit=min(limit, 100))
    for d in docs:
        d["id"] = str(d.pop("_id"))
    return docs


# ----- Reviews -----
@app.post("/reviews", response_model=dict)
def create_review(review: ReviewCreate):
    # Ensure media exists
    try:
        _id = ObjectId(review.media_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid media_id")

    media_doc = db["media"].find_one({"_id": _id})
    if not media_doc:
        raise HTTPException(status_code=404, detail="Media not found")

    review_id = create_document("review", review)
    return {"id": review_id}


@app.get("/reviews", response_model=List[dict])
def list_reviews(username: Optional[str] = None, media_id: Optional[str] = None, limit: int = 50):
    filt = {}
    if username:
        filt["username"] = username
    if media_id:
        try:
            filt["media_id"] = media_id
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid media_id")
    docs = get_documents("review", filter_dict=filt, limit=min(limit, 100))
    for d in docs:
        d["id"] = str(d.pop("_id"))
    return docs


# ----- Schema exposure (for viewer tools) -----
class SchemaInfo(BaseModel):
    name: str
    fields: dict


@app.get("/schema", response_model=List[SchemaInfo])
def get_schema():
    items: List[SchemaInfo] = []
    for name, model in SCHEMAS.items():
        items.append(SchemaInfo(name=name, fields=model.model_json_schema()))
    return items


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
