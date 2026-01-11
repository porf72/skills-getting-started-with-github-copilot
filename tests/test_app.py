import sys
from pathlib import Path
import copy

# Ensure src is importable when tests run from project root
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

import app as app_module
from fastapi.testclient import TestClient

# Keep a pristine copy of the in-memory activities and restore before each test
ORIGINAL = copy.deepcopy(app_module.activities)
client = TestClient(app_module.app)

import pytest

@pytest.fixture(autouse=True)
def reset_activities():
    app_module.activities = copy.deepcopy(ORIGINAL)
    yield


def test_get_activities():
    resp = client.get("/activities")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)
    assert "Chess Club" in data


def test_signup_and_unregister_flow():
    email = "testuser@example.com"
    activity = "Chess Club"

    # ensure not present
    resp = client.get("/activities")
    before = resp.json()[activity]["participants"]
    assert email not in before

    # signup
    resp = client.post(f"/activities/{activity}/signup?email={email}")
    assert resp.status_code == 200
    assert "Signed up" in resp.json().get("message", "")

    resp = client.get("/activities")
    assert email in resp.json()[activity]["participants"]

    # duplicate signup should return 400
    resp = client.post(f"/activities/{activity}/signup?email={email}")
    assert resp.status_code == 400

    # unregister
    resp = client.post(f"/activities/{activity}/unregister?email={email}")
    assert resp.status_code == 200
    assert "Unregistered" in resp.json().get("message", "")

    resp = client.get("/activities")
    assert email not in resp.json()[activity]["participants"]


def test_signup_unknown_activity():
    resp = client.post("/activities/NoSuchActivity/signup?email=a@b.com")
    assert resp.status_code == 404


def test_unregister_not_signed():
    # Unregister an email that is not signed up should return 400
    resp = client.post("/activities/Chess%20Club/unregister?email=nosuch@x.com")
    assert resp.status_code == 400
