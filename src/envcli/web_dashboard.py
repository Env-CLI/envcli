"""
Web Dashboard for EnvCLI using Streamlit.
"""

# Import modules - use absolute imports with path setup for compatibility
import sys
import os
# Add the package directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
package_dir = os.path.dirname(current_dir)
if package_dir not in sys.path:
    sys.path.insert(0, package_dir)

# Use absolute imports
from envcli.config import list_profiles, get_current_profile
from envcli.env_manager import EnvManager
from envcli.ai_assistant import AIAssistant
from envcli.audit_reporting import AuditReporter
from envcli.telemetry import TelemetryAnalyzer
from envcli.monitoring import MonitoringSystem

import streamlit as st


def _initialize_streamlit():
    """Initialize Streamlit only when dashboard is actually run."""
    import streamlit as st

    st.set_page_config(
        page_title="EnvCLI Dashboard",
        page_icon="🔐",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Custom CSS
    st.markdown("""
    <style>
        .main-header {
            font-size: 2.5rem;
            font-weight: bold;
            color: #1f77b4;
            text-align: center;
            margin-bottom: 2rem;
        }
        .metric-card {
            background-color: #f0f2f6;
            padding: 1rem;
            border-radius: 0.5rem;
            border-left: 0.25rem solid #1f77b4;
        }
        .alert-card {
            background-color: #ffebee;
            padding: 1rem;
            border-radius: 0.5rem;
            border-left: 0.25rem solid #d32f2f;
        }
    </style>
    """, unsafe_allow_html=True)


def main():
    # Initialize Streamlit only when dashboard is run
    _initialize_streamlit()

    st.markdown('<div class="main-header">🔐 EnvCLI Enterprise Dashboard</div>', unsafe_allow_html=True)

    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Select Page",
        ["Overview", "Profiles", "Analytics", "AI Insights", "Audit & Compliance", "Monitoring"]
    )

    # Profile selector in sidebar
    profiles = list_profiles()
    if profiles:
        current_profile = st.sidebar.selectbox("Current Profile", profiles, index=profiles.index(get_current_profile()) if get_current_profile() in profiles else 0)
    else:
        st.error("No profiles found. Create one using the CLI.")
        return

    # Main content
    if page == "Overview":
        show_overview(current_profile)
    elif page == "Profiles":
        show_profiles()
    elif page == "Analytics":
        show_analytics()
    elif page == "AI Insights":
        show_ai_insights(current_profile)
    elif page == "Audit & Compliance":
        show_audit_compliance()
    elif page == "Monitoring":
        show_monitoring()

def show_overview(current_profile):
    """Show overview dashboard."""
    st.header("📊 Overview")

    col1, col2, col3, col4 = st.columns(4)

    # Metrics
    manager = EnvManager(current_profile)
    env_vars = manager.load_env()

    with col1:
        st.metric("Total Variables", len(env_vars))

    with col2:
        secrets = sum(1 for k in env_vars.keys() if any(word in k.lower() for word in ['secret', 'key', 'token', 'password']))
        st.metric("Secrets", secrets)

    with col3:
        profiles_count = len(list_profiles())
        st.metric("Profiles", profiles_count)

    with col4:
        # Calculate compliance score
        from envcli.audit_reporting import AuditReporter
        reporter = AuditReporter()
        report = reporter.generate_governance_report(current_profile)
        score = report.get('governance_score', 0)
        st.metric("Compliance Score", f"{score}%")

    # Environment Variables Table
    st.subheader("🔑 Environment Variables")

    # Mask sensitive data
    display_vars = {}
    for key, value in env_vars.items():
        if any(word in key.lower() for word in ['secret', 'key', 'token', 'password']):
            display_vars[key] = "••••••••"
        else:
            display_vars[key] = value

    import pandas as pd
    df = pd.DataFrame(list(display_vars.items()), columns=['Variable', 'Value'])
    st.dataframe(df, width='stretch')

    # Recent Activity
    st.subheader("📈 Recent Activity")
    analyzer = TelemetryAnalyzer()
    insights = analyzer.generate_report()["insights"]

    if insights:
        for insight in insights[:5]:
            with st.container():
                if insight["severity"] == "error":
                    st.error(f"❌ {insight['message']}")
                elif insight["severity"] == "warning":
                    st.warning(f"⚠️ {insight['message']}")
                elif insight["severity"] == "info":
                    st.info(f"ℹ️ {insight['message']}")
                else:
                    st.success(f"✅ {insight['message']}")
    else:
        st.success("✅ All systems operational - no issues detected")

