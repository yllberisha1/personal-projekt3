# Fitness Web App (FastAPI + Streamlit + SQLite3)

Complete full-stack fitness tracker built with a strict stack:
- Python
- FastAPI + Pydantic + Uvicorn
- Streamlit frontend
- sqlite3 (no ORM)
- Manual token authentication (no JWT libs)
- OOP services and managers

## Folder Structure

```text
backend/
  __init__.py
  main.py
  init_db.py
  database.py
  models.py
  schemas.py
  auth.py
  services/
    __init__.py
    user_service.py
    workout_service.py
    nutrition_service.py
  routers/
    __init__.py
    user_router.py
    workout_router.py
    nutrition_router.py
frontend/
  app.py
  api_client.py
  pages/
    __init__.py
    login.py
    dashboard.py
    workouts.py
    nutrition.py
    progress.py
requirements.txt
README.md
```

## Setup and Run

1. Create and activate virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Initialize database:

```powershell
cd backend
python init_db.py
```

4. Run backend API:

```powershell
uvicorn main:app --reload
```

5. Run Streamlit frontend (new terminal):

```powershell
cd frontend
streamlit run app.py
```

## Authentication

- Register with username/email/password
- Password stored as SHA-256 hash
- Login returns token
- Send token in protected requests:

```http
Authorization: Bearer <token>
```

- Logout invalidates token in DB

## Main API Endpoints

### Auth
- `POST /register`
- `POST /login`
- `POST /logout`

### Workouts
- `GET /workouts`
- `POST /workouts`
- `PUT /workouts/{id}`
- `DELETE /workouts/{id}`

### Nutrition
- `GET /meals`
- `POST /meals`
- `PUT /meals/{id}`
- `DELETE /meals/{id}`

### Progress / User
- `GET /dashboard`
- `GET /weights`
- `POST /weights`
- `PUT /weights/{id}`
- `DELETE /weights/{id}`

## Example Requests

### Register

```bash
curl -X POST http://127.0.0.1:8000/register \
  -H "Content-Type: application/json" \
  -d '{"username":"fit_user","email":"fit_user@example.com","password":"StrongPass123"}'
```

### Login

```bash
curl -X POST http://127.0.0.1:8000/login \
  -H "Content-Type: application/json" \
  -d '{"username_or_email":"fit_user","password":"StrongPass123"}'
```

### Create Workout (Protected)

```bash
curl -X POST http://127.0.0.1:8000/workouts \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"workout_name":"Running","duration_minutes":40,"calories_burned":420,"date":"2026-02-14"}'
```

### Get Meals (Protected)

```bash
curl -X GET http://127.0.0.1:8000/meals \
  -H "Authorization: Bearer <token>"
```
