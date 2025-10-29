#!/usr/bin/env python3
"""Test Ollama auto-detection functionality."""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from envcli.ai_providers import OllamaProvider

def test_ollama_autodetect():
    """Test Ollama auto-detection."""
    print("🧪 Testing Ollama Auto-Detection\n")
    
    # Test 1: Check if Ollama is running
    print("1️⃣  Checking if Ollama is running...")
    ollama = OllamaProvider()
    
    if ollama.is_available():
        print("   ✓ Ollama is running")
    else:
        print("   ✗ Ollama is not running")
        print("   💡 Start with: ollama serve")
        return False
    
    # Test 2: Get available models
    print("\n2️⃣  Getting available models...")
    models = ollama.get_available_models()
    
    if models:
        print(f"   ✓ Found {len(models)} model(s):")
        for model in models:
            print(f"      • {model}")
    else:
        print("   ✗ No models found")
        print("   💡 Pull a model with: ollama pull llama3.2")
        return False
    
    # Test 3: Auto-detect model
    print("\n3️⃣  Testing auto-detection...")
    ollama_auto = OllamaProvider()  # No model specified
    
    if ollama_auto.model:
        print(f"   ✓ Auto-detected model: {ollama_auto.model}")
    else:
        print("   ✗ Could not auto-detect model")
        return False
    
    # Test 4: Test with specific model
    print("\n4️⃣  Testing with specific model...")
    if models:
        test_model = models[0]
        ollama_specific = OllamaProvider(model=test_model)
        print(f"   ✓ Created provider with model: {ollama_specific.model}")
        print(f"   ✓ Provider name: {ollama_specific.get_provider_name()}")
    
    # Test 5: Test with non-existent model
    print("\n5️⃣  Testing error handling...")
    ollama_bad = OllamaProvider(model="nonexistent-model-xyz")
    
    try:
        # This should fail gracefully
        metadata = {
            "variable_count": 3,
            "variable_names": ["TEST_VAR", "API_KEY", "DEBUG"]
        }
        result = ollama_bad.analyze_metadata(metadata, "test")
        print("   ✗ Should have raised an error")
        return False
    except ValueError as e:
        print(f"   ✓ Correctly raised error: {str(e)[:80]}...")
    except Exception as e:
        print(f"   ✓ Raised error: {str(e)[:80]}...")
    
    print("\n✅ All tests passed!")
    return True

if __name__ == "__main__":
    try:
        success = test_ollama_autodetect()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

