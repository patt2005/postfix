#!/usr/bin/env python3
"""
Test script to verify TikTok account management features
"""

import os
import sys

def test_imports():
    """Test that all required modules can be imported"""
    try:
        from app import app
        from models import db, User, TikTokAccount
        from display_api import display_bp
        print("✓ All imports successful")
        return True
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False

def test_routes():
    """Test that all required routes exist"""
    from app import app
    
    required_routes = [
        '/auth/tiktok',
        '/auth/tiktok/add',
        '/auth/tiktok/callback',
        '/api/accounts/list',
        '/api/accounts/switch/<int:account_id>',
        '/api/accounts/<int:account_id>',
        '/api/user/profile/<int:account_id>',
        '/api/user/videos/<int:account_id>',
    ]
    
    with app.app_context():
        existing_routes = [str(rule) for rule in app.url_map.iter_rules()]
        
        all_found = True
        for route in required_routes:
            # Handle parameterized routes
            route_pattern = route.replace('<int:account_id>', '<account_id>')
            found = any(route_pattern in str(r) or route in str(r) for r in existing_routes)
            
            if found:
                print(f"✓ Route exists: {route}")
            else:
                print(f"✗ Route missing: {route}")
                all_found = False
    
    return all_found

def test_template_features():
    """Check if template has required features"""
    template_path = 'templates/dashboard.html'
    
    if not os.path.exists(template_path):
        print(f"✗ Template not found: {template_path}")
        return False
    
    with open(template_path, 'r') as f:
        content = f.read()
    
    required_elements = [
        'accountPicker',  # Account selection dropdown
        'removeAccountBtn',  # Remove account button
        'addAccountBtn',  # Add account button
        'accountInfo',  # Account info display
        'refreshAccountBtn',  # Refresh account button
        'displayAccountInfo',  # Display function
        '/auth/tiktok/add',  # Add account route
        '/api/accounts/',  # API endpoint for account management
        '/api/user/profile/',  # Display API endpoint
    ]
    
    all_found = True
    for element in required_elements:
        if element in content:
            print(f"✓ Template contains: {element}")
        else:
            print(f"✗ Template missing: {element}")
            all_found = False
    
    return all_found

def main():
    print("=" * 50)
    print("TikTok Account Management Feature Test")
    print("=" * 50)
    
    results = []
    
    print("\n1. Testing imports...")
    results.append(test_imports())
    
    print("\n2. Testing routes...")
    results.append(test_routes())
    
    print("\n3. Testing template features...")
    results.append(test_template_features())
    
    print("\n" + "=" * 50)
    if all(results):
        print("✓ All tests passed! Account management features are implemented.")
    else:
        print("✗ Some tests failed. Please review the implementation.")
    print("=" * 50)

if __name__ == "__main__":
    main()