#!/usr/bin/env python3
"""
Manual test script for AI provider functionality.
Run this to verify the AI provider system works correctly.
"""

import sys
import os
sys.path.insert(0, 'src')

from envcli.ai_providers import get_provider, PatternMatchingProvider
from envcli.ai_assistant import AIAssistant


def test_provider_factory():
    """Test provider factory."""
    print("Testing provider factory...")
    
    providers = ["openai", "anthropic", "google", "ollama", "pattern-matching"]
    for name in providers:
        try:
            provider = get_provider(name)
            print(f"  ✓ {name}: {provider.get_provider_name()}")
        except Exception as e:
            print(f"  ✗ {name}: {e}")
            return False
    
    return True


def test_pattern_matching():
    """Test pattern matching provider."""
    print("\nTesting pattern matching provider...")
    
    try:
        provider = PatternMatchingProvider()
        assert provider.is_available() == True, "Pattern matching should always be available"
        print(f"  ✓ Provider available: {provider.get_provider_name()}")
        
        metadata = {"variable_count": 5, "variable_names": ["TEST"]}
        result = provider.analyze_metadata(metadata, "test")
        assert isinstance(result, str), "Result should be a string"
        assert len(result) > 0, "Result should not be empty"
        print(f"  ✓ Analysis works (returned {len(result)} chars)")
        
        return True
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


def test_provider_availability():
    """Test provider availability checks."""
    print("\nTesting provider availability...")
    
    providers = {
        "pattern-matching": True,  # Always available
        "openai": os.getenv("OPENAI_API_KEY") is not None,
        "anthropic": os.getenv("ANTHROPIC_API_KEY") is not None,
        "google": os.getenv("GOOGLE_API_KEY") is not None,
    }
    
    for name, expected in providers.items():
        try:
            provider = get_provider(name)
            available = provider.is_available()
            status = "✓" if available == expected else "✗"
            print(f"  {status} {name}: available={available} (expected={expected})")
        except Exception as e:
            print(f"  ✗ {name}: {e}")
            return False
    
    return True


def test_ai_assistant():
    """Test AI assistant integration."""
    print("\nTesting AI assistant...")
    
    try:
        ai = AIAssistant()
        print(f"  ✓ AI assistant created")
        
        # Test provider status
        status = ai.get_provider_status()
        assert 'enabled' in status, "Status should have 'enabled' field"
        assert 'providers' in status, "Status should have 'providers' field"
        assert len(status['providers']) == 5, "Should have 5 providers"
        print(f"  ✓ Provider status works ({len(status['providers'])} providers)")
        
        # Test configuration
        result = ai.configure_provider("pattern-matching")
        assert result['success'] == True, "Configuration should succeed"
        print(f"  ✓ Provider configuration works")
        
        return True
    except Exception as e:
        print(f"  ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_custom_models():
    """Test custom model configuration."""
    print("\nTesting custom models...")
    
    test_cases = [
        ("openai", "gpt-4o", "gpt-4o"),
        ("anthropic", "claude-3-opus-20240229", "claude-3-opus"),
        ("google", "gemini-1.5-pro", "gemini-1.5-pro"),
        ("ollama", "llama3.2", "llama3.2"),
    ]
    
    for provider_name, model, expected_in_name in test_cases:
        try:
            provider = get_provider(provider_name, model=model)
            name = provider.get_provider_name()
            assert expected_in_name in name, f"Model {expected_in_name} should be in provider name"
            print(f"  ✓ {provider_name} with {model}: {name}")
        except Exception as e:
            print(f"  ✗ {provider_name} with {model}: {e}")
            return False
    
    return True


def main():
    """Run all tests."""
    print("=" * 60)
    print("AI Provider System Manual Tests")
    print("=" * 60)
    
    tests = [
        ("Provider Factory", test_provider_factory),
        ("Pattern Matching", test_pattern_matching),
        ("Provider Availability", test_provider_availability),
        ("AI Assistant", test_ai_assistant),
        ("Custom Models", test_custom_models),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ {name} failed with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    print("\n" + "=" * 60)
    print("Test Results")
    print("=" * 60)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")
    
    all_passed = all(result for _, result in results)
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ All tests passed!")
    else:
        print("✗ Some tests failed")
    print("=" * 60)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())

