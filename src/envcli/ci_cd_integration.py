"""
CI/CD integration for EnvCLI.
"""

import json
import os
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional
from .env_manager import EnvManager

class CICDPipeline:
    """CI/CD pipeline integration."""

    def __init__(self, pipeline_type: str = "auto"):
        self.pipeline_type = pipeline_type or self._detect_pipeline()
        self.env_vars = {}

    def _detect_pipeline(self) -> str:
        """Detect the current CI/CD pipeline."""
        # Check environment variables for different CI systems
        if os.getenv('GITHUB_ACTIONS'):
            return 'github_actions'
        elif os.getenv('GITLAB_CI'):
            return 'gitlab_ci'
        elif os.getenv('JENKINS_HOME'):
            return 'jenkins'
        elif os.getenv('CIRCLECI'):
            return 'circleci'
        elif os.getenv('TRAVIS'):
            return 'travis_ci'
        elif os.getenv('BUILDKITE'):
            return 'buildkite'
        else:
            return 'unknown'

    def load_pipeline_secrets(self, profile: str) -> bool:
        """Load secrets from CI/CD pipeline into profile."""
        try:
            if self.pipeline_type == 'github_actions':
                return self._load_github_actions_secrets(profile)
            elif self.pipeline_type == 'gitlab_ci':
                return self._load_gitlab_ci_secrets(profile)
            elif self.pipeline_type == 'jenkins':
                return self._load_jenkins_secrets(profile)
            elif self.pipeline_type == 'circleci':
                return self._load_circleci_secrets(profile)
            else:
                print(f"Unsupported pipeline type: {self.pipeline_type}")
                return False
        except Exception as e:
            print(f"Failed to load pipeline secrets: {e}")
            return False

    def _load_github_actions_secrets(self, profile: str) -> bool:
        """Load secrets from GitHub Actions."""
        env_vars = {}

        # GitHub Actions secrets are available as environment variables
        # They follow the pattern: INPUT_<UPPERCASE_NAME>
        for key, value in os.environ.items():
            if key.startswith('INPUT_') and key != 'INPUT_':
                # Remove INPUT_ prefix and convert to original name
                original_key = key[6:]  # Remove 'INPUT_'
                env_vars[original_key] = value

        if env_vars:
            manager = EnvManager(profile)
            manager.save_env(env_vars)
            return True
        return False

    def _load_gitlab_ci_secrets(self, profile: str) -> bool:
        """Load secrets from GitLab CI."""
        env_vars = {}

        # GitLab CI variables are available as environment variables
        # Look for variables that might be secrets (this is a heuristic)
        secret_indicators = ['secret', 'key', 'token', 'password']

        for key, value in os.environ.items():
            if any(indicator in key.lower() for indicator in secret_indicators):
                env_vars[key] = value

        if env_vars:
            manager = EnvManager(profile)
            manager.save_env(env_vars)
            return True
        return False

    def _load_jenkins_secrets(self, profile: str) -> bool:
        """Load secrets from Jenkins."""
        # Jenkins secrets are typically available through credential binding
        # This is more complex and would require Jenkins-specific setup
        print("Jenkins integration requires credential binding setup")
        return False

    def _load_circleci_secrets(self, profile: str) -> bool:
        """Load secrets from CircleCI."""
        env_vars = {}

        # CircleCI environment variables
        for key, value in os.environ.items():
            if key.startswith('CIRCLE_') or 'SECRET' in key.upper():
                env_vars[key] = value

        if env_vars:
            manager = EnvManager(profile)
            manager.save_env(env_vars)
            return True
        return False

    def generate_pipeline_config(self, profile: str, pipeline_type: Optional[str] = None) -> str:
        """Generate CI/CD pipeline configuration."""
        pipeline = pipeline_type or self.pipeline_type

        if pipeline == 'github_actions':
            return self._generate_github_actions_config(profile)
        elif pipeline == 'gitlab_ci':
            return self._generate_gitlab_ci_config(profile)
        elif pipeline == 'jenkins':
            return self._generate_jenkins_config(profile)
        else:
            return f"# Unsupported pipeline type: {pipeline}"

    def _generate_github_actions_config(self, profile: str) -> str:
        """Generate GitHub Actions workflow configuration."""
        config = f"""name: Deploy with EnvCLI

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install EnvCLI
      run: pip install envcli

    - name: Load Environment
      run: envcli env load-shell {profile}

    - name: Deploy
      run: |
        # Your deployment commands here
        echo "Deployment completed"
"""

        return config

    def _generate_gitlab_ci_config(self, profile: str) -> str:
        """Generate GitLab CI configuration."""
        config = f"""stages:
  - deploy

deploy:
  stage: deploy
  script:
    - pip install envcli
    - envcli env load-shell {profile}
    - echo "Deployment completed"
"""

        return config

    def _generate_jenkins_config(self, profile: str) -> str:
        """Generate Jenkins pipeline configuration."""
        config = f"""pipeline {{
    agent any

    stages {{
        stage('Deploy') {{
            steps {{
                sh 'pip install envcli'
                sh 'envcli env load-shell {profile}'
                sh 'echo "Deployment completed"'
            }}
        }}
    }}
}}"""

        return config

    def validate_pipeline_setup(self) -> Dict[str, Any]:
        """Validate CI/CD pipeline setup."""
        result = {
            "pipeline_type": self.pipeline_type,
            "detected": self.pipeline_type != "unknown",
            "capabilities": []
        }

        if self.pipeline_type == "github_actions":
            result["capabilities"] = ["secrets", "environment_variables", "artifacts"]
        elif self.pipeline_type == "gitlab_ci":
            result["capabilities"] = ["secrets", "environment_variables", "artifacts", "docker"]
        elif self.pipeline_type == "jenkins":
            result["capabilities"] = ["secrets", "environment_variables", "artifacts", "plugins"]
        elif self.pipeline_type == "circleci":
            result["capabilities"] = ["secrets", "environment_variables", "artifacts", "docker"]

        return result

