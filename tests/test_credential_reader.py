"""Tests for credential_reader module."""

import json
import time
from pathlib import Path

import pytest

from app.credential_reader import Credentials, read_credentials, CredentialError, DEFAULT_CREDENTIALS_PATH


class TestReadCredentials:
    """Tests for read_credentials()."""

    def test_reads_valid_credentials(self, tmp_path):
        cred_file = tmp_path / ".credentials.json"
        cred_file.write_text(json.dumps({
            "claudeAiOauth": {
                "accessToken": "sk-ant-oat01-test-token",
                "refreshToken": "sk-ant-ort01-test-refresh",
                "expiresAt": int(time.time() * 1000) + 3_600_000,
                "scopes": ["user:inference"],
                "subscriptionType": "max",
                "rateLimitTier": "default_claude_max_5x",
            }
        }))

        creds = read_credentials(cred_file)

        assert isinstance(creds, Credentials)
        assert creds.access_token == "sk-ant-oat01-test-token"
        assert creds.refresh_token == "sk-ant-ort01-test-refresh"
        assert creds.subscription_type == "max"
        assert creds.rate_limit_tier == "default_claude_max_5x"

    def test_raises_on_missing_file(self, tmp_path):
        missing = tmp_path / "nonexistent.json"

        with pytest.raises(CredentialError, match="not found"):
            read_credentials(missing)

    def test_raises_on_malformed_json(self, tmp_path):
        cred_file = tmp_path / ".credentials.json"
        cred_file.write_text("{not valid json")

        with pytest.raises(CredentialError, match="parse"):
            read_credentials(cred_file)

    def test_raises_on_missing_oauth_key(self, tmp_path):
        cred_file = tmp_path / ".credentials.json"
        cred_file.write_text(json.dumps({"someOtherKey": {}}))

        with pytest.raises(CredentialError, match="claudeAiOauth"):
            read_credentials(cred_file)

    def test_raises_on_missing_access_token(self, tmp_path):
        cred_file = tmp_path / ".credentials.json"
        cred_file.write_text(json.dumps({
            "claudeAiOauth": {
                "refreshToken": "sk-ant-ort01-test",
                "expiresAt": int(time.time() * 1000) + 3_600_000,
            }
        }))

        with pytest.raises(CredentialError, match="accessToken"):
            read_credentials(cred_file)

    def test_detects_expired_token(self, tmp_path):
        cred_file = tmp_path / ".credentials.json"
        cred_file.write_text(json.dumps({
            "claudeAiOauth": {
                "accessToken": "sk-ant-oat01-expired",
                "refreshToken": "sk-ant-ort01-test",
                "expiresAt": int(time.time() * 1000) - 1000,
                "subscriptionType": "max",
                "rateLimitTier": "default_claude_max_5x",
            }
        }))

        creds = read_credentials(cred_file)
        assert creds.is_expired is True

    def test_detects_non_expired_token(self, tmp_path):
        cred_file = tmp_path / ".credentials.json"
        cred_file.write_text(json.dumps({
            "claudeAiOauth": {
                "accessToken": "sk-ant-oat01-valid",
                "refreshToken": "sk-ant-ort01-test",
                "expiresAt": int(time.time() * 1000) + 3_600_000,
                "subscriptionType": "max",
                "rateLimitTier": "default_claude_max_5x",
            }
        }))

        creds = read_credentials(cred_file)
        assert creds.is_expired is False

    def test_uses_default_path(self):
        """read_credentials() without arguments uses ~/.claude/.credentials.json."""
        expected = Path.home() / ".claude" / ".credentials.json"
        assert DEFAULT_CREDENTIALS_PATH == expected

    def test_handles_float_expires_at(self, tmp_path):
        """expiresAt may arrive as a float from JSON; is_expired must still work."""
        cred_file = tmp_path / ".credentials.json"
        cred_file.write_text(json.dumps({
            "claudeAiOauth": {
                "accessToken": "sk-ant-oat01-test",
                "expiresAt": time.time() * 1000 + 3_600_000.0,
            }
        }))

        creds = read_credentials(cred_file)
        assert creds.is_expired is False
