from datetime import date, timedelta

from app.models import Priority, Status, Task

FUTURE = (date.today() + timedelta(days=5)).isoformat()


def make(client, **overrides):
    payload = {"title": "Sample task", "priority": "medium"}
    payload.update(overrides)
    return client.post("/tasks", json=payload)


def test_homepage_serves_task_manager(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Your day, in focus." in response.text
    assert 'id="sort-by"' in response.text
    assert 'data-filter="overdue"' in response.text
    assert 'data-summary-filter="in_progress"' in response.text
    assert 'id="theme-toggle"' in response.text
    assert 'data-theme="dark"' in response.text


def test_create_task(client):
    r = make(client, title="  Buy milk  ", due_date=FUTURE)
    assert r.status_code == 201
    body = r.json()
    assert body["id"] == 1
    assert body["title"] == "Buy milk"  # whitespace trimmed
    assert body["status"] == "pending"
    assert body["is_overdue"] is False


def test_create_validation_errors(client):
    assert make(client, title="   ").status_code == 422
    assert make(client, title="x" * 101).status_code == 422
    assert make(client, priority="urgent").status_code == 422
    assert make(client, due_date="2000-01-01").status_code == 422
    assert make(client, due_date="not-a-date").status_code == 422


def test_get_task_and_404(client):
    make(client)
    assert client.get("/tasks/1").status_code == 200
    r = client.get("/tasks/999")
    assert r.status_code == 404
    assert "not found" in r.json()["detail"]


def test_list_filter_search_sort_paginate(client):
    make(client, title="Alpha", priority="low")
    make(client, title="Beta report", priority="high", status="in_progress")
    make(client, title="Gamma", priority="high", description="contains report text")

    assert client.get("/tasks").json()["total"] == 3
    assert client.get("/tasks?priority=high").json()["total"] == 2
    assert client.get("/tasks?status=in_progress").json()["total"] == 1
    assert client.get("/tasks?q=report").json()["total"] == 2

    titles = [t["title"] for t in client.get("/tasks?sort_by=title&order=asc").json()["items"]]
    assert titles == ["Alpha", "Beta report", "Gamma"]

    first = client.get("/tasks?sort_by=priority&order=desc").json()["items"][0]
    assert first["priority"] == "high"

    page = client.get("/tasks?limit=2&offset=2").json()
    assert page["total"] == 3 and len(page["items"]) == 1


def test_update_task(client):
    make(client)
    r = client.patch("/tasks/1", json={"status": "in_progress", "priority": "high"})
    assert r.status_code == 200
    assert r.json()["status"] == "in_progress"
    assert r.json()["title"] == "Sample task"  # untouched
    assert client.patch("/tasks/1", json={"status": "bogus"}).status_code == 422
    assert client.patch("/tasks/999", json={"title": "x"}).status_code == 404


def test_complete_task(client):
    make(client)
    r = client.post("/tasks/1/complete")
    assert r.status_code == 200 and r.json()["status"] == "completed"


def test_delete_task(client):
    make(client)
    assert client.delete("/tasks/1").status_code == 204
    assert client.get("/tasks/1").status_code == 404
    assert client.delete("/tasks/1").status_code == 404


def test_overdue_and_stats(client, db_session):
    # Past due dates are rejected by the API, so insert directly for this test.
    yesterday = date.today() - timedelta(days=1)
    db_session.add_all([
        Task(title="Late", priority=Priority.high, status=Status.pending, due_date=yesterday),
        Task(title="Late but done", priority=Priority.low, status=Status.completed, due_date=yesterday),
    ])
    db_session.commit()
    make(client, title="On time", due_date=FUTURE)

    overdue = client.get("/tasks?overdue=true").json()
    assert overdue["total"] == 1
    assert overdue["items"][0]["title"] == "Late"
    assert overdue["items"][0]["is_overdue"] is True

    stats = client.get("/tasks/stats").json()
    assert stats["total"] == 3
    assert stats["overdue"] == 1
    assert stats["by_status"]["completed"] == 1
    assert stats["by_priority"]["high"] == 1
