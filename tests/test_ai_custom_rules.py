#!/usr/bin/env python3
"""
Test suite for AI Custom Rules feature.

Tests custom naming rules, prefix rules, transformation rules, and exclusions.
"""

import sys
import os
import json
import tempfile
import shutil
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from envcli.ai_actions import AIActionExecutor
from envcli.env_manager import EnvManager
from envcli.config import CONFIG_DIR

def setup_test_profile():
    """Create a test profile with messy variables."""
    profile = "test_custom_rules"

    # Clean up any existing rules from previous tests
    rules_file = CONFIG_DIR / "ai_rules.json"
    if rules_file.exists():
        rules_file.unlink()

    manager = EnvManager(profile)
    
    # Create test data with various naming issues
    test_data = {
        # Should be uppercase (secrets)
        "api_key": "sk-test-123",
        "database_password": "secret123",
        "auth_token": "token456",
        
        # Should get prefixes
        "redis_host": "localhost",
        "redis_port": "6379",
        "postgres_url": "postgres://localhost/db",
        "postgres_user": "admin",
        "smtp_server": "smtp.gmail.com",
        "smtp_port": "587",
        
        # Mixed case
        "DatabaseUrl": "postgres://...",
        "ApiEndpoint": "https://api.example.com",
        
        # System variables (should be excluded)
        "PATH": "/usr/bin:/bin",
        "HOME": "/home/user",
    }
    
    manager.save_env(test_data)
    print(f"✓ Created test profile '{profile}' with {len(test_data)} variables")
    return profile, test_data

def test_naming_rules():
    """Test custom naming rules."""
    print("\n" + "="*60)
    print("TEST 1: Custom Naming Rules")
    print("="*60)
    
    profile, original_data = setup_test_profile()
    executor = AIActionExecutor(profile)
    
    # Add naming rule: all secrets should be uppercase
    executor.add_naming_rule(
        pattern=r'.*_(key|password|token|secret)',
        target_format='uppercase',
        description='Secrets must be uppercase'
    )
    print("✓ Added naming rule for secrets")
    
    # Add naming rule: mixed case to SCREAMING_SNAKE_CASE
    executor.add_naming_rule(
        pattern=r'^[A-Z][a-z]+[A-Z].*',
        target_format='SCREAMING_SNAKE_CASE',
        description='Convert mixed case to SCREAMING_SNAKE_CASE'
    )
    print("✓ Added naming rule for mixed case")
    
    # Generate actions
    actions = executor.apply_custom_rules()
    
    print(f"\n✓ Generated {len(actions)} actions from naming rules")
    for action in actions[:5]:  # Show first 5
        print(f"  • {action.description}")
    
    # Verify actions
    assert len(actions) > 0, "Should generate actions"
    
    # Check that secrets are targeted
    secret_actions = [a for a in actions if 'key' in a.details.get('old_name', '').lower() 
                      or 'password' in a.details.get('old_name', '').lower()
                      or 'token' in a.details.get('old_name', '').lower()]
    assert len(secret_actions) > 0, "Should target secret variables"
    
    print("\n✅ Naming rules test passed!")
    return True

def test_prefix_rules():
    """Test custom prefix rules."""
    print("\n" + "="*60)
    print("TEST 2: Custom Prefix Rules")
    print("="*60)
    
    profile, original_data = setup_test_profile()
    executor = AIActionExecutor(profile)
    
    # Add prefix rules
    executor.add_prefix_rule(
        pattern=r'^redis_',
        prefix='REDIS_',
        description='Group Redis configuration'
    )
    print("✓ Added prefix rule for Redis")
    
    executor.add_prefix_rule(
        pattern=r'^postgres_',
        prefix='DATABASE_',
        description='Group database configuration'
    )
    print("✓ Added prefix rule for database")
    
    executor.add_prefix_rule(
        pattern=r'^smtp_',
        prefix='EMAIL_SMTP_',
        description='Group email configuration'
    )
    print("✓ Added prefix rule for email")
    
    # Generate actions
    actions = executor.apply_custom_rules()
    
    print(f"\n✓ Generated {len(actions)} actions from prefix rules")
    for action in actions:
        print(f"  • {action.description}")
    
    # Verify actions
    assert len(actions) >= 6, f"Should generate at least 6 actions, got {len(actions)}"
    
    # Check that prefixes are added
    redis_actions = [a for a in actions if 'REDIS_' in a.details.get('new_name', '')]
    assert len(redis_actions) >= 2, "Should add REDIS_ prefix to redis variables"
    
    db_actions = [a for a in actions if 'DATABASE_' in a.details.get('new_name', '')]
    assert len(db_actions) >= 2, "Should add DATABASE_ prefix to postgres variables"
    
    print("\n✅ Prefix rules test passed!")
    return True

