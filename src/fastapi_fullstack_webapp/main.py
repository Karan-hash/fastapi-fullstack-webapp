from fastapi import FastAPI
from fastapi.responses import HTMLResponse
app = FastAPI()

posts: list[dict] = [
    {
        "id": 1,
        "author": "Karan Kaushal",
        "title": "FastAPI is Awesome",
        "content": "This framework is really easy to use and super fast.",
        "date_posted": "April 20, 2025",
    },
    {
        "id": 2,
        "author": "Jane Doe",
        "title": "Python is Great for Web Development",
        "content": "Python is a great language for web development, and FastAPI makes it even better.",
        "date_posted": "April 21, 2025",
    },
    {
        "id": 3,
        "author": "John Smith",
        "title": "Understanding REST APIs",
        "content": "REST APIs provide a standard way for applications to communicate over HTTP.",
        "date_posted": "April 22, 2025",
    },
    {
        "id": 4,
        "author": "Emily Johnson",
        "title": "Why Learn FastAPI?",
        "content": "FastAPI offers automatic validation, type hints, and incredible performance.",
        "date_posted": "April 23, 2025",
    },
    {
        "id": 5,
        "author": "Michael Brown",
        "title": "Deploying FastAPI with Docker",
        "content": "Docker makes deploying FastAPI applications simple and consistent across environments.",
        "date_posted": "April 24, 2025",
    },
    {
        "id": 6,
        "author": "Sarah Wilson",
        "title": "Async Programming in Python",
        "content": "Async programming allows handling multiple requests efficiently using async and await.",
        "date_posted": "April 25, 2025",
    },
    {
        "id": 7,
        "author": "David Miller",
        "title": "Working with Pydantic",
        "content": "Pydantic provides powerful data validation and serialization using Python type hints.",
        "date_posted": "April 26, 2025",
    },
    {
        "id": 8,
        "author": "Olivia Taylor",
        "title": "Dependency Injection in FastAPI",
        "content": "Dependency injection helps keep your code modular, reusable, and easier to test.",
        "date_posted": "April 27, 2025",
    },
    {
        "id": 9,
        "author": "Daniel Anderson",
        "title": "Building CRUD APIs",
        "content": "CRUD operations form the foundation of most backend APIs and database applications.",
        "date_posted": "April 28, 2025",
    },
    {
        "id": 10,
        "author": "Sophia Martinez",
        "title": "JWT Authentication with FastAPI",
        "content": "JWT authentication provides a secure and scalable way to protect API endpoints.",
        "date_posted": "April 29, 2025",
    },
]
@app.get("/", response_class=HTMLResponse, include_in_schema=False)
@app.get("/posts", response_class=HTMLResponse, include_in_schema=False)
def home():
    return f"<h1>{posts[0]['title']}</h1>"

@app.get("/api/posts")
def get_posts():
    return posts