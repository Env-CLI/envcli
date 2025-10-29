"""
AI Actions - Safe application of AI recommendations without compromising secrets.

This module provides functionality to apply AI-generated recommendations
while preserving all sensitive values.
"""

import json
import re
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from pathlib import Path
from .env_manager import EnvManager
from .config import CONFIG_DIR

ACTIONS_LOG_FILE = CONFIG_DIR / "ai_actions_log.json"
AI_RULES_FILE = CONFIG_DIR / "ai_rules.json"


class AIAction:
    """Represents a single AI-recommended action."""
    
    def __init__(self, action_type: str, description: str, details: Dict[str, Any]):
        self.action_type = action_type
        self.description = description
        self.details = details
        self.applied = False
        self.timestamp = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "action_type": self.action_type,
            "description": self.description,
            "details": self.details,
            "applied": self.applied,
            "timestamp": self.timestamp
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AIAction':
        action = cls(data["action_type"], data["description"], data["details"])
        action.applied = data.get("applied", False)
        action.timestamp = data.get("timestamp")
        return action


class AIActionExecutor:
    """Executes AI recommendations safely without exposing secrets."""

    def __init__(self, profile: str):
        self.profile = profile
        self.manager = EnvManager(profile)
        self.actions: List[AIAction] = []
        self.custom_rules = self._load_custom_rules()
    
    def parse_recommendations(self, recommendations: str) -> List[AIAction]:
        """
        Parse AI recommendations and extract actionable items.

        This looks for common patterns in AI recommendations:
        - Rename X to Y
        - Add prefix/suffix
        - Standardize naming
        - Group related variables

        Also applies custom rules if enabled.
        """
        actions = []

        # First, apply custom rules if enabled
        if self.custom_rules.get("enabled", True):
            custom_actions = self.apply_custom_rules()
            actions.extend(custom_actions)

        # Get current variables
        env_vars = self.manager.load_env()
        var_names = list(env_vars.keys())
        
        # Pattern 1: Rename suggestions
        # Look for: "rename X to Y", "X should be Y", "change X to Y"
        for var_name in var_names:
            # Check for lowercase that should be uppercase
            if var_name.islower() and any(word in var_name for word in ['key', 'secret', 'token', 'password']):
                new_name = var_name.upper()
                actions.append(AIAction(
                    action_type="rename",
                    description=f"Rename '{var_name}' to '{new_name}' (uppercase for secrets)",
                    details={
                        "old_name": var_name,
                        "new_name": new_name,
                        "reason": "Secret variables should be uppercase"
                    }
                ))
            
            # Check for inconsistent naming (mixed case)
            if any(c.isupper() for c in var_name) and any(c.islower() for c in var_name) and '_' not in var_name:
                new_name = var_name.upper()
                actions.append(AIAction(
                    action_type="rename",
                    description=f"Standardize '{var_name}' to '{new_name}' (consistent case)",
                    details={
                        "old_name": var_name,
                        "new_name": new_name,
                        "reason": "Use consistent UPPER_SNAKE_CASE"
                    }
                ))
        
        # Pattern 2: Add prefixes for organization
        # Group variables by common patterns
        groups = self._identify_variable_groups(var_names)
        for group_name, variables in groups.items():
            if len(variables) > 1 and not all(v.startswith(group_name.upper() + '_') for v in variables):
                for var in variables:
                    if not var.startswith(group_name.upper() + '_'):
                        new_name = f"{group_name.upper()}_{var}"
                        actions.append(AIAction(
                            action_type="add_prefix",
                            description=f"Add '{group_name.upper()}_' prefix to '{var}'",
                            details={
                                "old_name": var,
                                "new_name": new_name,
                                "prefix": group_name.upper(),
                                "reason": f"Group {group_name}-related variables"
                            }
                        ))
        
        self.actions = actions
        return actions
    
    def _identify_variable_groups(self, var_names: List[str]) -> Dict[str, List[str]]:
        """Identify groups of related variables."""
        groups = {}
        
        # Common prefixes to look for
        common_groups = {
            'database': ['db', 'database', 'postgres', 'mysql', 'mongo'],
            'api': ['api', 'endpoint', 'url'],
            'auth': ['auth', 'token', 'key', 'secret', 'password'],
            'aws': ['aws', 's3', 'ec2', 'lambda'],
            'redis': ['redis', 'cache'],
            'email': ['email', 'smtp', 'mail'],
        }
        
        for group_name, keywords in common_groups.items():
            matching_vars = []
            for var in var_names:
                var_lower = var.lower()
                if any(keyword in var_lower for keyword in keywords):
                    matching_vars.append(var)
            
            if matching_vars:
                groups[group_name] = matching_vars
        
        return groups
    
    def preview_actions(self) -> List[Dict[str, Any]]:
        """Preview all pending actions without applying them."""
        return [action.to_dict() for action in self.actions if not action.applied]
    
    def apply_action(self, action: AIAction, dry_run: bool = False) -> Dict[str, Any]:
        """
        Apply a single action safely.
        
        Args:
            action: The action to apply
            dry_run: If True, don't actually make changes
            
        Returns:
            Result dictionary with success status and details
        """
        env_vars = self.manager.load_env()
        
        if action.action_type == "rename":
            old_name = action.details["old_name"]
            new_name = action.details["new_name"]
            
            if old_name not in env_vars:
                return {
                    "success": False,
                    "message": f"Variable '{old_name}' not found",
                    "action": action.to_dict()
                }
            
            if new_name in env_vars:
                return {
                    "success": False,
                    "message": f"Variable '{new_name}' already exists",
                    "action": action.to_dict()
                }
            
            if not dry_run:
                # Preserve the value, just change the key
                value = env_vars[old_name]
                del env_vars[old_name]
                env_vars[new_name] = value
                self.manager.save_env(env_vars)
                
                action.applied = True
                action.timestamp = datetime.now().isoformat()
                self._log_action(action)
            
            return {
                "success": True,
                "message": f"Renamed '{old_name}' to '{new_name}'",
                "action": action.to_dict(),
                "dry_run": dry_run
            }
        
        elif action.action_type == "add_prefix":
            old_name = action.details["old_name"]
            new_name = action.details["new_name"]
            
            if old_name not in env_vars:
                return {
                    "success": False,
                    "message": f"Variable '{old_name}' not found",
                    "action": action.to_dict()
                }
            
            if new_name in env_vars:
                return {
                    "success": False,
                    "message": f"Variable '{new_name}' already exists",
                    "action": action.to_dict()
                }
            
            if not dry_run:
                # Preserve the value, just change the key
                value = env_vars[old_name]
                del env_vars[old_name]
                env_vars[new_name] = value
                self.manager.save_env(env_vars)
                
                action.applied = True
                action.timestamp = datetime.now().isoformat()
                self._log_action(action)
            
            return {
                "success": True,
                "message": f"Added prefix to '{old_name}' → '{new_name}'",
                "action": action.to_dict(),
                "dry_run": dry_run
            }
        
        return {
            "success": False,
            "message": f"Unknown action type: {action.action_type}",
            "action": action.to_dict()
        }
    
    def apply_all_actions(self, dry_run: bool = False) -> Dict[str, Any]:
        """
        Apply all pending actions.
        
        Args:
            dry_run: If True, preview changes without applying
            
        Returns:
            Summary of all actions
        """
        results = []
        success_count = 0
        failure_count = 0
        
        for action in self.actions:
            if not action.applied:
                result = self.apply_action(action, dry_run=dry_run)
                results.append(result)
                
                if result["success"]:
                    success_count += 1
                else:
                    failure_count += 1
        
        return {
            "total_actions": len(results),
            "successful": success_count,
            "failed": failure_count,
            "results": results,
            "dry_run": dry_run
        }
    
    def _log_action(self, action: AIAction):
        """Log an applied action for audit trail."""
        log_entry = {
            "profile": self.profile,
            "action": action.to_dict(),
            "timestamp": datetime.now().isoformat()
        }
        
        # Load existing log
        log = []
        if ACTIONS_LOG_FILE.exists():
            with open(ACTIONS_LOG_FILE, 'r') as f:
                log = json.load(f)
        
        # Append new entry
        log.append(log_entry)
        
        # Save log
        ACTIONS_LOG_FILE.parent.mkdir(exist_ok=True)
        with open(ACTIONS_LOG_FILE, 'w') as f:
            json.dump(log, f, indent=2)
    
    def get_action_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get history of applied actions."""
        if not ACTIONS_LOG_FILE.exists():
            return []

        with open(ACTIONS_LOG_FILE, 'r') as f:
            log = json.load(f)

        # Filter by profile and return most recent
        profile_log = [entry for entry in log if entry["profile"] == self.profile]
        return profile_log[-limit:]

    def _load_custom_rules(self) -> Dict[str, Any]:
        """Load custom AI action rules."""
        if AI_RULES_FILE.exists():
            with open(AI_RULES_FILE, 'r') as f:
                return json.load(f)
        return {
            "naming_rules": [],
            "prefix_rules": [],
            "transformation_rules": [],
            "exclusions": [],
            "enabled": True
        }

    def _save_custom_rules(self):
        """Save custom rules to file."""
        AI_RULES_FILE.parent.mkdir(exist_ok=True)
        with open(AI_RULES_FILE, 'w') as f:
            json.dump(self.custom_rules, f, indent=2)

    def add_naming_rule(self, pattern: str, target_format: str, description: str = ""):
        """
        Add a custom naming rule.

        Args:
            pattern: Regex pattern to match variable names
            target_format: Target naming format (uppercase, lowercase, snake_case, etc.)
            description: Human-readable description
        """
        rule = {
            "type": "naming",
            "pattern": pattern,
            "target_format": target_format,
            "description": description,
            "created_at": datetime.now().isoformat()
        }
        self.custom_rules["naming_rules"].append(rule)
        self._save_custom_rules()

    def add_prefix_rule(self, pattern: str, prefix: str, description: str = ""):
        """
        Add a custom prefix rule.

        Args:
            pattern: Regex pattern to match variable names
            prefix: Prefix to add
            description: Human-readable description
        """
        rule = {
            "type": "prefix",
            "pattern": pattern,
            "prefix": prefix,
            "description": description,
            "created_at": datetime.now().isoformat()
        }
        self.custom_rules["prefix_rules"].append(rule)
        self._save_custom_rules()

    def add_transformation_rule(self, pattern: str, transformation: str, description: str = ""):
        """
        Add a custom transformation rule.

        Args:
            pattern: Regex pattern to match variable names
            transformation: Transformation to apply (e.g., "replace:old:new")
            description: Human-readable description
        """
        rule = {
            "type": "transformation",
            "pattern": pattern,
            "transformation": transformation,
            "description": description,
            "created_at": datetime.now().isoformat()
        }
        self.custom_rules["transformation_rules"].append(rule)
        self._save_custom_rules()

    def add_exclusion(self, pattern: str, description: str = ""):
        """
        Add an exclusion pattern (variables that should never be modified).

        Args:
            pattern: Regex pattern to match variable names to exclude
            description: Human-readable description
        """
        exclusion = {
            "pattern": pattern,
            "description": description,
            "created_at": datetime.now().isoformat()
        }
        self.custom_rules["exclusions"].append(exclusion)
        self._save_custom_rules()

    def list_custom_rules(self) -> Dict[str, Any]:
        """List all custom rules."""
        return self.custom_rules

    def remove_rule(self, rule_type: str, index: int) -> bool:
        """
        Remove a custom rule by type and index.

        Args:
            rule_type: Type of rule (naming_rules, prefix_rules, transformation_rules, exclusions)
            index: Index of the rule to remove

        Returns:
            True if removed, False if not found
        """
        if rule_type not in self.custom_rules:
            return False

        rules = self.custom_rules[rule_type]
        if 0 <= index < len(rules):
            rules.pop(index)
            self._save_custom_rules()
            return True

        return False

    def _is_excluded(self, var_name: str) -> bool:
        """Check if a variable is excluded from modifications."""
        for exclusion in self.custom_rules.get("exclusions", []):
            pattern = exclusion["pattern"]
            if re.match(pattern, var_name):
                return True
        return False

    def apply_custom_rules(self) -> List[AIAction]:
        """
        Apply custom rules to generate actions.

        Returns:
            List of actions generated from custom rules
        """
        if not self.custom_rules.get("enabled", True):
            return []

        actions = []
        env_vars = self.manager.load_env()
        var_names = list(env_vars.keys())

        # Apply naming rules
        for rule in self.custom_rules.get("naming_rules", []):
            pattern = rule["pattern"]
            target_format = rule["target_format"]

            for var_name in var_names:
                if self._is_excluded(var_name):
                    continue

                if re.match(pattern, var_name):
                    new_name = self._apply_naming_format(var_name, target_format)
                    if new_name != var_name:
                        actions.append(AIAction(
                            action_type="rename",
                            description=f"Apply naming rule: '{var_name}' to '{new_name}'",
                            details={
                                "old_name": var_name,
                                "new_name": new_name,
                                "reason": rule.get("description", "Custom naming rule"),
                                "rule_type": "custom_naming"
                            }
                        ))

        # Apply prefix rules
        for rule in self.custom_rules.get("prefix_rules", []):
            pattern = rule["pattern"]
            prefix = rule["prefix"]

            for var_name in var_names:
                if self._is_excluded(var_name):
                    continue

                if re.match(pattern, var_name) and not var_name.startswith(prefix):
                    new_name = f"{prefix}{var_name}"
                    actions.append(AIAction(
                        action_type="add_prefix",
                        description=f"Add prefix '{prefix}' to '{var_name}'",
                        details={
                            "old_name": var_name,
                            "new_name": new_name,
                            "prefix": prefix,
                            "reason": rule.get("description", "Custom prefix rule"),
                            "rule_type": "custom_prefix"
                        }
                    ))

        # Apply transformation rules
        for rule in self.custom_rules.get("transformation_rules", []):
            pattern = rule["pattern"]
            transformation = rule["transformation"]

            for var_name in var_names:
                if self._is_excluded(var_name):
                    continue

                if re.match(pattern, var_name):
                    new_name = self._apply_transformation(var_name, transformation)
                    if new_name != var_name:
                        actions.append(AIAction(
                            action_type="transform",
                            description=f"Transform '{var_name}' to '{new_name}'",
                            details={
                                "old_name": var_name,
                                "new_name": new_name,
                                "transformation": transformation,
                                "reason": rule.get("description", "Custom transformation"),
                                "rule_type": "custom_transform"
                            }
                        ))

        return actions

    def _apply_naming_format(self, var_name: str, target_format: str) -> str:
        """Apply a naming format to a variable name."""
        if target_format == "uppercase":
            return var_name.upper()
        elif target_format == "lowercase":
            return var_name.lower()
        elif target_format == "snake_case":
            # Convert to snake_case
            s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', var_name)
            return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
        elif target_format == "SCREAMING_SNAKE_CASE":
            s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', var_name)
            return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).upper()
        elif target_format == "camelCase":
            components = var_name.split('_')
            return components[0].lower() + ''.join(x.title() for x in components[1:])
        elif target_format == "PascalCase":
            components = var_name.split('_')
            return ''.join(x.title() for x in components)
        else:
            return var_name

    def _apply_transformation(self, var_name: str, transformation: str) -> str:
        """Apply a transformation to a variable name."""
        if transformation.startswith("replace:"):
            parts = transformation.split(":", 2)
            if len(parts) == 3:
                _, old, new = parts
                return var_name.replace(old, new)
        elif transformation.startswith("regex:"):
            parts = transformation.split(":", 3)
            if len(parts) == 4:
                _, pattern, replacement, _ = parts
                return re.sub(pattern, replacement, var_name)
        elif transformation.startswith("remove_prefix:"):
            prefix = transformation.split(":", 1)[1]
            if var_name.startswith(prefix):
                return var_name[len(prefix):]
        elif transformation.startswith("remove_suffix:"):
            suffix = transformation.split(":", 1)[1]
            if var_name.endswith(suffix):
                return var_name[:-len(suffix)]

        return var_name

