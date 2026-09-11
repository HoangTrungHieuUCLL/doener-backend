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
