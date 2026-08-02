# FastAPI Full-Stack Web Application

This project is built using **FastAPI** and **Python**.

## Prerequisites

- Python 3.14+
- Git
- Homebrew (macOS)
- uv (Recommended) or pip

---

# Setup using `uv` (Recommended)

## 1. Install `uv`

```bash
brew install uv
```

Verify the installation:

```bash
uv --version
```

---

## 2. Clone the repository

```bash
git clone https://github.com/Karan-hash/fastapi-fullstack-webapp.git
cd fastapi-fullstack-webapp
```

---

## 3. Initialize the project (Only required once)

```bash
uv init
```

---

## 4. Install FastAPI

```bash
uv add "fastapi[standard]"
```

This command will automatically:

- Create a `.venv` virtual environment
- Install FastAPI
- Install Uvicorn
- Generate `uv.lock`
- Update `pyproject.toml`

---

## 5. Activate the virtual environment

```bash
source .venv/bin/activate
```

---

## 6. Run the application

```bash
uv run fastapi dev main.py
```

Application URLs:

- http://127.0.0.1:8000
- Swagger Docs: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

---

## Installing dependencies after cloning

If the project already contains a `pyproject.toml` and `uv.lock`, simply run:

```bash
uv sync
```

---

# Setup using `pip`

## 1. Create a virtual environment

```bash
python3 -m venv .venv
```

---

## 2. Activate it

macOS / Linux

```bash
source .venv/bin/activate
```

Windows

```powershell
.venv\Scripts\activate
```

---

## 3. Upgrade pip

```bash
python -m pip install --upgrade pip
```

---

## 4. Install FastAPI

```bash
pip install "fastapi[standard]"
```

---

## 5. Run the application

```bash
fastapi dev main.py
```

or

```bash
uvicorn main:app --reload
```

---

## Deactivate the virtual environment

```bash
deactivate
```

---

# .gitignore

```gitignore
.venv/
.myenv/
__pycache__/
*.pyc
.env
```

---

# Useful Commands

Check Python version

```bash
python3 --version
```

Check uv version

```bash
uv --version
```

List installed packages

```bash
uv pip list
```

Update dependencies

```bash
uv sync
```
## Run the Application

```bash
cd src/fastapi_fullstack_webapp
uv run fastapi dev main.py
```

Once the server starts, open:

- http://127.0.0.1:8000
- http://127.0.0.1:8000/docs
- http://127.0.0.1:8000/redoc