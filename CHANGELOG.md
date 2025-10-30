# Changelog

All notable changes to EnvCLI will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [3.0.0] - 2024-10-29

### Added

- **Beautiful TUI** - Modern terminal user interface built with Textual
  - 18 integrated modules (Dashboard, Variables, Profiles, Encryption, AI Analysis, etc.)
  - Organized sidebar with grouped modules
  - Keyboard shortcuts (Q/Ctrl+C/Ctrl+D to quit)
  - Real-time updates and notifications
  
- **AI-Powered Features**
  - Multiple AI providers (OpenAI, Anthropic, Google Gemini, Ollama)
  - AI Safe Actions - Apply recommendations without exposing secrets
  - Custom Rules & Policies - Define your own conventions
  - Predictive Analytics - Forecast environment issues
  
- **Enterprise Security**
  - AES-256 encryption for sensitive variables
  - RBAC (Role-Based Access Control)
  - Compliance frameworks (SOC2, HIPAA, PCI-DSS, GDPR)
  - Audit logging with detailed tracking
  
- **Multi-Cloud Integration**
  - AWS Secrets Manager
  - Azure Key Vault
  - Google Cloud Secret Manager
  - Kubernetes Secrets & ConfigMaps
  
- **Automation & CI/CD**
  - GitHub Actions integration
  - GitLab CI support
  - Jenkins pipeline support
  - Event hooks and webhooks
  
- **Monitoring & Analytics**
  - Real-time monitoring dashboard
  - Usage analytics and insights
  - Performance metrics
  - Predictive analytics

### Changed

- Removed beta access control system
- Improved sidebar design with better icons and grouping
- Updated installation to use GitHub releases

### Fixed

- VSCode keyboard shortcut conflicts (removed Ctrl+Q)
- TUI initialization and access prompt issues
- Sidebar styling and visual hierarchy

## [2.0.0] - Previous Release

### Added

- Core environment variable management
- Profile system
- Basic encryption
- CLI interface

---

## Installation

```bash
# Install from GitHub
pip install git+https://github.com/Nom-nom-hub/env-cli.git

# Or download from releases
pip install envcli-3.0.0-py3-none-any.whl
```

## Usage

```bash
# Launch TUI
envcli tui

# View help
envcli --help
```