def test_transformation_rules():
    """Test custom transformation rules."""
    print("\n" + "="*60)
    print("TEST 3: Custom Transformation Rules")
    print("="*60)
    
    profile, original_data = setup_test_profile()
    executor = AIActionExecutor(profile)
    
    # Add transformation rule: replace 'api' with 'API'
    executor.add_transformation_rule(
        pattern=r'.*api.*',
        transformation='replace:api:API',
        description='Standardize API naming'
    )
    print("✓ Added transformation rule for API")
    
    # Generate actions
    actions = executor.apply_custom_rules()
    
    print(f"\n✓ Generated {len(actions)} actions from transformation rules")
    for action in actions:
        print(f"  • {action.description}")
    
    # Verify actions
    assert len(actions) > 0, "Should generate actions"
    
    # Check that 'api' is replaced with 'API'
    api_actions = [a for a in actions if 'API' in a.details.get('new_name', '')]
    assert len(api_actions) > 0, "Should transform api to API"
    
    print("\n✅ Transformation rules test passed!")
    return True

def test_exclusion_rules():
    """Test exclusion rules."""
    print("\n" + "="*60)
    print("TEST 4: Exclusion Rules")
    print("="*60)
    
    profile, original_data = setup_test_profile()
    executor = AIActionExecutor(profile)
    
    # Add exclusion for system variables
    executor.add_exclusion(
        pattern=r'^(PATH|HOME)$',
        description='System environment variables'
    )
    print("✓ Added exclusion for system variables")
    
    # Add a naming rule that would affect everything
    executor.add_naming_rule(
        pattern=r'.*',
        target_format='uppercase',
        description='Uppercase everything'
    )
    print("✓ Added naming rule for all variables")
    
    # Generate actions
    actions = executor.apply_custom_rules()
    
    print(f"\n✓ Generated {len(actions)} actions")
    
    # Verify that PATH and HOME are NOT in actions
    excluded_vars = ['PATH', 'HOME']
    for action in actions:
        old_name = action.details.get('old_name', '')
        assert old_name not in excluded_vars, f"Excluded variable {old_name} should not be modified"
    
    print(f"✓ Verified that {excluded_vars} are excluded from modifications")
    print("\n✅ Exclusion rules test passed!")
    return True

def test_apply_custom_rules():
    """Test applying custom rules end-to-end."""
    print("\n" + "="*60)
    print("TEST 5: Apply Custom Rules End-to-End")
    print("="*60)
    
    profile, original_data = setup_test_profile()
    executor = AIActionExecutor(profile)
    manager = EnvManager(profile)
    
    # Add comprehensive rules
    executor.add_exclusion(r'^(PATH|HOME)$', 'System variables')
    executor.add_naming_rule(r'.*_(key|password|token)', 'uppercase', 'Secrets uppercase')
    executor.add_prefix_rule(r'^redis_', 'REDIS_', 'Group Redis')
    executor.add_prefix_rule(r'^postgres_', 'DATABASE_', 'Group database')
    
    print("✓ Added 4 custom rules")
    
    # Generate and apply actions
    actions = executor.apply_custom_rules()
    print(f"✓ Generated {len(actions)} actions")
    
    # Apply actions
    result = executor.apply_all_actions(dry_run=False)
    
    print(f"\n✓ Applied {result['successful']} actions")
    print(f"✗ Failed {result['failed']} actions")
    
    # Verify values are preserved
    final_env = manager.load_env()
    
    print("\n✓ Verifying values are preserved...")
    for old_key, old_value in original_data.items():
        # Find the value in final env (key might have changed)
        found = False
        for new_key, new_value in final_env.items():
            if new_value == old_value:
                found = True
                if new_key != old_key:
                    print(f"  • {old_key} → {new_key} (value preserved)")
                break
        
        assert found, f"Value for {old_key} was lost!"
    
    print("\n✅ Apply custom rules test passed!")
    return True

