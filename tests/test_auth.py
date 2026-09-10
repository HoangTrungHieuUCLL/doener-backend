def test_signup_then_login_flow(client):
    signup_resp = client.post(
        "/auth/signup",
        json={"username": "bob", "password": "s3cret!", "display_name": "Bob"},
    )
    assert signup_resp.status_code == 201
    body = signup_resp.json()
    assert body["token_type"] == "bearer"
    assert body["user"]["username"] == "bob"
    assert body["user"]["display_name"] == "Bob"
    assert "access_token" in body and body["access_token"]

    login_resp = client.post("/auth/login", json={"username": "bob", "password": "s3cret!"})
    assert login_resp.status_code == 200
    login_body = login_resp.json()
    assert login_body["user"]["username"] == "bob"

    me_resp = client.get(
        "/auth/me", headers={"Authorization": f"Bearer {login_body['access_token']}"}
    )
    assert me_resp.status_code == 200
    assert me_resp.json()["username"] == "bob"


def test_signup_duplicate_username_conflicts(client):
    client.post(
        "/auth/signup",
        json={"username": "carol", "password": "pw12345", "display_name": "Carol"},
    )
    resp = client.post(
        "/auth/signup",
        json={"username": "carol", "password": "other", "display_name": "Carol 2"},
    )
    assert resp.status_code == 409


def test_login_bad_credentials_is_401(client):
    client.post(
        "/auth/signup",
        json={"username": "dave", "password": "correct-pw", "display_name": "Dave"},
    )
    resp = client.post("/auth/login", json={"username": "dave", "password": "wrong-pw"})
    assert resp.status_code == 401


def test_protected_endpoint_rejects_missing_token(client):
    resp = client.get("/exercises")
    assert resp.status_code == 401


def test_protected_endpoint_rejects_bad_token(client):
    resp = client.get("/exercises", headers={"Authorization": "Bearer not-a-real-token"})
    assert resp.status_code == 401


def test_protected_endpoint_accepts_valid_token(client, auth_headers):
    headers = auth_headers()
    resp = client.get("/exercises", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()) > 0
