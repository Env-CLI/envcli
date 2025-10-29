"""
Policy engine for EnvCLI - Enforce rules on environment variables.
"""

import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
from .config import CONFIG_DIR
from .env_manager import EnvManager

POLICY_FILE = CONFIG_DIR / "policies.json"

class PolicyEngine:
    """Enforce policies on environment variables."""

    def __init__(self):
        self.policies = self._load_policies()

    def _load_policies(self) -> Dict[str, Any]:
        """Load policy definitions."""
        if POLICY_FILE.exists():
            with open(POLICY_FILE, 'r') as f:
                return json.load(f)
        return {
            "required_keys": [],
            "prohibited_patterns": [],
            "naming_conventions": [],
            "key_rotation_schedule": None,
            "value_constraints": [],
            "enabled": True
        }

    def _save_policies(self):
        """Save policy definitions."""
        POLICY_FILE.parent.mkdir(exist_ok=True)
        with open(POLICY_FILE, 'w') as f:
            json.dump(self.policies, f, indent=2)

    def add_required_key_policy(self, key_pattern: str, description: str = ""):
        """Add a policy for required keys."""
        policy = {
            "type": "required_key",
            "pattern": key_pattern,
            "description": description,
            "created_at": datetime.now().isoformat()
        }
        self.policies["required_keys"].append(policy)
        self._save_policies()

    def add_prohibited_pattern_policy(self, pattern: str, description: str = ""):
        """Add a policy for prohibited patterns."""
        policy = {
            "type": "prohibited_pattern",
            "pattern": pattern,
            "description": description,
            "created_at": datetime.now().isoformat()
        }
        self.policies["prohibited_patterns"].append(policy)
        self._save_policies()

    def add_naming_convention_policy(self, convention: str, description: str = ""):
        """Add a naming convention policy."""
        policy = {
            "type": "naming_convention",
            "convention": convention,
            "description": description,
            "created_at": datetime.now().isoformat()
        }
        self.policies["naming_conventions"].append(policy)
        self._save_policies()

    def set_key_rotation_schedule(self, days: int):
        """Set key rotation schedule in days."""
        self.policies["key_rotation_schedule"] = {
            "days": days,
            "last_rotation": datetime.now().isoformat()
        }
        self._save_policies()

    def validate_profile(self, profile: str) -> Dict[str, Any]:
        """Validate a profile against all policies."""
        if not self.policies.get("enabled", True):
            return {"valid": True, "violations": [], "message": "Policy engine disabled"}

        manager = EnvManager(profile)
        env_vars = manager.load_env()

        violations = []

        # Check required keys
        violations.extend(self._check_required_keys(env_vars, profile))

        # Check prohibited patterns
        violations.extend(self._check_prohibited_patterns(env_vars, profile))

        # Check naming conventions
        violations.extend(self._check_naming_conventions(env_vars, profile))

        # Check value constraints
        violations.extend(self._check_value_constraints(env_vars, profile))

        # Check key rotation
        rotation_violations = self._check_key_rotation(profile)
        if rotation_violations:
            violations.extend(rotation_violations)

        result = {
            "valid": len(violations) == 0,
            "violations": violations,
            "profile": profile,
            "validated_at": datetime.now().isoformat()
        }

        return result

    def _check_required_keys(self, env_vars: Dict[str, str], profile: str) -> List[Dict[str, Any]]:
        """Check for required keys."""
        violations = []

        for policy in self.policies["required_keys"]:
            pattern = policy["pattern"]
            regex = re.compile(pattern)

            found = any(regex.match(key) for key in env_vars.keys())

            if not found:
                violations.append({
                    "policy_type": "required_key",
                    "severity": "error",
                    "message": f"Required key pattern '{pattern}' not found",
                    "profile": profile,
                    "policy": policy
                })

        return violations

    def _check_prohibited_patterns(self, env_vars: Dict[str, str], profile: str) -> List[Dict[str, Any]]:
        """Check for prohibited patterns in values."""
        violations = []

        for policy in self.policies["prohibited_patterns"]:
            pattern = policy["pattern"]

            for key, value in env_vars.items():
                if re.search(pattern, value, re.IGNORECASE):
                    violations.append({
                        "policy_type": "prohibited_pattern",
                        "severity": "high",
                        "message": f"Prohibited pattern '{pattern}' found in variable '{key}'",
                        "profile": profile,
                        "variable": key,
                        "policy": policy
                    })

        return violations

    def _check_naming_conventions(self, env_vars: Dict[str, str], profile: str) -> List[Dict[str, Any]]:
        """Check naming conventions."""
        violations = []

        for policy in self.policies["naming_conventions"]:
            convention = policy["convention"]

            for key in env_vars.keys():
                if convention == "uppercase" and not key.isupper():
                    violations.append({
                        "policy_type": "naming_convention",
                        "severity": "medium",
                        "message": f"Variable '{key}' should be uppercase",
                        "profile": profile,
                        "variable": key,
                        "policy": policy
                    })
                elif convention == "snake_case" and not re.match(r'^[a-z][a-z0-9_]*[a-z0-9]$', key):
                    violations.append({
                        "policy_type": "naming_convention",
                        "severity": "low",
                        "message": f"Variable '{key}' should follow snake_case convention",
                        "profile": profile,
                        "variable": key,
                        "policy": policy
                    })

        return violations

    def _check_value_constraints(self, env_vars: Dict[str, str], profile: str) -> List[Dict[str, Any]]:
        """Check value constraints."""
        violations = []

        for policy in self.policies["value_constraints"]:
            constraint_type = policy.get("constraint_type")
            pattern = policy.get("pattern", "")
            max_length = policy.get("max_length")

            for key, value in env_vars.items():
                if constraint_type == "pattern" and pattern:
                    if not re.match(pattern, value):
                        violations.append({
                            "policy_type": "value_constraint",
                            "severity": "medium",
                            "message": f"Value for '{key}' doesn't match required pattern",
                            "profile": profile,
                            "variable": key,
                            "policy": policy
                        })

                elif constraint_type == "max_length" and max_length:
                    if len(value) > max_length:
                        violations.append({
                            "policy_type": "value_constraint",
                            "severity": "low",
                            "message": f"Value for '{key}' exceeds maximum length of {max_length}",
                            "profile": profile,
                            "variable": key,
                            "policy": policy
                        })

        return violations

    def _check_key_rotation(self, profile: str) -> List[Dict[str, Any]]:
        """Check if key rotation is needed."""
        violations = []

        rotation_schedule = self.policies.get("key_rotation_schedule")
        if rotation_schedule:
            days = rotation_schedule["days"]
            last_rotation = datetime.fromisoformat(rotation_schedule["last_rotation"])
            days_since_rotation = (datetime.now() - last_rotation).days

            if days_since_rotation > days:
                violations.append({
                    "policy_type": "key_rotation",
                    "severity": "medium",
                    "message": f"Key rotation overdue by {days_since_rotation - days} days",
                    "profile": profile,
                    "days_overdue": days_since_rotation - days
                })

        return violations

    def enforce_policies_on_change(self, profile: str, changes: Dict[str, Any]) -> Dict[str, Any]:
        """Enforce policies when environment variables change."""
        validation = self.validate_profile(profile)

        if not validation["valid"]:
            # Block changes that violate policies
            return {
                "allowed": False,
                "violations": validation["violations"],
                "message": "Policy violations prevent this change"
            }

        return {
            "allowed": True,
            "violations": [],
            "message": "All policies satisfied"
        }

    def get_policy_summary(self) -> Dict[str, Any]:
        """Get a summary of all policies."""
        return {
            "enabled": self.policies.get("enabled", True),
            "required_keys_count": len(self.policies["required_keys"]),
            "prohibited_patterns_count": len(self.policies["prohibited_patterns"]),
            "naming_conventions_count": len(self.policies["naming_conventions"]),
            "key_rotation_enabled": self.policies.get("key_rotation_schedule") is not None,
            "last_updated": datetime.now().isoformat()
        }
