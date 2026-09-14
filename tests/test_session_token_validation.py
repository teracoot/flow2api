"""Regression tests for stale Labs session-token responses."""

import unittest
from datetime import datetime, timedelta, timezone

from src.services.flow_client import FlowClient


class SessionTokenValidationTests(unittest.TestCase):
    def test_rejects_google_refresh_required_response(self):
        with self.assertRaisesRegex(RuntimeError, "ACCESS_TOKEN_REFRESH_NEEDED"):
            FlowClient._validate_session_response({
                "user": {"email": "user@example.com"},
                "access_token": "expired-token",
                "expires": "2099-01-01T00:00:00.000Z",
                "error": "ACCESS_TOKEN_REFRESH_NEEDED",
            })

    def test_rejects_expired_access_token(self):
        expired = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()
        with self.assertRaisesRegex(RuntimeError, "expired access token"):
            FlowClient._validate_session_response({
                "user": {"email": "user@example.com"},
                "access_token": "expired-token",
                "expires": expired,
            })

    def test_accepts_future_access_token_without_error(self):
        future = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        result = FlowClient._validate_session_response({
            "user": {"email": "user@example.com"},
            "access_token": "current-token",
            "expires": future,
        })
        self.assertEqual(result["access_token"], "current-token")


if __name__ == "__main__":
    unittest.main()
