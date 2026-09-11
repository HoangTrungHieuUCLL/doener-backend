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
