# Taskly — Task / To-Do Manager

A task management app with a responsive web interface and a **Python, FastAPI and SQLite** backend. Manage tasks in the browser or use the REST API for filtering, search, sorting, pagination and summary statistics.

## Features

- Full CRUD for tasks (`POST`, `GET`, `PATCH`, `DELETE`)
- Fields: title, description, priority (low/medium/high), status (pending/in_progress/completed), due date
- Filter by status, priority and overdue; search by text; sort; paginate
- `GET /tasks/stats` summary (counts by status/priority, overdue count)
- Taskly web interface with task creation, editing, completion, deletion, search, status filters, overdue view and sorting
- Input validation (blank titles, invalid enums, past due dates) and proper 404 handling
- Persistent storage in SQLite (`todo.db`, created automatically)
- Auto-generated interactive docs (Swagger UI)
- Automated tests with pytest

## Prerequisites

- Python **3.10 or newer** (check with `python --version`)
- pip
- Git (optional, for cloning)

## Installation

```bash
# 1. Get the code
git clone <your-repo-url>
cd todo-manager

# 2. Create and activate a virtual environment
python -m venv venv

# Windows (PowerShell / CMD)
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt
```

> On macOS/Linux use `python3` instead of `python` if needed.

## Run the server

```bash
uvicorn app.main:app --reload
```

- API: http://127.0.0.1:8000
- **Task manager website: http://127.0.0.1:8000/**
- **Interactive docs (Swagger UI): http://127.0.0.1:8000/docs**
- Alternative docs (ReDoc): http://127.0.0.1:8000/redoc

The database file `todo.db` is created automatically on first run.

### Using the Taskly website

Open http://127.0.0.1:8000/ after starting the server. Changes are saved to SQLite through the API.

- Select **New task** to create a task with an optional description, priority, status and due date. Use **Edit**, the completion checkbox or **Delete** to manage tasks.
- Search by task title or description, or filter by **To do**, **In progress**, **Completed** or **Overdue**.
- Choose a sort field (**Recently added**, **Due date**, **Priority** or **Task name**) and an ascending or descending order.
- Select the **All tasks**, **In progress**, **Completed** or **Overdue** dashboard card to filter the task list to that summary.
- Use the **Dark mode / Light mode** control in the header to switch themes. The app follows your device preference on first visit and remembers your choice in this browser.
- The layout adapts to mobile screens. The website and API docs are available locally while the server is running.

### Optional: load dummy sample data

```bash
python seed.py
```

## API endpoints

| Method | Endpoint                    | Purpose                                        |
| ------ | --------------------------- | ---------------------------------------------- |
| POST   | `/tasks`                    | Create a task                                  |
| GET    | `/tasks`                    | List tasks (filter / search / sort / paginate) |
| GET    | `/tasks/stats`              | Summary statistics                             |
| GET    | `/tasks/{task_id}`          | View one task                                  |
| PATCH  | `/tasks/{task_id}`          | Update fields of a task                        |
| POST   | `/tasks/{task_id}/complete` | Mark a task completed                          |
| DELETE | `/tasks/{task_id}`          | Delete a task                                  |

### List query parameters

`status`, `priority`, `q` (search), `overdue` (true/false), `sort_by` (created_at, due_date, title, priority), `order` (asc/desc), `limit` (1-100, default 20), `offset`.

## Testing the API

### Option 1: Swagger UI (easiest)

Open http://127.0.0.1:8000/docs, expand an endpoint, click **Try it out**, then **Execute**.

### Option 2: curl

```bash
# Create (use a future due date, format YYYY-MM-DD)
curl -X POST http://127.0.0.1:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{"title":"Finish project","description":"FastAPI + SQLite","priority":"high","due_date":"2026-10-26"}'

# List all / filter / search
curl http://127.0.0.1:8000/tasks
curl "http://127.0.0.1:8000/tasks?status=pending&priority=high"
curl "http://127.0.0.1:8000/tasks?q=project&sort_by=due_date&order=asc"
curl "http://127.0.0.1:8000/tasks?overdue=true"

# Get one
curl http://127.0.0.1:8000/tasks/1

# Update
curl -X PATCH http://127.0.0.1:8000/tasks/1 \
  -H "Content-Type: application/json" \
  -d '{"status":"in_progress"}'

# Mark complete
curl -X POST http://127.0.0.1:8000/tasks/1/complete

# Stats
curl http://127.0.0.1:8000/tasks/stats

# Delete
curl -X DELETE http://127.0.0.1:8000/tasks/1
```

> Windows CMD users: use double quotes and escape inner quotes (`\"`), or just use Swagger UI / PowerShell.

### Error handling examples

| Request                                  | Result                   |
| ---------------------------------------- | ------------------------ |
| `GET /tasks/999`                         | `404 Task 999 not found` |
| `POST /tasks` with blank title           | `422 Validation error`   |
| `POST /tasks` with a past `due_date`     | `422 Validation error`   |
| `PATCH /tasks/1` with `"status":"bogus"` | `422 Validation error`   |

## Run automated tests

```bash
pytest -v
```

Tests use an in-memory database, so your real `todo.db` is never touched.

## Project structure

```
todo-manager/
├── app/
│   ├── main.py          # FastAPI app and startup
│   ├── database.py      # SQLite engine and session
│   ├── models.py        # SQLAlchemy table definition
│   ├── schemas.py       # Pydantic validation / response models
│   ├── crud.py          # Database operations
│   └── routers/
│       └── tasks.py     # API endpoints
├── tests/
│   ├── conftest.py
│   └── test_tasks.py
├── seed.py              # Dummy data loader
├── requirements.txt
├── .gitignore
└── README.md
```

## Architecture notes

- **Routers** handle HTTP only; **crud.py** handles database logic; **schemas** validate input and shape output; **models** define the table.
- `PATCH` uses `exclude_unset`, so only the fields you send are changed.
- `is_overdue` is computed at response time, so it never goes stale.
- Only dummy data is used; no secrets or real personal data are stored.

## Troubleshooting

- **`uvicorn` not recognized:** activate the virtual environment first, or run `python -m uvicorn app.main:app --reload`.
- **`ModuleNotFoundError: app`:** run commands from the project root (the `todo-manager` folder).
- **Port 8000 busy:** use `uvicorn app.main:app --reload --port 8001`.
- **Reset the data:** stop the server and delete `todo.db`.
