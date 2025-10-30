"""
AI Assistant for EnvCLI - Metadata-only analysis and recommendations.
"""

import json
import hashlib
from typing import Dict, List, Optional, Any
from datetime import datetime
from .config import CONFIG_DIR
from .env_manager import EnvManager
from .ai_providers import get_provider, AIProvider

AI_CONFIG_FILE = CONFIG_DIR / "ai_config.json"

class AIAssistant:
    """AI-powered assistant for environment variable analysis."""

    def __init__(self):
        self.enabled = self._check_ai_enabled()
        self.config = self._load_config()
        self.provider = self._get_provider()

    def _check_ai_enabled(self) -> bool:
        """Check if AI features are enabled."""
        if AI_CONFIG_FILE.exists():
            with open(AI_CONFIG_FILE, 'r') as f:
                config = json.load(f)
                return config.get("enabled", False)
        return False

    def _load_config(self) -> Dict[str, Any]:
        """Load AI configuration."""
        if AI_CONFIG_FILE.exists():
            with open(AI_CONFIG_FILE, 'r') as f:
                return json.load(f)
        return {
            "enabled": False,
            "provider": "pattern-matching",
            "model": None
        }

    def _get_provider(self) -> Optional[AIProvider]:
        """Get the configured AI provider."""
        if not self.enabled:
            return None

        provider_name = self.config.get("provider", "pattern-matching")
        model = self.config.get("model")

        try:
            if model:
                return get_provider(provider_name, model=model)
            else:
                return get_provider(provider_name)
        except Exception:
            # Fallback to pattern matching if provider fails
            return get_provider("pattern-matching")

    def enable_ai(self, provider: str = "pattern-matching", model: Optional[str] = None):
        """Enable AI features with specified provider."""
        config = {
            "enabled": True,
            "provider": provider,
            "model": model,
            "last_updated": datetime.now().isoformat()
        }

        AI_CONFIG_FILE.parent.mkdir(exist_ok=True)
        with open(AI_CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)

        self.enabled = True
        self.config = config
        self.provider = self._get_provider()

    def disable_ai(self):
        """Disable AI features."""
        if AI_CONFIG_FILE.exists():
            config = self.config.copy()
            config["enabled"] = False
            with open(AI_CONFIG_FILE, 'w') as f:
                json.dump(config, f, indent=2)
        self.enabled = False
        self.provider = None

    def configure_provider(self, provider: str, model: Optional[str] = None) -> Dict[str, Any]:
        """Configure AI provider and return status."""
        try:
            # Test the provider
            test_provider = get_provider(provider, model=model) if model else get_provider(provider)

            if not test_provider.is_available():
                return {
                    "success": False,
                    "provider": provider,
                    "message": f"Provider '{provider}' is not available. Check configuration.",
                    "provider_name": test_provider.get_provider_name()
                }

            # Update config
            self.config["provider"] = provider
            if model:
                self.config["model"] = model
            self.config["last_updated"] = datetime.now().isoformat()

            AI_CONFIG_FILE.parent.mkdir(exist_ok=True)
            with open(AI_CONFIG_FILE, 'w') as f:
                json.dump(self.config, f, indent=2)

            self.provider = test_provider

            return {
                "success": True,
                "provider": provider,
                "message": f"Provider configured successfully",
                "provider_name": test_provider.get_provider_name()
            }
        except Exception as e:
            return {
                "success": False,
                "provider": provider,
                "message": str(e)
            }

    def get_provider_status(self) -> Dict[str, Any]:
        """Get current provider status and available providers."""
        current_provider = self.config.get("provider", "pattern-matching")
        current_model = self.config.get("model")

        # Check available providers
        available_providers = []
        for provider_name in ["openai", "anthropic", "google", "ollama", "pattern-matching"]:
            try:
                provider = get_provider(provider_name)
                available_providers.append({
                    "name": provider_name,
                    "display_name": provider.get_provider_name(),
                    "available": provider.is_available(),
                    "current": provider_name == current_provider
                })
            except:
                pass

        return {
            "enabled": self.enabled,
            "current_provider": current_provider,
            "current_model": current_model,
            "providers": available_providers
        }

    def analyze_variable_naming(self, profile: str) -> List[Dict[str, Any]]:
        """Analyze variable naming patterns and provide recommendations."""
        if not self.enabled:
            return []

        manager = EnvManager(profile)
        env_vars = manager.load_env()

        recommendations = []

        # Analyze naming patterns
        for var_name, var_value in env_vars.items():
            issues = self._analyze_variable_name(var_name, var_value)

            for issue in issues:
                recommendations.append({
                    "type": "naming",
                    "severity": issue["severity"],
                    "variable": var_name,
                    "profile": profile,
                    "message": issue["message"],
                    "suggestion": issue["suggestion"]
                })

        return recommendations

    def _analyze_variable_name(self, name: str, value: str) -> List[Dict[str, str]]:
        """Analyze a single variable name for issues."""
        issues = []

        # Check for common naming issues
        if name.isupper():
            # Check for non-standard separators
            if '_' not in name and len(name) > 10:
                issues.append({
                    "severity": "info",
                    "message": f"Variable '{name}' uses no separators - consider using underscores",
                    "suggestion": f"Consider renaming to: {self._suggest_better_name(name)}"
                })

        # Check for potential secret indicators
        secret_indicators = ['secret', 'key', 'token', 'password', 'auth']
        has_secret_indicator = any(indicator in name.lower() for indicator in secret_indicators)

        if has_secret_indicator and not name.isupper():
            issues.append({
                "severity": "warning",
                "message": f"Secret variable '{name}' should be uppercase",
                "suggestion": f"Rename to: {name.upper()}"
            })

        # Check for overly generic names
        generic_names = ['VAR', 'VALUE', 'DATA', 'CONFIG']
        if name.upper() in generic_names:
            issues.append({
                "severity": "warning",
                "message": f"Variable name '{name}' is too generic",
                "suggestion": "Use a more descriptive name that indicates its purpose"
            })

        return issues

    def _suggest_better_name(self, name: str) -> str:
        """Suggest a better variable name."""
        # Simple heuristics for name improvement
        if len(name) > 15 and '_' not in name:
            # Insert underscores before capital letters or numbers
            import re
            suggestion = re.sub(r'([A-Z]|[0-9]+)', r'_\1', name).strip('_').upper()
            return suggestion
        return name

    def detect_drift_patterns(self, profiles: List[str]) -> List[Dict[str, Any]]:
        """Analyze drift patterns across profiles."""
        if not self.enabled or len(profiles) < 2:
            return []

        insights = []

        # Compare variable patterns across profiles
        profile_data = {}
        for profile in profiles:
            manager = EnvManager(profile)
            env_vars = manager.load_env()
            profile_data[profile] = {
                "count": len(env_vars),
                "prefixes": self._extract_prefixes(list(env_vars.keys())),
                "patterns": self._analyze_patterns(env_vars)
            }

        # Look for inconsistencies
        all_prefixes = set()
        for data in profile_data.values():
            all_prefixes.update(data["prefixes"])

        for prefix in all_prefixes:
            present_in = [p for p, data in profile_data.items() if prefix in data["prefixes"]]
            missing_from = [p for p in profiles if p not in present_in]

            if len(present_in) > 0 and len(missing_from) > 0:
                insights.append({
                    "type": "drift",
                    "severity": "info",
                    "message": f"Variable prefix '{prefix}' present in {present_in} but missing from {missing_from}",
                    "suggestion": "Consider standardizing variable prefixes across profiles"
                })

        return insights

    def _extract_prefixes(self, var_names: List[str]) -> set:
        """Extract common prefixes from variable names."""
        prefixes = set()
        for name in var_names:
            if '_' in name:
                prefix = name.split('_')[0]
                if len(prefix) >= 2:  # Avoid single letter prefixes
                    prefixes.add(prefix.upper())
        return prefixes

    def _analyze_patterns(self, env_vars: Dict[str, str]) -> Dict[str, Any]:
        """Analyze patterns in environment variables."""
        patterns = {
            "uppercase_ratio": sum(1 for k in env_vars.keys() if k.isupper()) / len(env_vars),
            "has_secrets": any(any(word in k.lower() for word in ['secret', 'key', 'token', 'password'])
                             for k in env_vars.keys()),
            "avg_length": sum(len(k) for k in env_vars.keys()) / len(env_vars)
        }
        return patterns

    def generate_recommendations(self, profile: str) -> Dict[str, Any]:
        """Generate comprehensive AI recommendations for a profile."""
        if not self.enabled:
            return {"error": "AI features are disabled"}

        # Get pattern-based recommendations (always available)
        pattern_recommendations = self.analyze_variable_naming(profile)

        # Try to get AI-powered recommendations if provider is available
        ai_recommendations = None
        if self.provider and self.provider.get_provider_name() != "Pattern Matching (Local)":
            try:
                manager = EnvManager(profile)
                env_vars = manager.load_env()

                # Create metadata (no sensitive values)
                metadata = {
                    "variable_count": len(env_vars),
                    "variable_names": list(env_vars.keys()),
                    "naming_patterns": self._analyze_patterns(env_vars),
                    "prefixes": list(self._extract_prefixes(list(env_vars.keys())))
                }

                context = f"Analyzing profile '{profile}' with {len(env_vars)} environment variables"
                ai_recommendations = self.provider.analyze_metadata(metadata, context)
            except Exception as e:
                ai_recommendations = f"AI analysis failed: {str(e)}"

        recommendations = {
            "pattern_analysis": pattern_recommendations,
            "ai_analysis": ai_recommendations,
            "provider": self.provider.get_provider_name() if self.provider else "None",
            "generated_at": datetime.now().isoformat(),
            "profile": profile
        }

        return recommendations

    def get_metadata_hash(self, data: Dict[str, Any]) -> str:
        """Generate a hash of metadata for privacy-preserving analysis."""
        # Create a metadata representation without sensitive values
        metadata = {}
        for key, value in data.items():
            metadata[key] = {
                "length": len(str(value)),
                "type": type(value).__name__,
                "pattern": self._get_value_pattern(str(value))
            }

        # Hash the metadata
        metadata_str = json.dumps(metadata, sort_keys=True)
        return hashlib.sha256(metadata_str.encode()).hexdigest()[:16]

    def _get_value_pattern(self, value: str) -> str:
        """Extract a pattern from a value without revealing the content."""
        if len(value) == 0:
            return "empty"

        # Check for common patterns
        if value.replace('.', '').replace('-', '').isdigit():
            return "numeric"
        elif '@' in value and '.' in value:
            return "email"
        elif '://' in value:
            return "url"
        elif len(value) > 50:
            return "long_text"
        else:
            return "short_text"
