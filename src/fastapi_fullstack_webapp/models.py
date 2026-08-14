from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


# User model represents the "users" table in the database.
class User(Base):
    __tablename__ = "users"

    # Primary key for the users table.
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Username must be unique and cannot be NULL.
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    # Email must be unique and cannot be NULL.
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)

    password_hash: Mapped[str]=mapped_column(String(200), nullable=False)

    # Optional profile image filename.
    # If no image is uploaded, the value will be NULL.
    image_file: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
        default=None,
    )

    # One-to-Many relationship:
    # One user can have multiple posts.
    # Example:
    # user.posts -> [Post1, Post2, Post3]
    posts: Mapped[list["Post"]] = relationship(
        back_populates="author", cascade="all, delete-orphan"
    )

    # Computed property (not stored in the database).
    # Returns the profile image path if available,
    # otherwise returns the default profile image.
    @property
    def image_path(self) -> str:
        if self.image_file:
            return f"/media/profile_pics/{self.image_file}"
        return "/static/profile_pics/default.jpg"


# Post model represents the "posts" table in the database.
class Post(Base):
    __tablename__ = "posts"

    # Primary key for the posts table.
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Blog post title.
    title: Mapped[str] = mapped_column(String(100), nullable=False)

    # Blog post content.
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Foreign key linking this post to a user.
    # Every post must belong to a user.
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    # Automatically stores the current UTC time
    # when a new post is created.
    date_posted: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
    )

    # Many-to-One relationship:
    # Every post belongs to one user.
    # Example:
    # post.author -> User object
    author: Mapped["User"] = relationship(
        back_populates="posts"
    )

'''
Overall Flow
database.py
        │
        ▼
     Base Class
        │
        ▼
models.py
        │
        ├── User Table
        │
        └── Post Table
                │
                ▼
         SQLAlchemy ORM
                │
                ▼
            SQLite Database
'''