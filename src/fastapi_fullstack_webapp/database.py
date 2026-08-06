from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# Database connection URL.
# sqlite:///./blog.db means:
# - sqlite://      -> SQLite database
# - ./blog.db      -> Create or use blog.db in the current project directory
DATABASE_URL= "sqlite:///./blog.db"

# Create the SQLAlchemy engine.
# The engine is responsible for establishing and managing the database connection.
#
# connect_args={"check_same_thread": False}
# SQLite normally allows only the thread that created the connection
# to use it. Setting this to False allows FastAPI to access the database
# from multiple threads.
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# Create a Session factory.
#
# A Session represents a conversation with the database.
# Every request will create its own session using SessionLocal().
#
# autocommit=False
# -> Changes are NOT automatically saved.
#    You must explicitly call db.commit().
#
# autoflush=False
# -> SQLAlchemy will not automatically synchronize pending changes
#    before executing queries.
#
# bind=engine
# -> Connect this session to the engine created above.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Base class for all SQLAlchemy models.
#
# Every model (User, Post, Comment, etc.) will inherit from this class.
#
# Example:
#
# class Post(Base):
#     __tablename__ = "posts"
#     ...
#
# SQLAlchemy uses this base class to keep track of all models
# and create their corresponding database tables.

class Base(DeclarativeBase):
    pass


# Dependency function for FastAPI.
#
# A new database session is created for every request.
#
# yield pauses the function and gives the session to the route.
# After the request is completed, the session is automatically closed.
#
# Example:
#
# @app.get("/posts")
# def get_posts(db: Session = Depends(get_db)):
#     ...
#
# This ensures proper database connection management and prevents
# connection leaks.

def get_db():
    with SessionLocal() as db:
        yield db

'''
Request
   │
   ▼
Depends(get_db)
   │
   ▼
SessionLocal()
   │
   ▼
Database Session
   │
   ▼
CRUD Operations
   │
   ▼
db.commit() / db.rollback()
   │
   ▼
yield finishes
   │
   ▼
Session Automatically Closed
'''