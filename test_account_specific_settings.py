#!/usr/bin/env python3
"""
Test script to verify account-specific settings from creator_info API
"""

import json

def test_account_specific_storage():
    """Check that dashboard stores account-specific settings"""
    print("\n1. Testing account-specific settings storage...")
    
    with open('templates/dashboard.html', 'r') as f:
        content = f.read()
    
    checks = [
        ('accountCreatorInfo[accountId]', "Stores settings per account"),
        ('max_video_duration:', "Stores max video duration"),
        ('privacy_level_options:', "Stores privacy options"),
        ('comment_disabled:', "Stores comment settings"),
        ('duet_disabled:', "Stores duet settings"),
        ('stitch_disabled:', "Stores stitch settings")
    ]
    
    all_found = True
    for check_text, description in checks:
        if check_text in content:
            print(f"✓ {description}")
        else:
            print(f"✗ Missing: {description}")
            all_found = False
    
    return all_found

def test_privacy_options_handling():
    """Check that privacy options are account-specific"""
    print("\n2. Testing privacy options handling...")
    
    with open('templates/dashboard.html', 'r') as f:
        content = f.read()
    
    checks = [
        ('updatePrivacyOptionsForAccount', "Has account-specific privacy function"),
        ('privacy_level_options ||', "Uses account privacy options"),
        ('FOLLOWER_OF_CREATOR', "Handles private account option"),
        ('privacyLabels', "Maps privacy values to labels")
    ]
    
    all_found = True
    for check_text, description in checks:
        if check_text in content:
            print(f"✓ {description}")
        else:
            print(f"✗ Missing: {description}")
            all_found = False
    
    return all_found

def test_max_duration_validation():
    """Check that max duration is account-specific"""
    print("\n3. Testing max duration validation...")
    
    with open('templates/dashboard.html', 'r') as f:
        content = f.read()
    
    checks = [
        ('accountCreatorInfo[accountId]?.max_video_duration', "Uses account-specific max duration"),
        ('exceeds maximum allowed duration of ${maxDuration} seconds for this account', "Shows account-specific error"),
        ('Maximum duration allowed for this account', "Alert mentions account-specific limit")
    ]
    
    all_found = True
    for check_text, description in checks:
        if check_text in content:
            print(f"✓ {description}")
        else:
            print(f"✗ Missing: {description}")
            all_found = False
    
    return all_found

def test_interaction_settings():
    """Check that interaction settings are account-specific"""
    print("\n4. Testing interaction settings...")
    
    with open('templates/dashboard.html', 'r') as f:
        content = f.read()
    
    checks = [
        ('updateInteractionSettingsForAccount', "Has account-specific interaction function"),
        ('creatorSettings.comment_disabled', "Checks comment restrictions"),
        ('creatorSettings.duet_disabled', "Checks duet restrictions"),
        ('creatorSettings.stitch_disabled', "Checks stitch restrictions")
    ]
    
    all_found = True
    for check_text, description in checks:
        if check_text in content:
            print(f"✓ {description}")
        else:
            print(f"✗ Missing: {description}")
            all_found = False
    
    return all_found

def show_example_usage():
    """Show example of account-specific settings"""
    print("\n5. Example Account-Specific Settings:")
    print("-" * 40)
    
    example = {
        "Account 1 (Public)": {
            "max_video_duration": 300,
            "privacy_level_options": ["PUBLIC_TO_EVERYONE", "MUTUAL_FOLLOW_FRIENDS", "SELF_ONLY"],
            "comment_disabled": False,
            "duet_disabled": False,
            "stitch_disabled": False
        },
        "Account 2 (Private)": {
            "max_video_duration": 60,
            "privacy_level_options": ["FOLLOWER_OF_CREATOR", "MUTUAL_FOLLOW_FRIENDS", "SELF_ONLY"],
            "comment_disabled": False,
            "duet_disabled": True,  # Private accounts can't be dueted
            "stitch_disabled": True   # Private accounts can't be stitched
        }
    }
    
    print(json.dumps(example, indent=2))
    print("\nEach account has its own settings based on creator_info API response!")
    
    return True

def main():
    print("=" * 50)
    print("Testing Account-Specific Settings Implementation")
    print("=" * 50)
    
    results = []
    
    results.append(test_account_specific_storage())
    results.append(test_privacy_options_handling())
    results.append(test_max_duration_validation())
    results.append(test_interaction_settings())
    results.append(show_example_usage())
    
    print("\n" + "=" * 50)
    if all(results):
        print("✓ Account-specific settings properly implemented")
        print("✓ Each account has its own max duration and privacy options")
        print("✓ Form validation uses account-specific limits")
    else:
        print("⚠ Some areas may need attention")
    print("=" * 50)

if __name__ == "__main__":
    main()