"""
Audit reporting for EnvCLI compliance and governance.
"""

import json
import csv
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from .config import CONFIG_DIR, list_profiles
from .env_manager import EnvManager
from .telemetry import TelemetryAnalyzer

AUDIT_DIR = CONFIG_DIR / "audits"

class AuditReporter:
    """Generate audit reports for compliance and governance."""

    def __init__(self):
        AUDIT_DIR.mkdir(exist_ok=True)

    def generate_compliance_report(self, output_format: str = "json",
                                 days: int = 30) -> str:
        """Generate a compliance audit report."""
        report_data = self._collect_audit_data(days)

        if output_format == "json":
            return self._export_json(report_data)
        elif output_format == "csv":
            return self._export_csv(report_data)
        elif output_format == "pdf":
            return self._export_pdf(report_data)
        else:
            raise ValueError(f"Unsupported format: {output_format}")

    def _collect_audit_data(self, days: int) -> Dict[str, Any]:
        """Collect audit data for the specified period."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        report = {
            "report_type": "compliance_audit",
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "days": days
            },
            "profiles": {},
            "summary": {},
            "generated_at": end_date.isoformat()
        }

        # Analyze each profile
        profiles = list_profiles()
        for profile in profiles:
            profile_data = self._analyze_profile(profile, start_date, end_date)
            report["profiles"][profile] = profile_data

        # Generate summary
        report["summary"] = self._generate_summary(report["profiles"])

        return report

    def _analyze_profile(self, profile: str, start_date: datetime,
                        end_date: datetime) -> Dict[str, Any]:
        """Analyze a single profile for audit data."""
        manager = EnvManager(profile)
        env_vars = manager.load_env()

        analysis = {
            "variable_count": len(env_vars),
            "secrets_count": 0,
            "compliance_issues": [],
            "naming_issues": [],
            "access_patterns": {}
        }

        # Analyze variables
        for var_name, var_value in env_vars.items():
            # Count secrets
            if any(word in var_name.lower() for word in ['secret', 'key', 'token', 'password']):
                analysis["secrets_count"] += 1

            # Check naming compliance
            if not var_name.isupper():
                analysis["naming_issues"].append({
                    "variable": var_name,
                    "issue": "not_uppercase",
                    "severity": "low"
                })

            # Check for prohibited patterns
            if any(pattern in var_value.lower() for pattern in ['password', 'secret']):
                analysis["compliance_issues"].append({
                    "variable": var_name,
                    "issue": "contains_sensitive_data",
                    "severity": "high"
                })

        return analysis

    def _generate_summary(self, profiles_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary statistics."""
        total_profiles = len(profiles_data)
        total_variables = sum(p["variable_count"] for p in profiles_data.values())
        total_secrets = sum(p["secrets_count"] for p in profiles_data.values())

        compliance_issues = sum(len(p["compliance_issues"]) for p in profiles_data.values())
        naming_issues = sum(len(p["naming_issues"]) for p in profiles_data.values())

        return {
            "total_profiles": total_profiles,
            "total_variables": total_variables,
            "total_secrets": total_secrets,
            "compliance_issues": compliance_issues,
            "naming_issues": naming_issues,
            "overall_score": self._calculate_compliance_score(
                total_variables, compliance_issues, naming_issues
            )
        }

    def _calculate_compliance_score(self, total_vars: int, compliance_issues: int,
                                  naming_issues: int) -> float:
        """Calculate a compliance score (0-100)."""
        if total_vars == 0:
            return 100.0

        # Weight compliance issues more heavily
        weighted_issues = (compliance_issues * 3) + naming_issues
        score = max(0, 100 - (weighted_issues / total_vars * 100))

        return round(score, 1)

    def _export_json(self, data: Dict[str, Any]) -> str:
        """Export audit data as JSON."""
        filename = f"audit_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = AUDIT_DIR / filename

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)

        return str(filepath)

    def _export_csv(self, data: Dict[str, Any]) -> str:
        """Export audit data as CSV."""
        filename = f"audit_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        filepath = AUDIT_DIR / filename

        # Flatten the data for CSV
        rows = []

        # Add summary
        summary = data["summary"]
        rows.append(["Summary", "", "", ""])
        rows.append(["Total Profiles", summary["total_profiles"], "", ""])
        rows.append(["Total Variables", summary["total_variables"], "", ""])
        rows.append(["Total Secrets", summary["total_secrets"], "", ""])
        rows.append(["Compliance Issues", summary["compliance_issues"], "", ""])
        rows.append(["Naming Issues", summary["naming_issues"], "", ""])
        rows.append(["Overall Score", f"{summary['overall_score']}%", "", ""])
        rows.append(["", "", "", ""])

        # Add profile details
        for profile_name, profile_data in data["profiles"].items():
            rows.append([f"Profile: {profile_name}", "", "", ""])
            rows.append(["Variable Count", profile_data["variable_count"], "", ""])
            rows.append(["Secrets Count", profile_data["secrets_count"], "", ""])

            # Add issues
            for issue in profile_data["compliance_issues"]:
                rows.append(["Compliance Issue", issue["variable"], issue["issue"], issue["severity"]])

            for issue in profile_data["naming_issues"]:
                rows.append(["Naming Issue", issue["variable"], issue["issue"], issue["severity"]])

            rows.append(["", "", "", ""])

        # Write CSV
        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["Category", "Detail", "Issue", "Severity"])
            writer.writerows(rows)

        return str(filepath)

    def _export_pdf(self, data: Dict[str, Any]) -> str:
        """Export audit data as PDF."""
        filename = f"audit_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = AUDIT_DIR / filename

        doc = SimpleDocTemplate(str(filepath), pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()

        # Title
        title = Paragraph("EnvCLI Compliance Audit Report", styles['Title'])
        elements.append(title)
        elements.append(Spacer(1, 12))

        # Summary section
        summary = data["summary"]
        summary_data = [
            ["Metric", "Value"],
            ["Total Profiles", str(summary["total_profiles"])],
            ["Total Variables", str(summary["total_variables"])],
            ["Total Secrets", str(summary["total_secrets"])],
            ["Compliance Issues", str(summary["compliance_issues"])],
            ["Naming Issues", str(summary["naming_issues"])],
            ["Overall Score", f"{summary['overall_score']}%"]
        ]

        summary_table = Table(summary_data)
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))

        elements.append(Paragraph("Summary", styles['Heading2']))
        elements.append(summary_table)
        elements.append(Spacer(1, 20))

        # Build PDF
        doc.build(elements)

        return str(filepath)

    def generate_governance_report(self, profile: str) -> Dict[str, Any]:
        """Generate a governance report for a specific profile."""
        analyzer = TelemetryAnalyzer()
        insights = analyzer.generate_report()["insights"]

        # Filter insights for the profile
        profile_insights = [i for i in insights if i.get("profile") == profile]

        report = {
            "profile": profile,
            "governance_score": self._calculate_governance_score(profile_insights),
            "insights": profile_insights,
            "recommendations": self._generate_recommendations(profile_insights),
            "generated_at": datetime.now().isoformat()
        }

        return report

    def _calculate_governance_score(self, insights: List[Dict]) -> float:
        """Calculate governance score based on insights."""
        if not insights:
            return 100.0

        # Count by severity
        severity_weights = {"error": 10, "warning": 5, "info": 2, "suggestion": 1}
        total_penalty = sum(severity_weights.get(i.get("severity", "info"), 1) for i in insights)

        # Base score minus penalties
        score = max(0, 100 - total_penalty)
        return round(score, 1)

    def _generate_recommendations(self, insights: List[Dict]) -> List[str]:
        """Generate governance recommendations."""
        recommendations = []

        # Group by type
        by_type = {}
        for insight in insights:
            insight_type = insight.get("type", "unknown")
            if insight_type not in by_type:
                by_type[insight_type] = []
            by_type[insight_type].append(insight)

        # Generate recommendations based on insight types
        if "unused_variable" in by_type:
            recommendations.append("Remove unused environment variables to reduce attack surface")

        if "environment_drift" in by_type:
            recommendations.append("Standardize environment configurations across profiles")

        if "stale_variable" in by_type:
            recommendations.append("Review and update stale environment variables")

        if not recommendations:
            recommendations.append("Environment configuration is well-governed")

        return recommendations
