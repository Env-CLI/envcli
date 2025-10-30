import json
from pathlib import Path
from typing import Dict, Any, List
import jsonschema
from .env_manager import EnvManager

def validate_env_vars(env_vars: Dict[str, str], schema_path: str, strict: bool = False) -> List[str]:
    """Validate environment variables against a schema.

    Returns a list of validation errors.
    """
    schema_file = Path(schema_path)
    if not schema_file.exists():
        raise FileNotFoundError(f"Schema file {schema_path} not found")

    with open(schema_file, 'r') as f:
        if schema_file.suffix == '.json':
            schema = json.load(f)
        elif schema_file.suffix in ['.yaml', '.yml']:
            import yaml
            schema = yaml.safe_load(f)
        else:
            raise ValueError("Schema must be JSON or YAML")

    # Convert env vars to the format expected by the schema
    # Assume schema expects object with string values
    try:
        jsonschema.validate(env_vars, schema)
        return []
    except jsonschema.ValidationError as e:
        if strict:
            return [str(e)]
        else:
            # In non-strict mode, collect all errors
            errors = []
            while e:
                errors.append(f"{e.message} at {e.absolute_path}")
                e = e.context[0] if e.context else None
            return errors
    except Exception as e:
        return [f"Schema validation error: {e}"]

def validate_profile(profile: str, schema_path: str, strict: bool = False) -> List[str]:
    """Validate a profile against a schema."""
    manager = EnvManager(profile)
    env_vars = manager.load_env()
    return validate_env_vars(env_vars, schema_path, strict)
