"""
Telemetry and insights for EnvCLI.
"""

import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from .config import CONFIG_DIR, get_command_stats
from .env_manager import EnvManager

TELEMETRY_FILE = CONFIG_DIR / "telemetry.json"

class TelemetryAnalyzer:
    """Analyze environment variable usage and detect insights."""

    def __init__(self):
        self.data = self._load_telemetry()
        self.insights = []

    def _load_telemetry(self) -> Dict:
        """Load telemetry data."""
        if TELEMETRY_FILE.exists():
            with open(TELEMETRY_FILE, 'r') as f:
                return json.load(f)
        return {
            "variable_usage": {},
            "command_patterns": {},
            "environment_drift": {},
            "last_analysis": None
        }

    def _save_telemetry(self):
        """Save telemetry data."""
        self.data["last_analysis"] = datetime.now().isoformat()
        TELEMETRY_FILE.parent.mkdir(exist_ok=True)
        with open(TELEMETRY_FILE, 'w') as f:
            json.dump(self.data, f, indent=2)

    def track_variable_access(self, profile: str, variable: str, accessed_by: str = "unknown"):
        """Track variable access."""
        key = f"{profile}:{variable}"
        if key not in self.data["variable_usage"]:
            self.data["variable_usage"][key] = {
                "first_accessed": datetime.now().isoformat(),
                "last_accessed": datetime.now().isoformat(),
                "access_count": 0,
                "accessed_by": []
            }

        usage = self.data["variable_usage"][key]
        usage["last_accessed"] = datetime.now().isoformat()
        usage["access_count"] += 1

        if accessed_by not in usage["accessed_by"]:
            usage["accessed_by"].append(accessed_by)

        self._save_telemetry()

    def analyze_unused_variables(self, profiles: List[str] = None) -> List[Dict]:
        """Analyze and identify potentially unused variables."""
        insights = []

        if profiles is None:
            from .config import list_profiles
            profiles = list_profiles()

        for profile in profiles:
            manager = EnvManager(profile)
            env_vars = manager.load_env()

            for var_name, var_value in env_vars.items():
                key = f"{profile}:{var_name}"
                usage = self.data["variable_usage"].get(key)

                if not usage:
                    # Variable never accessed
                    insights.append({
                        "type": "unused_variable",
                        "severity": "warning",
                        "profile": profile,
                        "variable": var_name,
                        "message": f"Variable '{var_name}' in profile '{profile}' has never been accessed",
                        "suggestion": "Consider removing if no longer needed"
                    })
                else:
                    # Check for old access
                    last_accessed = datetime.fromisoformat(usage["last_accessed"])
                    days_since_access = (datetime.now() - last_accessed).days

                    if days_since_access > 30:
                        insights.append({
                            "type": "stale_variable",
                            "severity": "info",
                            "profile": profile,
                            "variable": var_name,
                            "message": f"Variable '{var_name}' not accessed for {days_since_access} days",
                            "last_accessed": usage["last_accessed"]
                        })

        return insights

    def analyze_environment_drift(self, profiles: List[str] = None) -> List[Dict]:
        """Analyze drift between environments."""
        insights = []

        if profiles is None:
            from .config import list_profiles
            profiles = list_profiles()

        if len(profiles) < 2:
            return insights

        # Compare each pair of profiles
        for i, profile1 in enumerate(profiles):
            manager1 = EnvManager(profile1)
            env1 = manager1.load_env()

            for profile2 in profiles[i+1:]:
                manager2 = EnvManager(profile2)
                env2 = manager2.load_env()

                drift = self._calculate_drift(env1, env2, profile1, profile2)
                if drift:
                    insights.extend(drift)

        return insights

    def _calculate_drift(self, env1: Dict[str, str], env2: Dict[str, str],
                        profile1: str, profile2: str) -> List[Dict]:
        """Calculate drift between two environments."""
        insights = []

        # Find common variables with different values
        common_keys = set(env1.keys()) & set(env2.keys())
        for key in common_keys:
            if env1[key] != env2[key]:
                # Check if values look like they should be different (e.g., URLs with different environments)
                if self._is_expected_difference(env1[key], env2[key], key):
                    continue

                insights.append({
                    "type": "environment_drift",
                    "severity": "warning",
                    "profiles": [profile1, profile2],
                    "variable": key,
                    "message": f"Variable '{key}' differs between '{profile1}' and '{profile2}'",
                    "values": {
                        profile1: self._mask_value(key, env1[key]),
                        profile2: self._mask_value(key, env2[key])
                    },
                    "suggestion": "Ensure this difference is intentional"
                })

        # Find variables present in one but not the other
        only_in_1 = set(env1.keys()) - set(env2.keys())
        only_in_2 = set(env2.keys()) - set(env1.keys())

        for key in only_in_1:
            insights.append({
                "type": "missing_variable",
                "severity": "info",
                "missing_in": profile2,
                "present_in": profile1,
                "variable": key,
                "message": f"Variable '{key}' exists in '{profile1}' but not in '{profile2}'"
            })

        for key in only_in_2:
            insights.append({
                "type": "extra_variable",
                "severity": "info",
                "extra_in": profile2,
                "not_in": profile1,
                "variable": key,
                "message": f"Variable '{key}' exists in '{profile2}' but not in '{profile1}'"
            })

        return insights

    def _is_expected_difference(self, val1: str, val2: str, key: str) -> bool:
        """Check if a difference between values is expected."""
        # Common patterns that are expected to differ between environments
        if any(env_indicator in val1.lower() or env_indicator in val2.lower()
               for env_indicator in ['dev', 'staging', 'prod', 'test', 'qa']):
            return True

        # URLs with different subdomains
        if key.lower().endswith('_url') or 'url' in key.lower():
            return True

        # Database names with environment suffixes
        if 'database' in key.lower() or 'db_' in key.lower():
            return True

        return False

    def _mask_value(self, key: str, value: str) -> str:
        """Mask sensitive values."""
        if any(word in key.lower() for word in ['secret', 'key', 'token', 'password']):
            return '*' * len(value)
        return value

    def analyze_command_patterns(self) -> List[Dict]:
        """Analyze command usage patterns."""
        insights = []

        stats = get_command_stats()

        # Find most/least used commands
        if stats:
            most_used = max(stats.items(), key=lambda x: x[1])
            least_used = min(stats.items(), key=lambda x: x[1])

            insights.append({
                "type": "command_usage",
                "severity": "info",
                "message": f"Most used command: '{most_used[0]}' ({most_used[1]} times)",
                "data": dict(stats)
            })

            if len(stats) > 1:
                insights.append({
                    "type": "command_usage",
                    "severity": "info",
                    "message": f"Least used command: '{least_used[0]}' ({least_used[1]} times)"
                })

        # Detect potential automation opportunities
        total_commands = sum(stats.values())
        if total_commands > 100:
            insights.append({
                "type": "automation_opportunity",
                "severity": "suggestion",
                "message": f"High command usage ({total_commands} total). Consider setting up auto-loading or hooks.",
                "suggestion": "Use 'envcli shell auto-load' or event hooks for automation"
            })

        return insights

    def generate_report(self) -> Dict:
        """Generate a comprehensive insights report."""
        report = {
            "generated_at": datetime.now().isoformat(),
            "insights": []
        }

        # Collect all insights
        report["insights"].extend(self.analyze_unused_variables())
        report["insights"].extend(self.analyze_environment_drift())
        report["insights"].extend(self.analyze_command_patterns())

        # Group by severity
        severity_counts = Counter(insight["severity"] for insight in report["insights"])
        report["summary"] = {
            "total_insights": len(report["insights"]),
            "by_severity": dict(severity_counts)
        }

        return report

    def get_insights_summary(self) -> str:
        """Get a human-readable insights summary."""
        report = self.generate_report()

        summary = f"📊 EnvCLI Insights Report ({len(report['insights'])} insights)\n\n"

        if report["insights"]:
            # Group by type
            by_type = defaultdict(list)
            for insight in report["insights"]:
                by_type[insight["type"]].append(insight)

            for insight_type, insights in by_type.items():
                summary += f"🔍 {insight_type.replace('_', ' ').title()} ({len(insights)}):\n"
                for insight in insights[:3]:  # Show first 3 of each type
                    severity_emoji = {
                        "error": "❌",
                        "warning": "⚠️",
                        "info": "ℹ️",
                        "suggestion": "💡"
                    }.get(insight["severity"], "•")

                    summary += f"  {severity_emoji} {insight['message']}\n"

                if len(insights) > 3:
                    summary += f"  ... and {len(insights) - 3} more\n"

                summary += "\n"

        return summary
