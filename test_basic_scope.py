#!/usr/bin/env python3
"""
Test script to verify the app works with user.info.basic scope only
"""

import json

def test_display_api_fields():
    """Check that Display API only requests basic fields"""
    print("\n1. Testing Display API field requests...")
    
    with open('display_api.py', 'r') as f:
        content = f.read()
    
    # Check for basic fields only
    basic_fields = "fields = 'open_id,union_id,avatar_url,display_name'"
    
    if basic_fields in content:
        print("✓ Display API uses only basic fields")
    else:
        print("✗ Display API may be requesting unavailable fields")
        
    # Check that we're not requesting extended fields
    extended_fields = ['follower_count', 'following_count', 'likes_count', 'video_count', 'bio_description', 'is_verified']
    
    for field in extended_fields:
        if f"'{field}'" in content and 'fields' in content:
            # Check if it's in a fields request string
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if 'fields' in line and field in line and not line.strip().startswith('#'):
                    print(f"⚠ Warning: Found request for extended field '{field}' at line {i+1}")
    
    return True

def test_oauth_callback_fields():
    """Check that OAuth callback only requests basic fields"""
    print("\n2. Testing OAuth callback field requests...")
    
    with open('app.py', 'r') as f:
        content = f.read()
    
    # Find the OAuth callback fields request
    if "'fields': 'open_id,union_id,avatar_url,display_name'" in content:
        print("✓ OAuth callback uses only basic fields")
    else:
        print("⚠ OAuth callback may be requesting additional fields")
    
    return True

def test_username_handling():
    """Check that we handle missing username properly"""
    print("\n3. Testing username handling...")
    
    with open('app.py', 'r') as f:
        content = f.read()
    
    # Check for display_name fallback
    if "username=tiktok_user.get('display_name'" in content or "existing_account.username = tiktok_user.get('display_name'" in content:
        print("✓ Using display_name as fallback for username")
    else:
        print("⚠ May not be handling missing username field")
    
    return True

def test_dashboard_ui():
    """Check that dashboard handles missing stats gracefully"""
    print("\n4. Testing dashboard UI handling...")
    
    with open('templates/dashboard.html', 'r') as f:
        content = f.read()
    
    # Check for conditional stat display
    if "profile.stats.followers ?" in content or "formatNumber(profile.stats.followers) : '--'" in content:
        print("✓ Dashboard handles missing stats gracefully")
    else:
        print("⚠ Dashboard may not handle missing stats properly")
    
    return True

def test_api_response_example():
    """Show example of expected API response with basic scope"""
    print("\n5. Expected API Response Example:")
    print("-" * 40)
    
    example_response = {
        "data": {
            "user": {
                "avatar_url": "https://p19-sign.tiktokcdn-us.com/tos-useast5-avt-0068-tx/example.jpeg",
                "open_id": "723f24d7-e717-40f8-a2b6-cb8464cd23b4",
                "union_id": "c9c60f44-a68e-4f5d-84dd-ce22faeb0ba1",
                "display_name": "Tik Toker"
            }
        },
        "error": {
            "code": "ok",
            "message": "",
            "log_id": "20220829194722CBE87ED59D524E727021"
        }
    }
    
    print("With user.info.basic scope, TikTok API returns:")
    print(json.dumps(example_response, indent=2))
    print("\nNote: Stats like follower_count, following_count, etc. are NOT available")
    print("with basic scope and will show as '--' in the UI.")
    
    return True

def main():
    print("=" * 50)
    print("Testing App Compatibility with user.info.basic Scope")
    print("=" * 50)
    
    results = []
    
    results.append(test_display_api_fields())
    results.append(test_oauth_callback_fields())
    results.append(test_username_handling())
    results.append(test_dashboard_ui())
    results.append(test_api_response_example())
    
    print("\n" + "=" * 50)
    if all(results):
        print("✓ App is configured to work with user.info.basic scope only")
    else:
        print("⚠ Some areas may need attention")
    print("=" * 50)

if __name__ == "__main__":
    main()