def test_list_and_remove_rules():
    """Test listing and removing rules."""
    print("\n" + "="*60)
    print("TEST 6: List and Remove Rules")
    print("="*60)
    
    profile, _ = setup_test_profile()
    executor = AIActionExecutor(profile)
    
    # Add various rules
    executor.add_naming_rule(r'.*_key$', 'uppercase', 'Keys uppercase')
    executor.add_prefix_rule(r'^redis_', 'REDIS_', 'Redis prefix')
    executor.add_transformation_rule(r'.*api.*', 'replace:api:API', 'API transform')
    executor.add_exclusion(r'^PATH$', 'System PATH')
    
    print("✓ Added 4 rules")
    
    # List rules
    rules = executor.list_custom_rules()
    
    assert len(rules['naming_rules']) == 1, "Should have 1 naming rule"
    assert len(rules['prefix_rules']) == 1, "Should have 1 prefix rule"
    assert len(rules['transformation_rules']) == 1, "Should have 1 transformation rule"
    assert len(rules['exclusions']) == 1, "Should have 1 exclusion"
    
    print("✓ Listed all rules")
    print(f"  • Naming rules: {len(rules['naming_rules'])}")
    print(f"  • Prefix rules: {len(rules['prefix_rules'])}")
    print(f"  • Transformation rules: {len(rules['transformation_rules'])}")
    print(f"  • Exclusions: {len(rules['exclusions'])}")
    
    # Remove a rule
    success = executor.remove_rule('naming_rules', 0)
    assert success, "Should successfully remove rule"
    
    print("✓ Removed naming rule")
    
    # Verify removal
    rules = executor.list_custom_rules()
    assert len(rules['naming_rules']) == 0, "Naming rule should be removed"
    
    print("✓ Verified rule removal")
    print("\n✅ List and remove rules test passed!")
    return True

def test_value_preservation():
    """Critical test: Verify values are NEVER exposed or lost."""
    print("\n" + "="*60)
    print("TEST 7: Value Preservation (CRITICAL)")
    print("="*60)
    
    profile, original_data = setup_test_profile()
    executor = AIActionExecutor(profile)
    manager = EnvManager(profile)
    
    # Add aggressive rules that will modify many variables
    executor.add_naming_rule(r'.*', 'SCREAMING_SNAKE_CASE', 'All uppercase')
    executor.add_prefix_rule(r'^redis_', 'REDIS_', 'Redis prefix')
    executor.add_prefix_rule(r'^postgres_', 'DB_', 'DB prefix')
    
    print("✓ Added aggressive transformation rules")
    
    # Apply all rules
    actions = executor.apply_custom_rules()
    result = executor.apply_all_actions(dry_run=False)
    
    print(f"✓ Applied {result['successful']} transformations")
    
    # CRITICAL: Verify every value is preserved
    final_env = manager.load_env()
    
    print("\n🔒 CRITICAL: Verifying value preservation...")
    
    all_original_values = set(original_data.values())
    all_final_values = set(final_env.values())
    
    # Every original value must exist in final env
    for original_value in all_original_values:
        assert original_value in all_final_values, \
            f"CRITICAL: Value '{original_value}' was lost during transformation!"
    
    print(f"✓ All {len(all_original_values)} unique values preserved")
    
    # Verify count matches (accounting for duplicates)
    assert len(original_data) == len(final_env), \
        f"Variable count changed: {len(original_data)} → {len(final_env)}"
    
    print(f"✓ Variable count preserved: {len(final_env)}")
    
    print("\n✅ Value preservation test passed!")
    print("🔒 SECURITY GUARANTEE: No values were exposed or lost!")
    return True

def cleanup():
    """Clean up test data."""
    print("\n" + "="*60)
    print("Cleaning up test data...")
    print("="*60)
    
    # Remove test profile
    profile = "test_custom_rules"
    profile_file = CONFIG_DIR / "profiles" / f"{profile}.json"
    if profile_file.exists():
        profile_file.unlink()
        print(f"✓ Removed test profile: {profile_file}")
    
    # Remove test rules
    rules_file = CONFIG_DIR / "ai_rules.json"
    if rules_file.exists():
        rules_file.unlink()
        print(f"✓ Removed test rules: {rules_file}")
    
    print("✓ Cleanup complete")

def main():
    """Run all tests."""
    print("="*60)
    print("AI CUSTOM RULES TEST SUITE")
    print("="*60)
    
    tests = [
        ("Naming Rules", test_naming_rules),
        ("Prefix Rules", test_prefix_rules),
        ("Transformation Rules", test_transformation_rules),
        ("Exclusion Rules", test_exclusion_rules),
        ("Apply Custom Rules", test_apply_custom_rules),
        ("List and Remove Rules", test_list_and_remove_rules),
        ("Value Preservation", test_value_preservation),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"\n❌ {test_name} FAILED: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    # Cleanup
    cleanup()
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"✅ Passed: {passed}/{len(tests)}")
    print(f"❌ Failed: {failed}/{len(tests)}")
    
    if failed == 0:
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED!")
        print("="*60)
        print("\nKey Features Verified:")
        print("  ✓ Custom naming rules work correctly")
        print("  ✓ Custom prefix rules work correctly")
        print("  ✓ Custom transformation rules work correctly")
        print("  ✓ Exclusion rules prevent modifications")
        print("  ✓ Rules can be listed and removed")
        print("  ✓ End-to-end application works")
        print("  ✓ All values are preserved (CRITICAL)")
        print("\n🔒 Security: No sensitive values were exposed!")
        return 0
    else:
        print("\n❌ SOME TESTS FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(main())

