def _get_exercise_id(client, headers, key="a_goblet_squat"):
    exercises = client.get("/exercises", headers=headers).json()
    return next(e["id"] for e in exercises if e["key"] == key)


def test_finish_session_computes_total_volume_kg(client, auth_headers):
    headers = auth_headers()
    exercise_id = _get_exercise_id(client, headers, "a_goblet_squat")

    create_resp = client.post("/sessions", json={"workout_key": "A"}, headers=headers)
    assert create_resp.status_code == 201
    session_id = create_resp.json()["id"]
    assert create_resp.json()["total_volume_kg"] is None
    assert create_resp.json()["finished_at"] is None

    # weight-based sets: contribute weight * reps
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

    # a time-based set (no weight/reps) should contribute 0 to volume
    plank_id = _get_exercise_id(client, headers, "a_forearm_plank")
    client.post(
        f"/sessions/{session_id}/sets",
        json={"exercise_id": plank_id, "duration_sec": 30},
        headers=headers,
    )

    finish_resp = client.post(f"/sessions/{session_id}/finish", headers=headers)
    assert finish_resp.status_code == 200
    body = finish_resp.json()
    assert body["finished_at"] is not None
    assert body["duration_sec"] is not None and body["duration_sec"] >= 0

    expected_volume = 40 * 8 + 42.5 * 6
    assert body["total_volume_kg"] == expected_volume


def test_finish_already_finished_session_is_409(client, auth_headers):
    headers = auth_headers()
    session_id = client.post("/sessions", json={"workout_key": "A"}, headers=headers).json()["id"]
    first = client.post(f"/sessions/{session_id}/finish", headers=headers)
    assert first.status_code == 200
    second = client.post(f"/sessions/{session_id}/finish", headers=headers)
    assert second.status_code == 409


def test_set_number_increments_per_exercise(client, auth_headers):
    headers = auth_headers()
    exercise_id = _get_exercise_id(client, headers)
    session_id = client.post("/sessions", json={"workout_key": "A"}, headers=headers).json()["id"]

    r1 = client.post(
        f"/sessions/{session_id}/sets",
        json={"exercise_id": exercise_id, "weight_kg": 20, "reps": 8},
        headers=headers,
    )
    r2 = client.post(
        f"/sessions/{session_id}/sets",
        json={"exercise_id": exercise_id, "weight_kg": 20, "reps": 8},
        headers=headers,
    )
    assert r1.json()["set_number"] == 1
    assert r2.json()["set_number"] == 2


def test_new_max_weight_sets_pr_flag_true(client, auth_headers):
    headers = auth_headers()
    exercise_id = _get_exercise_id(client, headers)
    session_id = client.post("/sessions", json={"workout_key": "A"}, headers=headers).json()["id"]

    resp = client.post(
        f"/sessions/{session_id}/sets",
        json={"exercise_id": exercise_id, "weight_kg": 50, "reps": 5},
        headers=headers,
    )
    assert resp.status_code == 201
    assert resp.json()["is_new_pr"] is True

    prs = client.get("/stats/prs", headers=headers).json()
    assert len(prs) == 1
    assert prs[0]["best_weight_kg"] == 50


def test_non_max_weight_does_not_flag_pr(client, auth_headers):
    headers = auth_headers()
    exercise_id = _get_exercise_id(client, headers)
    session_id = client.post("/sessions", json={"workout_key": "A"}, headers=headers).json()["id"]

    first = client.post(
        f"/sessions/{session_id}/sets",
        json={"exercise_id": exercise_id, "weight_kg": 50, "reps": 5},
        headers=headers,
    )
    assert first.json()["is_new_pr"] is True

    second = client.post(
        f"/sessions/{session_id}/sets",
        json={"exercise_id": exercise_id, "weight_kg": 45, "reps": 5},
        headers=headers,
    )
    assert second.status_code == 201
    assert second.json()["is_new_pr"] is False

    prs = client.get("/stats/prs", headers=headers).json()
    assert len(prs) == 1
    assert prs[0]["best_weight_kg"] == 50


def test_add_set_to_finished_session_is_409(client, auth_headers):
    headers = auth_headers()
    exercise_id = _get_exercise_id(client, headers)
    session_id = client.post("/sessions", json={"workout_key": "A"}, headers=headers).json()["id"]
    client.post(f"/sessions/{session_id}/finish", headers=headers)

    resp = client.post(
        f"/sessions/{session_id}/sets",
        json={"exercise_id": exercise_id, "weight_kg": 10, "reps": 5},
        headers=headers,
    )
    assert resp.status_code == 409


def test_session_not_owned_by_caller_is_404(client, auth_headers):
    headers_a = auth_headers(username="userA", password="pw12345", display_name="A")
    headers_b = auth_headers(username="userB", password="pw12345", display_name="B")

    session_id = client.post(
        "/sessions", json={"workout_key": "A"}, headers=headers_a
    ).json()["id"]

    resp = client.get(f"/sessions/{session_id}", headers=headers_b)
    assert resp.status_code == 404


def test_together_endpoint_lists_all_users(client, auth_headers):
    auth_headers(username="together1", password="pw12345", display_name="T1")
    auth_headers(username="together2", password="pw12345", display_name="T2")
    headers = auth_headers(username="together3", password="pw12345", display_name="T3")

    resp = client.get("/together", headers=headers)
    assert resp.status_code == 200
    usernames = {entry["username"] for entry in resp.json()}
    assert {"together1", "together2", "together3"}.issubset(usernames)
