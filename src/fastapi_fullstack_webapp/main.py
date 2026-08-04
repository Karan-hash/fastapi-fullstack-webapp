from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

app = FastAPI()

templates = Jinja2Templates(directory="templates")

app.mount("/static", StaticFiles(directory="static"), name="static")

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
# @app.get("/", response_class=HTMLResponse, include_in_schema=False)
# @app.get("/posts", response_class=HTMLResponse, include_in_schema=False)
# def home():
#     return f"<h1>{posts[0]['title']}</h1>"

# @app.get("/api/posts")
# def get_posts():
#     return posts


@app.get("/", include_in_schema=False, name="home")
@app.get("/posts", include_in_schema=False, name="posts")
def home(request: Request):
    return templates.TemplateResponse(request, "home.html", {"posts": posts, "title":"Home"} )


@app.get("/post/{post_id}", include_in_schema=False)
def posts_page(request: Request, post_id: int):
    for post in posts:
        if post.get("id") == post_id:
            title = post["title"][:50]
            return templates.TemplateResponse(request, "post.html", {"post": post, "title":title} )
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post Not Found")

@app.get("/api/posts")
def get_posts():
    return posts

@app.get("/api/posts/{post_id}")
def get_post(post_id: int):
    for post in posts:
        if post.get("id") == post_id:
            return post
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post Not Found")


@app.exception_handler(StarletteHTTPException)
def general_http_exception_handler(request: Request, exception: StarletteHTTPException):
    message = (
        exception.detail
        if exception.detail
        else "An error occurred. Please check your request and try again."
    )

    if request.url.path.startswith("/api"):
        return JSONResponse(
            status_code=exception.status_code,
            content={"detail": message},
        )

    return templates.TemplateResponse(
        request,
        "error.html",
        {
            "status_code": exception.status_code,
            "title": exception.status_code,
            "message": message,
        },
        status_code=exception.status_code,
    )

@app.exception_handler(RequestValidationError)
def validation_exception_handler(request: Request, exception: RequestValidationError):
    if request.url.path.startswith("/api"):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={"detail": exception.errors()},
        )

    return templates.TemplateResponse(
        request,
        "error.html",
        {
            "status_code": status.HTTP_422_UNPROCESSABLE_CONTENT,
            "title": status.HTTP_422_UNPROCESSABLE_CONTENT,
            "message": "Invalid request. Please check your input and try again.",
        },
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
    )