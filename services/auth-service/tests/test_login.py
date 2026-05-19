from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_login_succeeds_with_known_user():
    r = client.post("/login", json={"username": "op-42", "password": "operator"})
    assert r.status_code == 201 or r.status_code == 200
    body = r.json()
    assert "token" in body
    assert "freeweigh.operator" in body["groups"]


def test_login_rejects_bad_password():
    r = client.post("/login", json={"username": "op-42", "password": "wrong"})
    assert r.status_code == 401
    assert r.json()["detail"] == "invalid_credentials"


def test_login_rejects_unknown_user():
    r = client.post("/login", json={"username": "ghost", "password": "anything"})
    assert r.status_code == 401