def show_profiles():
    """Show profiles management."""
    st.header("📁 Profile Management")

    profiles = list_profiles()

    if not profiles:
        st.error("No profiles found")
        return

    # Profile cards
    cols = st.columns(3)
    for i, profile in enumerate(profiles):
        with cols[i % 3]:
            manager = EnvManager(profile)
            env_vars = manager.load_env()

            with st.container():
                is_active = profile == get_current_profile()
                if is_active:
                    st.success(f"🎯 {profile} (Active)")
                else:
                    st.info(f"📁 {profile}")

                st.metric("Variables", len(env_vars))
                secrets = sum(1 for k in env_vars.keys() if any(word in k.lower() for word in ['secret', 'key', 'token', 'password']))
                st.metric("Secrets", secrets)

                if st.button(f"Switch to {profile}", key=f"switch_{profile}"):
                    from envcli.config import set_current_profile
                    set_current_profile(profile)
                    st.success(f"Switched to profile '{profile}'")
                    st.rerun()

def show_analytics():
    """Show analytics dashboard."""
    st.header("📈 Analytics Dashboard")

    analyzer = TelemetryAnalyzer()
    from envcli.config import get_command_stats
    stats = get_command_stats()

    if not stats:
        st.warning("No analytics data available. Enable analytics with `envcli analytics enable`")
        return

    # Command usage chart
    st.subheader("Command Usage")

    commands = list(stats.keys())
    usage = list(stats.values())

    import plotly.express as px
    fig = px.bar(
        x=commands,
        y=usage,
        title="Command Usage Statistics",
        labels={'x': 'Command', 'y': 'Usage Count'}
    )
    st.plotly_chart(fig, use_container_width=True)

    # Usage table
    st.subheader("Detailed Statistics")
    import pandas as pd
    df = pd.DataFrame(list(stats.items()), columns=['Command', 'Usage Count'])
    df = df.sort_values('Usage Count', ascending=False)
    st.dataframe(df, width='stretch')

def show_ai_insights(current_profile):
    """Show AI insights."""
    st.header("🤖 AI Insights")

    try:
        ai = AIAssistant()
        recommendations = ai.generate_recommendations(current_profile)

        if "error" in recommendations:
            st.error(f"AI Error: {recommendations['error']}")
            return

        # Naming improvements
        if recommendations.get("naming_improvements"):
            st.subheader("📝 Naming Recommendations")

            for rec in recommendations["naming_improvements"][:10]:
                if rec["severity"] == "error":
                    st.error(f"❌ {rec['message']}")
                elif rec["severity"] == "warning":
                    st.warning(f"⚠️ {rec['message']}")
                else:
                    st.info(f"ℹ️ {rec['message']}")

                if rec.get("suggestion"):
                    st.caption(f"Suggestion: {rec['suggestion']}")
        else:
            st.success("✅ No naming issues detected")

        # Drift analysis
        st.subheader("🔄 Environment Drift Analysis")
        profiles = list_profiles()
        if len(profiles) > 1:
            from envcli.telemetry import TelemetryAnalyzer
            analyzer = TelemetryAnalyzer()
            drift_insights = analyzer.analyze_environment_drift(profiles)

            if drift_insights:
                for insight in drift_insights[:5]:
                    st.warning(f"⚠️ {insight['message']}")
            else:
                st.success("✅ No environment drift detected")
        else:
            st.info("Need multiple profiles for drift analysis")

    except Exception as e:
        st.error(f"AI analysis failed: {e}")

