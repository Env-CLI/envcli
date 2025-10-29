import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from envcli.validation import validate_env_vars, validate_profile


class TestValidation:
    def test_validate_env_vars_valid_json_schema(self, temp_config_dir):
        """Test validating env vars against a valid JSON schema."""
        # Create test schema
        schema = {
            "type": "object",
            "properties": {
                "API_KEY": {"type": "string"},
                "DATABASE_URL": {"type": "string"},
                "DEBUG": {"type": "string", "enum": ["true", "false"]}
            },
            "required": ["API_KEY", "DATABASE_URL"]
        }
        schema_file = temp_config_dir / "schema.json"
        with open(schema_file, 'w') as f:
            json.dump(schema, f)

        # Test data that should pass validation
        env_vars = {
            "API_KEY": "test-key",
            "DATABASE_URL": "postgresql://localhost/db",
            "DEBUG": "true"
        }

        errors = validate_env_vars(env_vars, str(schema_file))
        assert errors == []

    def test_validate_env_vars_valid_yaml_schema(self, temp_config_dir):
        """Test validating env vars against a valid YAML schema."""
        import yaml

        # Create test schema
        schema = {
            "type": "object",
            "properties": {
                "API_KEY": {"type": "string"},
                "PORT": {"type": "string", "pattern": "^\\d+$"}
            },
            "required": ["API_KEY"]
        }
        schema_file = temp_config_dir / "schema.yaml"
        with open(schema_file, 'w') as f:
            yaml.dump(schema, f)

        # Test data that should pass validation
        env_vars = {
            "API_KEY": "test-key",
            "PORT": "8080"
        }

        errors = validate_env_vars(env_vars, str(schema_file))
        assert errors == []

    def test_validate_env_vars_missing_required_field(self, temp_config_dir):
        """Test validation fails when required field is missing."""
        schema = {
            "type": "object",
            "properties": {
                "API_KEY": {"type": "string"},
                "DATABASE_URL": {"type": "string"}
            },
            "required": ["API_KEY", "DATABASE_URL"]
        }
        schema_file = temp_config_dir / "schema.json"
        with open(schema_file, 'w') as f:
            json.dump(schema, f)

        # Missing required DATABASE_URL
        env_vars = {
            "API_KEY": "test-key"
        }

        errors = validate_env_vars(env_vars, str(schema_file))
        assert len(errors) > 0
        assert any("DATABASE_URL" in error for error in errors)

    def test_validate_env_vars_wrong_type(self, temp_config_dir):
        """Test validation fails when field has wrong type."""
        schema = {
            "type": "object",
            "properties": {
                "PORT": {"type": "integer"}
            }
        }
        schema_file = temp_config_dir / "schema.json"
        with open(schema_file, 'w') as f:
            json.dump(schema, f)

        # PORT should be integer but is string
        env_vars = {
            "PORT": "8080"
        }

        errors = validate_env_vars(env_vars, str(schema_file))
        assert len(errors) > 0
        assert any("PORT" in error for error in errors)

    def test_validate_env_vars_enum_violation(self, temp_config_dir):
        """Test validation fails when enum constraint is violated."""
        schema = {
            "type": "object",
            "properties": {
                "ENV": {"type": "string", "enum": ["dev", "staging", "prod"]}
            }
        }
        schema_file = temp_config_dir / "schema.json"
        with open(schema_file, 'w') as f:
            json.dump(schema, f)

        # ENV has invalid value
        env_vars = {
            "ENV": "invalid"
        }

        errors = validate_env_vars(env_vars, str(schema_file))
        assert len(errors) > 0
        assert any("ENV" in error for error in errors)

    def test_validate_env_vars_pattern_violation(self, temp_config_dir):
        """Test validation fails when pattern constraint is violated."""
        schema = {
            "type": "object",
            "properties": {
                "EMAIL": {"type": "string", "pattern": "^[^@]+@[^@]+\\.[^@]+$"}
            }
        }
        schema_file = temp_config_dir / "schema.json"
        with open(schema_file, 'w') as f:
            json.dump(schema, f)

        # EMAIL doesn't match pattern
        env_vars = {
            "EMAIL": "invalid-email"
        }

        errors = validate_env_vars(env_vars, str(schema_file))
        assert len(errors) > 0
        assert any("EMAIL" in error for error in errors)

    def test_validate_env_vars_strict_mode(self, temp_config_dir):
        """Test validation in strict mode returns single error."""
        schema = {
            "type": "object",
            "properties": {
                "API_KEY": {"type": "string"},
                "DATABASE_URL": {"type": "string"}
            },
            "required": ["API_KEY", "DATABASE_URL"]
        }
        schema_file = temp_config_dir / "schema.json"
        with open(schema_file, 'w') as f:
            json.dump(schema, f)

        # Missing both required fields
        env_vars = {}

        errors = validate_env_vars(env_vars, str(schema_file), strict=True)
        assert len(errors) == 1  # Only one error in strict mode

    def test_validate_env_vars_non_strict_mode(self, temp_config_dir):
        """Test validation in non-strict mode returns multiple errors."""
        schema = {
            "type": "object",
            "properties": {
                "API_KEY": {"type": "string"},
                "DATABASE_URL": {"type": "string"},
                "PORT": {"type": "string"}
            },
            "required": ["API_KEY", "DATABASE_URL", "PORT"]
        }
        schema_file = temp_config_dir / "schema.json"
        with open(schema_file, 'w') as f:
            json.dump(schema, f)

        # Missing all required fields
        env_vars = {}

        errors = validate_env_vars(env_vars, str(schema_file), strict=False)
        assert len(errors) >= 1  # Multiple errors in non-strict mode

    def test_validate_env_vars_schema_not_found(self, temp_config_dir):
        """Test validation fails when schema file doesn't exist."""
        env_vars = {"API_KEY": "test"}
        nonexistent_schema = temp_config_dir / "nonexistent.json"

        with pytest.raises(FileNotFoundError, match="Schema file .* not found"):
            validate_env_vars(env_vars, str(nonexistent_schema))

    def test_validate_env_vars_unsupported_format(self, temp_config_dir):
        """Test validation fails with unsupported schema format."""
        env_vars = {"API_KEY": "test"}
        schema_file = temp_config_dir / "schema.txt"
        schema_file.write_text("invalid format")

        with pytest.raises(ValueError, match="Schema must be JSON or YAML"):
            validate_env_vars(env_vars, str(schema_file))

    def test_validate_env_vars_json_schema_error(self, temp_config_dir):
        """Test validation handles JSON schema errors gracefully."""
        # Invalid schema that will cause jsonschema error
        invalid_schema = {
            "type": "invalid_type",
            "properties": {}
        }
        schema_file = temp_config_dir / "invalid.json"
        with open(schema_file, 'w') as f:
            json.dump(invalid_schema, f)

        env_vars = {"API_KEY": "test"}

        errors = validate_env_vars(env_vars, str(schema_file))
        assert len(errors) > 0
        assert any("Schema validation error" in error for error in errors)

    @patch('envcli.validation.EnvManager')
    def test_validate_profile(self, mock_env_manager, temp_config_dir):
        """Test validating a profile against schema."""
        # Mock EnvManager
        mock_manager = MagicMock()
        mock_env_manager.return_value = mock_manager
        mock_manager.load_env.return_value = {
            "API_KEY": "test-key",
            "DATABASE_URL": "postgresql://localhost/db"
        }

        # Create valid schema
        schema = {
            "type": "object",
            "properties": {
                "API_KEY": {"type": "string"},
                "DATABASE_URL": {"type": "string"}
            },
            "required": ["API_KEY"]
        }
        schema_file = temp_config_dir / "schema.json"
        with open(schema_file, 'w') as f:
            json.dump(schema, f)

        errors = validate_profile("test_profile", str(schema_file))

        assert errors == []
        mock_env_manager.assert_called_with("test_profile")
        mock_manager.load_env.assert_called_once()

    @patch('envcli.validation.EnvManager')
    def test_validate_profile_with_errors(self, mock_env_manager, temp_config_dir):
        """Test validating a profile that has validation errors."""
        # Mock EnvManager
        mock_manager = MagicMock()
        mock_env_manager.return_value = mock_manager
        mock_manager.load_env.return_value = {
            "API_KEY": "test-key"
            # Missing DATABASE_URL
        }

        # Create schema requiring DATABASE_URL
        schema = {
            "type": "object",
            "properties": {
                "API_KEY": {"type": "string"},
                "DATABASE_URL": {"type": "string"}
            },
            "required": ["API_KEY", "DATABASE_URL"]
        }
        schema_file = temp_config_dir / "schema.json"
        with open(schema_file, 'w') as f:
            json.dump(schema, f)

        errors = validate_profile("test_profile", str(schema_file))

        assert len(errors) > 0
        assert any("DATABASE_URL" in error for error in errors)

    def test_validate_env_vars_complex_schema(self, temp_config_dir):
        """Test validation with complex schema including nested objects."""
        schema = {
            "type": "object",
            "properties": {
                "APP_CONFIG": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "version": {"type": "string"}
                    },
                    "required": ["name"]
                },
                "FEATURE_FLAGS": {
                    "type": "object",
                    "patternProperties": {
                        ".*": {"type": "boolean"}
                    }
                }
            }
        }
        schema_file = temp_config_dir / "complex.json"
        with open(schema_file, 'w') as f:
            json.dump(schema, f)

        # Valid data
        env_vars = {
            "APP_CONFIG": '{"name": "myapp", "version": "1.0"}',
            "FEATURE_FLAGS": '{"debug": true, "experimental": false}'
        }

        # This is a simplified test - in reality, the env vars are strings
        # but the schema expects objects. This would normally fail,
        # but we're testing the validation mechanism
        errors = validate_env_vars(env_vars, str(schema_file))
        # Since env_vars contains strings but schema expects objects,
        # this should produce validation errors
        assert len(errors) > 0

    def test_validate_env_vars_empty_schema(self, temp_config_dir):
        """Test validation with empty schema (should accept anything)."""
        schema = {"type": "object"}
        schema_file = temp_config_dir / "empty.json"
        with open(schema_file, 'w') as f:
            json.dump(schema, f)

        env_vars = {
            "ANY_KEY": "any_value",
            "ANOTHER_KEY": "another_value"
        }

        errors = validate_env_vars(env_vars, str(schema_file))
        assert errors == []

    def test_validate_env_vars_additional_properties(self, temp_config_dir):
        """Test validation with additionalProperties constraint."""
        schema = {
            "type": "object",
            "properties": {
                "API_KEY": {"type": "string"}
            },
            "additionalProperties": False
        }
        schema_file = temp_config_dir / "strict.json"
        with open(schema_file, 'w') as f:
            json.dump(schema, f)

        # Valid: only allowed property
        valid_vars = {"API_KEY": "test"}

        # Invalid: extra property
        invalid_vars = {"API_KEY": "test", "EXTRA": "not_allowed"}

        assert validate_env_vars(valid_vars, str(schema_file)) == []
        assert len(validate_env_vars(invalid_vars, str(schema_file))) > 0
