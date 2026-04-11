"""HTTP API client for fetching todos and calendar data from the server."""

import ujson


# Mock data for testing when server is not available
MOCK_TODOS = [
    {"title": "Review pull requests", "done": False, "priority": "high"},
    {"title": "Update documentation", "done": False, "priority": "medium"},
    {"title": "Fix thermal printer alignment", "done": True, "priority": "low"},
    {"title": "Deploy new firmware", "done": False, "priority": "high"},
    {"title": "Buy thermal paper rolls", "done": False, "priority": "low"},
]

MOCK_EVENTS = [
    {"time": "09:00", "title": "Team standup", "location": "Zoom"},
    {"time": "11:30", "title": "Code review session", "location": ""},
    {"time": "14:00", "title": "Sprint planning", "location": "Conf Room B"},
    {"time": "16:00", "title": "1:1 with manager", "location": "Zoom"},
]


class APIClient:
    """Fetches todo lists and calendar data from the server API."""

    def __init__(self, server_url, timeout=10):
        self.server_url = server_url.rstrip('/')
        self.timeout = timeout
        self._use_mock = False

    def _get(self, endpoint):
        """Make an HTTP GET request and return parsed JSON."""
        try:
            import urequests
            url = f"{self.server_url}{endpoint}"
            print(f"[API] GET {url}")
            response = urequests.get(url, timeout=self.timeout)
            if response.status_code == 200:
                data = ujson.loads(response.text)
                response.close()
                return data
            else:
                print(f"[API] Error: HTTP {response.status_code}")
                response.close()
                return None
        except ImportError:
            print("[API] urequests not available, using mock data")
            self._use_mock = True
            return None
        except Exception as e:
            print(f"[API] Request failed: {e}")
            return None

    def get_todos(self):
        """Fetch today's todo list from the server."""
        if self._use_mock:
            print("[API] Using mock todo data")
            return MOCK_TODOS

        data = self._get("/todos")
        if data is None:
            print("[API] Falling back to mock todo data")
            self._use_mock = True
            return MOCK_TODOS
        return data

    def get_calendar(self):
        """Fetch today's calendar events from the server."""
        if self._use_mock:
            print("[API] Using mock calendar data")
            return MOCK_EVENTS

        data = self._get("/calendar")
        if data is None:
            print("[API] Falling back to mock calendar data")
            return MOCK_EVENTS
        return data

    def is_server_available(self):
        """Check if the server is reachable."""
        try:
            import urequests
            response = urequests.get(f"{self.server_url}/health", timeout=3)
            available = response.status_code == 200
            response.close()
            return available
        except Exception:
            return False
