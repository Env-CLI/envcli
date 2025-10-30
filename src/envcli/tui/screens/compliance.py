"""
Compliance screen for EnvCLI TUI.
"""

from textual.app import ComposeResult
from textual.containers import Container, Vertical, Horizontal, VerticalScroll
from textual.widgets import Static, Button, DataTable, Select, Label
from textual.message import Message

from ...compliance_frameworks import ComplianceFrameworkManager
from ...config import get_current_profile, list_profiles


class ComplianceScreen(Container):
    """Compliance management screen."""

    DEFAULT_CSS = """
    ComplianceScreen {
        layout: vertical;
        height: 100%;
        padding: 1;
    }

    .instructions-section {
        height: auto;
        margin-bottom: 1;
    }

    .info-box {
        background: $surface;
        border: solid $accent;
        padding: 1 2;
        color: $text;
    }

    .screen-header {
        text-style: bold;
        color: $primary;
        text-align: center;
        height: 3;
        content-align: center middle;
        margin-bottom: 1;
    }

    .section-title {
        text-style: bold;
        color: $primary;
        height: 2;
        margin-top: 1;
        margin-bottom: 1;
    }

    .compliance-section {
        height: auto;
        margin-bottom: 1;
    }

    .compliance-select {
        width: 100%;
        margin-bottom: 1;
    }

    .button-row {
        height: auto;
        align: left middle;
    }

    .compliance-status {
        background: $surface;
        border: solid $border;
        padding: 1;
        margin-bottom: 1;
        height: auto;
    }

    .compliance-table {
        height: auto;
        max-height: 15;
        margin-bottom: 1;
    }

    .assessment-results {
        background: $surface;
        border: solid $primary;
        padding: 1;
        margin-bottom: 1;
        height: auto;
        min-height: 8;
    }

    .recommendations {
        background: $surface;
        border: solid $warning;
        padding: 1;
        margin-bottom: 1;
        height: auto;
        min-height: 5;
    }
    """

    def __init__(self):
        super().__init__()
        self.compliance_manager = ComplianceFrameworkManager()
        self.current_profile = get_current_profile()
        self.selected_framework = None
        self.current_assessment = None

    def compose(self) -> ComposeResult:
        """Compose the compliance screen."""
        yield Static("✅ Compliance Management", id="compliance-header", classes="screen-header")

        with VerticalScroll(id="compliance-content"):
            # Instructions
            yield Container(
                Static(
                    "💡 How to use:\n"
                    "1. Select a framework from the dropdown below\n"
                    "2. Click '🔍 Assess Compliance' to run automated checks\n"
                    "3. Review results and recommendations below",
                    classes="info-box"
                ),
                classes="instructions-section"
            )

            # Framework selector
            yield Static("📋 Select Compliance Framework", classes="section-title")
            with Container(classes="compliance-section"):
                frameworks = self.compliance_manager.list_frameworks()
                framework_options = [
                    (f"{info['name']} - {info['description']}", name)
                    for name, info in frameworks.items()
                ]
                yield Select(
                    framework_options,
                    id="framework-select",
                    prompt="Select a framework",
                    classes="compliance-select"
                )
                with Horizontal(classes="button-row"):
                    yield Button("🔍 Assess Compliance", id="assess-btn", variant="primary")
                    yield Button("✅ Enable Framework", id="enable-framework-btn", variant="success")
                    yield Button("❌ Disable Framework", id="disable-framework-btn", variant="error")

            # Compliance status overview
            yield Static("📊 Compliance Status", classes="section-title")
            yield Container(
                Static(self._get_compliance_status(), id="compliance-status-text"),
                classes="compliance-status"
            )

            # Frameworks table
            yield Static("📋 Available Frameworks", classes="section-title")
            yield DataTable(id="frameworks-table", classes="compliance-table")

            # Assessment results
            yield Static("🔍 Assessment Results", classes="section-title")
            yield Container(
                Static("Select a framework and click 'Assess Compliance' to view results", id="assessment-results"),
                classes="assessment-results"
            )

            # Requirements check table
            yield Static("✓ Requirements Check", classes="section-title")
            yield DataTable(id="requirements-table", classes="compliance-table")

            # Violations and recommendations
            yield Static("⚠️ Recommendations", classes="section-title")
            yield Container(
                Static("No recommendations yet", id="recommendations-text"),
                classes="recommendations"
            )

            # Actions
            with Horizontal(classes="button-row"):
                yield Button("📄 Generate Report", id="generate-report-btn", variant="primary")
                yield Button("🔄 Refresh", id="refresh-compliance-btn", variant="default")

    def on_mount(self) -> None:
        """Initialize tables when screen is mounted."""
        self._setup_frameworks_table()
        self._setup_requirements_table()
        self._load_frameworks()

    def _get_compliance_status(self) -> str:
        """Get compliance status summary."""
        frameworks = self.compliance_manager.list_frameworks()
        enabled_count = sum(1 for f in frameworks.values() if f["enabled"])
        total_count = len(frameworks)

        status = f"📊 {enabled_count}/{total_count} frameworks enabled\n"
        status += f"📁 Current profile: {self.current_profile}\n"

        if self.current_assessment:
            overall = self.current_assessment.get("overall_compliance", "unknown")
            status += f"🔍 Last assessment: {overall.replace('_', ' ').title()}"
        else:
            status += "🔍 No assessment performed yet"

        return status

    def _setup_frameworks_table(self) -> None:
        """Setup the frameworks table."""
        table = self.query_one("#frameworks-table", DataTable)
        table.clear(columns=True)
        table.add_columns("Framework", "Name", "Description", "Status")

    def _setup_requirements_table(self) -> None:
        """Setup the requirements check table."""
        table = self.query_one("#requirements-table", DataTable)
        table.clear(columns=True)
        table.add_columns("Requirement", "Status", "Details")

    def _load_frameworks(self) -> None:
        """Load frameworks into the table."""
        table = self.query_one("#frameworks-table", DataTable)
        table.clear()

        frameworks = self.compliance_manager.list_frameworks()
        for name, info in frameworks.items():
            status = "✅ Enabled" if info["enabled"] else "❌ Disabled"
            table.add_row(
                name.upper(),
                info["name"],
                info["description"],
                status
            )

    def _load_requirements(self, assessment: dict) -> None:
        """Load requirements check results into the table."""
        table = self.query_one("#requirements-table", DataTable)
        table.clear()

        checks = assessment.get("requirements_check", {})
        for requirement, check_result in checks.items():
            status = "✅ Pass" if check_result.get("compliant", False) else "❌ Fail"
            details = check_result.get("details", "No details")
            table.add_row(
                requirement.replace("_", " ").title(),
                status,
                details
            )

    async def on_select_changed(self, event: Select.Changed) -> None:
        """Handle framework selection."""
        if event.select.id == "framework-select":
            self.selected_framework = event.value
            self.notify(f"Selected framework: {event.value}")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id

        if button_id == "enable-framework-btn":
            await self._enable_framework()
        elif button_id == "disable-framework-btn":
            await self._disable_framework()
        elif button_id == "assess-btn":
            await self._assess_compliance()
        elif button_id == "generate-report-btn":
            await self._generate_report()
        elif button_id == "refresh-compliance-btn":
            await self._refresh_compliance()

    async def _enable_framework(self) -> None:
        """Enable the selected framework."""
        if not self.selected_framework:
            self.notify("Please select a framework first", severity="warning")
            return

        try:
            self.compliance_manager.enable_framework(self.selected_framework)
            self.notify(f"✅ Enabled framework: {self.selected_framework.upper()}", severity="information")
            self._load_frameworks()
            self._update_status()
        except Exception as e:
            self.notify(f"Error enabling framework: {e}", severity="error")

    async def _disable_framework(self) -> None:
        """Disable the selected framework."""
        if not self.selected_framework:
            self.notify("Please select a framework first", severity="warning")
            return

        try:
            self.compliance_manager.disable_framework(self.selected_framework)
            self.notify(f"❌ Disabled framework: {self.selected_framework.upper()}", severity="information")
            self._load_frameworks()
            self._update_status()
        except Exception as e:
            self.notify(f"Error disabling framework: {e}", severity="error")

    async def _assess_compliance(self) -> None:
        """Assess compliance for the selected framework."""
        if not self.selected_framework:
            self.notify("⚠️ Please select a framework from the dropdown first", severity="warning", timeout=5)
            return

        try:
            # Check if framework is enabled, if not, enable it automatically
            frameworks = self.compliance_manager.list_frameworks()
            if not frameworks.get(self.selected_framework, {}).get("enabled", False):
                self.notify(f"🔄 Enabling {self.selected_framework.upper()} framework...", severity="information")
                self.compliance_manager.enable_framework(self.selected_framework)
                self._load_frameworks()
                self._update_status()

            self.notify(f"🔍 Assessing compliance for {self.selected_framework.upper()}...", severity="information")
            assessment = self.compliance_manager.assess_compliance(
                self.selected_framework,
                self.current_profile
            )

            if "error" in assessment:
                self.notify(f"❌ {assessment['error']}", severity="error", timeout=8)
                return

            self.current_assessment = assessment
            self._load_requirements(assessment)
            self._update_assessment_results(assessment)
            self._update_recommendations(assessment)
            self._update_status()

            overall = assessment.get("overall_compliance", "unknown")
            self.notify(f"✅ Assessment complete: {overall.replace('_', ' ').title()}", severity="information", timeout=5)

        except Exception as e:
            self.notify(f"❌ Error assessing compliance: {str(e)}", severity="error", timeout=8)

    def _update_assessment_results(self, assessment: dict) -> None:
        """Update the assessment results display."""
        results_widget = self.query_one("#assessment-results", Static)

        overall = assessment.get("overall_compliance", "unknown")
        timestamp = assessment.get("timestamp", "N/A")
        checks = assessment.get("requirements_check", {})

        compliant_count = sum(1 for check in checks.values() if check.get("compliant", False))
        total_checks = len(checks)

        results = f"📊 Overall Status: {overall.replace('_', ' ').title()}\n"
        results += f"📅 Assessed: {timestamp}\n"
        results += f"✓ Compliant: {compliant_count}/{total_checks} requirements\n"

        if overall == "compliant":
            results += "\n✅ All compliance requirements met!"
        elif overall == "mostly_compliant":
            results += "\n⚠️ Most requirements met, some improvements needed"
        else:
            results += "\n❌ Significant compliance gaps detected"

        results_widget.update(results)

    def _update_recommendations(self, assessment: dict) -> None:
        """Update the recommendations display."""
        recommendations_widget = self.query_one("#recommendations-text", Static)

        recommendations = assessment.get("recommendations", [])

        if not recommendations:
            recommendations_widget.update("✅ No recommendations - all requirements met!")
        else:
            rec_text = "\n".join(f"• {rec}" for rec in recommendations)
            recommendations_widget.update(rec_text)

    def _update_status(self) -> None:
        """Update the compliance status display."""
        status_widget = self.query_one("#compliance-status-text", Static)
        status_widget.update(self._get_compliance_status())

    async def _generate_report(self) -> None:
        """Generate a compliance report."""
        if not self.selected_framework:
            self.notify("⚠️ Please select a framework from the dropdown first", severity="warning", timeout=5)
            return

        try:
            # Check if framework is enabled
            frameworks = self.compliance_manager.list_frameworks()
            if not frameworks.get(self.selected_framework, {}).get("enabled", False):
                self.notify(f"⚠️ Framework {self.selected_framework.upper()} is not enabled. Enable it first or run an assessment.", severity="warning", timeout=8)
                return

            profiles = list_profiles()
            self.notify(f"📄 Generating compliance report for {len(profiles)} profiles...", severity="information")

            report = self.compliance_manager.generate_compliance_report(
                self.selected_framework,
                profiles
            )

            summary = report.get("summary", {})
            compliant = summary.get("compliant_profiles", 0)
            total = summary.get("total_profiles", 0)
            rate = summary.get("compliance_rate", 0) * 100

            self.notify(
                f"✅ Report generated: {compliant}/{total} profiles compliant ({rate:.1f}%)",
                severity="information",
                timeout=8
            )

        except Exception as e:
            self.notify(f"❌ Error generating report: {str(e)}", severity="error", timeout=8)

    async def _refresh_compliance(self) -> None:
        """Refresh the compliance screen."""
        try:
            self._load_frameworks()
            self._update_status()
            self.notify("🔄 Compliance data refreshed", severity="information")
        except Exception as e:
            self.notify(f"Error refreshing: {e}", severity="error")

