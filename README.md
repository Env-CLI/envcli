# EnvCLI

A comprehensive environment variable management platform with AI-powered governance, enterprise security, multi-cloud operations, and compliance automation.

## Installation

### Install from GitHub (Recommended)

```bash
# Using pip
pip install git+https://github.com/Env-CLI/envcli.git

# Using uv (faster)
uv tool install git+https://github.com/Env-CLI/envcli.git
```

### Install from Release

Download the latest `.whl` file from [Releases](https://github.com/Env-CLI/envcli/releases) and install:

```bash
pip install envcli-3.0.0-py3-none-any.whl
```

### Development Installation

```bash
git clone https://github.com/Env-CLI/envcli.git
cd envcli
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

## Features

### AI-Powered Intelligence

- Multiple AI providers: OpenAI, Anthropic, Google Gemini, Ollama, or local pattern matching
- Smart analysis with recommendations for naming, security, and compliance
- Safe actions: Apply AI recommendations automatically without exposing secrets
- Custom rules and policies: Define your own naming conventions and transformation rules
- Privacy-first: Only metadata analyzed, never raw secrets
- Predictive analytics: Forecast environment issues before they occur
- Risk assessment: Automated risk scoring and mitigation suggestions

See [AI Provider Guide](docs/AI_PROVIDERS.md), [AI Safe Actions](docs/AI_SAFE_ACTIONS.md), and [Custom Rules](docs/AI_CUSTOM_RULES.md) for detailed configuration. (docs created by ai for now till I have time)

### Enterprise-Grade Security

- Role-based access control with granular permissions
- Advanced encryption: Fernet, PyNaCl, cloud-native encryption
- Audit logging with complete audit trails for all operations
- Compliance frameworks: SOC2, GDPR, HIPAA automated checks

### Multi-Cloud Native

- AWS SSM Parameter Store
- Azure Key Vault
- GCP Secret Manager
- HashiCorp Vault
- Kubernetes Secrets and ConfigMaps

### Interfaces

- Terminal User Interface (TUI): Full-featured Textual-powered TUI with 18 integrated modules
- Interactive dashboard: Visual environment management in your terminal
- Web dashboard: Streamlit-based web application
- REST API: Complete programmatic access
- Rich CLI: Colorful, intuitive command-line experience

### Advanced Automation

- Event-driven hooks: Webhooks and scripts for all operations
- CI/CD integration: Native pipeline support and environment promotion
- Monitoring and alerting: Health checks and automated notifications
- Policy engine: Automated rule enforcement and validation

## Quick Start

Launch the Terminal User Interface:

```bash
envcli tui
```

Or use the CLI:

```bash
# View help
envcli --help

# Initialize a profile
envcli profile init --name dev

# Add variables
envcli env add API_KEY "your-secret-key"
envcli env add DATABASE_URL "postgresql://localhost/db"

# List variables (with masking)
envcli env list

# Import from .env file
envcli env import .env

# Export to different formats
envcli env export config.json --format json
envcli env export config.yaml --format yaml

# Compare profiles
envcli env diff dev prod

# Switch profiles
envcli profile use prod
```

## AI Features

```bash
# Configure AI provider
envcli ai enable --provider openai
envcli ai enable --provider anthropic
envcli ai enable --provider google
envcli ai enable --provider ollama

# Analyze environment
envcli ai analyze --profile dev

# Get and apply suggestions
envcli ai suggest --profile dev
envcli ai apply --preview
envcli ai apply --yes

# Custom rules
envcli ai add-rule naming '.*_(key|secret|token)' uppercase
envcli ai list-rules
```

## Cloud Sync

```bash
# AWS SSM
envcli sync push aws_ssm /myapp/prod
envcli sync pull aws_ssm /myapp/prod

# HashiCorp Vault
envcli sync push vault /myapp/prod
envcli sync pull vault /myapp/prod

# Kubernetes
envcli sync push-k8s-secret my-secret --namespace production

# Azure Key Vault
envcli sync push-azure-kv --prefix myapp

# Google Cloud Secret Manager
envcli sync push-gcp-sm --prefix myapp
```

## Compliance and Security

```bash
# Enable compliance framework
envcli compliance enable soc2
envcli compliance assess soc2 --profile prod
envcli compliance report soc2

# RBAC
envcli rbac enable
envcli rbac add-user alice admin
envcli rbac audit-log

# Encryption
envcli encrypt encrypt secret.env
envcli encrypt decrypt secret.env
```

## CI/CD Integration

```bash
# Detect CI/CD environment
envcli ci detect

# Load pipeline secrets
envcli ci load-secrets

# Promote environments
envcli ci promote dev staging
```

## Architecture

EnvCLI features a modular, enterprise-ready architecture:

### Core Modules

- **env_manager.py** - Environment variable CRUD, format handling, encryption
- **ai_assistant.py** - Metadata-only AI analysis and recommendations
- **audit_reporting.py** - Compliance reports, governance scoring
- **policy_engine.py** - Rule enforcement, validation, constraints
- **rbac.py** - Role-based access control, audit logging
- **sync.py** - Multi-cloud integrations
- **dashboard.py** - Visual interface with Textual
- **team_collaboration.py** - Shared profiles, access control
- **shell_integration.py** - Cross-shell auto-loading
- **event_hooks.py** - Webhook and script automation
- **telemetry.py** - Insights and analytics

### Security Design

- Zero-trust architecture: All operations are auditable and permission-controlled
- Metadata-only AI: AI never sees raw secrets, only hashed metadata
- Enterprise encryption: Fernet, PyNaCl, and cloud-native encryption
- Compliance reporting: Detailed audit trails and governance scoring
- Access control: RBAC with admin/member/guest roles
- Policy enforcement: Automated rule checking and violation prevention

## Requirements

- Python >= 3.11
- Core: typer, rich, python-dotenv, cryptography, pyyaml, jsonschema
- Cloud: boto3, hvac, PyNaCl, httpx, requests
- AI: transformers, torch
- UI: textual, questionary
- Reporting: reportlab, pandas
- System: psutil

## Documentation

- [AI Provider Guide](docs/AI_PROVIDERS.md)
- [AI Safe Actions](docs/AI_SAFE_ACTIONS.md)
- [Custom Rules](docs/AI_CUSTOM_RULES.md)
- [AI Architecture](docs/AI_ARCHITECTURE.md)
- [Quick Reference](docs/AI_QUICK_REFERENCE.md)

## Contributing

Contributions are welcome. Key areas for contribution:

- Additional cloud sync providers
- More format parsers
- Enhanced TUI features
- Plugin ecosystem development
- Testing and documentation

## License

MIT
