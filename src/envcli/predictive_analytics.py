"""
Predictive Analytics for EnvCLI - Forecast environment issues before they happen.
"""

import json
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import defaultdict, Counter
import re

from .config import CONFIG_DIR
from .telemetry import TelemetryAnalyzer

PREDICTIVE_DATA_FILE = CONFIG_DIR / "predictive_data.json"

class PredictiveAnalytics:
    """Predictive analytics for environment management."""

    def __init__(self):
        self.data = self._load_predictive_data()
        self.analyzer = TelemetryAnalyzer()

    def _load_predictive_data(self) -> Dict[str, Any]:
        """Load predictive analytics data."""
        if PREDICTIVE_DATA_FILE.exists():
            with open(PREDICTIVE_DATA_FILE, 'r') as f:
                return json.load(f)
        return {
            "patterns": {},
            "predictions": [],
            "last_updated": None
        }

    def _save_predictive_data(self):
        """Save predictive analytics data."""
        PREDICTIVE_DATA_FILE.parent.mkdir(exist_ok=True)
        with open(PREDICTIVE_DATA_FILE, 'w') as f:
            json.dump(self.data, f, indent=2)

    def analyze_variable_patterns(self) -> Dict[str, Any]:
        """Analyze patterns in variable usage and predict future needs."""
        predictions = []

        # Analyze variable naming patterns
        profiles = []
        from .config import list_profiles
        profiles = list_profiles()

        all_vars = set()
        profile_vars = {}

        for profile in profiles:
            from .env_manager import EnvManager
            manager = EnvManager(profile)
            env_vars = manager.load_env()
            profile_vars[profile] = set(env_vars.keys())
            all_vars.update(env_vars.keys())

        # Predict missing variables across environments
        for profile in profiles:
            missing_vars = all_vars - profile_vars[profile]
            if missing_vars:
                predictions.append({
                    "type": "missing_variables",
                    "severity": "info",
                    "profile": profile,
                    "prediction": f"Profile '{profile}' might be missing {len(missing_vars)} variables found in other profiles",
                    "details": list(missing_vars)[:5],  # Show first 5
                    "confidence": min(0.8, len(missing_vars) / len(all_vars))
                })

        # Analyze variable value patterns
        for profile in profiles:
            from .env_manager import EnvManager
            manager = EnvManager(profile)
            env_vars = manager.load_env()

            for key, value in env_vars.items():
                pattern = self._analyze_value_pattern(key, value)
                if pattern:
                    predictions.append({
                        "type": "value_pattern",
                        "severity": "info",
                        "profile": profile,
                        "variable": key,
                        "prediction": pattern["prediction"],
                        "confidence": pattern["confidence"]
                    })

        # Predict security issues
        security_predictions = self._predict_security_issues(profiles)
        predictions.extend(security_predictions)

        # Predict configuration drift
        drift_predictions = self._predict_configuration_drift(profiles)
        predictions.extend(drift_predictions)

        self.data["predictions"] = predictions
        self.data["last_updated"] = datetime.now().isoformat()
        self._save_predictive_data()

        return {
            "predictions": predictions,
            "total_predictions": len(predictions),
            "generated_at": datetime.now().isoformat()
        }

    def _analyze_value_pattern(self, key: str, value: str) -> Optional[Dict[str, Any]]:
        """Analyze a variable value for patterns and predictions."""
        # Check for environment-specific URLs
        if 'url' in key.lower() or 'endpoint' in key.lower():
            if 'localhost' in value or '127.0.0.1' in value:
                return {
                    "prediction": f"Variable '{key}' appears to be using localhost - consider environment-specific URLs",
                    "confidence": 0.7
                }

        # Check for placeholder values
        placeholder_patterns = [
            r'^placeholder.*$',
            r'^your.*$',
            r'^example.*$',
            r'^change.*$',
            r'^replace.*$'
        ]

        for pattern in placeholder_patterns:
            if re.match(pattern, value, re.IGNORECASE):
                return {
                    "prediction": f"Variable '{key}' appears to contain placeholder text - replace with actual value",
                    "confidence": 0.9
                }

        # Check for potentially sensitive data in non-secret variables
        if not any(word in key.lower() for word in ['secret', 'key', 'token', 'password']):
            # Look for patterns that might indicate sensitive data
            sensitive_patterns = [
                r'\b\d{4}[\s\-]\d{4}[\s\-]\d{4}[\s\-]\d{4}\b',  # Credit card
                r'\b\d{3}[\s\-]\d{3}[\s\-]\d{4}\b',  # SSN
                r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',  # Email
            ]

            for pattern in sensitive_patterns:
                if re.search(pattern, value):
                    return {
                        "prediction": f"Variable '{key}' may contain sensitive data - consider moving to secret variable",
                        "confidence": 0.6
                    }

        return None

    def _predict_security_issues(self, profiles: List[str]) -> List[Dict[str, Any]]:
        """Predict potential security issues."""
        predictions = []

        for profile in profiles:
            from .env_manager import EnvManager
            manager = EnvManager(profile)
            env_vars = manager.load_env()

            # Check for weak passwords (heuristics)
            for key, value in env_vars.items():
                if 'password' in key.lower():
                    if len(value) < 8:
                        predictions.append({
                            "type": "security_weak_password",
                            "severity": "high",
                            "profile": profile,
                            "variable": key,
                            "prediction": f"Password in '{key}' appears to be weak (length < 8)",
                            "confidence": 0.8
                        })
                    elif value in ['password', '123456', 'admin', 'root']:
                        predictions.append({
                            "type": "security_common_password",
                            "severity": "critical",
                            "profile": profile,
                            "variable": key,
                            "prediction": f"Password in '{key}' is a common/weak password",
                            "confidence": 0.95
                        })

            # Check for exposed secrets
            exposed_vars = []
            for key in env_vars.keys():
                if any(word in key.lower() for word in ['secret', 'key', 'token']):
                    if not key.isupper():
                        exposed_vars.append(key)

            if exposed_vars:
                predictions.append({
                    "type": "security_naming",
                    "severity": "medium",
                    "profile": profile,
                    "prediction": f"Found {len(exposed_vars)} potentially sensitive variables not using uppercase naming",
                    "details": exposed_vars[:3],
                    "confidence": 0.7
                })

        return predictions

    def _predict_configuration_drift(self, profiles: List[str]) -> List[Dict[str, Any]]:
        """Predict configuration drift between environments."""
        predictions = []

        if len(profiles) < 2:
            return predictions

        # Compare variable sets across profiles
        profile_vars = {}
        for profile in profiles:
            from .env_manager import EnvManager
            manager = EnvManager(profile)
            env_vars = manager.load_env()
            profile_vars[profile] = set(env_vars.keys())

        # Find inconsistencies
        all_vars = set()
        for vars_set in profile_vars.values():
            all_vars.update(vars_set)

        for var in all_vars:
            present_in = [p for p, vars_set in profile_vars.items() if var in vars_set]
            missing_from = [p for p in profiles if p not in present_in]

            if len(present_in) > 0 and len(missing_from) > 0:
                # Calculate drift risk
                coverage = len(present_in) / len(profiles)
                if coverage < 0.5:  # Variable missing from more than half of profiles
                    predictions.append({
                        "type": "configuration_drift",
                        "severity": "medium",
                        "prediction": f"Variable '{var}' shows configuration drift - present in {len(present_in)}/{len(profiles)} profiles",
                        "present_in": present_in,
                        "missing_from": missing_from,
                        "confidence": min(0.9, 1.0 - coverage)
                    })

        return predictions

    def forecast_usage_trends(self, days_ahead: int = 30) -> Dict[str, Any]:
        """Forecast future usage trends."""
        stats = self.analyzer.command_stats

        if not stats:
            return {"error": "No usage data available"}

        # Simple trend analysis
        total_commands = sum(stats.values())
        avg_daily = total_commands / max(1, 30)  # Assume 30 days of data

        forecast = {
            "current_usage": total_commands,
            "avg_daily": avg_daily,
            "forecasted_daily": avg_daily * 1.1,  # 10% growth assumption
            "forecasted_total": avg_daily * 1.1 * days_ahead,
            "top_commands": sorted(stats.items(), key=lambda x: x[1], reverse=True)[:3],
            "predictions": []
        }

        # Predict based on usage patterns
        if total_commands > 1000:
            forecast["predictions"].append({
                "type": "high_usage",
                "message": "High command usage detected - consider automation or training",
                "confidence": 0.8
            })

        # Predict sync frequency
        sync_count = stats.get("sync", 0)
        if sync_count > 50:
            forecast["predictions"].append({
                "type": "sync_frequency",
                "message": "Frequent sync operations - consider automated sync schedules",
                "confidence": 0.7
            })

        return forecast

    def get_risk_assessment(self) -> Dict[str, Any]:
        """Provide overall risk assessment."""
        assessment = {
            "overall_risk": "low",
            "risk_factors": [],
            "recommendations": [],
            "generated_at": datetime.now().isoformat()
        }

        # Run predictive analysis
        predictions = self.analyze_variable_patterns()["predictions"]

        # Categorize risks
        high_risk = [p for p in predictions if p.get("severity") == "critical"]
        medium_risk = [p for p in predictions if p.get("severity") == "high"]
        low_risk = [p for p in predictions if p.get("severity") in ["medium", "warning"]]

        if high_risk:
            assessment["overall_risk"] = "high"
            assessment["risk_factors"].extend([p["prediction"] for p in high_risk[:3]])
        elif medium_risk:
            assessment["overall_risk"] = "medium"
            assessment["risk_factors"].extend([p["prediction"] for p in medium_risk[:3]])
        elif low_risk:
            assessment["overall_risk"] = "low"
            assessment["risk_factors"].extend([p["prediction"] for p in low_risk[:2]])

        # Generate recommendations
        if assessment["overall_risk"] == "high":
            assessment["recommendations"].extend([
                "Immediate security review required",
                "Consider suspending deployments until issues resolved",
                "Audit all recent changes"
            ])
        elif assessment["overall_risk"] == "medium":
            assessment["recommendations"].extend([
                "Review and address identified issues",
                "Implement additional monitoring",
                "Consider security training for team"
            ])
        else:
            assessment["recommendations"].extend([
                "Continue current security practices",
                "Regular monitoring recommended",
                "Consider proactive security enhancements"
            ])

        return assessment
