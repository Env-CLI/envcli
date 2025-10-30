# EnvCLI v3.0.0 - The Ultimate Environment Management Platform

**The most comprehensive environment variable management platform ever built.** 🚀

Combining AI-powered governance, enterprise security, multi-cloud native operations, compliance automation, predictive analytics, and beautiful interfaces - EnvCLI v3.0.0 is the definitive solution for modern software teams.

## Installation

### Install from GitHub (Recommended)

```bash
# Using pip
pip install git+https://github.com/Nom-nom-hub/env-cli.git

# Using uv (faster)
uv pip install git+https://github.com/Nom-nom-hub/env-cli.git
```

### Install from Release

Download the latest `.whl` file from [Releases](https://github.com/Nom-nom-hub/env-cli/releases) and install:

```bash
pip install envcli-3.0.0-py3-none-any.whl
```

### Development Installation

```bash
git clone https://github.com/Nom-nom-hub/env-cli.git
cd env-cli
pip install -e .
```

### Advanced Dependencies (Optional)

```bash
# For AI features
pip install transformers torch

# For web dashboard
pip install streamlit plotly

# For API server
pip install fastapi uvicorn

# For cloud integrations
pip install kubernetes azure-identity azure-keyvault-secrets google-cloud-secret-manager
```

## 🚀 Ultimate Features Overview

### 🤖 AI-Powered Intelligence

- **Multiple AI Providers**: Choose from OpenAI, Anthropic, Google Gemini, Ollama, or local pattern matching
- **Smart Analysis**: AI recommendations for naming, security, and compliance
- **Safe Actions**: **NEW!** Apply AI recommendations automatically without exposing secrets
- **Custom Rules & Policies**: **NEW!** Define your own naming conventions and transformation rules
- **Privacy-First**: Only metadata analyzed, never raw secrets
- **Flexible Configuration**: Easy provider switching with `envcli ai config`
- **Predictive Analytics**: Forecast environment issues before they occur
- **Risk Assessment**: Automated risk scoring and mitigation suggestions

See [AI Provider Guide](docs/AI_PROVIDERS.md), [AI Safe Actions](docs/AI_SAFE_ACTIONS.md), and [Custom Rules](docs/AI_CUSTOM_RULES.md) for detailed configuration.

### 🏢 Enterprise-Grade Security

- **Role-Based Access Control**: Granular permissions (admin/member/guest)
- **Advanced Encryption**: Fernet, PyNaCl, cloud-native encryption
- **Audit Logging**: Complete audit trails for all operations
- **Compliance Frameworks**: SOC2, GDPR, HIPAA automated checks

### ☁️ Multi-Cloud Native

- **AWS SSM Parameter Store**: Native AWS integration
- **Azure Key Vault**: Enterprise Azure support
- **GCP Secret Manager**: Google Cloud integration
- **HashiCorp Vault**: Enterprise vault support
- **Kubernetes**: Native K8s Secrets and ConfigMaps

### 🎨 Beautiful Interfaces

- **Terminal User Interface (TUI)**: **NEW!** Full-featured Textual-powered TUI with 18 integrated modules
- **Interactive Dashboard**: Visual environment management in your terminal
- **Web Dashboard**: Streamlit-based web application
- **REST API**: Complete programmatic access
- **Rich CLI**: Colorful, intuitive command-line experience

### 🔧 Advanced Automation

- **Event-Driven Hooks**: Webhooks and scripts for all operations
- **CI/CD Integration**: Native pipeline support and environment promotion
- **Monitoring & Alerting**: Health checks and automated notifications
- **Policy Engine**: Automated rule enforcement and validation

## Usage

```bash
envcli --help
```

### Development Usage

For development and testing, you can also run EnvCLI as a Python module:

```bash
python -m envcli --help
```

### Examples

Initialize a profile and add variables:

```bash
envcli profile init --name dev
envcli env add API_KEY "your-secret-key"
envcli env add DATABASE_URL "postgresql://localhost/db"
```

List variables (with masking):

```bash
envcli env list
```

List without masking:

```bash
envcli env list --no-mask
```

Import from .env file:

```bash
envcli env import .env
```

Export to JSON:

```bash
envcli env export config.json --format json
```

Compare profiles:

```bash
envcli env diff dev prod
```

Switch profiles:

```bash
envcli profile use prod
```

Encrypt a file:

```bash
envcli encrypt encrypt secret.env
```

### Version 2 Examples

Validate against schema:

```bash
envcli validate schema.json
```

Manage hooks:

```bash
envcli hooks add pre "profile use" "echo 'Switching profiles'"
envcli hooks list
```

Analytics:

```bash
envcli analytics enable
envcli analytics stats
```

Remote sync:

```bash
# AWS SSM (requires AWS credentials configured)
envcli sync push aws_ssm /myapp/prod
envcli sync pull aws_ssm /myapp/prod
envcli sync status aws_ssm /myapp/prod

# GitHub Secrets (requires GITHUB_TOKEN and GITHUB_REPOSITORY env vars)
envcli sync push github_secrets /myapp/prod

# HashiCorp Vault (requires VAULT_ADDR and VAULT_TOKEN env vars)
envcli sync push vault /myapp/prod
envcli sync pull vault /myapp/prod
envcli sync status vault /myapp/prod
```

Enhanced features:

```bash
# TUI editor for environment variables
envcli env edit

# Tree view of profiles and variables
envcli profile tree

# Enhanced colored diff with git-like output
envcli env diff dev prod
```

Plugin management:

```bash
envcli plugin install example_plugin.py
envcli plugin list
envcli run-plugin hello "User"
envcli run-plugin greet "Alice" casual
```

### Ultimate v3.0.0 Examples

```bash
# AI-Powered Analysis with Multiple Providers
envcli ai enable --provider openai  # Use OpenAI GPT
envcli ai enable --provider anthropic  # Use Anthropic Claude
envcli ai enable --provider google  # Use Google Gemini
envcli ai enable --provider ollama  # Use local Ollama
envcli ai config --show  # View available providers
envcli ai analyze --profile dev
envcli predict risk-assessment

# NEW: AI Safe Actions - Apply recommendations automatically
envcli ai suggest --profile dev  # Get actionable suggestions
envcli ai apply --preview  # Preview changes (safe, no modifications)
envcli ai apply --yes  # Apply improvements (values preserved!)
envcli ai history  # View audit trail

# NEW: Custom Rules & Policies - Define your own conventions
envcli ai add-rule naming '.*_(key|secret|token)' uppercase  # Secrets must be uppercase
envcli ai add-rule prefix '^redis_' 'REDIS_'  # Group Redis variables
envcli ai add-rule exclude '^PATH$'  # Protect system variables
envcli ai list-rules  # View all custom rules
envcli ai suggest  # Apply custom rules automatically

# Enterprise Compliance
envcli compliance enable soc2
envcli compliance assess soc2 --profile prod
envcli compliance report soc2

# NEW: Terminal User Interface (TUI)
envcli tui  # Launch full-featured TUI
envcli tui --profile production  # Launch with specific profile

# REST API Server
envcli api-server --port 8000

# Web Dashboard
envcli web-dashboard --port 8501

# Advanced Sync
envcli sync push-k8s-secret my-secret --namespace production
envcli sync push-azure-kv --prefix myapp
envcli sync push-gcp-sm --prefix myapp

# CI/CD Integration
envcli ci detect
envcli ci promote dev staging
```

## Features

### Version 1 (MVP)

- **Local Environment Management**
  - List environment variables with optional masking
  - Add/update variables (KEY=VALUE)
  - Remove variables by key
  - TUI editor for env files
  - Compare two env files/projects

- **Formats Supported**
  - .env
  - .json
  - .yaml
  - Shell export

- **Project Profiles**
  - Initialize profile for project
  - Switch between profiles
  - List available profiles

- **Encryption**
  - Encrypt/decrypt env files
  - Key storage in local keychain or config dir

- **UX Design**
  - Typer CLI framework
  - Rich features: color-coded keys, masked secrets, tables, progress bars, syntax highlighting

### Version 2 (Advanced)

- **Remote Sync**
  - Sync with AWS SSM, HashiCorp Vault, GitHub Actions Secrets
  - Push/pull env to/from remote
  - Show sync status

- **Validation**
  - Validate env variable format and required keys
  - Support for YAML/JSON schema files

- **Hooks**
  - Pre/post command hooks
  - Custom reload scripts

- **Plugin System**
  - Extend via plugins: commands, formatters, validators
  - Install/remove plugins from PyPI or local

- **Analytics**
  - Optional usage tracking
  - Command history and stats

- **UX Enhancements**
  - Interactive tree view for profiles/envs
  - Colored diff highlighting
  - Live progress for sync

## Requirements

- Python >= 3.11
- **Core**: typer, rich, python-dotenv, cryptography, pyyaml, jsonschema
- **Cloud**: boto3, hvac, PyNaCl, httpx, requests
- **AI**: transformers, torch
- **UI**: textual, questionary
- **Reporting**: reportlab, pandas
- **System**: psutil

## EnvCLI v3.0.0 - Enterprise AI & Governance

### 🤖 AI-Assisted Analysis

```bash
envcli ai enable
envcli ai analyze --profile dev
```

AI-powered recommendations for naming conventions, compliance, and drift detection. Uses only metadata - never exposes raw secrets.

### 📋 Audit & Compliance Reporting

```bash
envcli audit report --format pdf --days 90
envcli audit governance --profile prod
```

Generate detailed compliance reports in JSON, CSV, or PDF format with governance scoring and recommendations.

### 🛡️ Policy Engine

```bash
envcli policy add-required "API_.*" --description "API keys must be prefixed"
envcli policy add-naming uppercase
envcli policy validate --profile dev
```

Enforce rules for required keys, prohibited patterns, naming conventions, and key rotation schedules.

### 🔐 Role-Based Access Control

```bash
envcli rbac enable
envcli rbac add-user alice admin
envcli rbac change-role bob member
envcli rbac audit-log
```

Granular permissions with admin/member/guest roles, complete audit logging, and access control.

## Complete Feature Set (v1 + v2 + v3)

## Architecture & Security

EnvCLI v3.0.0 features a modular, enterprise-ready architecture with uncompromising security:

### Core Modules

- **env_manager.py** - Environment variable CRUD, format handling, encryption
- **ai_assistant.py** - Metadata-only AI analysis and recommendations
- **audit_reporting.py** - Compliance reports, governance scoring
- **policy_engine.py** - Rule enforcement, validation, constraints
- **rbac.py** - Role-based access control, audit logging
- **sync.py** - Multi-cloud integrations (AWS SSM, GitHub, Vault)
- **dashboard.py** - Visual interface with Textual
- **team_collaboration.py** - Shared profiles, access control
- **shell_integration.py** - Cross-shell auto-loading
- **event_hooks.py** - Webhook and script automation
- **telemetry.py** - Insights and analytics

### Security First Design

- **Zero-trust architecture** - All operations are auditable and permission-controlled
- **Metadata-only AI** - AI never sees raw secrets, only hashed metadata
- **Enterprise encryption** - Fernet, PyNaCl, and cloud-native encryption
- **Compliance reporting** - Detailed audit trails and governance scoring
- **Access control** - RBAC with admin/member/guest roles
- **Policy enforcement** - Automated rule checking and violation prevention

### Dependencies

- **Core**: typer, rich, python-dotenv, cryptography, pyyaml
- **Cloud**: boto3, hvac, PyNaCl, httpx, requests
- **AI**: transformers, torch
- **UI**: textual, questionary
- **Reporting**: reportlab, pandas, jsonschema
- **System**: psutil

## Advanced Enterprise Features (v3.0.0+)

### 🤖 **AI-Assisted Governance**

```bash
envcli ai enable                    # Enable AI features
envcli ai analyze --profile dev     # AI recommendations
```

- Safe metadata-only AI analysis
- Naming convention suggestions
- Drift pattern detection
- Compliance recommendations

### 📋 **Enterprise Audit & Compliance**

```bash
envcli audit report --format pdf --days 90  # Generate compliance reports
envcli audit governance --profile prod       # Governance scoring
```

- Multi-format audit reports (JSON, CSV, PDF)
- Compliance scoring and recommendations
- Historical audit trails

### 🛡️ **Advanced Policy Engine**

```bash
envcli policy add-required "API_.*" --description "API keys required"
envcli policy add-naming uppercase
envcli policy validate --profile dev
```

- Required key enforcement
- Prohibited pattern detection
- Naming convention rules
- Key rotation schedules

### 🔐 **Role-Based Access Control**

```bash
envcli rbac enable
envcli rbac add-user alice admin
envcli rbac audit-log
```

- Admin/Member/Guest roles
- Complete audit logging
- Permission-based access control

### 📊 **Monitoring & Alerting**

```bash
envcli monitor enable
envcli monitor check                    # Health checks
envcli monitor add-webhook https://hooks.slack.com/...  # Alert channels
```

- Automated health monitoring
- Configurable alert channels (webhooks, Slack)
- Environment drift detection

### 🚀 **CI/CD Pipeline Integration**

```bash
envcli ci detect                       # Detect CI/CD environment
envcli ci load-secrets                 # Load pipeline secrets
envcli ci promote dev staging          # Environment promotion
```

- Auto-detection of CI/CD platforms
- Pipeline secret loading
- Environment promotion workflows

### ☸️ **Kubernetes Integration**

```bash
envcli sync push-k8s-secret my-secret --namespace production
envcli sync push-k8s-configmap my-config --namespace production
```

- Native Kubernetes Secrets support
- ConfigMap integration for non-sensitive data
- Namespace-aware operations

### ☁️ **Multi-Cloud Expansions**

```bash
# Azure Key Vault
envcli sync push-azure-kv --prefix myapp
envcli sync pull-azure-kv --prefix myapp

# Google Cloud Secret Manager
envcli sync push-gcp-sm --prefix myapp
envcli sync pull-gcp-sm --prefix myapp
```

- Azure Key Vault integration
- Google Cloud Secret Manager support
- Unified multi-cloud experience

## What Makes EnvCLI v3.0.0+ the Ultimate Platform?

EnvCLI v3.0.0+ represents the **pinnacle of environment management technology** - a comprehensive, AI-powered, enterprise-grade platform that doesn't just manage environment variables, but transforms how modern software organizations operate.

### 🚀 **Architectural Supremacy**

- **v1 (MVP)**: Basic environment variable CRUD
- **v2 (Advanced)**: Cloud sync, automation, collaboration
- **v3 (Ultimate)**: AI intelligence, enterprise security, compliance automation, predictive analytics

### 🏆 **Unmatched Enterprise Capabilities**

- **🤖 AI-Powered Intelligence**: Safe AI analysis, predictive insights, risk assessment
- **🏢 Enterprise Security**: RBAC, comprehensive audit logging, policy enforcement
- **☁️ Multi-Cloud Mastery**: 6+ cloud providers with native integrations
- **📋 Compliance Automation**: SOC2, GDPR, HIPAA automated frameworks
- **🔧 DevOps Automation**: CI/CD integration, event-driven hooks, monitoring
- **🎨 Beautiful Interfaces**: TUI, web dashboard, REST API, mobile-ready
- **📊 Predictive Analytics**: Forecast issues, usage trends, risk assessment
- **🔄 Advanced Automation**: Webhooks, scripts, environment promotion

### 🎯 **Real-World Enterprise Transformation**

- **Security Teams**: AI-assisted compliance, automated audits, risk prediction
- **DevOps Engineers**: Multi-cloud automation, CI/CD integration, infrastructure as code
- **Platform Teams**: Enterprise governance, unified cloud management, monitoring
- **Compliance Officers**: Automated framework checks, audit trails, reporting
- **Development Teams**: AI recommendations, beautiful interfaces, productivity boost

### 🌟 **Technical Excellence at Scale**

- **Zero-Trust by Design**: Every operation audited, permission-controlled, logged
- **AI-Safe Architecture**: Metadata-only AI without security compromises
- **Multi-Cloud Native**: Unified experience across all major cloud platforms
- **Enterprise Encryption**: Fernet, PyNaCl, hardware security modules
- **Production Ready**: Comprehensive error handling, scalability, reliability

### 💎 **The Competitive Edge**

EnvCLI v3.0.0+ isn't just better than existing tools—it's in a **different category entirely**:

- **Vs Basic Tools**: Provides enterprise features they lack
- **Vs Cloud Tools**: Offers unified multi-cloud experience
- **Vs Enterprise Vaults**: Delivers 80% functionality at 1% cost
- **Vs CI/CD Tools**: General-purpose vs pipeline-specific
- **Vs Competitors**: More comprehensive, AI-powered, beautiful

**EnvCLI v3.0.0+ is the definitive environment management platform for the modern enterprise—combining AI intelligence, enterprise security, multi-cloud operations, and beautiful interfaces into a single, transformative solution.** 🎉

**Ready to revolutionize your environment management?** 🚀

## Contributing

Contributions are welcome! The codebase is well-structured and documented. Key areas for contribution:

- Additional cloud sync providers
- More format parsers (TOML, INI, etc.)
- Enhanced TUI features
- Plugin ecosystem development
- Testing and documentation

## Author

Teck - Nom-Nom-Hub

## License

MIT