def show_audit_compliance():
    """Show audit and compliance dashboard."""
    st.header("📋 Audit & Compliance")

    # Compliance score chart
    st.subheader("Compliance Overview")

    reporter = AuditReporter()
    profiles = list_profiles()

    compliance_data = []
    for profile in profiles:
        report = reporter.generate_governance_report(profile)
        compliance_data.append({
            "Profile": profile,
            "Score": report.get("governance_score", 0),
            "Variables": len(EnvManager(profile).load_env())
        })

    if compliance_data:
        import pandas as pd
        df = pd.DataFrame(compliance_data)

        # Compliance score chart
        import plotly.express as px
        fig = px.bar(
            df,
            x="Profile",
            y="Score",
            title="Compliance Scores by Profile",
            color="Score",
            color_continuous_scale="RdYlGn"
        )
        st.plotly_chart(fig, use_container_width=True)

        # Detailed table
        st.dataframe(df, width='stretch')

    # Generate reports
    st.subheader("Generate Reports")
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📄 Generate JSON Report"):
            report_path = reporter.generate_compliance_report("json", 30)
            st.success(f"Report generated: {report_path}")

    with col2:
        if st.button("📊 Generate CSV Report"):
            report_path = reporter.generate_compliance_report("csv", 30)
            st.success(f"Report generated: {report_path}")

    with col3:
        if st.button("📑 Generate PDF Report"):
            report_path = reporter.generate_compliance_report("pdf", 30)
            st.success(f"Report generated: {report_path}")

def show_monitoring():
    """Show monitoring dashboard."""
    st.header("📊 Monitoring & Alerts")

    try:
        monitor = MonitoringSystem()

        # Health status
        status = monitor.get_health_status()

        col1, col2, col3 = st.columns(3)

        with col1:
            status_color = "🟢" if status["status"] == "active" else "🔴"
            st.metric("Status", f"{status_color} {status['status'].title()}")

        with col2:
            st.metric("Last Check", status.get("last_check", "Never")[:19])

        with col3:
            st.metric("Alert Channels", status.get("alert_channels", 0))

        # Run health check
        if st.button("🔍 Run Health Check"):
            with st.spinner("Running health checks..."):
                results = monitor.run_health_check()

            st.subheader("Health Check Results")

            if results.get("alerts_triggered"):
                st.error(f"🚨 {len(results['alerts_triggered'])} alerts triggered")

            if "checks" in results:
                for check_name, check_data in results["checks"].items():
                    if check_data["status"] == "healthy":
                        st.success(f"✅ {check_name}: {check_data.get('count', 'OK')}")
                    else:
                        st.warning(f"⚠️ {check_name}: {check_data}")

        # Recent alerts
        st.subheader("Recent Alerts")
        alerts = monitor.list_alerts(10)

        if alerts:
            for alert in alerts:
                timestamp = alert["timestamp"][:19]
                severity_emoji = {"error": "❌", "warning": "⚠️", "info": "ℹ️"}.get(alert.get("severity"), "•")
                st.write(f"{severity_emoji} {timestamp}: {alert['message']}")
        else:
            st.success("✅ No recent alerts")

    except Exception as e:
        st.error(f"Monitoring dashboard error: {e}")

def run_web_dashboard(port: int = 8501):
    import streamlit.web.cli as st_cli
    import sys
    import os
    dashboard_file = os.path.abspath(__file__)

    # Get the parent directory (envcli package directory)
    package_dir = os.path.dirname(os.path.dirname(dashboard_file))

    # Add the parent directory to Python path so relative imports work
    if package_dir not in sys.path:
        sys.path.insert(0, package_dir)

    sys.argv = ["streamlit", "run", dashboard_file, "--server.port", str(port)]
    st_cli.main()

# Run the main dashboard when this file is executed (by Streamlit or directly)
if __name__ == "__main__":
    main()
