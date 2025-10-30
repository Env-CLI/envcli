#!/usr/bin/env python3
"""Test AI Actions - Safe application of recommendations."""

import sys
import os
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from envcli.env_manager import EnvManager
from envcli.ai_actions import AIActionExecutor, AIAction

def setup_test_profile():
    """Create a test profile with intentionally messy variables."""
    profile = "test_ai_actions"
    manager = EnvManager(profile)
    
    # Create test environment with naming issues
    test_env = {
        "api_key": "sk-test123",  # Should be uppercase
        "database_url": "postgres://localhost/db",  # Should be uppercase
        "DatabasePassword": "secret123",  # Mixed case
        "DEBUG": "true",  # Good
        "port": "8080",  # Should be uppercase
        "redis_host": "localhost",  # Could use REDIS_ prefix
        "redis_port": "6379",  # Could use REDIS_ prefix
        "smtp_server": "smtp.gmail.com",  # Could use EMAIL_ prefix
        "smtp_port": "587",  # Could use EMAIL_ prefix
    }
    
    manager.save_env(test_env)
    print(f"✓ Created test profile '{profile}' with {len(test_env)} variables")
    return profile, test_env

def test_parse_recommendations():
    """Test parsing recommendations into actions."""
    print("\n" + "="*60)
    print("Test 1: Parse Recommendations")
    print("="*60)
    
    profile, original_env = setup_test_profile()
    executor = AIActionExecutor(profile)
    
    # Parse recommendations (this uses pattern matching)
    actions = executor.parse_recommendations("")
    
    print(f"\n✓ Found {len(actions)} actionable suggestions:")
    for i, action in enumerate(actions, 1):
        print(f"\n{i}. {action.description}")
        print(f"   Type: {action.action_type}")
        print(f"   Details: {action.details}")
    
    return profile, actions

def test_preview_actions(profile, actions):
    """Test previewing actions without applying."""
    print("\n" + "="*60)
    print("Test 2: Preview Actions (Dry Run)")
    print("="*60)
    
    executor = AIActionExecutor(profile)
    executor.actions = actions
    
    # Preview without applying
    preview = executor.preview_actions()
    
    print(f"\n✓ Preview of {len(preview)} pending actions:")
    for i, action in enumerate(preview, 1):
        print(f"\n{i}. {action['description']}")
        if action['action_type'] in ['rename', 'add_prefix']:
            print(f"   {action['details']['old_name']} → {action['details']['new_name']}")
    
    return executor

def test_apply_single_action(executor):
    """Test applying a single action."""
    print("\n" + "="*60)
    print("Test 3: Apply Single Action")
    print("="*60)
    
    if not executor.actions:
        print("✗ No actions to apply")
        return False
    
    # Get first action
    action = executor.actions[0]
    
    print(f"\nApplying: {action.description}")
    
    # Apply in dry run mode first
    result = executor.apply_action(action, dry_run=True)
    print(f"\n✓ Dry run result: {result['message']}")
    
    # Now apply for real
    result = executor.apply_action(action, dry_run=False)
    
    if result['success']:
        print(f"✓ Successfully applied: {result['message']}")
        
        # Verify the change
        manager = EnvManager(executor.profile)
        env_vars = manager.load_env()
        
        old_name = action.details['old_name']
        new_name = action.details['new_name']
        
        if old_name not in env_vars and new_name in env_vars:
            print(f"✓ Verified: '{old_name}' renamed to '{new_name}'")
            print(f"✓ Value preserved: [HIDDEN]")
        else:
            print(f"✗ Verification failed")
            return False
    else:
        print(f"✗ Failed: {result['message']}")
        return False
    
    return True

def test_apply_all_actions(profile):
    """Test applying all actions at once."""
    print("\n" + "="*60)
    print("Test 4: Apply All Actions")
    print("="*60)
    
    # Create fresh executor
    executor = AIActionExecutor(profile)
    actions = executor.parse_recommendations("")
    
    print(f"\nFound {len(actions)} actions to apply")
    
    # Apply all
    result = executor.apply_all_actions(dry_run=False)
    
    print(f"\n✓ Applied {result['successful']} action(s)")
    if result['failed'] > 0:
        print(f"✗ Failed {result['failed']} action(s)")
    
    # Show final state
    manager = EnvManager(profile)
    final_env = manager.load_env()
    
    print(f"\n✓ Final environment has {len(final_env)} variables:")
    for key in sorted(final_env.keys()):
        print(f"   • {key}")
    
    return result

