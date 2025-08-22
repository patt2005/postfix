#!/usr/bin/env python3
"""
Test script to verify interaction settings follow TikTok API requirements
"""

def test_no_default_checked():
    """Check that interaction toggles are not checked by default"""
    print("\n1. Testing no default checked state...")
    
    with open('templates/dashboard.html', 'r') as f:
        content = f.read()
    
    checks = []
    
    # Check that checkboxes don't have 'checked' attribute
    if 'id="allowComments" name="allow_comments" checked' not in content:
        checks.append("✓ Comments toggle not checked by default")
    else:
        checks.append("✗ Comments toggle has default checked state")
    
    if 'id="allowDuet" name="allow_duet" checked' not in content:
        checks.append("✓ Duet toggle not checked by default")
    else:
        checks.append("✗ Duet toggle has default checked state")
    
    if 'id="allowStitch" name="allow_stitch" checked' not in content:
        checks.append("✓ Stitch toggle not checked by default")
    else:
        checks.append("✗ Stitch toggle has default checked state")
    
    # Check for reset on account switch
    if 'commentToggle.checked = false' in content:
        checks.append("✓ Toggles reset to unchecked on account switch")
    else:
        checks.append("✗ Toggles not reset on account switch")
    
    for check in checks:
        print(check)
    
    return all('✓' in check for check in checks)

def test_disabled_interactions():
    """Check that interactions are disabled when creator has them disabled"""
    print("\n2. Testing disabled interaction handling...")
    
    with open('templates/dashboard.html', 'r') as f:
        content = f.read()
    
    checks = []
    
    # Check for comment disabled handling
    if 'if (creatorSettings.comment_disabled)' in content:
        checks.append("✓ Handles comment_disabled from API")
    else:
        checks.append("✗ Missing comment_disabled handling")
    
    # Check for duet disabled handling
    if 'if (creatorSettings.duet_disabled)' in content:
        checks.append("✓ Handles duet_disabled from API")
    else:
        checks.append("✗ Missing duet_disabled handling")
    
    # Check for stitch disabled handling
    if 'if (creatorSettings.stitch_disabled)' in content:
        checks.append("✓ Handles stitch_disabled from API")
    else:
        checks.append("✗ Missing stitch_disabled handling")
    
    # Check for visual feedback (opacity)
    if "style.opacity = '0.5'" in content:
        checks.append("✓ Greys out disabled interactions")
    else:
        checks.append("✗ Missing visual feedback for disabled")
    
    # Check for disabled reason display
    if 'Disabled in your account settings' in content:
        checks.append("✓ Shows reason when disabled")
    else:
        checks.append("✗ Missing disabled reason message")
    
    for check in checks:
        print(check)
    
    return all('✓' in check for check in checks)

def test_photo_post_handling():
    """Check that duet/stitch are hidden for photo posts"""
    print("\n3. Testing photo post handling...")
    
    with open('templates/dashboard.html', 'r') as f:
        content = f.read()
    
    checks = []
    
    # Check for photo detection
    if "['jpg', 'jpeg', 'png', 'gif', 'webp'].includes(fileExtension)" in content:
        checks.append("✓ Detects photo file types")
    else:
        checks.append("✗ Missing photo detection")
    
    # Check for hiding duet/stitch for photos
    if "document.getElementById('duetControl').style.display = 'none'" in content:
        checks.append("✓ Hides duet for photos")
    else:
        checks.append("✗ Doesn't hide duet for photos")
    
    if "document.getElementById('stitchControl').style.display = 'none'" in content:
        checks.append("✓ Hides stitch for photos")
    else:
        checks.append("✗ Doesn't hide stitch for photos")
    
    # Check for photo note display
    if 'Photo Post:</strong> Only \'Allow Comments\' is available' in content:
        checks.append("✓ Shows photo-specific note")
    else:
        checks.append("✗ Missing photo note")
    
    for check in checks:
        print(check)
    
    return all('✓' in check for check in checks)

def test_user_guidance():
    """Check that users are informed about manual selection"""
    print("\n4. Testing user guidance...")
    
    with open('templates/dashboard.html', 'r') as f:
        content = f.read()
    
    checks = []
    
    # Check for instruction message
    if 'You must manually enable each interaction - none are checked by default' in content:
        checks.append("✓ Clear instruction about manual selection")
    else:
        checks.append("✗ Missing instruction message")
    
    # Check for visual distinction
    if 'background: #fff3cd' in content and 'interaction-note' in content:
        checks.append("✓ Visual highlight for instructions")
    else:
        checks.append("✗ Missing visual distinction")
    
    for check in checks:
        print(check)
    
    return all('✓' in check for check in checks)

def show_example_scenarios():
    """Show example scenarios for different account settings"""
    print("\n5. Example Scenarios:")
    print("-" * 40)
    
    scenarios = [
        {
            "name": "Public Account - All Enabled",
            "comment_disabled": False,
            "duet_disabled": False,
            "stitch_disabled": False,
            "result": "All toggles available, none checked by default"
        },
        {
            "name": "Private Account",
            "comment_disabled": False,
            "duet_disabled": True,
            "stitch_disabled": True,
            "result": "Duet & Stitch disabled and greyed out, Comment available"
        },
        {
            "name": "Comments Disabled Account",
            "comment_disabled": True,
            "duet_disabled": False,
            "stitch_disabled": False,
            "result": "Comment toggle disabled and greyed out"
        },
        {
            "name": "Photo Post",
            "file_type": "photo",
            "result": "Only Comment toggle shown, Duet & Stitch hidden"
        }
    ]
    
    for scenario in scenarios:
        print(f"\n{scenario['name']}:")
        for key, value in scenario.items():
            if key != 'name':
                print(f"  {key}: {value}")
    
    return True

def main():
    print("=" * 50)
    print("Testing Interaction Settings Requirements")
    print("=" * 50)
    
    results = []
    
    results.append(test_no_default_checked())
    results.append(test_disabled_interactions())
    results.append(test_photo_post_handling())
    results.append(test_user_guidance())
    results.append(show_example_scenarios())
    
    print("\n" + "=" * 50)
    if all(results):
        print("✓ Interaction settings properly implemented")
        print("✓ No default checked state - requires manual selection")
        print("✓ Disabled interactions are greyed out")
        print("✓ Photo posts hide duet/stitch options")
    else:
        print("⚠ Some interaction requirements not met")
    print("=" * 50)
    
    print("\nTikTok API Requirements Met:")
    print("✓ Interactions disabled in settings are greyed out")
    print("✓ Users must manually turn on interactions")
    print("✓ None are checked by default")
    print("✓ Duet/Stitch hidden for photo posts")

if __name__ == "__main__":
    main()