class EnvironmentPromotion:
    """Handle environment promotion across stages."""

    def __init__(self):
        self.stages = ["dev", "staging", "prod"]

    def promote_environment(self, from_stage: str, to_stage: str) -> bool:
        """Promote environment variables from one stage to another."""
        if from_stage not in self.stages or to_stage not in self.stages:
            print(f"Invalid stages. Available: {', '.join(self.stages)}")
            return False

        if self.stages.index(from_stage) >= self.stages.index(to_stage):
            print("Can only promote forward in the pipeline")
            return False

        try:
            # Load from source stage
            source_manager = EnvManager(from_stage)
            env_vars = source_manager.load_env()

            # Apply promotion rules (e.g., modify URLs, scale resources)
            promoted_vars = self._apply_promotion_rules(env_vars, from_stage, to_stage)

            # Save to target stage
            target_manager = EnvManager(to_stage)
            target_manager.save_env(promoted_vars)

            print(f"Successfully promoted environment from {from_stage} to {to_stage}")
            return True

        except Exception as e:
            print(f"Promotion failed: {e}")
            return False

    def _apply_promotion_rules(self, env_vars: Dict[str, str], from_stage: str, to_stage: str) -> Dict[str, str]:
        """Apply promotion rules to environment variables."""
        promoted = env_vars.copy()

        # Example rules - customize based on your needs
        for key, value in promoted.items():
            if 'url' in key.lower() and from_stage in value:
                # Replace stage in URLs
                promoted[key] = value.replace(from_stage, to_stage)

            elif 'replicas' in key.lower() and to_stage == 'prod':
                # Scale up for production
                try:
                    replicas = int(value)
                    promoted[key] = str(replicas * 3)  # Example scaling
                except ValueError:
                    pass

        return promoted

    def preview_promotion(self, from_stage: str, to_stage: str) -> Dict[str, Any]:
        """Preview what changes would be made during promotion."""
        source_manager = EnvManager(from_stage)
        source_vars = source_manager.load_env()

        target_manager = EnvManager(to_stage)
        target_vars = target_manager.load_env()

        promoted_vars = self._apply_promotion_rules(source_vars, from_stage, to_stage)

        changes = {
            "added": {k: v for k, v in promoted_vars.items() if k not in target_vars},
            "modified": {k: {"from": target_vars.get(k), "to": v}
                        for k, v in promoted_vars.items()
                        if k in target_vars and target_vars[k] != v},
            "removed": {k: v for k, v in target_vars.items() if k not in promoted_vars}
        }

        return {
            "from_stage": from_stage,
            "to_stage": to_stage,
            "changes": changes,
            "total_changes": sum(len(v) for v in changes.values())
        }
