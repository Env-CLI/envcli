"""
Monitoring and alerting system for EnvCLI.
"""

import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
import httpx
from .config import CONFIG_DIR
from .telemetry import TelemetryAnalyzer

MONITORING_CONFIG_FILE = CONFIG_DIR / "monitoring.json"
ALERTS_FILE = CONFIG_DIR / "alerts.json"

class MonitoringSystem:
    """Monitor environment health and trigger alerts."""

    def __init__(self):
        self.config = self._load_config()
        self.alerts = self._load_alerts()
        self.analyzer = TelemetryAnalyzer()

    def _load_config(self) -> Dict[str, Any]:
        """Load monitoring configuration."""
        if MONITORING_CONFIG_FILE.exists():
            with open(MONITORING_CONFIG_FILE, 'r') as f:
                return json.load(f)
        return {
            "enabled": False,
            "check_interval": 3600,  # 1 hour
            "alert_channels": [],
            "health_checks": {
                "unused_variables": {"enabled": True, "threshold": 10},
                "environment_drift": {"enabled": True, "threshold": 5},
                "policy_violations": {"enabled": True, "threshold": 1},
                "sync_failures": {"enabled": True, "threshold": 3}
            }
        }

    def _save_config(self):
        """Save monitoring configuration."""
        MONITORING_CONFIG_FILE.parent.mkdir(exist_ok=True)
        with open(MONITORING_CONFIG_FILE, 'w') as f:
            json.dump(self.config, f, indent=2)

    def _load_alerts(self) -> List[Dict[str, Any]]:
        """Load alerts history."""
        if ALERTS_FILE.exists():
            with open(ALERTS_FILE, 'r') as f:
                return json.load(f)
        return []

    def _save_alerts(self):
        """Save alerts history."""
        ALERTS_FILE.parent.mkdir(exist_ok=True)
        with open(ALERTS_FILE, 'w') as f:
            json.dump(self.alerts[-1000:], f, indent=2)  # Keep last 1000 alerts

    def enable_monitoring(self):
        """Enable the monitoring system."""
        self.config["enabled"] = True
        self.config["last_check"] = datetime.now().isoformat()
        self._save_config()

    def disable_monitoring(self):
        """Disable the monitoring system."""
        self.config["enabled"] = False
        self._save_config()

    def add_alert_channel(self, channel_type: str, config: Dict[str, Any]):
        """Add an alert notification channel."""
        channel = {
            "type": channel_type,
            "config": config,
            "enabled": True,
            "created_at": datetime.now().isoformat()
        }
        self.config["alert_channels"].append(channel)
        self._save_config()

    def run_health_check(self) -> Dict[str, Any]:
        """Run comprehensive health check."""
        if not self.config["enabled"]:
            return {"status": "disabled"}

        results = {
            "timestamp": datetime.now().isoformat(),
            "checks": {},
            "alerts_triggered": []
        }

        # Check unused variables
        if self.config["health_checks"]["unused_variables"]["enabled"]:
            unused = self.analyzer.analyze_unused_variables()
            threshold = self.config["health_checks"]["unused_variables"]["threshold"]
            if len(unused) >= threshold:
                results["checks"]["unused_variables"] = {
                    "status": "warning",
                    "count": len(unused),
                    "threshold": threshold
                }
                results["alerts_triggered"].append(self._create_alert("unused_variables", unused))
            else:
                results["checks"]["unused_variables"] = {
                    "status": "healthy",
                    "count": len(unused)
                }

        # Check environment drift
        if self.config["health_checks"]["environment_drift"]["enabled"]:
            drift_issues = self.analyzer.analyze_environment_drift()
            threshold = self.config["health_checks"]["environment_drift"]["threshold"]
            if len(drift_issues) >= threshold:
                results["checks"]["environment_drift"] = {
                    "status": "warning",
                    "count": len(drift_issues),
                    "threshold": threshold
                }
                results["alerts_triggered"].append(self._create_alert("environment_drift", drift_issues))
            else:
                results["checks"]["environment_drift"] = {
                    "status": "healthy",
                    "count": len(drift_issues)
                }

        # Send alerts
        for alert in results["alerts_triggered"]:
            self._send_alert(alert)

        # Update last check time
        self.config["last_check"] = results["timestamp"]
        self._save_config()

        return results

    def _create_alert(self, alert_type: str, data: Any) -> Dict[str, Any]:
        """Create an alert."""
        alert = {
            "id": f"{alert_type}_{int(time.time())}",
            "type": alert_type,
            "severity": "warning",
            "message": f"Health check failed: {alert_type}",
            "data": data,
            "timestamp": datetime.now().isoformat(),
            "resolved": False
        }

        self.alerts.append(alert)
        self._save_alerts()

        return alert

    def _send_alert(self, alert: Dict[str, Any]):
        """Send alert through configured channels."""
        for channel in self.config["alert_channels"]:
            if not channel.get("enabled", True):
                continue

            try:
                if channel["type"] == "webhook":
                    self._send_webhook_alert(channel["config"], alert)
                elif channel["type"] == "slack":
                    self._send_slack_alert(channel["config"], alert)
                elif channel["type"] == "email":
                    self._send_email_alert(channel["config"], alert)
            except Exception as e:
                print(f"Failed to send alert via {channel['type']}: {e}")

    def _send_webhook_alert(self, config: Dict[str, Any], alert: Dict[str, Any]):
        """Send alert via webhook."""
        url = config.get("url")
        if not url:
            return

        payload = {
            "alert": alert,
            "source": "EnvCLI Monitoring"
        }

        with httpx.Client(timeout=10) as client:
            response = client.post(url, json=payload)
            response.raise_for_status()

    def _send_slack_alert(self, config: Dict[str, Any], alert: Dict[str, Any]):
        """Send alert via Slack webhook."""
        webhook_url = config.get("webhook_url")
        if not webhook_url:
            return

        payload = {
            "text": f"🚨 EnvCLI Alert: {alert['message']}",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"🚨 *EnvCLI Alert*\n{alert['message']}\nType: {alert['type']}\nSeverity: {alert['severity']}"
                    }
                }
            ]
        }

        with httpx.Client(timeout=10) as client:
            response = client.post(webhook_url, json=payload)
            response.raise_for_status()

    def _send_email_alert(self, config: Dict[str, Any], alert: Dict[str, Any]):
        """Send alert via email (placeholder - would need SMTP setup)."""
        # This would require SMTP configuration
        # For now, just log the alert
        print(f"Email alert: {alert['message']} (SMTP not configured)")

    def get_health_status(self) -> Dict[str, Any]:
        """Get current health status."""
        last_check = self.config.get("last_check")
        if not last_check:
            return {"status": "never_checked"}

        last_check_time = datetime.fromisoformat(last_check)
        time_since_check = datetime.now() - last_check_time

        return {
            "status": "active" if self.config["enabled"] else "disabled",
            "last_check": last_check,
            "time_since_check": f"{time_since_check.seconds // 3600}h {(time_since_check.seconds % 3600) // 60}m",
            "alert_channels": len(self.config["alert_channels"]),
            "total_alerts": len(self.alerts)
        }

    def list_alerts(self, limit: int = 20) -> List[Dict[str, Any]]:
        """List recent alerts."""
        return sorted(self.alerts, key=lambda x: x["timestamp"], reverse=True)[:limit]
