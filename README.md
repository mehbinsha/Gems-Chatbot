# Chatbot + Result Analyzer (Flask + SQLite)

This project combines:
- A chatbot API/UI with DB-managed intents (rule-based or optional ML fallback)
- An admin panel (JWT protected) for intent and recommendation rule management
- A marksheet OCR analyzer that extracts subject marks and suggests courses

## Tech Stack

- Backend: Flask, Flask-SQLAlchemy, Flask-Migrate, Flask-JWT-Extended
- Database: SQLite (default), configurable via `DATABASE_URL`
- OCR: Tesseract + `pytesseract` + Pillow
- Frontend: static HTML/CSS/JS served by Flask

## Project Structure

```text
.
├─ backend/
│  ├─ __init__.py
│  ├─ app.py
│  ├─ config.py
│  ├─ extensions.py
│  ├─ models.py
│  ├─ seed.py
│  ├─ migrations/
│  │  ├─ 001_create_tables.sql
│  │  ├─ 002_seed_data.sql
│  │  └─ 003_result_analysis_features.sql
│  ├─ nlp/
│  │  ├─ intents.json
│  │  ├─ ml_engine.py
│  │  └─ rule_based.py
│  ├─ routes/
│  │  ├─ admin_routes.py
│  │  ├─ chat_routes.py
│  │  └─ result_routes.py
│  ├─ scripts/
│  │  └─ migrate.py
│  └─ services/
│     ├─ chat_service.py
│     ├─ intent_service.py
│     ├─ result_analysis_service.py
│     └─ result_preference_service.py
├─ frontend/
│  ├─ chat_interface.html
│  ├─ admin.html
│  ├─ result_upload.html
│  ├─ css/
│  └─ js/
├─ ml/
├─ .env.example
├─ requirements.txt
└─ run.py
```

## Local Setup (Windows)

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

### OCR Requirement (Tesseract)

Install Tesseract OCR and ensure `tesseract.exe` is available.

- Default path used by this app: `C:\Program Files\Tesseract-OCR\tesseract.exe`
- If installed elsewhere, add it to `PATH` or set `pytesseract.pytesseract.tesseract_cmd` accordingly.

Without Tesseract, `/analyze-result` will return:
- `500 {"error":"Tesseract OCR is not installed or not available in PATH."}`

## Environment Variables

See `.env.example`:
- `HOST`, `PORT`
- `USE_ML`
- `SECRET_KEY`, `JWT_SECRET_KEY`
- `DATABASE_URL`
- `DEFAULT_ADMIN_EMAIL`, `DEFAULT_ADMIN_PASSWORD`

## Database Migration

```bash
python backend/scripts/migrate.py
```

Applied migrations:
- `001_create_tables.sql`: core tables
- `002_seed_data.sql`: initial seed data
- `003_result_analysis_features.sql`: result preference + result history tables

Note: at startup, the app also runs `db.create_all()` and ensures default admin/intents are seeded.

## Run the App

```bash
python run.py
```

Default URLs:
- Chat UI: `http://127.0.0.1:5000/`
- Admin UI: `http://127.0.0.1:5000/admin`
- Result upload page: `http://127.0.0.1:5000/result_upload.html`

Default admin credentials:
- Email: `admin@example.com`
- Password: `Admin@12345`

## API Reference

### Chat

- `POST /chat`
  - JSON body:
    ```json
    { "message": "hello" }
    ```
  - Response:
    ```json
    { "response": "..." }
    ```

### Result Analysis (OCR)

- `POST /analyze-result`
  - Content-Type: `multipart/form-data`
  - Form field: `file` (`.jpg`, `.jpeg`, `.png`)
  - Success response:
    ```json
    {
      "name": "John Doe",
      "subjects": { "Maths": 92, "Physics": 88, "English": 90 },
      "total": 270,
      "average": 90.0,
      "strength_subjects": ["Maths", "English"],
      "recommended_courses": ["Computer Science", "Engineering", "Data Science"]
    }
    ```
  - Common errors:
    - `400`: missing file / invalid file type / invalid image
    - `422`: OCR worked but no valid subject marks parsed
    - `500`: Tesseract missing or unexpected processing failure

### Admin Auth (Public)

- `POST /api/admin/auth/login`
  - Body:
    ```json
    { "email": "admin@example.com", "password": "Admin@12345" }
    ```
  - Response:
    ```json
    { "token": "<jwt-token>", "email": "admin@example.com" }
    ```

### Admin APIs (JWT required)

Pass token as:
- `Authorization: Bearer <token>`

Endpoints:
- `GET /api/admin/intents`
- `POST /api/admin/intents`
- `POST /api/admin/intents/smart`
- `PUT /api/admin/intents/<intent_id>`
- `PUT /api/admin/intents/<intent_id>/smart`
- `DELETE /api/admin/intents/<intent_id>`
- `GET /api/admin/intents/<intent_id>/preview`
- `GET /api/admin/result-preferences`
- `PUT /api/admin/result-preferences`
- `GET /api/admin/result-history?limit=50`

## Result Recommendation Rules

Course recommendations are based on average marks and configurable rules stored in `result_analysis_preferences`.

Default rules are defined in:
- `backend/services/result_preference_service.py`

Rules can be updated via:
- `PUT /api/admin/result-preferences`

Detailed module documentation:
- `docs/result-analysis.md`

## Security Notes

- Passwords are hashed using Werkzeug (`generate_password_hash`, `check_password_hash`).
- Admin endpoints use JWT (`@jwt_required()`).
- Replace default `SECRET_KEY` and `JWT_SECRET_KEY` in production.
- Use HTTPS in production.
- Restrict CORS origins in production.
