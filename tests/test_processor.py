import pytest
from types import SimpleNamespace

from processor import process_message, ValidationError


class FakeDbClient:
    def __init__(self, ok=True):
        self.ok = ok
        self.calls = []

    def create_olympiad(self, payload):
        self.calls.append(payload)
        if self.ok:
            return SimpleNamespace(ok=True, status_code=200, message="created", response_json=None)
        return SimpleNamespace(ok=False, status_code=400, message="bad_request", response_json={"detail": "bad"})


def test_validation_missing_fields():
    with pytest.raises(ValidationError):
        process_message({"first_name": "A"}, FakeDbClient())


def test_process_message_success(monkeypatch):
    from parser import find_olymps as real_find

    def fake_find(full_name, dob):
        return [
            {"olymp_name": "O1", "profile": "P", "level": 1, "result": 1, "year": 2024},
            {"olymp_name": "O2", "profile": "P", "level": 2, "result": 0, "year": 2024},
        ]

    monkeypatch.setattr("parser.find_olymps", fake_find)
    data = {
        "first_name": "Ivan",
        "last_name": "Ivanov",
        "middle_name": "",
        "date_of_birth": "01-12-2000",
        "user_tg_id": "123",
    }
    db = FakeDbClient(ok=True)
    out = process_message(data, db)
    assert out["created"] == 2
    assert out["total"] == 2
    assert len(db.calls) == 2
    assert db.calls[0]["is_displayed"] is True
    assert db.calls[1]["is_displayed"] is True