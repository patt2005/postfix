#!/usr/bin/env python3
"""
Test script to verify the app shows only display names without @ symbols
"""

def test_no_at_symbols():
    """Check that @ symbols are removed from display"""
    print("\n1. Testing for @ symbols in templates...")
    
    with open('templates/dashboard.html', 'r') as f:
        content = f.read()
    
    issues = []
    
    # Check for @ in account displays
    if '@{{ account.username }}' in content:
        issues.append("Found @{{ account.username }} in template")
    
    if '@${currentAccount.username}' in content:
        issues.append("Found @${currentAccount.username} in JavaScript")
        
    if '`@${' in content and 'username' in content:
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if '`@${' in line and 'username' in line and 'showStatus' not in line:
                # Allow status messages but not display elements
                if 'getElementById' in line or 'textContent' in line:
                    issues.append(f"Found @ symbol at line {i+1}")
    
    if not issues:
        print("✓ No @ symbols found in account displays")
    else:
        for issue in issues:
            print(f"✗ {issue}")
    
    return len(issues) == 0

def test_no_tiktok_user_placeholder():
    """Check that 'TikTok User' placeholder is removed"""
    print("\n2. Testing for 'TikTok User' placeholder...")
    
    with open('app.py', 'r') as f:
        content = f.read()
    
    issues = []
    
    if "'TikTok User'" in content:
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if "'TikTok User'" in line and not line.strip().startswith('#'):
                issues.append(f"Found 'TikTok User' at line {i+1}")
    
    if not issues:
        print("✓ No 'TikTok User' placeholder found")
    else:
        for issue in issues:
            print(f"✗ {issue}")
    
    return len(issues) == 0

def test_display_name_usage():
    """Check that display_name is properly used"""
    print("\n3. Testing display_name usage...")
    
    with open('templates/dashboard.html', 'r') as f:
        content = f.read()
    
    checks = [
        ("account.display_name or account.username", "Using display_name fallback in dropdown"),
        ("profile.display_name || profile.username", "Using display_name fallback in profile"),
        ("currentAccount.display_name || currentAccount.username", "Using display_name fallback in JavaScript")
    ]
    
    all_found = True
    for check_text, description in checks:
        if check_text in content:
            print(f"✓ {description}")
        else:
            print(f"✗ Missing: {description}")
            all_found = False
    
    return all_found

def test_oauth_handling():
    """Check OAuth callback handles display_name correctly"""
    print("\n4. Testing OAuth callback...")
    
    with open('app.py', 'r') as f:
        content = f.read()
    
    checks = [
        ("display_name = tiktok_user.get('display_name'", "Gets display_name from API"),
        ("username=display_name", "Uses display_name as username"),
        ("'fields': 'open_id,union_id,avatar_url,display_name'", "Only requests basic fields")
    ]
    
    all_found = True
    for check_text, description in checks:
        if check_text in content:
            print(f"✓ {description}")
        else:
            print(f"✗ Missing: {description}")
            all_found = False
    
    return all_found

def main():
    print("=" * 50)
    print("Testing Display Name Only Implementation")
    print("=" * 50)
    
    results = []
    
    results.append(test_no_at_symbols())
    results.append(test_no_tiktok_user_placeholder())
    results.append(test_display_name_usage())
    results.append(test_oauth_handling())
    
    print("\n" + "=" * 50)
    if all(results):
        print("✓ App correctly shows only display names without @ symbols")
        print("✓ No 'TikTok User' placeholders")
        print("✓ Clean, simple display of account names")
    else:
        print("⚠ Some areas may need attention")
    print("=" * 50)

if __name__ == "__main__":
    main()