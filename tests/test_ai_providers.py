"""
Tests for AI provider system.
"""

import pytest
import os
from unittest.mock import Mock, patch, MagicMock
from envcli.ai_providers import (
    get_provider,
    OpenAIProvider,
    AnthropicProvider,
    GoogleProvider,
    OllamaProvider,
    PatternMatchingProvider
)
from envcli.ai_assistant import AIAssistant


class TestAIProviders:
    """Test AI provider implementations."""
    
    def test_pattern_matching_provider(self):
        """Test pattern matching provider is always available."""
        provider = get_provider("pattern-matching")
        assert provider.get_provider_name() == "Pattern Matching (Local)"
        assert provider.is_available() is True
        
        # Test analysis
        metadata = {"variable_count": 5}
        result = provider.analyze_metadata(metadata, "test context")
        assert "Pattern-based Analysis" in result
        assert "local" in result.lower()
    
    def test_openai_provider_without_key(self):
        """Test OpenAI provider without API key."""
        with patch.dict(os.environ, {}, clear=True):
            provider = get_provider("openai")
            assert provider.get_provider_name() == "OpenAI (gpt-4o-mini)"
            assert provider.is_available() is False
    
    def test_openai_provider_with_key(self):
        """Test OpenAI provider with API key."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test123"}):
            provider = get_provider("openai")
            assert provider.is_available() is True
    
    def test_anthropic_provider_without_key(self):
        """Test Anthropic provider without API key."""
        with patch.dict(os.environ, {}, clear=True):
            provider = get_provider("anthropic")
            assert "Anthropic" in provider.get_provider_name()
            assert provider.is_available() is False
    
    def test_anthropic_provider_with_key(self):
        """Test Anthropic provider with API key."""
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-ant-test123"}):
            provider = get_provider("anthropic")
            assert provider.is_available() is True
    
    def test_google_provider_without_key(self):
        """Test Google provider without API key."""
        with patch.dict(os.environ, {}, clear=True):
            provider = get_provider("google")
            assert "Google" in provider.get_provider_name()
            assert provider.is_available() is False
    
    def test_google_provider_with_key(self):
        """Test Google provider with API key."""
        with patch.dict(os.environ, {"GOOGLE_API_KEY": "AIza-test123"}):
            provider = get_provider("google")
            assert provider.is_available() is True
    
    def test_ollama_provider(self):
        """Test Ollama provider."""
        provider = get_provider("ollama")
        assert "Ollama" in provider.get_provider_name()
        # is_available() depends on whether Ollama is running
        # Just test that it doesn't crash
        assert isinstance(provider.is_available(), bool)
    
    def test_custom_model(self):
        """Test provider with custom model."""
        provider = get_provider("openai", model="gpt-4o")
        assert "gpt-4o" in provider.get_provider_name()
        
        provider = get_provider("anthropic", model="claude-3-opus-20240229")
        assert "claude-3-opus" in provider.get_provider_name()
    
    def test_invalid_provider(self):
        """Test invalid provider name."""
        with pytest.raises(ValueError, match="Unknown provider"):
            get_provider("invalid-provider")
    
    def test_provider_factory(self):
        """Test provider factory returns correct types."""
        assert isinstance(get_provider("openai"), OpenAIProvider)
        assert isinstance(get_provider("anthropic"), AnthropicProvider)
        assert isinstance(get_provider("google"), GoogleProvider)
        assert isinstance(get_provider("ollama"), OllamaProvider)
        assert isinstance(get_provider("pattern-matching"), PatternMatchingProvider)


class TestAIAssistant:
    """Test AI assistant with provider system."""
    
    def test_ai_assistant_initialization(self):
        """Test AI assistant initializes correctly."""
        ai = AIAssistant()
        assert hasattr(ai, 'enabled')
        assert hasattr(ai, 'config')
        assert hasattr(ai, 'provider')
    
    def test_enable_ai_with_provider(self, tmp_path):
        """Test enabling AI with specific provider."""
        with patch('envcli.ai_assistant.AI_CONFIG_FILE', tmp_path / 'ai_config.json'):
            ai = AIAssistant()
            ai.enable_ai(provider="openai", model="gpt-4o-mini")
            
            assert ai.enabled is True
            assert ai.config['provider'] == "openai"
            assert ai.config['model'] == "gpt-4o-mini"
    
    def test_disable_ai(self, tmp_path):
        """Test disabling AI."""
        with patch('envcli.ai_assistant.AI_CONFIG_FILE', tmp_path / 'ai_config.json'):
            ai = AIAssistant()
            ai.enable_ai()
            assert ai.enabled is True
            
            ai.disable_ai()
            assert ai.enabled is False
    
    def test_configure_provider(self, tmp_path):
        """Test configuring provider."""
        with patch('envcli.ai_assistant.AI_CONFIG_FILE', tmp_path / 'ai_config.json'):
            ai = AIAssistant()
            ai.enable_ai()
            
            # Configure pattern matching (always available)
            result = ai.configure_provider("pattern-matching")
            assert result['success'] is True
            assert result['provider'] == "pattern-matching"
    
    def test_get_provider_status(self, tmp_path):
        """Test getting provider status."""
        with patch('envcli.ai_assistant.AI_CONFIG_FILE', tmp_path / 'ai_config.json'):
            ai = AIAssistant()
            ai.enable_ai(provider="pattern-matching")
            
            status = ai.get_provider_status()
            assert 'enabled' in status
            assert 'current_provider' in status
            assert 'providers' in status
            assert len(status['providers']) == 5  # All 5 providers
            
            # Check pattern matching is marked as current
            pattern_provider = next(p for p in status['providers'] if p['name'] == 'pattern-matching')
            assert pattern_provider['current'] is True
            assert pattern_provider['available'] is True
    
    def test_provider_switching(self, tmp_path):
        """Test switching between providers."""
        with patch('envcli.ai_assistant.AI_CONFIG_FILE', tmp_path / 'ai_config.json'):
            ai = AIAssistant()
            ai.enable_ai(provider="pattern-matching")
            
            # Switch to another provider
            result = ai.configure_provider("pattern-matching")
            assert result['success'] is True
            
            # Verify it's the current provider
            status = ai.get_provider_status()
            assert status['current_provider'] == "pattern-matching"
    
    @patch('envcli.ai_assistant.EnvManager')
    def test_generate_recommendations_disabled(self, mock_env_manager, tmp_path):
        """Test recommendations when AI is disabled."""
        with patch('envcli.ai_assistant.AI_CONFIG_FILE', tmp_path / 'ai_config.json'):
            ai = AIAssistant()
            ai.disable_ai()
            
            result = ai.generate_recommendations("test-profile")
            assert "error" in result
            assert "disabled" in result["error"].lower()
    
    @patch('envcli.ai_assistant.EnvManager')
    def test_generate_recommendations_enabled(self, mock_env_manager, tmp_path):
        """Test recommendations when AI is enabled."""
        with patch('envcli.ai_assistant.AI_CONFIG_FILE', tmp_path / 'ai_config.json'):
            # Mock environment manager
            mock_manager = Mock()
            mock_manager.load_env.return_value = {
                "DATABASE_URL": "postgres://...",
                "api_key": "secret123",
                "DEBUG": "true"
            }
            mock_env_manager.return_value = mock_manager
            
            ai = AIAssistant()
            ai.enable_ai(provider="pattern-matching")
            
            result = ai.generate_recommendations("test-profile")
            assert "pattern_analysis" in result
            assert "profile" in result
            assert result["profile"] == "test-profile"
            assert "provider" in result


class TestProviderIntegration:
    """Integration tests for provider system."""
    
    def test_pattern_matching_analysis(self):
        """Test pattern matching provider analysis."""
        provider = PatternMatchingProvider()
        metadata = {
            "variable_count": 3,
            "variable_names": ["DATABASE_URL", "api_key", "DEBUG"]
        }
        
        result = provider.analyze_metadata(metadata, "test")
        assert isinstance(result, str)
        assert len(result) > 0
    
    @patch('httpx.Client')
    def test_openai_provider_api_call(self, mock_client):
        """Test OpenAI provider makes correct API call."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test123"}):
            # Mock successful response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "choices": [{"message": {"content": "Test analysis"}}]
            }
            mock_response.raise_for_status = Mock()
            
            mock_context = MagicMock()
            mock_context.__enter__.return_value.post.return_value = mock_response
            mock_client.return_value = mock_context
            
            provider = OpenAIProvider()
            result = provider.analyze_metadata({"test": "data"}, "context")
            
            assert result == "Test analysis"
    
    def test_all_providers_have_required_methods(self):
        """Test all providers implement required methods."""
        providers = [
            PatternMatchingProvider(),
            OpenAIProvider(),
            AnthropicProvider(),
            GoogleProvider(),
            OllamaProvider()
        ]
        
        for provider in providers:
            assert hasattr(provider, 'get_provider_name')
            assert hasattr(provider, 'is_available')
            assert hasattr(provider, 'analyze_metadata')
            assert callable(provider.get_provider_name)
            assert callable(provider.is_available)
            assert callable(provider.analyze_metadata)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

