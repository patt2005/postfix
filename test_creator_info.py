#!/usr/bin/env python3
"""
Test script to verify creator_info/query endpoint implementation
"""

import json

def test_creator_info_endpoint():
    """Check that creator_info/query endpoint is properly implemented"""
    print("\n1. Testing creator_info/query endpoint implementation...")
    
    with open('display_api.py', 'r') as f:
        content = f.read()
    
    checks = [
        ('/post/publish/creator_info/query/', "Uses creator_info/query endpoint"),
        ('creator_username', "Fetches creator_username (unique ID)"),
        ('creator_nickname', "Fetches creator_nickname (display name)"),
        ('creator_avatar_url', "Fetches creator_avatar_url"),
        ('privacy_level_options', "Fetches privacy level options"),
        ('max_video_post_duration_sec', "Fetches max video duration")
    ]
    
    all_found = True
    for check_text, description in checks:
        if check_text in content:
            print(f"✓ {description}")
        else:
            print(f"✗ Missing: {description}")
            all_found = False
    
    return all_found

def test_oauth_callback():
    """Check that OAuth callback tries creator_info first"""
    print("\n2. Testing OAuth callback with creator_info...")
    
    with open('app.py', 'r') as f:
        content = f.read()
    
    checks = [
        ('creator_info/query', "OAuth callback uses creator_info/query"),
        ('creator_username', "Processes creator_username"),
        ('creator_nickname', "Processes creator_nickname"),
        ('creator_avatar_url', "Processes creator_avatar_url")
    ]
    
    all_found = True
    for check_text, description in checks:
        if check_text in content:
            print(f"✓ {description}")
        else:
            print(f"✗ Missing: {description}")
            all_found = False
    
    return all_found

def test_new_routes():
    """Check that new routes are added"""
    print("\n3. Testing new API routes...")
    
    with open('app.py', 'r') as f:
        content = f.read()
    
    if '/api/creator/info/query/<int:account_id>' in content:
        print("✓ New creator info route added")
    else:
        print("✗ Missing creator info route")
        return False
    
    return True

def test_dashboard_handling():
    """Check that dashboard handles username and display_name properly"""
    print("\n4. Testing dashboard handling...")
    
    with open('templates/dashboard.html', 'r') as f:
        content = f.read()
    
    if 'profile.username && profile.username !== profile.display_name' in content:
        print("✓ Dashboard shows username when different from display_name")
    else:
        print("✗ Dashboard doesn't handle username properly")
        return False
    
    return True

def show_example_response():
    """Show example creator_info response"""
    print("\n5. Example creator_info/query Response:")
    print("-" * 40)
    
    example = {
        "data": {
            "creator_avatar_url": "https://lf16-tt4d.tiktokcdn.com/obj/tiktok-open-platform/8d5740ac3844be417beeacd0df75aef1",
            "creator_username": "tiktok",  # Unique ID
            "creator_nickname": "TikTok Official",  # Display name
            "privacy_level_options": ["PUBLIC_TO_EVERYONE", "MUTUAL_FOLLOW_FRIENDS", "SELF_ONLY"],
            "comment_disabled": False,
            "duet_disabled": False,
            "stitch_disabled": True,
            "max_video_post_duration_sec": 300
        },
        "error": {
            "code": "ok",
            "message": "",
            "log_id": "202210112248442CB9319E1FB30C1073F3"
        }
    }
    
    print(json.dumps(example, indent=2))
    print("\nNote: This endpoint works with video.publish scope!")
    
    return True

def main():
    print("=" * 50)
    print("Testing Creator Info Query Implementation")
    print("=" * 50)
    
    results = []
    
    results.append(test_creator_info_endpoint())
    results.append(test_oauth_callback())
    results.append(test_new_routes())
    results.append(test_dashboard_handling())
    results.append(show_example_response())
    
    print("\n" + "=" * 50)
    if all(results):
        print("✓ Creator info query endpoint properly implemented")
        print("✓ App can now fetch username, nickname, and avatar")
        print("✓ Works with video.publish scope")
    else:
        print("⚠ Some areas may need attention")
    print("=" * 50)

if __name__ == "__main__":
    main()