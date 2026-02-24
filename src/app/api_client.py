# api_client.py
#
# Copyright 2026 Stephen Lewis
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Pure protocol logic for the Anthropic usage API."""

import json

try:
    from .config import APP_ID, VERSION
    from .usage_model import UsageData, parse_usage_response
except ImportError:
    from config import APP_ID, VERSION
    from usage_model import UsageData, parse_usage_response

API_URL = "https://api.anthropic.com/api/oauth/usage"
USER_AGENT = f"{APP_ID}/{VERSION}"


class ApiError(Exception):
    """Raised when an API request fails."""


def build_request_headers(access_token: str) -> dict[str, str]:
    """Build the HTTP headers for the usage endpoint."""
    return {
        "Authorization": f"Bearer {access_token}",
        "User-Agent": USER_AGENT,
        "anthropic-beta": "oauth-2025-04-20",
    }


def parse_response_body(body: str) -> UsageData:
    """Parse a JSON response body into UsageData.

    Raises:
        ApiError: If the body is not valid JSON or not a JSON object.
    """
    try:
        raw = json.loads(body)
    except (json.JSONDecodeError, ValueError) as exc:
        raise ApiError(f"Failed to parse API response: {exc}") from exc

    if not isinstance(raw, dict):
        raise ApiError("Failed to parse API response: expected JSON object")

    return parse_usage_response(raw)
