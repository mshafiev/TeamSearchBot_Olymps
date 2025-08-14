from types import SimpleNamespace
from unittest.mock import patch, Mock

from http_client import HttpClient
from db_client import DatabaseApiClient


def make_db_client():
    http = HttpClient(base_url="http://db:8000", token=None)
    return DatabaseApiClient(http)


@patch("requests.Session.post")
def test_db_client_success(post_mock: Mock):
    post_mock.return_value = SimpleNamespace(status_code=200, headers={"Content-Type": "application/json"}, json=lambda: {"id": 1})
    client = make_db_client()
    res = client.create_olympiad({"name": "x"})
    assert res.ok
    assert res.status_code == 200


@patch("requests.Session.post")
def test_db_client_bad_request(post_mock: Mock):
    post_mock.return_value = SimpleNamespace(status_code=400, headers={"Content-Type": "application/json"}, json=lambda: {"detail": "bad"})
    client = make_db_client()
    res = client.create_olympiad({"name": "x"})
    assert not res.ok
    assert res.message == "bad_request"