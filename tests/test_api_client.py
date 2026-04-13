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


class TestAPIClientJsonImport:
    """Test the ujson/json fallback import."""

    def test_json_module_available(self):
        """The json module should be available (either ujson or stdlib json)."""
        from lib import api_client
        # The module should have resolved json one way or another
        assert hasattr(api_client, 'json')

    def test_json_loads_works(self):
        """json.loads should work regardless of which json module was imported."""
        from lib import api_client
        data = api_client.json.loads('{"key": "value"}')
        assert data == {"key": "value"}

    def test_json_loads_array(self):
        from lib import api_client
        data = api_client.json.loads('[1, 2, 3]')
        assert data == [1, 2, 3]


class TestAPIClientGet:
    """Test the internal _get method."""

    def test_get_builds_correct_url(self):
        c = APIClient("http://myserver:8080")
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '[]'
        sys.modules["urequests"].get = MagicMock(return_value=mock_response)

        c._get("/todos")

        sys.modules["urequests"].get.assert_called_once_with(
            "http://myserver:8080/todos", timeout=10
        )

    def test_get_uses_custom_timeout(self):
        c = APIClient("http://myserver:8080", timeout=30)
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '[]'
        sys.modules["urequests"].get = MagicMock(return_value=mock_response)

        c._get("/data")

        sys.modules["urequests"].get.assert_called_once_with(
            "http://myserver:8080/data", timeout=30
        )

    def test_get_closes_response_on_success(self):
        c = APIClient("http://localhost:8080")
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '{"result": true}'
        sys.modules["urequests"].get = MagicMock(return_value=mock_response)

        c._get("/test")

        mock_response.close.assert_called_once()

    def test_get_closes_response_on_error_status(self):
        c = APIClient("http://localhost:8080")
        mock_response = MagicMock()
        mock_response.status_code = 500
        sys.modules["urequests"].get = MagicMock(return_value=mock_response)

        result = c._get("/test")

        assert result is None
        mock_response.close.assert_called_once()

    def test_get_returns_none_on_import_error(self):
        c = APIClient("http://localhost:8080")
        sys.modules["urequests"].get = MagicMock(side_effect=ImportError("no urequests"))

        result = c._get("/test")

        assert result is None
        assert c._use_mock is True

    def test_get_returns_none_on_network_error(self):
        c = APIClient("http://localhost:8080")
        sys.modules["urequests"].get = MagicMock(side_effect=OSError("Connection refused"))

        result = c._get("/test")

        assert result is None

    def test_get_parses_json_response(self):
        c = APIClient("http://localhost:8080")
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '[{"title": "Test", "done": false}]'
        sys.modules["urequests"].get = MagicMock(return_value=mock_response)

        result = c._get("/todos")

        assert result == [{"title": "Test", "done": False}]


class TestAPIClientGetCalendarEdgeCases:
    def test_calendar_does_not_set_use_mock_on_single_failure(self):
        """get_calendar falls back but doesn't permanently set _use_mock."""
        c = APIClient("http://localhost:8080")
        mock_response = MagicMock()
        mock_response.status_code = 500
        sys.modules["urequests"].get = MagicMock(return_value=mock_response)

        result = c.get_calendar()

        assert result == MOCK_EVENTS
        # Note: get_calendar doesn't set _use_mock = True (unlike get_todos)
        assert c._use_mock is False

    def test_get_calendar_after_todos_sets_mock(self):
        """Once _use_mock is True from get_todos, get_calendar also uses mock."""
        c = APIClient("http://localhost:8080")
        c._use_mock = True

        todos = c.get_todos()
        events = c.get_calendar()

        assert todos == MOCK_TODOS
        assert events == MOCK_EVENTS


class TestAPIClientGetTodosEdgeCases:
    def test_get_todos_sets_use_mock_on_failure(self):
        """get_todos should set _use_mock so subsequent calls skip network."""
        c = APIClient("http://localhost:8080")
        assert c._use_mock is False

        sys.modules["urequests"].get = MagicMock(side_effect=Exception("fail"))
        c.get_todos()

        assert c._use_mock is True

    def test_consecutive_mock_calls_skip_network(self):
        c = APIClient("http://localhost:8080")
        c._use_mock = True

        sys.modules["urequests"].get = MagicMock(side_effect=Exception("should not be called"))

        result1 = c.get_todos()
        result2 = c.get_todos()

        assert result1 == MOCK_TODOS
        assert result2 == MOCK_TODOS
