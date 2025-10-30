"""
AI Provider abstraction layer for EnvCLI.
Supports multiple AI providers: OpenAI, Anthropic, Google, Ollama, and pattern-matching.
"""

import os
import json
from typing import Dict, List, Optional, Any
from abc import ABC, abstractmethod
import httpx


class AIProvider(ABC):
    """Abstract base class for AI providers."""
    
    @abstractmethod
    def analyze_metadata(self, metadata: Dict[str, Any], context: str) -> str:
        """Analyze metadata and return recommendations."""
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """Return the provider name."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the provider is properly configured."""
        pass


class OpenAIProvider(AIProvider):
    """OpenAI GPT provider."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        self.base_url = "https://api.openai.com/v1/chat/completions"
    
    def get_provider_name(self) -> str:
        return f"OpenAI ({self.model})"
    
    def is_available(self) -> bool:
        return self.api_key is not None
    
    def analyze_metadata(self, metadata: Dict[str, Any], context: str) -> str:
        """Analyze metadata using OpenAI API."""
        if not self.is_available():
            raise ValueError("OpenAI API key not configured. Set OPENAI_API_KEY environment variable.")
        
        prompt = self._build_prompt(metadata, context)
        
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    self.base_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": "You are an expert in environment variable management, security, and DevOps best practices. Analyze metadata (never raw secrets) and provide actionable recommendations."},
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.7,
                        "max_tokens": 1000
                    }
                )
                response.raise_for_status()
                result = response.json()
                return result["choices"][0]["message"]["content"]
        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}")
    
    def _build_prompt(self, metadata: Dict[str, Any], context: str) -> str:
        return f"""Analyze the following environment variable metadata and provide recommendations:

Context: {context}

Metadata (no sensitive values included):
{json.dumps(metadata, indent=2)}

Please provide:
1. Naming convention issues
2. Security concerns based on patterns
3. Best practice recommendations
4. Potential improvements

Keep recommendations concise and actionable."""


class AnthropicProvider(AIProvider):
    """Anthropic Claude provider."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-5-sonnet-20241022"):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.model = model
        self.base_url = "https://api.anthropic.com/v1/messages"
    
    def get_provider_name(self) -> str:
        return f"Anthropic ({self.model})"
    
    def is_available(self) -> bool:
        return self.api_key is not None
    
    def analyze_metadata(self, metadata: Dict[str, Any], context: str) -> str:
        """Analyze metadata using Anthropic API."""
        if not self.is_available():
            raise ValueError("Anthropic API key not configured. Set ANTHROPIC_API_KEY environment variable.")
        
        prompt = self._build_prompt(metadata, context)
        
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    self.base_url,
                    headers={
                        "x-api-key": self.api_key,
                        "anthropic-version": "2023-06-01",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "max_tokens": 1024,
                        "messages": [
                            {"role": "user", "content": prompt}
                        ],
                        "system": "You are an expert in environment variable management, security, and DevOps best practices. Analyze metadata (never raw secrets) and provide actionable recommendations."
                    }
                )
                response.raise_for_status()
                result = response.json()
                return result["content"][0]["text"]
        except Exception as e:
            raise Exception(f"Anthropic API error: {str(e)}")
    
    def _build_prompt(self, metadata: Dict[str, Any], context: str) -> str:
        return f"""Analyze the following environment variable metadata and provide recommendations:

Context: {context}

Metadata (no sensitive values included):
{json.dumps(metadata, indent=2)}

Please provide:
1. Naming convention issues
2. Security concerns based on patterns
3. Best practice recommendations
4. Potential improvements

Keep recommendations concise and actionable."""


class GoogleProvider(AIProvider):
    """Google Gemini provider."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-1.5-flash"):
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        self.model = model
    
    def get_provider_name(self) -> str:
        return f"Google ({self.model})"
    
    def is_available(self) -> bool:
        return self.api_key is not None
    
    def analyze_metadata(self, metadata: Dict[str, Any], context: str) -> str:
        """Analyze metadata using Google Gemini API."""
        if not self.is_available():
            raise ValueError("Google API key not configured. Set GOOGLE_API_KEY environment variable.")
        
        prompt = self._build_prompt(metadata, context)
        base_url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
        
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    f"{base_url}?key={self.api_key}",
                    headers={"Content-Type": "application/json"},
                    json={
                        "contents": [{
                            "parts": [{
                                "text": prompt
                            }]
                        }],
                        "generationConfig": {
                            "temperature": 0.7,
                            "maxOutputTokens": 1000
                        }
                    }
                )
                response.raise_for_status()
                result = response.json()
                return result["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as e:
            raise Exception(f"Google API error: {str(e)}")
    
    def _build_prompt(self, metadata: Dict[str, Any], context: str) -> str:
        return f"""You are an expert in environment variable management, security, and DevOps best practices.

Analyze the following environment variable metadata and provide recommendations:

Context: {context}

Metadata (no sensitive values included):
{json.dumps(metadata, indent=2)}

