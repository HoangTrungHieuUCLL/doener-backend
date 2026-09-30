from datetime import date


def test_delete_plan_removes_it(client, auth_headers):
    headers = auth_headers()
    today = date.today().isoformat()

    client.post("/plan", json={"date": today, "workout_key": "A"}, headers=headers)
    assert client.get("/plan", params={"from": today, "to": today}, headers=headers).json() == [
        {"id": 1, "date": today, "workout_key": "A"}
    ]

    resp = client.delete("/plan", params={"date": today}, headers=headers)
    assert resp.status_code == 204
    assert client.get("/plan", params={"from": today, "to": today}, headers=headers).json() == []


def test_delete_plan_on_unplanned_date_is_a_noop(client, auth_headers):
    headers = auth_headers()
    resp = client.delete("/plan", params={"date": "2030-01-01"}, headers=headers)
    assert resp.status_code == 204


def _keys(client, headers, day):
    return [p["workout_key"] for p in client.get("/plan", params={"from": day, "to": day}, headers=headers).json()]


def test_plan_replaces_by_default_and_append_adds_a_second_workout(client, auth_headers):
    headers = auth_headers()
    today = date.today().isoformat()

    client.post("/plan", json={"date": today, "workout_key": "A"}, headers=headers)
    client.post("/plan", json={"date": today, "workout_key": "B"}, headers=headers)
    assert _keys(client, headers, today) == ["B"]

    client.post("/plan", json={"date": today, "workout_key": "cardio", "append": True}, headers=headers)
    assert _keys(client, headers, today) == ["B", "cardio"]

    # A plain (non-append) plan makes it the day's only workout again.
    client.post("/plan", json={"date": today, "workout_key": "C"}, headers=headers)
    assert _keys(client, headers, today) == ["C"]


def test_delete_plan_removes_every_workout_that_day(client, auth_headers):
    headers = auth_headers()
    today = date.today().isoformat()
    client.post("/plan", json={"date": today, "workout_key": "A"}, headers=headers)
    client.post("/plan", json={"date": today, "workout_key": "B", "append": True}, headers=headers)

    client.delete("/plan", params={"date": today}, headers=headers)
    assert _keys(client, headers, today) == []
