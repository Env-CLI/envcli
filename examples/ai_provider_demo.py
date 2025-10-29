#!/usr/bin/env python3
"""
Demo script showing how to use different AI providers with EnvCLI.
"""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from envcli.ai_assistant import AIAssistant
from envcli.ai_providers import get_provider


def demo_provider_status():
    """Show current provider status."""
    print("=" * 60)
    print("AI Provider Status Demo")
    print("=" * 60)
    
    ai = AIAssistant()
    status = ai.get_provider_status()
    
    print(f"\n✓ AI Enabled: {status['enabled']}")
    print(f"✓ Current Provider: {status['current_provider']}")
    if status['current_model']:
        print(f"✓ Current Model: {status['current_model']}")
    
    print("\nAvailable Providers:")
    for provider in status['providers']:
        icon = "✓" if provider['available'] else "✗"
        current = " (CURRENT)" if provider['current'] else ""
        print(f"  {icon} {provider['name']}: {provider['display_name']}{current}")


def demo_provider_switching():
    """Demo switching between providers."""
    print("\n" + "=" * 60)
    print("Provider Switching Demo")
    print("=" * 60)
    
    ai = AIAssistant()
    
    # Try pattern matching (always available)
    print("\n1. Configuring Pattern Matching provider...")
    result = ai.configure_provider("pattern-matching")
    print(f"   Result: {result['message']}")
    print(f"   Provider: {result['provider_name']}")
    
    # Try OpenAI (if API key is set)
    if os.getenv("OPENAI_API_KEY"):
        print("\n2. Configuring OpenAI provider...")
        result = ai.configure_provider("openai", model="gpt-4o-mini")
        print(f"   Result: {result['message']}")
        print(f"   Provider: {result['provider_name']}")
    else:
        print("\n2. OpenAI provider not available (OPENAI_API_KEY not set)")
    
    # Try Anthropic (if API key is set)
    if os.getenv("ANTHROPIC_API_KEY"):
        print("\n3. Configuring Anthropic provider...")
        result = ai.configure_provider("anthropic")
        print(f"   Result: {result['message']}")
        print(f"   Provider: {result['provider_name']}")
    else:
        print("\n3. Anthropic provider not available (ANTHROPIC_API_KEY not set)")
    
    # Try Google (if API key is set)
    if os.getenv("GOOGLE_API_KEY"):
        print("\n4. Configuring Google provider...")
        result = ai.configure_provider("google")
        print(f"   Result: {result['message']}")
        print(f"   Provider: {result['provider_name']}")
    else:
        print("\n4. Google provider not available (GOOGLE_API_KEY not set)")


def demo_provider_analysis():
    """Demo analysis with different providers."""
    print("\n" + "=" * 60)
    print("Provider Analysis Demo")
    print("=" * 60)
    
    # Create sample metadata
    metadata = {
        "variable_count": 5,
        "variable_names": ["DATABASE_URL", "api_key", "DEBUG", "secret_token", "PORT"],
        "naming_patterns": {
            "uppercase_ratio": 0.6,
            "has_secrets": True,
            "avg_length": 10.2
        },
        "prefixes": ["DATABASE", "DEBUG"]
    }
    
    context = "Sample environment with mixed naming conventions"
    
    # Test pattern matching
    print("\n1. Pattern Matching Analysis:")
    try:
        provider = get_provider("pattern-matching")
        result = provider.analyze_metadata(metadata, context)
        print(result)
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test OpenAI if available
    if os.getenv("OPENAI_API_KEY"):
        print("\n2. OpenAI Analysis:")
        try:
            provider = get_provider("openai", model="gpt-4o-mini")
            if provider.is_available():
                print("   Analyzing with OpenAI...")
                result = provider.analyze_metadata(metadata, context)
                print(f"   {result[:200]}...")  # Show first 200 chars
            else:
                print("   OpenAI not available")
        except Exception as e:
            print(f"   Error: {e}")
    
    # Test Ollama if running
    print("\n3. Ollama Analysis:")
    try:
        provider = get_provider("ollama", model="llama3.2")
        if provider.is_available():
            print("   Analyzing with Ollama (this may take a moment)...")
            result = provider.analyze_metadata(metadata, context)
            print(f"   {result[:200]}...")  # Show first 200 chars
        else:
            print("   Ollama not available (not running)")
    except Exception as e:
        print(f"   Error: {e}")


def main():
    """Run all demos."""
    print("\n🤖 EnvCLI AI Provider Demo\n")
    
    # Demo 1: Show provider status
    demo_provider_status()
    
    # Demo 2: Switch providers
    demo_provider_switching()
    
    # Demo 3: Analyze with different providers
    demo_provider_analysis()
    
    print("\n" + "=" * 60)
    print("Demo Complete!")
    print("=" * 60)
    print("\nTo use these features in EnvCLI:")
    print("  envcli ai config --show")
    print("  envcli ai config --provider openai")
    print("  envcli ai analyze --profile dev")
    print("\nFor more info, see: docs/AI_PROVIDERS.md")


if __name__ == "__main__":
    main()

