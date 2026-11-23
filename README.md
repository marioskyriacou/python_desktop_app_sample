# Desktop App Example

PySide6 UI → FastAPI → SQLAlchemy → PostgreSQL, with a login and one screen to add and list data.

```
desktop_app_example/
├── backend/
│   ├── config.py        settings from .env (DB URL, secret key)
│   ├── database.py      engine, session, Base
│   ├── models.py        tables: users, items
│   ├── schemas.py       request/response shapes (Pydantic)
│   ├── security.py      password hashing + login tokens (JWT)
│   ├── main.py          API endpoints
│   └── create_user.py   creates the login user
├── frontend/
│   ├── api_client.py    the only place that calls the API
│   └── main.py          login page + items page
├── requirements.txt
└── .env.example
```

## 1. Create the PostgreSQL database

Open **psql** (or pgAdmin's Query Tool) as the `postgres` user and run:

```sql
CREATE USER app_user WITH PASSWORD 'app_password';
CREATE DATABASE app_db OWNER app_user;
```

The tables are created automatically when the API starts.

## 2. Install Python packages (Python 3.10+)

Run these from inside the `desktop_app_example` folder.

**Windows (PowerShell)**
```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

**macOS / Linux**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Then edit `.env`: check `DATABASE_URL` and set your own `SECRET_KEY`.

## 3. Create the login user

```bash
python -m backend.create_user
```

It asks for a username and password. Run it again with the same username to reset the password.

## 4. Start the API (terminal 1)

```bash
uvicorn backend.main:app --reload
```

Open http://127.0.0.1:8000/docs to test the API in the browser. Click **Authorize** and log in there first.

## 5. Start the desktop app (terminal 2, venv activated)

```bash
python -m frontend.main
```

Log in, add some items, and they're saved in PostgreSQL. To point the UI at another server, set `API_URL` (e.g. `API_URL=http://192.168.1.50:8000`).

## How a request flows

1. **Login:** the UI sends the username and password to `POST /auth/login`. The API checks the bcrypt hash and returns a token (JWT).
2. The UI stores the token in memory and sends it as `Authorization: Bearer <token>` on every request.
3. **Add item:** `POST /items` → `get_current_user` validates the token → the item is saved with `owner_id` = that user.
4. When the token expires (60 min by default), the API returns 401 and the UI goes back to the login page.

## Next steps when you grow this

- **Alembic** for database migrations, instead of `create_all`.
- **Run API calls in a background thread** (`QThreadPool`) so the UI never freezes on a slow network.
- **Split requirements** into backend and frontend, so the server doesn't need PySide6.
- **HTTPS** if the API runs on a server other than your own machine.
- **Tests** with `pytest` + FastAPI's `TestClient`.
