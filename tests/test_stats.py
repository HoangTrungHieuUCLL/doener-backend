from datetime import date, timedelta


def _get_exercise_id(client, headers, key="a_goblet_squat"):
    exercises = client.get("/exercises", headers=headers).json()
    return next(e["id"] for e in exercises if e["key"] == key)


def test_finish_session_duration_override_is_clamped(client, auth_headers):
    headers = auth_headers()
    session_id = client.post("/sessions", json={"workout_key": "A"}, headers=headers).json()["id"]

    # A duration far larger than the real wall-clock elapsed must be clamped down.
    resp = client.post(
        f"/sessions/{session_id}/finish",
        json={"duration_sec": 999_999},
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert 0 <= body["duration_sec"] < 999_999

    # A negative duration (e.g. a client bug) must never produce a negative record.
    session_id_2 = client.post("/sessions", json={"workout_key": "A"}, headers=headers).json()["id"]
    resp2 = client.post(
        f"/sessions/{session_id_2}/finish",
        json={"duration_sec": -5},
        headers=headers,
    )
    assert resp2.status_code == 200
    assert resp2.json()["duration_sec"] == 0


def test_last_sets_returns_most_recent_per_exercise(client, auth_headers):
    headers = auth_headers()
    exercise_id = _get_exercise_id(client, headers)
    session_id = client.post("/sessions", json={"workout_key": "A"}, headers=headers).json()["id"]

    client.post(
        f"/sessions/{session_id}/sets",
        json={"exercise_id": exercise_id, "weight_kg": 40, "reps": 8},
        headers=headers,
    )
    client.post(
        f"/sessions/{session_id}/sets",
        json={"exercise_id": exercise_id, "weight_kg": 42.5, "reps": 6},
        headers=headers,
    )

    resp = client.get("/stats/last-sets", headers=headers)
    assert resp.status_code == 200
    row = next(r for r in resp.json() if r["exercise_id"] == exercise_id)
    assert row["weight_kg"] == 42.5
    assert row["reps"] == 6


def test_exercise_progress_returns_ordered_points(client, auth_headers):
    headers = auth_headers()
    exercise_id = _get_exercise_id(client, headers)
    session_id = client.post("/sessions", json={"workout_key": "A"}, headers=headers).json()["id"]
    client.post(
        f"/sessions/{session_id}/sets",
        json={"exercise_id": exercise_id, "weight_kg": 40, "reps": 8},
        headers=headers,
    )

    resp = client.get(f"/stats/exercise/{exercise_id}/progress", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    assert body[0]["weight_kg"] == 40
    assert body[0]["reps"] == 8


def test_consistency_merges_plan_and_sessions(client, auth_headers):
    headers = auth_headers()
    today = date.today().isoformat()
    tomorrow = (date.today() + timedelta(days=1)).isoformat()

    client.post("/plan", json={"date": today, "workout_key": "A"}, headers=headers)
    client.post("/sessions", json={"workout_key": "A"}, headers=headers)

    resp = client.get(
        "/stats/consistency",
        params={"from": today, "to": tomorrow},
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    today_row = next(r for r in body if r["date"] == today)
    assert today_row["planned_key"] == "A"
    # session isn't finished yet, so done_key stays unset for today
    assert today_row["done_key"] is None


def _log(client, headers, session_id, exercise_id, weight, reps):
    return client.post(
        f"/sessions/{session_id}/sets",
        json={"exercise_id": exercise_id, "weight_kg": weight, "reps": reps},
        headers=headers,
    )


def _backdate(db, session_id, days_ago):
    """Shift a session into the past -- /sessions always stamps today."""
    from datetime import datetime, timedelta, timezone

    from app.models import WorkoutSession

    ws = db.get(WorkoutSession, session_id)
    ws.date = date.today() - timedelta(days=days_ago)
    ws.started_at = datetime.now(timezone.utc) - timedelta(days=days_ago)
    db.add(ws)
    db.commit()


def test_last_sets_returns_every_set_of_the_last_session(client, auth_headers):
    headers = auth_headers()
    exercise_id = _get_exercise_id(client, headers)
    session_id = client.post("/sessions", json={"workout_key": "A"}, headers=headers).json()["id"]

    _log(client, headers, session_id, exercise_id, 40, 10)
    _log(client, headers, session_id, exercise_id, 40, 9)
    _log(client, headers, session_id, exercise_id, 37.5, 8)

    row = next(
        r
        for r in client.get("/stats/last-sets", headers=headers).json()
        if r["exercise_id"] == exercise_id
    )

    assert row["session_id"] == session_id
    assert row["date"] == date.today().isoformat()
    assert [(s["set_number"], s["weight_kg"], s["reps"]) for s in row["sets"]] == [
        (1, 40, 10),
        (2, 40, 9),
        (3, 37.5, 8),
    ]
    # The flat fields stay the final set, which is what the client seeds with.
    assert (row["weight_kg"], row["reps"]) == (37.5, 8)


def test_last_sets_excludes_the_named_session(client, auth_headers, session):
    headers = auth_headers()
    exercise_id = _get_exercise_id(client, headers)

    previous = client.post("/sessions", json={"workout_key": "A"}, headers=headers).json()["id"]
    _log(client, headers, previous, exercise_id, 40, 10)
    _backdate(session, previous, days_ago=3)

    active = client.post("/sessions", json={"workout_key": "A"}, headers=headers).json()["id"]
    _log(client, headers, active, exercise_id, 45, 6)

    def row_for(params):
        body = client.get("/stats/last-sets", params=params, headers=headers).json()
        return next(r for r in body if r["exercise_id"] == exercise_id)

    # Unfiltered, "most recent" is the set just logged in the active session.
    assert row_for({})["weight_kg"] == 45

    # Excluding it, "last time" falls back to the genuinely previous session.
    excluded = row_for({"exclude_session_id": active})
    assert excluded["weight_kg"] == 40
    assert excluded["session_id"] == previous
    assert [p["session_id"] for p in excluded["trend"]] == [previous]


def test_last_sets_trend_is_chronological_and_capped(client, auth_headers, session):
    from app.routers.stats import TREND_LIMIT

    headers = auth_headers()
    exercise_id = _get_exercise_id(client, headers)

    # One session per day, heaviest set climbing by 1kg each time.
    total = TREND_LIMIT + 3
    for n in range(total):
        sid = client.post("/sessions", json={"workout_key": "A"}, headers=headers).json()["id"]
        _log(client, headers, sid, exercise_id, 20 + n, 8)
        _log(client, headers, sid, exercise_id, 15 + n, 8)  # lighter: must not win
        _backdate(session, sid, days_ago=total - n)

    trend = next(
        r
        for r in client.get("/stats/last-sets", headers=headers).json()
        if r["exercise_id"] == exercise_id
    )["trend"]

    assert len(trend) == TREND_LIMIT
    # Oldest-first, and each point is that session's top weight.
    assert [p["top_weight_kg"] for p in trend] == [
        20 + n for n in range(total - TREND_LIMIT, total)
    ]
    assert [p["date"] for p in trend] == sorted(p["date"] for p in trend)


def test_last_sets_omits_exercises_never_logged(client, auth_headers):
    headers = auth_headers()
    exercise_id = _get_exercise_id(client, headers)
    session_id = client.post("/sessions", json={"workout_key": "A"}, headers=headers).json()["id"]
    _log(client, headers, session_id, exercise_id, 40, 10)

    body = client.get("/stats/last-sets", headers=headers).json()
    assert [r["exercise_id"] for r in body] == [exercise_id]


def test_last_sets_ignores_other_users_sessions(client, auth_headers):
    alice = auth_headers()
    bob = auth_headers(username="bob", password="hunter2", display_name="Bob")
    exercise_id = _get_exercise_id(client, alice)

    alice_session = client.post("/sessions", json={"workout_key": "A"}, headers=alice).json()["id"]
    _log(client, alice, alice_session, exercise_id, 40, 10)

    assert client.get("/stats/last-sets", headers=bob).json() == []
