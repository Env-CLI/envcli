"""
Compliance Framework Helpers for EnvCLI.
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

from .config import CONFIG_DIR
from .env_manager import EnvManager

COMPLIANCE_CONFIG_FILE = CONFIG_DIR / "compliance_frameworks.json"

class ComplianceFrameworkManager:
    """Manage compliance frameworks and automated checks."""

    def __init__(self):
        self.frameworks = self._load_frameworks()

    def _load_frameworks(self) -> Dict[str, Any]:
        """Load compliance frameworks."""
        if COMPLIANCE_CONFIG_FILE.exists():
            with open(COMPLIANCE_CONFIG_FILE, 'r') as f:
                return json.load(f)
        return self._get_default_frameworks()

    def _save_frameworks(self):
        """Save compliance frameworks."""
        COMPLIANCE_CONFIG_FILE.parent.mkdir(exist_ok=True)
        with open(COMPLIANCE_CONFIG_FILE, 'w') as f:
            json.dump(self.frameworks, f, indent=2)

    def _get_default_frameworks(self) -> Dict[str, Any]:
        """Get default compliance frameworks."""
        return {
            "soc2": {
                "name": "SOC 2",
                "description": "System and Organization Controls 2",
                "enabled": False,
                "controls": {
                    "CC1.1": "COSO Principle 1: The entity demonstrates a commitment to integrity and ethical values",
                    "CC2.1": "COSO Principle 6: The entity specifies objectives with sufficient clarity",
                    "CC3.1": "COSO Principle 11: The entity selects and develops control activities",
                    "CC4.1": "COSO Principle 16: The entity identifies and assesses changes that could significantly affect the system of internal control",
                    "CC5.1": "COSO Principle 21: The entity evaluates and communicates internal control deficiencies"
                },
                "requirements": [
                    "naming_conventions",
                    "encryption_practices",
                    "access_management",
                    "monitoring_logging"
                ]
            },
            "gdpr": {
                "name": "GDPR",
                "description": "General Data Protection Regulation",
                "enabled": False,
                "articles": {
                    "Article 5": "Principles relating to processing of personal data",
                    "Article 25": "Data protection by design and by default",
                    "Article 32": "Security of processing",
                    "Article 33": "Notification of a personal data breach",
                    "Article 35": "Data protection impact assessment"
                },
                "requirements": [
                    "data_minimization",
                    "purpose_limitation",
                    "storage_limitation",
                    "data_portability",
                    "right_to_erasure"
                ]
            },
            "hipaa": {
                "name": "HIPAA",
                "description": "Health Insurance Portability and Accountability Act",
                "enabled": False,
                "rules": {
                    "Privacy Rule": "Protects individual's health information",
                    "Security Rule": "Sets standards for securing electronic protected health information",
                    "Breach Notification Rule": "Requires notification following a breach"
                },
                "requirements": [
                    "phi_protection",
                    "security_measures",
                    "audit_monitoring",
                    "breach_notification",
                    "access_controls"
                ]
            }
        }

    def enable_framework(self, framework: str):
        """Enable a compliance framework."""
        if framework in self.frameworks:
            self.frameworks[framework]["enabled"] = True
            self._save_frameworks()

    def disable_framework(self, framework: str):
        """Disable a compliance framework."""
        if framework in self.frameworks:
            self.frameworks[framework]["enabled"] = False
            self._save_frameworks()

    def list_frameworks(self) -> Dict[str, Any]:
        """List all available frameworks."""
        return {
            name: {
                "name": config["name"],
                "description": config["description"],
                "enabled": config["enabled"]
            }
            for name, config in self.frameworks.items()
        }

    def assess_compliance(self, framework: str, profile: str) -> Dict[str, Any]:
        """Assess compliance for a specific framework and profile."""
        if framework not in self.frameworks or not self.frameworks[framework]["enabled"]:
            return {"error": f"Framework '{framework}' not enabled"}

        assessment = {
            "framework": framework,
            "profile": profile,
            "timestamp": datetime.now().isoformat(),
            "overall_compliance": "unknown",
            "requirements_check": {},
            "recommendations": []
        }

        # Get environment variables
        manager = EnvManager(profile)
        env_vars = manager.load_env()

        # Framework-specific checks
        if framework == "soc2":
            assessment["requirements_check"] = self._check_soc2_compliance(env_vars)
        elif framework == "gdpr":
            assessment["requirements_check"] = self._check_gdpr_compliance(env_vars)
        elif framework == "hipaa":
            assessment["requirements_check"] = self._check_hipaa_compliance(env_vars)

        # Calculate overall compliance
        checks = assessment["requirements_check"]
        compliant_count = sum(1 for check in checks.values() if check.get("compliant", False))
        total_checks = len(checks)

        if total_checks == 0:
            assessment["overall_compliance"] = "unknown"
        elif compliant_count == total_checks:
            assessment["overall_compliance"] = "compliant"
        elif compliant_count >= total_checks * 0.8:
            assessment["overall_compliance"] = "mostly_compliant"
        else:
            assessment["overall_compliance"] = "non_compliant"

        # Generate recommendations
        assessment["recommendations"] = self._generate_compliance_recommendations(
            framework, assessment["requirements_check"]
        )

        return assessment

    def _check_soc2_compliance(self, env_vars: Dict[str, str]) -> Dict[str, Any]:
        """Check SOC 2 compliance requirements."""
        checks = {}

        # Check for proper environment variable naming conventions
        sensitive_keywords = ['password', 'secret', 'key', 'token', 'credential']
        sensitive_vars = [k for k in env_vars.keys() if any(keyword in k.lower() for keyword in sensitive_keywords)]

        # Check if sensitive variables follow naming conventions (end with _SECRET or similar)
        properly_named_sensitive = [k for k in sensitive_vars if k.upper().endswith(('_SECRET', '_KEY', '_TOKEN', '_PASSWORD'))]
        checks["naming_conventions"] = {
            "compliant": len(sensitive_vars) == 0 or len(properly_named_sensitive) == len(sensitive_vars),
            "details": f"{len(properly_named_sensitive)}/{len(sensitive_vars)} sensitive variables properly named",
            "evidence": properly_named_sensitive[:3] if properly_named_sensitive else sensitive_vars[:3]
        }

        # Check for encryption indicators
        encryption_indicators = ['encrypted', 'cipher', 'aes', 'pgp', 'kms']
        encrypted_vars = [k for k in env_vars.keys() if any(indicator in k.lower() for indicator in encryption_indicators)]
        checks["encryption_practices"] = {
            "compliant": len(encrypted_vars) > 0 or len(sensitive_vars) == 0,
            "details": f"Found {len(encrypted_vars)} encryption-related variables",
            "evidence": encrypted_vars[:3]
        }

        # Check for access control patterns
        access_patterns = ['role', 'permission', 'auth', 'iam', 'rbac']
        access_vars = [k for k in env_vars.keys() if any(pattern in k.lower() for pattern in access_patterns)]
        checks["access_management"] = {
            "compliant": len(access_vars) > 0,
            "details": f"Found {len(access_vars)} access control related variables",
            "evidence": access_vars[:3]
        }

        # Check for monitoring/logging
        monitoring_patterns = ['log', 'monitor', 'alert', 'audit', 'trace']
        monitoring_vars = [k for k in env_vars.keys() if any(pattern in k.lower() for pattern in monitoring_patterns)]
        checks["monitoring_logging"] = {
            "compliant": len(monitoring_vars) > 0,
            "details": f"Found {len(monitoring_vars)} monitoring/logging variables",
            "evidence": monitoring_vars[:3]
        }

        return checks

    def _check_gdpr_compliance(self, env_vars: Dict[str, str]) -> Dict[str, Any]:
        """Check GDPR compliance requirements."""
        checks = {}

        # Check for data minimization (avoid collecting unnecessary personal data)
        personal_data_indicators = ['email', 'phone', 'address', 'name', 'ssn', 'personal', 'pii']
        personal_vars = [k for k in env_vars.keys() if any(indicator in k.lower() for indicator in personal_data_indicators)]
        checks["data_minimization"] = {
            "compliant": len(personal_vars) == 0 or all('_SECRET' in k.upper() or '_ENCRYPTED' in k.upper() for k in personal_vars),
            "details": f"{len(personal_vars)} variables may contain personal data - ensure encryption",
            "evidence": personal_vars[:3]
        }

        # Check for consent management
        consent_indicators = ['consent', 'gdpr', 'privacy', 'opt_in', 'opt_out']
        consent_vars = [k for k in env_vars.keys() if any(indicator in k.lower() for indicator in consent_indicators)]
        checks["consent_management"] = {
            "compliant": len(consent_vars) > 0,
            "details": f"Found {len(consent_vars)} consent/privacy related variables",
            "evidence": consent_vars[:3]
        }

        # Check for data retention policies
        retention_indicators = ['retention', 'ttl', 'expiry', 'delete_after']
        retention_vars = [k for k in env_vars.keys() if any(indicator in k.lower() for indicator in retention_indicators)]
        checks["data_retention"] = {
            "compliant": len(retention_vars) > 0,
            "details": f"Found {len(retention_vars)} data retention related variables",
            "evidence": retention_vars[:3]
        }

        # Check for data portability
        export_indicators = ['export', 'backup', 'migration', 'portability']
        export_vars = [k for k in env_vars.keys() if any(indicator in k.lower() for indicator in export_indicators)]
        checks["data_portability"] = {
            "compliant": len(export_vars) > 0,
            "details": f"Found {len(export_vars)} data export/portability related variables",
            "evidence": export_vars[:3]
        }

        return checks

    def _check_hipaa_compliance(self, env_vars: Dict[str, str]) -> Dict[str, Any]:
        """Check HIPAA compliance requirements."""
        checks = {}

        # Check for PHI (Protected Health Information) handling
        phi_indicators = ['phi', 'medical', 'health', 'patient', 'ehr', 'diagnosis', 'treatment']
        phi_vars = [k for k in env_vars.keys() if any(indicator in k.lower() for indicator in phi_indicators)]
        checks["phi_protection"] = {
            "compliant": len(phi_vars) == 0 or all('_ENCRYPTED' in k.upper() or '_SECURE' in k.upper() for k in phi_vars),
            "details": f"{len(phi_vars)} variables may contain PHI - ensure proper encryption and access controls",
            "evidence": phi_vars[:3]
        }

        # Check for security measures
        security_indicators = ['encrypt', 'ssl', 'tls', 'secure', 'auth', 'token']
        security_vars = [k for k in env_vars.keys() if any(indicator in k.lower() for indicator in security_indicators)]
        checks["security_measures"] = {
            "compliant": len(security_vars) > 0,
            "details": f"Found {len(security_vars)} security-related variables",
            "evidence": security_vars[:3]
        }

        # Check for audit and monitoring
        audit_indicators = ['audit', 'log', 'monitor', 'track', 'alert']
        audit_vars = [k for k in env_vars.keys() if any(indicator in k.lower() for indicator in audit_indicators)]
        checks["audit_monitoring"] = {
            "compliant": len(audit_vars) > 0,
            "details": f"Found {len(audit_vars)} audit and monitoring related variables",
            "evidence": audit_vars[:3]
        }

        # Check for breach notification setup
        breach_indicators = ['breach', 'incident', 'alert', 'notify', 'response']
        breach_vars = [k for k in env_vars.keys() if any(indicator in k.lower() for indicator in breach_indicators)]
        checks["breach_notification"] = {
            "compliant": len(breach_vars) > 0,
            "details": f"Found {len(breach_vars)} breach/incident response related variables",
            "evidence": breach_vars[:3]
        }

        # Check for access controls
        access_indicators = ['role', 'permission', 'rbac', 'access', 'authorize']
        access_vars = [k for k in env_vars.keys() if any(indicator in k.lower() for indicator in access_indicators)]
        checks["access_controls"] = {
            "compliant": len(access_vars) > 0,
            "details": f"Found {len(access_vars)} access control related variables",
            "evidence": access_vars[:3]
        }

        return checks

    def _generate_compliance_recommendations(self, framework: str,
                                           checks: Dict[str, Any]) -> List[str]:
        """Generate compliance recommendations."""
        recommendations = []

        non_compliant = [k for k, v in checks.items() if not v.get("compliant", False)]

        if framework == "soc2":
            if "encryption_at_rest" in non_compliant:
                recommendations.append("Implement encryption for sensitive data at rest")
            if "access_controls" in non_compliant:
                recommendations.append("Strengthen access controls for administrative accounts")
            if "audit_logging" in non_compliant:
                recommendations.append("Implement comprehensive audit logging")

        elif framework == "gdpr":
            if "data_minimization" in non_compliant:
                recommendations.append("Implement data minimization principles")
            if "purpose_limitation" in non_compliant:
                recommendations.append("Document and limit data processing purposes")
            if "storage_limitation" in non_compliant:
                recommendations.append("Implement data retention and deletion policies")

        elif framework == "hipaa":
            if "phi_encryption" in non_compliant:
                recommendations.append("Encrypt all protected health information (PHI)")
            if "access_controls" in non_compliant:
                recommendations.append("Implement role-based access controls")
            if "audit_controls" in non_compliant:
                recommendations.append("Enable comprehensive audit logging")

        if not recommendations:
            recommendations.append("All compliance requirements appear to be met")

        return recommendations

    def generate_compliance_report(self, framework: str, profiles: List[str]) -> Dict[str, Any]:
        """Generate comprehensive compliance report."""
        report = {
            "framework": framework,
            "generated_at": datetime.now().isoformat(),
            "profiles_assessed": profiles,
            "assessments": {},
            "summary": {}
        }

        for profile in profiles:
            assessment = self.assess_compliance(framework, profile)
            report["assessments"][profile] = assessment

        # Generate summary
        assessments = report["assessments"]
        compliant_profiles = sum(1 for a in assessments.values()
                               if a.get("overall_compliance") == "compliant")
        total_profiles = len(assessments)

        report["summary"] = {
            "total_profiles": total_profiles,
            "compliant_profiles": compliant_profiles,
            "compliance_rate": compliant_profiles / total_profiles if total_profiles > 0 else 0,
            "overall_status": "compliant" if compliant_profiles == total_profiles else "needs_attention"
        }

        return report