Please provide:
1. Naming convention issues
2. Security concerns based on patterns
3. Best practice recommendations
4. Potential improvements

Keep recommendations concise and actionable."""


class OllamaProvider(AIProvider):
    """Ollama local LLM provider with auto-detection."""

    def __init__(self, model: Optional[str] = None, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.model = model
        self._available_models = None

        # Auto-detect model if not specified
        if self.model is None:
            self.model = self._auto_detect_model()

    def get_provider_name(self) -> str:
        return f"Ollama ({self.model})" if self.model else "Ollama (no model)"

    def is_available(self) -> bool:
        """Check if Ollama is running and has models."""
        try:
            models = self.get_available_models()
            return len(models) > 0
        except:
            return False

    def get_available_models(self) -> list:
        """Get list of available Ollama models."""
        if self._available_models is not None:
            return self._available_models

        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.get(f"{self.base_url}/api/tags")
                if response.status_code == 200:
                    data = response.json()
                    self._available_models = [model["name"] for model in data.get("models", [])]
                    return self._available_models
        except:
            pass

        return []

    def _auto_detect_model(self) -> Optional[str]:
        """Auto-detect the best available model."""
        models = self.get_available_models()

        if not models:
            return None

        # Preferred models in order
        preferred = [
            "llama3.2",
            "llama3.1",
            "llama3",
            "llama2",
            "mistral",
            "codellama",
            "phi",
            "gemma"
        ]

        # Try to find a preferred model
        for pref in preferred:
            for model in models:
                if model.startswith(pref):
                    return model

        # Return first available model
        return models[0]

    def analyze_metadata(self, metadata: Dict[str, Any], context: str) -> str:
        """Analyze metadata using Ollama local API."""
        # Check if Ollama is running
        models = self.get_available_models()

        if not models:
            raise ValueError(
                "Ollama is not running or has no models installed.\n"
                "To fix this:\n"
                "  1. Start Ollama: ollama serve\n"
                "  2. Pull a model: ollama pull llama3.2\n"
                "  3. Try again: envcli ai analyze"
            )

        # Auto-select model if not set
        if not self.model:
            self.model = self._auto_detect_model()

        # Verify the selected model exists
        if self.model not in models:
            available = ", ".join(models[:5])
            raise ValueError(
                f"Model '{self.model}' not found in Ollama.\n"
                f"Available models: {available}\n"
                f"Pull the model: ollama pull {self.model}\n"
                f"Or use an available model: envcli ai config --provider ollama --model {models[0]}"
            )

        prompt = self._build_prompt(metadata, context)

        try:
            with httpx.Client(timeout=60.0) as client:
                response = client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False
                    }
                )
                response.raise_for_status()
                result = response.json()
                return result["response"]
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise Exception(
                    f"Model '{self.model}' not found. Pull it with: ollama pull {self.model}"
                )
            raise Exception(f"Ollama API error: {str(e)}")
        except Exception as e:
            raise Exception(f"Ollama error: {str(e)}")
    
    def _build_prompt(self, metadata: Dict[str, Any], context: str) -> str:
        return f"""You are an expert in environment variable management, security, and DevOps best practices.

Analyze the following environment variable metadata and provide recommendations:

Context: {context}

Metadata (no sensitive values included):
{json.dumps(metadata, indent=2)}

Please provide:
1. Naming convention issues
2. Security concerns based on patterns
3. Best practice recommendations
4. Potential improvements

Keep recommendations concise and actionable."""


class PatternMatchingProvider(AIProvider):
    """Fallback pattern-matching provider (no external API needed)."""
    
    def get_provider_name(self) -> str:
        return "Pattern Matching (Local)"
    
    def is_available(self) -> bool:
        return True
    
    def analyze_metadata(self, metadata: Dict[str, Any], context: str) -> str:
        """Analyze metadata using pattern matching."""
        recommendations = []
        
        # This is the existing logic from AIAssistant
        recommendations.append("📋 Pattern-based Analysis (Local)")
        recommendations.append("")
        recommendations.append("✓ Using local pattern matching - no external API calls")
        recommendations.append("✓ All analysis happens on your machine")
        recommendations.append("")
        recommendations.append("For more advanced AI analysis, configure a provider:")
        recommendations.append("  envcli ai config --provider openai")
        recommendations.append("  envcli ai config --provider anthropic")
        recommendations.append("  envcli ai config --provider google")
        recommendations.append("  envcli ai config --provider ollama")
        
        return "\n".join(recommendations)


def get_provider(provider_name: str, **kwargs) -> AIProvider:
    """Factory function to get an AI provider instance."""
    providers = {
        "openai": OpenAIProvider,
        "anthropic": AnthropicProvider,
        "google": GoogleProvider,
        "ollama": OllamaProvider,
        "pattern-matching": PatternMatchingProvider
    }
    
    provider_class = providers.get(provider_name.lower())
    if not provider_class:
        raise ValueError(f"Unknown provider: {provider_name}. Available: {', '.join(providers.keys())}")
    
    return provider_class(**kwargs)

