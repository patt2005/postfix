#!/usr/bin/env python3
"""
Test script to verify cleanup of posting limits and creator info banner
"""

def test_posting_limit_removed():
    """Check that posting limit messages are removed"""
    print("\n1. Testing posting limit removal...")
    
    with open('templates/dashboard.html', 'r') as f:
        content = f.read()
    
    checks = []
    
    # Check for removed posting limit elements
    if "You've reached your posting limit" not in content:
        checks.append("✓ Posting limit message removed")
    else:
        checks.append("✗ Posting limit message still exists")
    
    if 'postingRestriction' not in content:
        checks.append("✓ Posting restriction div removed")
    else:
        checks.append("✗ Posting restriction div still exists")
    
    if 'handlePostingRestriction' not in content:
        checks.append("✓ handlePostingRestriction function removed")
    else:
        checks.append("✗ handlePostingRestriction function still exists")
    
    if 'creator_can_post' not in content:
        checks.append("✓ creator_can_post checks removed")
    else:
        checks.append("✗ creator_can_post checks still exist")
    
    for check in checks:
        print(check)
    
    return all('✓' in check for check in checks)

def test_creator_banner_simplified():
    """Check that creator info banner is simplified"""
    print("\n2. Testing creator banner simplification...")
    
    with open('templates/dashboard.html', 'r') as f:
        content = f.read()
    
    checks = []
    
    # Check for removed follower count in banner
    if 'followerCountSmall' not in content:
        checks.append("✓ Follower count removed from banner")
    else:
        checks.append("✗ Follower count still in banner")
    
    # Check that creator info banner is removed or hidden
    banner_count = content.count('creatorInfoBanner')
    if banner_count <= 2:  # Allow for CSS references
        checks.append("✓ Creator info banner simplified/removed")
    else:
        checks.append(f"✗ Creator info banner still has {banner_count} references")
    
    for check in checks:
        print(check)
    
    return all('✓' in check for check in checks)

def test_cleaner_interface():
    """Check for cleaner interface without unnecessary elements"""
    print("\n3. Testing interface cleanup...")
    
    with open('templates/dashboard.html', 'r') as f:
        content = f.read()
    
    checks = []
    
    # Check that max duration is still available where needed
    if 'maxDurationInfo' in content or 'max_video_duration' in content:
        checks.append("✓ Max duration info still available")
    else:
        checks.append("✗ Max duration info missing")
    
    # Check that unnecessary restrictions are gone
    if 'disable_form_inputs' not in content and 'el.disabled = true' not in content.replace('creatorSettings', ''):
        checks.append("✓ Unnecessary form disabling removed")
    else:
        checks.append("⚠ Some form disabling code may remain")
    
    for check in checks:
        print(check)
    
    return all('✓' in check for check in checks)

def main():
    print("=" * 50)
    print("Testing Dashboard Cleanup")
    print("=" * 50)
    
    results = []
    
    results.append(test_posting_limit_removed())
    results.append(test_creator_banner_simplified())
    results.append(test_cleaner_interface())
    
    print("\n" + "=" * 50)
    if all(results):
        print("✓ Dashboard successfully cleaned up")
        print("✓ Posting limit messages removed")
        print("✓ Creator banner simplified")
        print("✓ Cleaner, simpler interface")
    else:
        print("⚠ Some cleanup items may need attention")
    print("=" * 50)

if __name__ == "__main__":
    main()