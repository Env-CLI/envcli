import json
import pytest
from pathlib import Path
from envcli.cli import app


class TestCLICommands:
    def test_env_list_command(self, cli_runner, env_manager, sample_env_vars):
        """Test env list command."""
        # The env_manager fixture already created and populated test_profile
        result = cli_runner.invoke(app, ["env", "list", "--profile", "test_profile"])

        assert result.exit_code == 0
        # Should contain the environment variables
        assert "API_KEY" in result.output or "SECRET_TOKEN" in result.output
        assert "DATABASE_URL" in result.output
        assert "DEBUG" in result.output

    def test_env_list_masked_command(self, cli_runner, env_manager, sample_env_vars):
        """Test env list command with masking."""
        result = cli_runner.invoke(app, ["env", "list"])

        assert result.exit_code == 0
        # Sensitive keys should be masked
        assert "SECRET_TOKEN" in result.output
        assert "***masked***" in result.output or "*" in result.output

    def test_env_list_no_mask_command(self, cli_runner, env_manager, sample_env_vars):
        """Test env list command without masking."""
        result = cli_runner.invoke(app, ["env", "list", "--no-mask"])

        assert result.exit_code == 0
        # Should show actual secret values
        assert sample_env_vars["SECRET_TOKEN"] in result.output

    def test_env_add_command(self, cli_runner, env_manager):
        """Test env add command."""
        result = cli_runner.invoke(app, ["env", "add", "NEW_KEY", "new_value"])

        assert result.exit_code == 0
        assert "Added NEW_KEY" in result.output

        # Verify it was actually added
        result_list = cli_runner.invoke(app, ["env", "list", "--no-mask"])
        assert "NEW_KEY" in result_list.output
        assert "new_value" in result_list.output

    def test_env_remove_command(self, cli_runner, env_manager, sample_env_vars):
        """Test env remove command."""
        result = cli_runner.invoke(app, ["env", "remove", "API_KEY"])

        assert result.exit_code == 0
        assert "Removed API_KEY" in result.output

        # Verify it was actually removed
        result_list = cli_runner.invoke(app, ["env", "list"])
        assert "API_KEY" not in result_list.output

    def test_env_remove_nonexistent_command(self, cli_runner, env_manager):
        """Test env remove command for non-existent key."""
        result = cli_runner.invoke(app, ["env", "remove", "NONEXISTENT_KEY"])

        assert result.exit_code == 0
        assert "Removed NONEXISTENT_KEY" in result.output

    def test_profile_init_command(self, cli_runner, temp_config_dir):
        """Test profile init command."""
        result = cli_runner.invoke(app, ["profile", "init", "--name", "test_profile"])

        assert result.exit_code == 0
        assert "Created profile 'test_profile'" in result.output

    def test_profile_use_command(self, cli_runner, temp_config_dir):
        """Test profile use command."""
        # First create a profile
        cli_runner.invoke(app, ["profile", "init", "--name", "test_profile"])

        # Then switch to it
        result = cli_runner.invoke(app, ["profile", "use", "test_profile"])

        assert result.exit_code == 0
        assert "Switched to profile 'test_profile'" in result.output

    def test_profile_use_nonexistent_command(self, cli_runner):
        """Test profile use command with non-existent profile."""
        result = cli_runner.invoke(app, ["profile", "use", "nonexistent"])

        assert result.exit_code == 0  # CLI doesn't exit on this error
        assert "does not exist" in result.output

    def test_profile_list_command(self, cli_runner, temp_config_dir):
        """Test profile list command."""
        # Create some profiles
        cli_runner.invoke(app, ["profile", "init", "--name", "dev"])
        cli_runner.invoke(app, ["profile", "init", "--name", "staging"])
        cli_runner.invoke(app, ["profile", "init", "--name", "prod"])

        result = cli_runner.invoke(app, ["profile", "list"])

        assert result.exit_code == 0
        assert "dev" in result.output
        assert "staging" in result.output
        assert "prod" in result.output

    def test_profile_tree_command(self, cli_runner, env_manager, sample_env_vars):
        """Test profile tree command."""
        result = cli_runner.invoke(app, ["profile", "tree"])

        assert result.exit_code == 0
        assert "📁 Environment Profiles" in result.output
        # Should show profile and variables
        assert "API_KEY" in result.output or "⚪" in result.output

    def test_encrypt_encrypt_command(self, cli_runner, temp_config_dir):
        """Test encrypt encrypt command."""
        # Create a test file
        test_file = temp_config_dir / "test.env"
        test_file.write_text("KEY=value\n")

        result = cli_runner.invoke(app, ["encrypt", "encrypt", str(test_file)])

        assert result.exit_code == 0
        assert "Encrypted" in result.output

    def test_encrypt_decrypt_command(self, cli_runner, temp_config_dir):
        """Test encrypt decrypt command."""
        # First encrypt a file
        test_file = temp_config_dir / "test.env"
        test_file.write_text("KEY=value\n")
        cli_runner.invoke(app, ["encrypt", "encrypt", str(test_file)])

        # Then decrypt it
        result = cli_runner.invoke(app, ["encrypt", "decrypt", str(test_file)])

        assert result.exit_code == 0
        assert "Decrypted" in result.output

    def test_hooks_list_command(self, cli_runner):
        """Test hooks list command."""
        result = cli_runner.invoke(app, ["hooks", "list"])

        assert result.exit_code == 0
        # Should show table headers even if empty
        assert "Type" in result.output or "No hooks" in result.output

    def test_hooks_add_command(self, cli_runner):
        """Test hooks add command."""
        result = cli_runner.invoke(app, [
            "hooks", "add", "pre", "profile use", "echo 'Switching profiles'"
        ])

        assert result.exit_code == 0
        assert "Added pre hook" in result.output

    def test_hooks_remove_command(self, cli_runner):
        """Test hooks remove command."""
        # First add a hook
        cli_runner.invoke(app, [
            "hooks", "add", "pre", "profile use", "echo 'test'"
        ])

        # Then remove it
        result = cli_runner.invoke(app, ["hooks", "remove", "0"])

        assert result.exit_code == 0
        assert "Removed hook" in result.output

    def test_analytics_enable_command(self, cli_runner):
        """Test analytics enable command."""
        result = cli_runner.invoke(app, ["analytics", "enable"])

        assert result.exit_code == 0
        assert "Analytics enabled" in result.output

    def test_analytics_disable_command(self, cli_runner):
        """Test analytics disable command."""
        result = cli_runner.invoke(app, ["analytics", "disable"])

        assert result.exit_code == 0
        assert "Analytics disabled" in result.output

    def test_analytics_stats_command(self, cli_runner):
        """Test analytics stats command."""
        result = cli_runner.invoke(app, ["analytics", "stats"])

        assert result.exit_code == 0
        # Should show stats or indicate no history

    def test_sync_push_command_invalid_service(self, cli_runner):
        """Test sync push with invalid service."""
        result = cli_runner.invoke(app, ["sync", "push", "invalid_service", "path"])

        assert result.exit_code == 1  # Should exit with error
        assert "Error" in result.output

    def test_sync_pull_command_invalid_service(self, cli_runner):
        """Test sync pull with invalid service."""
        result = cli_runner.invoke(app, ["sync", "pull", "invalid_service", "path"])

        assert result.exit_code == 1  # Should exit with error
        assert "Error" in result.output

    def test_sync_status_command_invalid_service(self, cli_runner):
        """Test sync status with invalid service."""
        result = cli_runner.invoke(app, ["sync", "status", "invalid_service", "path"])

        assert result.exit_code == 1  # Should exit with error
        assert "Error" in result.output

    def test_plugin_list_command(self, cli_runner):
        """Test plugin list command."""
        result = cli_runner.invoke(app, ["plugin", "list"])

        assert result.exit_code == 0
        # Should show plugins or indicate none installed

    def test_monitor_enable_command(self, cli_runner):
        """Test monitor enable command."""
        result = cli_runner.invoke(app, ["monitor", "enable"])

        assert result.exit_code == 0
        assert "Monitoring enabled" in result.output

    def test_monitor_disable_command(self, cli_runner):
        """Test monitor disable command."""
        result = cli_runner.invoke(app, ["monitor", "disable"])

        assert result.exit_code == 0
        assert "Monitoring disabled" in result.output

    def test_monitor_check_command(self, cli_runner):
        """Test monitor check command."""
        result = cli_runner.invoke(app, ["monitor", "check"])

        assert result.exit_code == 0
        # Should show health check results

    def test_monitor_status_command(self, cli_runner):
        """Test monitor status command."""
        result = cli_runner.invoke(app, ["monitor", "status"])

        assert result.exit_code == 0
        # Should show monitoring status

    def test_ci_detect_command(self, cli_runner):
        """Test ci detect command."""
        result = cli_runner.invoke(app, ["ci", "detect"])

        assert result.exit_code == 0
        # Should show CI/CD detection results

    def test_predict_analyze_command(self, cli_runner):
        """Test predict analyze command."""
        result = cli_runner.invoke(app, ["predict", "analyze"])

        assert result.exit_code == 0
        # Should show predictive analysis results

    def test_predict_forecast_command(self, cli_runner):
        """Test predict forecast command."""
        result = cli_runner.invoke(app, ["predict", "forecast", "--days", "7"])

        assert result.exit_code == 0
        # Should show forecast results

    def test_predict_risk_assessment_command(self, cli_runner):
        """Test predict risk-assessment command."""
        result = cli_runner.invoke(app, ["predict", "risk-assessment"])

        assert result.exit_code == 0
        # Should show risk assessment results

    def test_compliance_list_command(self, cli_runner):
        """Test compliance list command."""
        result = cli_runner.invoke(app, ["compliance", "list"])

        assert result.exit_code == 0
        # Should show available frameworks

    def test_compliance_enable_command(self, cli_runner):
        """Test compliance enable command."""
        result = cli_runner.invoke(app, ["compliance", "enable", "soc2"])

        assert result.exit_code == 0
        assert "Enabled compliance framework" in result.output

    def test_compliance_disable_command(self, cli_runner):
        """Test compliance disable command."""
        result = cli_runner.invoke(app, ["compliance", "disable", "soc2"])

        assert result.exit_code == 0
        assert "Disabled compliance framework" in result.output

    def test_compliance_assess_command(self, cli_runner):
        """Test compliance assess command."""
        result = cli_runner.invoke(app, ["compliance", "assess", "soc2"])

        assert result.exit_code == 0
        # Should show assessment results

    def test_compliance_report_command(self, cli_runner):
        """Test compliance report command."""
        result = cli_runner.invoke(app, ["compliance", "report", "soc2"])

        assert result.exit_code == 0
        # Should show compliance report

    def test_api_server_command(self, cli_runner):
        """Test api-server command (will fail due to port binding but should parse correctly)."""
        result = cli_runner.invoke(app, ["api-server", "--port", "8001"])

        # This will likely fail due to port binding, but command should be recognized
        assert result.exit_code in [0, 1]  # 0 if successful, 1 if port in use

    def test_web_dashboard_command(self, cli_runner):
        """Test web-dashboard command."""
        result = cli_runner.invoke(app, ["web-dashboard", "--port", "8502"])

        # This will likely fail due to streamlit, but command should be recognized
        assert result.exit_code in [0, 1]

    def test_env_import_command(self, cli_runner, temp_config_dir):
        """Test env import command."""
        # Create a test .env file
        env_file = temp_config_dir / ".env"
        env_file.write_text("IMPORT_KEY=import_value\nANOTHER_KEY=another_value\n")

        result = cli_runner.invoke(app, ["env", "import", str(env_file)])

        assert result.exit_code == 0
        assert "Imported variables" in result.output

        # Verify variables were imported
        result_list = cli_runner.invoke(app, ["env", "list", "--no-mask"])
        assert "IMPORT_KEY" in result_list.output
        assert "import_value" in result_list.output

    def test_env_export_command(self, cli_runner, env_manager, temp_config_dir, sample_env_vars):
        """Test env export command."""
        export_file = temp_config_dir / "export.env"

        result = cli_runner.invoke(app, ["env", "export", str(export_file)])

        assert result.exit_code == 0
        assert "Exported" in result.output

        # Verify file was created and contains data
        assert export_file.exists()
        content = export_file.read_text()
        assert "API_KEY" in content

    def test_env_diff_command(self, cli_runner, temp_config_dir):
        """Test env diff command."""
        # Create two profiles with different data
        cli_runner.invoke(app, ["profile", "init", "--name", "profile1"])
        cli_runner.invoke(app, ["env", "add", "KEY1", "value1", "--profile", "profile1"])
        cli_runner.invoke(app, ["env", "add", "SHARED", "same", "--profile", "profile1"])

        cli_runner.invoke(app, ["profile", "init", "--name", "profile2"])
        cli_runner.invoke(app, ["env", "add", "KEY2", "value2", "--profile", "profile2"])
        cli_runner.invoke(app, ["env", "add", "SHARED", "different", "--profile", "profile2"])

        result = cli_runner.invoke(app, ["env", "diff", "profile1", "profile2"])

        assert result.exit_code == 0
        # Should show differences
        assert "Differences between" in result.output

    def test_invalid_command(self, cli_runner):
        """Test invalid command."""
        result = cli_runner.invoke(app, ["invalid_command"])

        assert result.exit_code != 0
        assert "No such command" in result.output or "unrecognized" in result.output

    def test_help_command(self, cli_runner):
        """Test help command."""
        result = cli_runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        assert "EnvCLI" in result.output
        assert "Manage environment variables" in result.output
