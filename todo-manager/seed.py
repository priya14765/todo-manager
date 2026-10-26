"""Fill the database with dummy tasks for demos:  python seed.py"""
from datetime import date, timedelta

from app import models
from app.database import Base, SessionLocal, engine
from app.models import Priority, Status, Task

Base.metadata.create_all(bind=engine)
today = date.today()

samples = [
    ("Finish internship mini-project", "Build the FastAPI + SQLite app", Priority.high, Status.in_progress, today + timedelta(days=2)),
    ("Complete Week 3 assessment", None, Priority.high, Status.pending, today + timedelta(days=1)),
    ("Write README", "Installation and API testing steps", Priority.medium, Status.pending, today + timedelta(days=3)),
    ("Push code to GitHub", None, Priority.medium, Status.pending, today + timedelta(days=3)),
    ("Revise Python basics", "Functions, OOP, file handling", Priority.low, Status.completed, today - timedelta(days=4)),
    ("Submit last week's worksheet", None, Priority.medium, Status.pending, today - timedelta(days=2)),
]

with SessionLocal() as db:
    if db.query(Task).count() == 0:
        db.add_all(
            Task(title=t, description=d, priority=p, status=s, due_date=due)
            for t, d, p, s, due in samples
        )
        db.commit()
        print(f"Inserted {len(samples)} sample tasks.")
    else:
        print("Database already has tasks; nothing inserted.")
