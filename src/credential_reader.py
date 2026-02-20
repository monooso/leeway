"""Reads OAuth credentials from ~/.claude/.credentials.json."""

import json
import time
from dataclasses import dataclass
from pathlib import Path

DEFAULT_CREDENTIALS_PATH = Path.home() / ".claude" / ".credentials.json"


class CredentialError(Exception):
    """Raised when credentials cannot be read or are invalid."""


@dataclass
class Credentials:
    """OAuth credentials for the Anthropic API."""

    access_token: str
    refresh_token: str | None
    expires_at: int  # milliseconds since epoch
    subscription_type: str | None
    rate_limit_tier: str | None

    @property
    def is_expired(self) -> bool:
        return time.time() * 1000 >= self.expires_at


def read_credentials(path: Path = DEFAULT_CREDENTIALS_PATH) -> Credentials:
    """Read and parse OAuth credentials.

    Args:
        path: Path to the credentials JSON file.

    Returns:
        Credentials dataclass.

    Raises:
        CredentialError: If the file is missing, malformed, or lacks required fields.
    """
    if not path.exists():
        raise CredentialError(f"Credentials file not found: {path}")

    try:
        data = json.loads(path.read_text())
    except (json.JSONDecodeError, ValueError) as exc:
        raise CredentialError(f"Failed to parse credentials: {exc}") from exc

    oauth = data.get("claudeAiOauth")
    if oauth is None:
        raise CredentialError("Missing 'claudeAiOauth' key in credentials file")

    access_token = oauth.get("accessToken")
    if not access_token:
        raise CredentialError("Missing 'accessToken' in claudeAiOauth")

    return Credentials(
        access_token=access_token,
        refresh_token=oauth.get("refreshToken"),
        expires_at=oauth.get("expiresAt", 0),
        subscription_type=oauth.get("subscriptionType"),
        rate_limit_tier=oauth.get("rateLimitTier"),
    )
