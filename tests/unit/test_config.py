import json
import yaml
import pytest
from pathlib import Path
from unittest.mock import patch, mock_open
from envcli.config import (
    CONFIG_DIR, CONFIG_FILE, PROFILES_DIR, DEFAULT_CONFIG,
    ensure_config_dir, load_config, save_config, get_current_profile,
    set_current_profile, list_profiles, create_profile, list_hooks,
    add_hook, remove_hook, is_analytics_enabled, set_analytics_enabled,
    log_command, get_command_stats
)


class TestConfig:
    def test_constants(self):
        """Test that config constants are properly defined."""
        assert CONFIG_DIR == Path.home() / ".envcli"
        assert CONFIG_FILE == CONFIG_DIR / "config.yaml"
        assert PROFILES_DIR == CONFIG_DIR / "profiles"

    def test_default_config(self):
        """Test default configuration values."""
        assert DEFAULT_CONFIG == {
            "default_profile": "dev",
            "remember_last_profile": True,
        }

    @patch('pathlib.Path.mkdir')
    def test_ensure_config_dir(self, mock_mkdir, temp_config_dir):
        """Test that config directories are created."""
        mock_mkdir.return_value = None

        ensure_config_dir()

        # Verify mkdir was called twice (for CONFIG_DIR and PROFILES_DIR)
        assert mock_mkdir.call_count == 2
        mock_mkdir.assert_any_call(exist_ok=True)
        mock_mkdir.assert_any_call(exist_ok=True)

    @patch('envcli.config.CONFIG_FILE')
    @patch('envcli.config.ensure_config_dir')
    def test_load_config_existing_file(self, mock_ensure_dir, mock_config_file, temp_config_dir):
        """Test loading config from existing file."""
        config_data = {"default_profile": "prod", "analytics_enabled": True}
        mock_config_file.exists.return_value = True

        with patch('builtins.open', mock_open(read_data=yaml.dump(config_data))) as mock_file:
            result = load_config()
            assert result == config_data
            mock_file.assert_called_with(mock_config_file, 'r')

    @patch('envcli.config.CONFIG_FILE')
    @patch('envcli.config.ensure_config_dir')
    def test_load_config_nonexistent_file(self, mock_ensure_dir, mock_config_file):
        """Test loading config when file doesn't exist returns defaults."""
        mock_config_file.exists.return_value = False

        result = load_config()
        assert result == DEFAULT_CONFIG.copy()

    @patch('envcli.config.CONFIG_FILE')
    @patch('envcli.config.ensure_config_dir')
    def test_load_config_empty_file(self, mock_ensure_dir, mock_config_file):
        """Test loading config from empty file returns defaults."""
        mock_config_file.exists.return_value = True

        with patch('builtins.open', mock_open(read_data="")):
            result = load_config()
            assert result == DEFAULT_CONFIG.copy()

    @patch('envcli.config.CONFIG_FILE')
    @patch('envcli.config.ensure_config_dir')
    def test_save_config(self, mock_ensure_dir, mock_config_file, temp_config_dir):
        """Test saving config to file."""
        config_data = {"default_profile": "test", "analytics_enabled": True}

        with patch('builtins.open', mock_open()) as mock_file:
            save_config(config_data)

            # Verify file was opened for writing
            mock_file.assert_called_with(mock_config_file, 'w')
            # Verify yaml.dump was called with correct data
            handle = mock_file()
            handle.write.assert_called()

    @patch('envcli.config.load_config')
    def test_get_current_profile_with_current(self, mock_load_config):
        """Test getting current profile when explicitly set."""
        mock_load_config.return_value = {
            "default_profile": "dev",
            "current_profile": "prod"
        }

        result = get_current_profile()
        assert result == "prod"

    @patch('envcli.config.load_config')
    def test_get_current_profile_fallback_to_default(self, mock_load_config):
        """Test getting current profile falls back to default when not set."""
        mock_load_config.return_value = {
            "default_profile": "dev"
        }

        result = get_current_profile()
        assert result == "dev"

    @patch('envcli.config.load_config')
    @patch('envcli.config.save_config')
    def test_set_current_profile(self, mock_save_config, mock_load_config):
        """Test setting current profile."""
        mock_load_config.return_value = {"default_profile": "dev"}

        set_current_profile("prod")

        # Verify config was loaded, updated, and saved
        mock_load_config.assert_called_once()
        mock_save_config.assert_called_once_with({
            "default_profile": "dev",
            "current_profile": "prod"
        })

    @patch('envcli.config.PROFILES_DIR')
    @patch('envcli.config.ensure_config_dir')
    def test_list_profiles(self, mock_ensure_dir, mock_profiles_dir, temp_config_dir):
        """Test listing available profiles."""
        # Create mock profile files
        mock_profiles_dir.glob.return_value = [
            Path("profile1.json"),
            Path("profile2.json"),
            Path("profile3.json")
        ]

        # Mock Path.stem to return profile names
        def mock_stem(self):
            return self.name.replace('.json', '')
        Path.stem = property(mock_stem)

        result = list_profiles()
        assert result == ["profile1", "profile2", "profile3"]

    @patch('envcli.config.PROFILES_DIR')
    @patch('envcli.config.ensure_config_dir')
    def test_list_profiles_empty(self, mock_ensure_dir, mock_profiles_dir):
        """Test listing profiles when none exist."""
        mock_profiles_dir.glob.return_value = []

        result = list_profiles()
        assert result == []

    @patch('envcli.config.PROFILES_DIR')
    @patch('envcli.config.ensure_config_dir')
    def test_create_profile_success(self, mock_ensure_dir, mock_profiles_dir, temp_config_dir):
        """Test creating a new profile successfully."""
        mock_profile_file = mock_profiles_dir / "new_profile.json"
        mock_profile_file.exists.return_value = False

        with patch('builtins.open', mock_open()) as mock_file:
            create_profile("new_profile")

            # Verify file was created
            mock_file.assert_called_with(mock_profile_file, 'w')
            # Verify empty dict was written
            handle = mock_file()
            handle.write.assert_called()

    @patch('envcli.config.PROFILES_DIR')
    @patch('envcli.config.ensure_config_dir')
    def test_create_profile_already_exists(self, mock_ensure_dir, mock_profiles_dir):
        """Test creating a profile that already exists raises error."""
        mock_profile_file = mock_profiles_dir / "existing_profile.json"
        mock_profile_file.exists.return_value = True

        with pytest.raises(ValueError, match="Profile 'existing_profile' already exists"):
            create_profile("existing_profile")

    @patch('envcli.config.load_config')
    def test_list_hooks(self, mock_load_config):
        """Test listing hooks."""
        hooks_data = [
            {"type": "pre", "command": "profile use", "hook_command": "echo 'Switching'"},
            {"type": "post", "command": "env add", "hook_command": "git commit"}
        ]
        mock_load_config.return_value = {"hooks": hooks_data}

        result = list_hooks()
        assert result == hooks_data

    @patch('envcli.config.load_config')
    def test_list_hooks_empty(self, mock_load_config):
        """Test listing hooks when none exist."""
        mock_load_config.return_value = {}

        result = list_hooks()
        assert result == []

    @patch('envcli.config.load_config')
    @patch('envcli.config.save_config')
    def test_add_hook(self, mock_save_config, mock_load_config):
        """Test adding a hook."""
        mock_load_config.return_value = {"default_profile": "dev"}

        add_hook("pre", "profile use", "echo 'test'")

        expected_config = {
            "default_profile": "dev",
            "hooks": [{
                "type": "pre",
                "command": "profile use",
                "hook_command": "echo 'test'"
            }]
        }
        mock_save_config.assert_called_once_with(expected_config)

    @patch('envcli.config.load_config')
    @patch('envcli.config.save_config')
    def test_add_hook_existing_hooks(self, mock_save_config, mock_load_config):
        """Test adding a hook when hooks already exist."""
        existing_hooks = [{"type": "pre", "command": "env add", "hook_command": "git add"}]
        mock_load_config.return_value = {
            "default_profile": "dev",
            "hooks": existing_hooks
        }

        add_hook("post", "profile use", "echo 'done'")

        # Verify that save_config was called with the correct config
        call_args = mock_save_config.call_args[0][0]
        assert call_args["default_profile"] == "dev"
        assert len(call_args["hooks"]) == 2
        assert call_args["hooks"][0] == existing_hooks[0]
        assert call_args["hooks"][1] == {
            "type": "post",
            "command": "profile use",
            "hook_command": "echo 'done'"
        }

    @patch('envcli.config.load_config')
    @patch('envcli.config.save_config')
    def test_remove_hook_valid_index(self, mock_save_config, mock_load_config):
        """Test removing a hook by valid index."""
        hooks = [
            {"type": "pre", "command": "cmd1", "hook_command": "hook1"},
            {"type": "post", "command": "cmd2", "hook_command": "hook2"},
            {"type": "pre", "command": "cmd3", "hook_command": "hook3"}
        ]
        mock_load_config.return_value = {
            "default_profile": "dev",
            "hooks": hooks
        }

        remove_hook(1)  # Remove second hook

        expected_config = {
            "default_profile": "dev",
            "hooks": [
                {"type": "pre", "command": "cmd1", "hook_command": "hook1"},
                {"type": "pre", "command": "cmd3", "hook_command": "hook3"}
            ]
        }
        mock_save_config.assert_called_once_with(expected_config)

    @patch('envcli.config.load_config')
    def test_remove_hook_invalid_index(self, mock_load_config):
        """Test removing a hook with invalid index raises error."""
        hooks = [{"type": "pre", "command": "cmd1", "hook_command": "hook1"}]
        mock_load_config.return_value = {
            "default_profile": "dev",
            "hooks": hooks
        }

        with pytest.raises(ValueError, match="Hook index 5 out of range"):
            remove_hook(5)

    @patch('envcli.config.load_config')
    def test_remove_hook_negative_index(self, mock_load_config):
        """Test removing a hook with negative index raises error."""
        hooks = [{"type": "pre", "command": "cmd1", "hook_command": "hook1"}]
        mock_load_config.return_value = {
            "default_profile": "dev",
            "hooks": hooks
        }

        with pytest.raises(ValueError, match="Hook index -1 out of range"):
            remove_hook(-1)

    @patch('envcli.config.load_config')
    def test_is_analytics_enabled_true(self, mock_load_config):
        """Test checking if analytics is enabled when it is."""
        mock_load_config.return_value = {"analytics_enabled": True}

        result = is_analytics_enabled()
        assert result is True

    @patch('envcli.config.load_config')
    def test_is_analytics_enabled_false(self, mock_load_config):
        """Test checking if analytics is enabled when it isn't."""
        mock_load_config.return_value = {"analytics_enabled": False}

        result = is_analytics_enabled()
        assert result is False

    @patch('envcli.config.load_config')
    def test_is_analytics_enabled_default(self, mock_load_config):
        """Test checking if analytics is enabled when not configured."""
        mock_load_config.return_value = {}

        result = is_analytics_enabled()
        assert result is False

    @patch('envcli.config.load_config')
    @patch('envcli.config.save_config')
    def test_set_analytics_enabled(self, mock_save_config, mock_load_config):
        """Test enabling/disabling analytics."""
        mock_load_config.return_value = {"default_profile": "dev"}

        set_analytics_enabled(True)

        expected_config = {
            "default_profile": "dev",
            "analytics_enabled": True
        }
        mock_save_config.assert_called_once_with(expected_config)

        set_analytics_enabled(False)

        expected_config["analytics_enabled"] = False
        assert mock_save_config.call_count == 2

    @patch('envcli.config.is_analytics_enabled')
    @patch('envcli.config.load_config')
    @patch('envcli.config.save_config')
    def test_log_command_analytics_enabled(self, mock_save_config, mock_load_config, mock_is_enabled):
        """Test logging command when analytics is enabled."""
        mock_is_enabled.return_value = True
        mock_load_config.return_value = {"default_profile": "dev"}

        log_command("env list")

        # Verify command was logged
        mock_save_config.assert_called_once()
        call_args = mock_save_config.call_args[0][0]

        assert "command_history" in call_args
        assert len(call_args["command_history"]) == 1
        assert call_args["command_history"][0]["command"] == "env list"
        assert "timestamp" in call_args["command_history"][0]

    @patch('envcli.config.is_analytics_enabled')
    def test_log_command_analytics_disabled(self, mock_is_enabled):
        """Test logging command when analytics is disabled does nothing."""
        mock_is_enabled.return_value = False

        # Should not raise any errors and not modify config
        log_command("env list")

    @patch('envcli.config.load_config')
    def test_log_command_limits_history(self, mock_load_config):
        """Test that command history is limited to last 100 commands."""
        # Mock 100 existing commands
        existing_history = [{"command": f"cmd{i}", "timestamp": f"time{i}"} for i in range(100)]
        mock_load_config.return_value = {
            "default_profile": "dev",
            "command_history": existing_history
        }

        with patch('envcli.config.save_config') as mock_save:
            with patch('envcli.config.is_analytics_enabled', return_value=True):
                log_command("new_command")

                # Verify history was trimmed to 100 items
                call_args = mock_save.call_args[0][0]
                assert len(call_args["command_history"]) == 100
                assert call_args["command_history"][-1]["command"] == "new_command"

    @patch('envcli.config.load_config')
    def test_get_command_stats(self, mock_load_config):
        """Test getting command usage statistics."""
        history = [
            {"command": "env list", "timestamp": "time1"},
            {"command": "env add", "timestamp": "time2"},
            {"command": "env list", "timestamp": "time3"},
            {"command": "profile use", "timestamp": "time4"},
            {"command": "env list", "timestamp": "time5"},
            {"command": "", "timestamp": "time6"}  # Empty command
        ]
        mock_load_config.return_value = {"command_history": history}

        result = get_command_stats()

        expected = {
            "env": 4,  # 3 "env list" + 1 "env add"
            "profile": 1,
            "unknown": 1  # Empty command
        }
        assert result == expected

    @patch('envcli.config.load_config')
    def test_get_command_stats_empty_history(self, mock_load_config):
        """Test getting command stats when no history exists."""
        mock_load_config.return_value = {}

        result = get_command_stats()
        assert result == {}
