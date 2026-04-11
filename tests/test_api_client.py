"""Tests for HTTP API client."""

import sys
import pytest
from unittest.mock import MagicMock, patch
from lib.api_client import APIClient, MOCK_TODOS, MOCK_EVENTS


class TestAPIClientInit:
    def test_default_values(self):
        c = APIClient("http://localhost:8080")
        assert c.server_url == "http://localhost:8080"
        assert c.timeout == 10
        assert c._use_mock is False

    def test_strips_trailing_slash(self):
        c = APIClient("http://localhost:8080/")
        assert c.server_url == "http://localhost:8080"

    def test_custom_timeout(self):
        c = APIClient("http://localhost", timeout=30)
        assert c.timeout == 30


class TestAPIClientGetTodos:
    def test_returns_mock_data_when_mock_mode(self):
        c = APIClient("http://localhost:8080")
        c._use_mock = True
        result = c.get_todos()
        assert result == MOCK_TODOS

    def test_falls_back_to_mock_on_request_failure(self):
        c = APIClient("http://localhost:8080")
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "{}"
        sys.modules["urequests"].get = MagicMock(return_value=mock_response)

        result = c.get_todos()

        assert result == MOCK_TODOS
        assert c._use_mock is True

    def test_returns_server_data_on_success(self):
        c = APIClient("http://localhost:8080")
        import json
        server_data = [{"title": "Server Task", "done": False}]
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = json.dumps(server_data)
        sys.modules["urequests"].get = MagicMock(return_value=mock_response)

        result = c.get_todos()

        assert result == server_data

    def test_falls_back_on_exception(self):
        c = APIClient("http://localhost:8080")
        sys.modules["urequests"].get = MagicMock(side_effect=Exception("Network error"))

        result = c.get_todos()

        assert result == MOCK_TODOS


class TestAPIClientGetCalendar:
    def test_returns_mock_data_when_mock_mode(self):
        c = APIClient("http://localhost:8080")
        c._use_mock = True
        result = c.get_calendar()
        assert result == MOCK_EVENTS

    def test_returns_server_data_on_success(self):
        c = APIClient("http://localhost:8080")
        import json
        server_data = [{"time": "10:00", "title": "Test Event"}]
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = json.dumps(server_data)
        sys.modules["urequests"].get = MagicMock(return_value=mock_response)

        result = c.get_calendar()

        assert result == server_data

    def test_falls_back_on_failure(self):
        c = APIClient("http://localhost:8080")
        mock_response = MagicMock()
        mock_response.status_code = 404
        sys.modules["urequests"].get = MagicMock(return_value=mock_response)

        result = c.get_calendar()

        assert result == MOCK_EVENTS


class TestAPIClientServerAvailable:
    def test_server_available(self):
        c = APIClient("http://localhost:8080")
        mock_response = MagicMock()
        mock_response.status_code = 200
        sys.modules["urequests"].get = MagicMock(return_value=mock_response)

        assert c.is_server_available() is True

    def test_server_unavailable(self):
        c = APIClient("http://localhost:8080")
        sys.modules["urequests"].get = MagicMock(side_effect=Exception("Connection refused"))

        assert c.is_server_available() is False

    def test_server_returns_non_200(self):
        c = APIClient("http://localhost:8080")
        mock_response = MagicMock()
        mock_response.status_code = 503
        sys.modules["urequests"].get = MagicMock(return_value=mock_response)

        assert c.is_server_available() is False


class TestMockData:
    def test_mock_todos_is_list(self):
        assert isinstance(MOCK_TODOS, list)
        assert len(MOCK_TODOS) > 0

    def test_mock_todos_have_required_fields(self):
        for todo in MOCK_TODOS:
            assert "title" in todo
            assert "done" in todo

    def test_mock_events_is_list(self):
        assert isinstance(MOCK_EVENTS, list)
        assert len(MOCK_EVENTS) > 0

    def test_mock_events_have_required_fields(self):
        for event in MOCK_EVENTS:
            assert "time" in event
            assert "title" in event
