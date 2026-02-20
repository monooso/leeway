"""Tests for statusline module."""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from statusline import (
    generate_statusline_script,
    update_claude_code_settings,
    remove_claude_code_settings,
    STATUSLINE_SCRIPT_NAME,
)


class TestGenerateStatuslineScript:
    """Tests for generate_statusline_script()."""

    def test_script_is_bash(self):
        script = generate_statusline_script()
        assert script.startswith("#!/bin/bash")

    def test_script_reads_credentials(self):
        script = generate_statusline_script()
        assert ".credentials.json" in script

    def test_script_calls_api(self):
        script = generate_statusline_script()
        assert "api.anthropic.com" in script

    def test_script_has_colour_gradient(self):
        script = generate_statusline_script()
        # Should contain ANSI colour codes for the 10-level gradient
        assert "\\033[38;5;" in script

    def test_script_has_progress_bar(self):
        script = generate_statusline_script()
        assert "▓" in script
        assert "░" in script

    def test_script_name_is_correct(self):
        assert STATUSLINE_SCRIPT_NAME == "statusline-command.sh"


class TestUpdateClaudeCodeSettings:
    """Tests for update_claude_code_settings()."""

    def test_creates_settings_file_if_missing(self, tmp_path):
        settings_path = tmp_path / "settings.json"
        script_path = tmp_path / "statusline-command.sh"

        update_claude_code_settings(settings_path, script_path)

        data = json.loads(settings_path.read_text())
        assert "statusLine" in data
        assert data["statusLine"]["type"] == "command"
        assert str(script_path) in data["statusLine"]["command"]

    def test_preserves_existing_settings(self, tmp_path):
        settings_path = tmp_path / "settings.json"
        settings_path.write_text(json.dumps({"existingKey": "existingValue"}))
        script_path = tmp_path / "statusline-command.sh"

        update_claude_code_settings(settings_path, script_path)

        data = json.loads(settings_path.read_text())
        assert data["existingKey"] == "existingValue"
        assert "statusLine" in data

    def test_overwrites_existing_statusline(self, tmp_path):
        settings_path = tmp_path / "settings.json"
        settings_path.write_text(json.dumps({
            "statusLine": {"type": "command", "command": "old-command"},
        }))
        script_path = tmp_path / "statusline-command.sh"

        update_claude_code_settings(settings_path, script_path)

        data = json.loads(settings_path.read_text())
        assert str(script_path) in data["statusLine"]["command"]


class TestRemoveClaudeCodeSettings:
    """Tests for remove_claude_code_settings()."""

    def test_removes_statusline_key(self, tmp_path):
        settings_path = tmp_path / "settings.json"
        settings_path.write_text(json.dumps({
            "statusLine": {"type": "command", "command": "something"},
            "otherKey": 42,
        }))

        remove_claude_code_settings(settings_path)

        data = json.loads(settings_path.read_text())
        assert "statusLine" not in data
        assert data["otherKey"] == 42

    def test_noop_if_no_statusline_key(self, tmp_path):
        settings_path = tmp_path / "settings.json"
        settings_path.write_text(json.dumps({"otherKey": 42}))

        remove_claude_code_settings(settings_path)

        data = json.loads(settings_path.read_text())
        assert data == {"otherKey": 42}

    def test_noop_if_file_missing(self, tmp_path):
        settings_path = tmp_path / "settings.json"
        # Should not raise
        remove_claude_code_settings(settings_path)
        assert not settings_path.exists()
