"""
Database Schemas for Cine+Play (films & jeux vidéo)

Each Pydantic model corresponds to a MongoDB collection (lowercased class name).
- User -> "user"
- Media -> "media"
- Review -> "review"

These are used for validation and to power the database viewer via GET /schema.
"""

from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, Literal
from datetime import datetime


class User(BaseModel):
    """Users of the platform"""
    username: str = Field(..., min_length=2, max_length=30, description="Public handle")
    display_name: Optional[str] = Field(None, max_length=60, description="Name shown on profile")
    avatar_url: Optional[HttpUrl] = Field(None, description="Avatar image URL")
    bio: Optional[str] = Field(None, max_length=300, description="Short bio")


class Media(BaseModel):
    """Movies and Games"""
    type: Literal["movie", "game"] = Field(..., description="Media type")
    title: str = Field(..., min_length=1, max_length=200)
    year: Optional[int] = Field(None, ge=1878, le=2100)
    poster_url: Optional[HttpUrl] = Field(None)
    tagline: Optional[str] = Field(None, max_length=160)


class Review(BaseModel):
    """A diary/review entry for a media item"""
    media_id: str = Field(..., description="ID of the media document")
    username: str = Field(..., min_length=2, max_length=30, description="Author username")
    rating: Optional[float] = Field(None, ge=0, le=5, description="Stars 0-5, .5 steps allowed")
    liked: bool = Field(False, description="Whether the user liked it")
    text: Optional[str] = Field(None, max_length=2000)
    watched_at: Optional[datetime] = Field(None, description="When watched/played")


# Expose a mapping for easy schema listing in the backend
SCHEMAS = {
    "User": User,
    "Media": Media,
    "Review": Review,
}