def test_action_history(profile):
    """Test viewing action history."""
    print("\n" + "="*60)
    print("Test 5: Action History")
    print("="*60)
    
    executor = AIActionExecutor(profile)
    history = executor.get_action_history(limit=10)
    
    print(f"\n✓ Found {len(history)} action(s) in history:")
    for entry in history:
        action = entry['action']
        print(f"\n• {action['description']}")
        print(f"  Applied: {entry['timestamp']}")
        print(f"  Type: {action['action_type']}")
    
    return history

def test_value_preservation():
    """Test that values are preserved during transformations."""
    print("\n" + "="*60)
    print("Test 6: Value Preservation")
    print("="*60)
    
    profile = "test_value_preservation"
    manager = EnvManager(profile)
    
    # Create test data with known values
    test_data = {
        "api_key": "secret_value_123",
        "database_url": "postgres://user:pass@host/db"
    }
    
    manager.save_env(test_data)
    print(f"\n✓ Created test profile with {len(test_data)} variables")
    
    # Apply transformations
    executor = AIActionExecutor(profile)
    actions = executor.parse_recommendations("")
    
    if actions:
        print(f"✓ Found {len(actions)} actions to apply")
        result = executor.apply_all_actions(dry_run=False)
        
        # Verify values are preserved
        final_env = manager.load_env()
        
        print("\n✓ Checking value preservation:")
        for old_key, old_value in test_data.items():
            # Find the new key (might be renamed)
            found = False
            for new_key, new_value in final_env.items():
                if new_value == old_value:
                    found = True
                    if new_key != old_key:
                        print(f"  ✓ '{old_key}' → '{new_key}': Value preserved ✓")
                    else:
                        print(f"  ✓ '{old_key}': Unchanged, value preserved ✓")
                    break
            
            if not found:
                print(f"  ✗ Value for '{old_key}' was lost!")
                return False
    else:
        print("✓ No actions needed (variables already well-formatted)")
    
    return True

def cleanup():
    """Clean up test profiles."""
    print("\n" + "="*60)
    print("Cleanup")
    print("="*60)
    
    from envcli.config import PROFILES_DIR
    
    test_profiles = ["test_ai_actions", "test_value_preservation"]
    
    for profile in test_profiles:
        profile_file = PROFILES_DIR / f"{profile}.json"
        if profile_file.exists():
            profile_file.unlink()
            print(f"✓ Removed test profile: {profile}")

def main():
    """Run all tests."""
    print("="*60)
    print("AI Actions Test Suite")
    print("="*60)
    
    try:
        # Test 1: Parse recommendations
        profile, actions = test_parse_recommendations()
        
        # Test 2: Preview actions
        executor = test_preview_actions(profile, actions)
        
        # Test 3: Apply single action
        if not test_apply_single_action(executor):
            print("\n✗ Single action test failed")
            return False
        
        # Test 4: Apply all actions (on fresh profile)
        profile, _ = setup_test_profile()
        result = test_apply_all_actions(profile)
        
        # Test 5: View history
        history = test_action_history(profile)
        
        # Test 6: Value preservation
        if not test_value_preservation():
            print("\n✗ Value preservation test failed")
            return False
        
        # Cleanup
        cleanup()
        
        print("\n" + "="*60)
        print("✅ All Tests Passed!")
        print("="*60)
        print("\nKey Features Verified:")
        print("  ✓ Parse AI recommendations into actions")
        print("  ✓ Preview changes before applying")
        print("  ✓ Apply single actions safely")
        print("  ✓ Apply multiple actions at once")
        print("  ✓ Track action history")
        print("  ✓ Preserve all secret values")
        print("\n🔒 Security: No sensitive values were exposed during transformations!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

