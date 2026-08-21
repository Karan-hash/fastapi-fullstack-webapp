# Populate Development Database

This script resets and repopulates the local development database with sample users, posts, and profile images.

## What the script does

When run, `populate_db.py` will:

- Create missing database tables before seeding data
- Clear existing password reset tokens, posts, and users
- Remove existing local profile pictures except `.gitkeep`
- Create 6 sample users
- Create 44 sample posts
- Upload sample profile pictures
- Update post dates for pagination testing

> Warning: This script deletes existing local development data before repopulating the database. Do not use it against a production database.

## Project location

Run the script from the project root, where `pyproject.toml` is located.

Example:

```bash
cd /Users/karan/Documents/FastApiLatestWork/fastapi-fullstack-webapp
```

## Install or sync dependencies

If dependencies are not already installed or the project environment needs to be refreshed:

```bash
uv sync
```

## Run the population script

Use Python module execution:

```bash
uv run python -m fastapi_fullstack_webapp.populate_db
```

Do not run the file directly with:

```bash
uv run populate_db.py
```

The project uses relative package imports such as:

```python
from . import models
```

Running the file directly does not provide the package context required for those imports.

## Expected output

A successful run should look similar to:

```text
Cleared existing data

Creating 6 users...
  Created: KaranKaushal
  Created: DefaultDude
  ...

Creating 44 posts...
  Created: 'Karan Kaushal: 44 Practical Lessons from Building with FastAPI'
  ...

Updating post dates...
Updated post dates

Done!
  6 users
  44 posts
  Profile pictures saved locally
```

## Recommended workflow

```bash
cd /Users/karan/Documents/FastApiLatestWork/fastapi-fullstack-webapp
uv sync
uv run python -m fastapi_fullstack_webapp.populate_db
```

## Troubleshooting

### `ImportError: attempted relative import with no known parent package`

Cause: `populate_db.py` was run directly.

Use:

```bash
uv run python -m fastapi_fullstack_webapp.populate_db
```

instead of:

```bash
uv run populate_db.py
```

### `RuntimeError: Directory 'static' does not exist`

Static, media, and template paths should be resolved relative to the application package using `Path(__file__).resolve().parent`.

Example:

```python
BASE_DIR = Path(__file__).resolve().parent

app.mount(
    "/static",
    StaticFiles(directory=BASE_DIR / "static"),
    name="static",
)

app.mount(
    "/media",
    StaticFiles(directory=BASE_DIR / "media"),
    name="media",
)

templates = Jinja2Templates(
    directory=BASE_DIR / "templates",
)
```

### `sqlite3.OperationalError: no such table: posts`

The population script must ensure database tables exist before deleting or inserting records.

The script should run:

```python
async with engine.begin() as conn:
    await conn.run_sync(Base.metadata.create_all)
```

before clearing existing data.

## Development only

This population script is intended for local development and testing. It should not be used for production data.
