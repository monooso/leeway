"""Tests for statusline module."""

import json
import stat

import pytest

from statusline import (
    BrokenSymlinkError,
    CorruptSettingsError,
    generate_statusline_script,
    install_statusline,
    remove_statusline_setting,
    STATUSLINE_SCRIPT_NAME,
    uninstall_statusline,
    update_statusline_setting,
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
        assert "\\033[38;5;" in script

    def test_script_has_progress_bar(self):
        script = generate_statusline_script()
        assert "\u2593" in script
        assert "\u2591" in script

    def test_script_name_is_correct(self):
        assert STATUSLINE_SCRIPT_NAME == "statusline-command.sh"

    def test_script_pipes_via_stdin(self):
        """Credentials and response should be piped via stdin, not interpolated."""
        script = generate_statusline_script()
        assert "sys.stdin" in script


class TestInstallStatusline:
    """Tests for install_statusline()."""

    def test_creates_script_file(self, tmp_path):
        script_path = tmp_path / "statusline-command.sh"
        settings_path = tmp_path / "settings.json"

        install_statusline(script_path=script_path, settings_path=settings_path)

        assert script_path.exists()
        assert script_path.read_text().startswith("#!/bin/bash")

    def test_script_is_executable(self, tmp_path):
        script_path = tmp_path / "statusline-command.sh"
        settings_path = tmp_path / "settings.json"

        install_statusline(script_path=script_path, settings_path=settings_path)

        mode = script_path.stat().st_mode
        assert mode & stat.S_IXUSR

    def test_updates_settings_file(self, tmp_path):
        script_path = tmp_path / "statusline-command.sh"
        settings_path = tmp_path / "settings.json"

        install_statusline(script_path=script_path, settings_path=settings_path)

        data = json.loads(settings_path.read_text())
        assert "statusLine" in data

    def test_creates_parent_directories(self, tmp_path):
        script_path = tmp_path / "sub" / "dir" / "statusline-command.sh"
        settings_path = tmp_path / "settings.json"

        install_statusline(script_path=script_path, settings_path=settings_path)

        assert script_path.exists()


class TestUninstallStatusline:
    """Tests for uninstall_statusline()."""

    def test_removes_script_file(self, tmp_path):
        script_path = tmp_path / "statusline-command.sh"
        settings_path = tmp_path / "settings.json"
        script_path.write_text("#!/bin/bash\n")
        settings_path.write_text(json.dumps({"statusLine": {"type": "command"}}))

        uninstall_statusline(script_path=script_path, settings_path=settings_path)

        assert not script_path.exists()

    def test_removes_settings_entry(self, tmp_path):
        script_path = tmp_path / "statusline-command.sh"
        settings_path = tmp_path / "settings.json"
        script_path.write_text("#!/bin/bash\n")
        settings_path.write_text(json.dumps({
            "statusLine": {"type": "command"},
            "otherKey": 42,
        }))

        uninstall_statusline(script_path=script_path, settings_path=settings_path)

        data = json.loads(settings_path.read_text())
        assert "statusLine" not in data
        assert data["otherKey"] == 42

    def test_noop_if_script_missing(self, tmp_path):
        script_path = tmp_path / "statusline-command.sh"
        settings_path = tmp_path / "settings.json"

        uninstall_statusline(script_path=script_path, settings_path=settings_path)

        assert not script_path.exists()


class TestUpdateStatuslineSetting:
    """Tests for update_statusline_setting()."""

    def test_creates_settings_file_if_missing(self, tmp_path):
        settings_path = tmp_path / "settings.json"
        script_path = tmp_path / "statusline-command.sh"

        update_statusline_setting(settings_path, script_path)

        data = json.loads(settings_path.read_text())
        assert "statusLine" in data
        assert data["statusLine"]["type"] == "command"
        assert str(script_path) in data["statusLine"]["command"]

    def test_preserves_existing_settings(self, tmp_path):
        settings_path = tmp_path / "settings.json"
        settings_path.write_text(json.dumps({"existingKey": "existingValue"}))
        script_path = tmp_path / "statusline-command.sh"

        update_statusline_setting(settings_path, script_path)

        data = json.loads(settings_path.read_text())
        assert data["existingKey"] == "existingValue"
        assert "statusLine" in data

    def test_overwrites_existing_statusline(self, tmp_path):
        settings_path = tmp_path / "settings.json"
        settings_path.write_text(json.dumps({
            "statusLine": {"type": "command", "command": "old-command"},
        }))
        script_path = tmp_path / "statusline-command.sh"

        update_statusline_setting(settings_path, script_path)

        data = json.loads(settings_path.read_text())
        assert str(script_path) in data["statusLine"]["command"]

    def test_raises_on_corrupt_settings_file(self, tmp_path):
        settings_path = tmp_path / "settings.json"
        settings_path.write_text("{not valid json")
        script_path = tmp_path / "statusline-command.sh"

        with pytest.raises(CorruptSettingsError):
            update_statusline_setting(settings_path, script_path)

    def test_raises_on_broken_symlink(self, tmp_path):
        settings_path = tmp_path / "settings.json"
        settings_path.symlink_to("/nonexistent/target/settings.json")
        script_path = tmp_path / "statusline-command.sh"

        with pytest.raises(BrokenSymlinkError):
            update_statusline_setting(settings_path, script_path)


class TestRemoveStatuslineSetting:
    """Tests for remove_statusline_setting()."""

    def test_removes_statusline_key(self, tmp_path):
        settings_path = tmp_path / "settings.json"
        settings_path.write_text(json.dumps({
            "statusLine": {"type": "command", "command": "something"},
            "otherKey": 42,
        }))

        remove_statusline_setting(settings_path)

        data = json.loads(settings_path.read_text())
        assert "statusLine" not in data
        assert data["otherKey"] == 42

    def test_noop_if_no_statusline_key(self, tmp_path):
        settings_path = tmp_path / "settings.json"
        settings_path.write_text(json.dumps({"otherKey": 42}))

        remove_statusline_setting(settings_path)

        data = json.loads(settings_path.read_text())
        assert data == {"otherKey": 42}

    def test_noop_if_file_missing(self, tmp_path):
        settings_path = tmp_path / "settings.json"
        remove_statusline_setting(settings_path)
        assert not settings_path.exists()

    def test_raises_on_broken_symlink(self, tmp_path):
        settings_path = tmp_path / "settings.json"
        settings_path.symlink_to("/nonexistent/target/settings.json")

        with pytest.raises(BrokenSymlinkError):
            remove_statusline_setting(settings_path)
