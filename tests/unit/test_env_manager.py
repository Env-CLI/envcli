import json
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, mock_open
from envcli.env_manager import EnvManager


class TestEnvManager:
    def test_init_with_profile(self, temp_config_dir):
        """Test initialization with specific profile."""
        with patch('envcli.env_manager.PROFILES_DIR', temp_config_dir / "profiles"):
            manager = EnvManager("test_profile")
            assert manager.profile == "test_profile"
            assert str(manager.profile_file).endswith("test_profile.json")

    def test_init_without_profile(self, temp_config_dir):
        """Test initialization without profile uses default."""
        with patch('envcli.env_manager.PROFILES_DIR', temp_config_dir / "profiles"):
            with patch('envcli.env_manager.get_current_profile', return_value="default"):
                manager = EnvManager()
                assert manager.profile == "default"

    def test_load_env_empty_profile(self, temp_config_dir):
        """Test loading empty profile returns empty dict."""
        with patch('envcli.env_manager.PROFILES_DIR', temp_config_dir / "profiles"):
            manager = EnvManager("empty_profile")
            result = manager.load_env()
            assert result == {}

    def test_load_env_existing_profile(self, temp_config_dir, sample_env_vars):
        """Test loading existing profile."""
        profiles_dir = temp_config_dir / "profiles"
        profiles_dir.mkdir(exist_ok=True)

        profile_file = profiles_dir / "test_profile.json"
        with open(profile_file, 'w') as f:
            json.dump(sample_env_vars, f)

        with patch('envcli.env_manager.PROFILES_DIR', profiles_dir):
            manager = EnvManager("test_profile")
            result = manager.load_env()
            assert result == sample_env_vars

    def test_save_env_creates_directory(self, temp_config_dir, sample_env_vars):
        """Test saving env vars creates profiles directory if needed."""
        profiles_dir = temp_config_dir / "profiles"

        with patch('envcli.env_manager.PROFILES_DIR', profiles_dir):
            manager = EnvManager("test_profile")
            manager.save_env(sample_env_vars)

            assert profiles_dir.exists()
            assert (profiles_dir / "test_profile.json").exists()

            # Verify content
            with open(profiles_dir / "test_profile.json", 'r') as f:
                saved_data = json.load(f)
            assert saved_data == sample_env_vars

    def test_list_env_unmasked(self, env_manager, sample_env_vars):
        """Test listing env vars without masking."""
        result = env_manager.list_env(mask=False)
        assert result == sample_env_vars

    def test_list_env_masked(self, env_manager, sample_env_vars):
        """Test listing env vars with masking for sensitive keys."""
        result = env_manager.list_env(mask=True)

        # Sensitive keys should be masked
        assert result["SECRET_TOKEN"] == "*" * len(sample_env_vars["SECRET_TOKEN"])
        assert result["API_KEY"] == "*" * len(sample_env_vars["API_KEY"])

        # Non-sensitive keys should not be masked
        assert result["DEBUG"] == sample_env_vars["DEBUG"]
        assert result["PORT"] == sample_env_vars["PORT"]

    def test_add_env_new_key(self, env_manager, sample_env_vars):
        """Test adding a new environment variable."""
        env_manager.add_env("NEW_KEY", "new_value")

        # Reload and check
        result = env_manager.load_env()
        assert result["NEW_KEY"] == "new_value"
        # Existing vars should still be there
        assert result["API_KEY"] == sample_env_vars["API_KEY"]

    def test_add_env_update_existing(self, env_manager, sample_env_vars):
        """Test updating an existing environment variable."""
        new_value = "updated_value"
        env_manager.add_env("API_KEY", new_value)

        result = env_manager.load_env()
        assert result["API_KEY"] == new_value

    def test_remove_env_existing_key(self, env_manager, sample_env_vars):
        """Test removing an existing environment variable."""
        env_manager.remove_env("API_KEY")

        result = env_manager.load_env()
        assert "API_KEY" not in result
        # Other keys should remain
        assert result["DEBUG"] == sample_env_vars["DEBUG"]

    def test_remove_env_nonexistent_key(self, env_manager, sample_env_vars):
        """Test removing a non-existent key does nothing."""
        env_manager.remove_env("NONEXISTENT_KEY")

        result = env_manager.load_env()
        assert result == sample_env_vars  # Should be unchanged

    def test_load_from_file_env_format(self, env_manager, temp_config_dir):
        """Test loading from .env format file."""
        env_content = """API_KEY=test_key
DATABASE_URL=postgresql://localhost/db
DEBUG=true
"""

        env_file = temp_config_dir / ".env"
        with open(env_file, 'w') as f:
            f.write(env_content)

        env_manager.load_from_file(str(env_file), format="env")

        result = env_manager.load_env()
        assert result["API_KEY"] == "test_key"
        assert result["DATABASE_URL"] == "postgresql://localhost/db"
        assert result["DEBUG"] == "true"

    def test_load_from_file_json_format(self, env_manager, temp_config_dir, sample_env_vars):
        """Test loading from JSON format file."""
        json_file = temp_config_dir / "config.json"
        with open(json_file, 'w') as f:
            json.dump(sample_env_vars, f)

        env_manager.load_from_file(str(json_file), format="json")

        result = env_manager.load_env()
        assert result == sample_env_vars

    def test_load_from_file_yaml_format(self, env_manager, temp_config_dir, sample_env_vars):
        """Test loading from YAML format file."""
        import yaml

        yaml_file = temp_config_dir / "config.yaml"
        with open(yaml_file, 'w') as f:
            yaml.dump(sample_env_vars, f)

        env_manager.load_from_file(str(yaml_file), format="yaml")

        result = env_manager.load_env()
        assert result == sample_env_vars

    def test_load_from_file_unsupported_format(self, env_manager, temp_config_dir):
        """Test loading from unsupported format raises error."""
        txt_file = temp_config_dir / "config.txt"
        with open(txt_file, 'w') as f:
            f.write("KEY=value")

        with pytest.raises(ValueError, match="Unsupported format"):
            env_manager.load_from_file(str(txt_file), format="txt")

    def test_load_from_file_nonexistent_file(self, env_manager):
        """Test loading from non-existent file raises error."""
        with pytest.raises(FileNotFoundError):
            env_manager.load_from_file("nonexistent.env")

    def test_load_from_file_filters_none_values(self, env_manager, temp_config_dir):
        """Test that None values are filtered out when loading."""
        # Create a .env file with some None values (dotenv can return None for malformed lines)
        with patch('envcli.env_manager.dotenv_values') as mock_dotenv:
            mock_dotenv.return_value = {
                "VALID_KEY": "valid_value",
                "NONE_KEY": None,
                "EMPTY_KEY": ""
            }

            env_file = temp_config_dir / ".env"
            env_file.touch()  # Create the file so it exists
            env_manager.load_from_file(str(env_file), format="env")

            result = env_manager.load_env()
            assert "VALID_KEY" in result
            assert "NONE_KEY" not in result
            assert "EMPTY_KEY" in result  # Empty string is not None

    def test_export_to_file_env_format(self, env_manager, temp_config_dir, sample_env_vars):
        """Test exporting to .env format."""
        export_file = temp_config_dir / "export.env"

        env_manager.export_to_file(str(export_file), format="env")

        # Verify file content
        with open(export_file, 'r') as f:
            content = f.read()

        lines = content.strip().split('\n')
        assert len(lines) == len(sample_env_vars)

        for line in lines:
            key, value = line.split('=', 1)
            assert key in sample_env_vars
            assert value == sample_env_vars[key]

    def test_export_to_file_json_format(self, env_manager, temp_config_dir, sample_env_vars):
        """Test exporting to JSON format."""
        export_file = temp_config_dir / "export.json"

        env_manager.export_to_file(str(export_file), format="json")

        with open(export_file, 'r') as f:
            result = json.load(f)

        assert result == sample_env_vars

    def test_export_to_file_yaml_format(self, env_manager, temp_config_dir, sample_env_vars):
        """Test exporting to YAML format."""
        import yaml

        export_file = temp_config_dir / "export.yaml"

        env_manager.export_to_file(str(export_file), format="yaml")

        with open(export_file, 'r') as f:
            result = yaml.safe_load(f)

        assert result == sample_env_vars

    def test_export_to_file_shell_format(self, env_manager, temp_config_dir, sample_env_vars):
        """Test exporting to shell format."""
        export_file = temp_config_dir / "export.sh"

        env_manager.export_to_file(str(export_file), format="shell")

        with open(export_file, 'r') as f:
            content = f.read()

        lines = content.strip().split('\n')
        assert len(lines) == len(sample_env_vars)

        for line in lines:
            assert line.startswith("export ")
            # Extract key=value part
            export_part = line[7:]  # Remove "export "
            key, value = export_part.split('=', 1)
            assert key in sample_env_vars
            # Value should be quoted
            assert value.startswith('"') and value.endswith('"')
            assert value.strip('"') == sample_env_vars[key]

    def test_export_to_file_unsupported_format(self, env_manager, temp_config_dir):
        """Test exporting to unsupported format raises error."""
        export_file = temp_config_dir / "export.txt"

        with pytest.raises(ValueError, match="Unsupported format"):
            env_manager.export_to_file(str(export_file), format="txt")

    def test_diff_identical_profiles(self, temp_config_dir, sample_env_vars):
        """Test diff between identical profiles."""
        profiles_dir = temp_config_dir / "profiles"
        profiles_dir.mkdir(exist_ok=True)

        # Create two identical profiles
        for profile_name in ["profile1", "profile2"]:
            profile_file = profiles_dir / f"{profile_name}.json"
            with open(profile_file, 'w') as f:
                json.dump(sample_env_vars, f)

        with patch('envcli.env_manager.PROFILES_DIR', profiles_dir):
            manager1 = EnvManager("profile1")
            result = manager1.diff("profile2")

            assert result["added"] == {}
            assert result["removed"] == {}
            assert result["changed"] == {}

    def test_diff_added_keys(self, temp_config_dir, sample_env_vars):
        """Test diff when other profile has additional keys."""
        profiles_dir = temp_config_dir / "profiles"
        profiles_dir.mkdir(exist_ok=True)

        # Profile 1: base vars
        profile1_file = profiles_dir / "profile1.json"
        with open(profile1_file, 'w') as f:
            json.dump(sample_env_vars, f)

        # Profile 2: base vars plus additional
        profile2_vars = {**sample_env_vars, "NEW_KEY": "new_value", "ANOTHER_KEY": "another_value"}
        profile2_file = profiles_dir / "profile2.json"
        with open(profile2_file, 'w') as f:
            json.dump(profile2_vars, f)

        with patch('envcli.env_manager.PROFILES_DIR', profiles_dir):
            manager1 = EnvManager("profile1")
            result = manager1.diff("profile2")

            assert result["added"] == {"NEW_KEY": "new_value", "ANOTHER_KEY": "another_value"}
            assert result["removed"] == {}
            assert result["changed"] == {}

    def test_diff_removed_keys(self, temp_config_dir, sample_env_vars):
        """Test diff when other profile has removed keys."""
        profiles_dir = temp_config_dir / "profiles"
        profiles_dir.mkdir(exist_ok=True)

        # Profile 1: full vars
        profile1_file = profiles_dir / "profile1.json"
        with open(profile1_file, 'w') as f:
            json.dump(sample_env_vars, f)

        # Profile 2: missing some keys
        profile2_vars = {k: v for k, v in sample_env_vars.items() if k != "API_KEY"}
        profile2_file = profiles_dir / "profile2.json"
        with open(profile2_file, 'w') as f:
            json.dump(profile2_vars, f)

        with patch('envcli.env_manager.PROFILES_DIR', profiles_dir):
            manager1 = EnvManager("profile1")
            result = manager1.diff("profile2")

            assert result["added"] == {}
            assert result["removed"] == {"API_KEY": sample_env_vars["API_KEY"]}
            assert result["changed"] == {}

    def test_diff_changed_values(self, temp_config_dir, sample_env_vars):
        """Test diff when values have changed."""
        profiles_dir = temp_config_dir / "profiles"
        profiles_dir.mkdir(exist_ok=True)

        # Profile 1: original values
        profile1_file = profiles_dir / "profile1.json"
        with open(profile1_file, 'w') as f:
            json.dump(sample_env_vars, f)

        # Profile 2: some changed values
        profile2_vars = sample_env_vars.copy()
        profile2_vars["API_KEY"] = "changed_key"
        profile2_vars["DEBUG"] = "false"
        profile2_file = profiles_dir / "profile2.json"
        with open(profile2_file, 'w') as f:
            json.dump(profile2_vars, f)

        with patch('envcli.env_manager.PROFILES_DIR', profiles_dir):
            manager1 = EnvManager("profile1")
            result = manager1.diff("profile2")

            assert result["added"] == {}
            assert result["removed"] == {}
            assert result["changed"] == {
                "API_KEY": {"old": sample_env_vars["API_KEY"], "new": "changed_key"},
                "DEBUG": {"old": sample_env_vars["DEBUG"], "new": "false"}
            }

    def test_diff_mixed_changes(self, temp_config_dir, sample_env_vars):
        """Test diff with mixed changes: added, removed, and changed."""
        profiles_dir = temp_config_dir / "profiles"
        profiles_dir.mkdir(exist_ok=True)

        # Profile 1
        profile1_file = profiles_dir / "profile1.json"
        with open(profile1_file, 'w') as f:
            json.dump(sample_env_vars, f)

        # Profile 2: mixed changes
        profile2_vars = sample_env_vars.copy()
        profile2_vars["API_KEY"] = "changed_key"  # changed
        profile2_vars["NEW_KEY"] = "new_value"    # added
        del profile2_vars["DEBUG"]                 # removed
        profile2_file = profiles_dir / "profile2.json"
        with open(profile2_file, 'w') as f:
            json.dump(profile2_vars, f)

        with patch('envcli.env_manager.PROFILES_DIR', profiles_dir):
            manager1 = EnvManager("profile1")
            result = manager1.diff("profile2")

            assert result["added"] == {"NEW_KEY": "new_value"}
            assert result["removed"] == {"DEBUG": sample_env_vars["DEBUG"]}
            assert result["changed"] == {"API_KEY": {"old": sample_env_vars["API_KEY"], "new": "changed_key"}}
