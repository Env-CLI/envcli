"""
Predictive analytics screen for EnvCLI TUI.
"""

from textual.containers import Container, Vertical, Horizontal, VerticalScroll
from textual.widgets import Static, Button, DataTable, Label, Select
from textual.message import Message
from ...predictive_analytics import PredictiveAnalytics
from ...config import get_current_profile, list_profiles


class PredictiveScreen(Container):
    """Predictive analytics and forecasting screen."""

    DEFAULT_CSS = """
    PredictiveScreen {
        layout: vertical;
        height: 100%;
    }

    #predictive-header {
        dock: top;
        height: auto;
        background: $boost;
        padding: 1;
        margin-bottom: 1;
    }

    #predictive-content {
        height: 1fr;
    }

    .predictive-section {
        border: solid $primary;
        height: auto;
        margin: 1;
        padding: 1;
    }

    .predictive-controls {
        layout: horizontal;
        height: auto;
        margin-top: 1;
    }

    .predictive-controls Button {
        margin-right: 1;
    }

    #risk-assessment {
        height: 12;
    }

    #predictions {
        height: 20;
    }

    #predictions-table {
        height: 1fr;
    }

    #usage-forecast {
        height: 15;
    }
    """

    def __init__(self):
        super().__init__()
        self.analyzer = PredictiveAnalytics()
        self.current_profile = get_current_profile()

    def compose(self):
        """Compose the predictive screen."""
        with VerticalScroll(id="predictive-content"):
            # Header
            with Vertical(id="predictive-header"):
                yield Static("🔮 Predictive Analytics", classes="header-title")
                yield Static(self._get_predictive_status(), id="predictive-status")

            # Risk Assessment Section
            with Vertical(id="risk-assessment", classes="predictive-section"):
                yield Static("⚠️ Risk Assessment", classes="section-title")
                yield Static(self._get_risk_assessment_display(), id="risk-display")
                with Horizontal(classes="predictive-controls"):
                    yield Button("🔍 Run Risk Assessment", id="run-risk-assessment")
                    yield Button("🔄 Refresh", id="refresh-risk")

            # Predictions Section
            with Vertical(id="predictions", classes="predictive-section"):
                yield Static("🎯 Predictions & Anomalies", classes="section-title")
                yield DataTable(id="predictions-table")
                with Horizontal(classes="predictive-controls"):
                    yield Button("🔮 Analyze Patterns", id="analyze-patterns")
                    yield Button("🔄 Refresh Predictions", id="refresh-predictions")

            # Usage Forecast Section
            with Vertical(id="usage-forecast", classes="predictive-section"):
                yield Static("📊 Usage Forecast", classes="section-title")
                yield Static(self._get_usage_forecast_display(), id="forecast-display")
                with Horizontal(classes="predictive-controls"):
                    yield Label("Forecast Days:")
                    yield Select(
                        options=[
                            ("7 days", "7"),
                            ("30 days", "30"),
                            ("60 days", "60"),
                            ("90 days", "90")
                        ],
                        value="30",
                        id="forecast-days"
                    )
                    yield Button("📈 Generate Forecast", id="generate-forecast")

    def on_mount(self):
        """Initialize the predictive screen."""
        self._setup_predictions_table()
        self._load_predictions()

    def _get_predictive_status(self) -> str:
        """Get predictive analytics status summary."""
        profiles = list_profiles()
        return f"Profile: {self.current_profile} | Total Profiles: {len(profiles)} | ML Model: Pattern-Based"

    def _get_risk_assessment_display(self) -> str:
        """Get risk assessment display."""
        try:
            assessment = self.analyzer.get_risk_assessment()
            
            risk_level = assessment.get("overall_risk", "unknown").upper()
            risk_emoji = {
                "LOW": "🟢",
                "MEDIUM": "🟡",
                "HIGH": "🔴",
                "CRITICAL": "🔴"
            }.get(risk_level, "⚪")
            
            lines = []
            lines.append(f"Overall Risk: {risk_emoji} {risk_level}")
            lines.append("")
            
            risk_factors = assessment.get("risk_factors", [])
            if risk_factors:
                lines.append("Risk Factors:")
                for factor in risk_factors[:3]:
                    lines.append(f"  • {factor}")
            else:
                lines.append("No significant risk factors detected")
            
            return "\n".join(lines)
        except Exception as e:
            return f"Failed to load risk assessment: {e}"

    def _get_usage_forecast_display(self) -> str:
        """Get usage forecast display."""
        try:
            forecast = self.analyzer.forecast_usage_trends(days_ahead=30)
            
            if "error" in forecast:
                return forecast["error"]
            
            lines = []
            lines.append(f"Current Usage: {forecast.get('current_usage', 0)} commands")
            lines.append(f"Avg Daily: {forecast.get('avg_daily', 0):.1f} commands/day")
            lines.append(f"Forecasted Daily: {forecast.get('forecasted_daily', 0):.1f} commands/day")
            lines.append(f"30-Day Forecast: {forecast.get('forecasted_total', 0):.0f} commands")
            lines.append("")
            
            top_commands = forecast.get("top_commands", [])
            if top_commands:
                lines.append("Top Commands:")
                for cmd, count in top_commands:
                    lines.append(f"  • {cmd}: {count}")
            
            return "\n".join(lines)
        except Exception as e:
            return f"Failed to load forecast: {e}"

    def _setup_predictions_table(self):
        """Setup the predictions table."""
        table = self.query_one("#predictions-table", DataTable)
        table.add_column("Type", width=25)
        table.add_column("Severity", width=12)
        table.add_column("Prediction", width=50)
        table.add_column("Confidence", width=12)

    def _load_predictions(self):
        """Load predictions into the table."""
        table = self.query_one("#predictions-table", DataTable)
        table.clear()

        try:
            result = self.analyzer.analyze_variable_patterns()
            predictions = result.get("predictions", [])
            
            if not predictions:
                table.add_row("info", "ℹ️", "No predictions available - run pattern analysis", "N/A")
                return
            
            for pred in predictions[:20]:  # Show first 20 predictions
                pred_type = pred.get("type", "unknown").replace("_", " ").title()
                severity = pred.get("severity", "info")
                
                # Add emoji based on severity
                severity_emoji = {
                    "critical": "🔴",
                    "high": "🟠",
                    "medium": "🟡",
                    "warning": "⚠️",
                    "info": "ℹ️",
                    "low": "🟢"
                }.get(severity, "•")
                
                prediction = pred.get("prediction", "No prediction")
                confidence = pred.get("confidence", 0)
                
                table.add_row(
                    pred_type,
                    f"{severity_emoji} {severity}",
                    prediction[:50],
                    f"{confidence*100:.0f}%"
                )
        except Exception as e:
            table.add_row("error", "❌", f"Failed to load predictions: {e}", "N/A")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id

        if button_id == "run-risk-assessment":
            await self._run_risk_assessment()
        elif button_id == "refresh-risk":
            self._refresh_risk()
        elif button_id == "analyze-patterns":
            await self._analyze_patterns()
        elif button_id == "refresh-predictions":
            self._refresh_predictions()
        elif button_id == "generate-forecast":
            self._generate_forecast()

    async def _run_risk_assessment(self):
        """Run risk assessment."""
        try:
            self.notify("Running risk assessment...", severity="information")
            
            assessment = self.analyzer.get_risk_assessment()
            
            # Update display
            risk_widget = self.query_one("#risk-display", Static)
            risk_widget.update(self._get_risk_assessment_display())
            
            risk_level = assessment.get("overall_risk", "unknown")
            self.notify(f"Risk assessment complete: {risk_level.upper()}", severity="information")
        except Exception as e:
            self.notify(f"Risk assessment failed: {e}", severity="error")

    def _refresh_risk(self):
        """Refresh risk assessment display."""
        try:
            risk_widget = self.query_one("#risk-display", Static)
            risk_widget.update(self._get_risk_assessment_display())
            self.notify("Risk assessment refreshed", severity="information")
        except Exception as e:
            self.notify(f"Failed to refresh risk assessment: {e}", severity="error")

    async def _analyze_patterns(self):
        """Analyze variable patterns."""
        try:
            self.notify("Analyzing patterns...", severity="information")
            
            result = self.analyzer.analyze_variable_patterns()
            
            # Refresh predictions table
            self._load_predictions()
            
            total = result.get("total_predictions", 0)
            self.notify(f"Pattern analysis complete: {total} predictions", severity="information")
        except Exception as e:
            self.notify(f"Pattern analysis failed: {e}", severity="error")

    def _refresh_predictions(self):
        """Refresh predictions display."""
        try:
            self._load_predictions()
            self.notify("Predictions refreshed", severity="information")
        except Exception as e:
            self.notify(f"Failed to refresh predictions: {e}", severity="error")

    def _generate_forecast(self):
        """Generate usage forecast."""
        try:
            # Get selected forecast days
            days_select = self.query_one("#forecast-days", Select)
            days = int(days_select.value)
            
            self.notify(f"Generating {days}-day forecast...", severity="information")
            
            # Generate forecast
            forecast = self.analyzer.forecast_usage_trends(days_ahead=days)
            
            # Update display
            forecast_widget = self.query_one("#forecast-display", Static)
            
            if "error" in forecast:
                forecast_widget.update(forecast["error"])
                self.notify(forecast["error"], severity="warning")
                return
            
            # Build display text
            lines = []
            lines.append(f"Current Usage: {forecast.get('current_usage', 0)} commands")
            lines.append(f"Avg Daily: {forecast.get('avg_daily', 0):.1f} commands/day")
            lines.append(f"Forecasted Daily: {forecast.get('forecasted_daily', 0):.1f} commands/day")
            lines.append(f"{days}-Day Forecast: {forecast.get('forecasted_total', 0):.0f} commands")
            lines.append("")
            
            top_commands = forecast.get("top_commands", [])
            if top_commands:
                lines.append("Top Commands:")
                for cmd, count in top_commands:
                    lines.append(f"  • {cmd}: {count}")
            
            forecast_widget.update("\n".join(lines))
            
            self.notify(f"{days}-day forecast generated", severity="information")
        except Exception as e:
            self.notify(f"Failed to generate forecast: {e}", severity="error")

