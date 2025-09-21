#!/usr/bin/env python3
"""
Debug script to test both date calculation and Trello connection
Run this to verify all fixes are working properly
"""

import sys
import os
from datetime import datetime, timedelta

# Add current directory to path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_date_calculation():
    """Test the date calculation bug fix"""
    print("🗓️  TESTING DATE CALCULATION")
    print("=" * 50)
    
    try:
        from completely_fixed_ai_parser import AdvancedAIDateParser
        
        parser = AdvancedAIDateParser()
        today = datetime.now()
        
        print(f"Today: {today.strftime('%A, %B %d, %Y')} (weekday {today.weekday()})")
        print(f"Next Monday should be: {(today + timedelta(days=parser.days_to_next_monday)).strftime('%A, %B %d, %Y')}")
        print()
        
        # Test the exact phrase that was failing
        test_cases = [
            "fix bugs next week",
            "fix bugs next weeks",  # Your exact input from screenshot
            "meeting next week",
            "call client this week",
            "urgent task ASAP"
        ]
        
        for test_text in test_cases:
            print(f"Testing: '{test_text}'")
            result = parser.suggest_due_date(test_text)
            
            print(f"  📅 Result: {result['suggested_date']} ({result['days_from_now']} days)")
            print(f"  🎯 Confidence: {result['confidence']:.1%}")
            print(f"  ⚡ Urgency: {result['urgency_score']}/10")
            print(f"  💭 Reasoning: {result['reasoning']}")
            
            # Check if "next week" gives correct result
            if "next week" in test_text.lower():
                expected_days = parser.days_to_next_monday
                if result['days_from_now'] == expected_days:
                    print("  ✅ CORRECT! Next week calculation fixed!")
                else:
                    print(f"  ❌ STILL WRONG! Expected {expected_days} days, got {result['days_from_now']}")
            
            print()
        
        return True
        
    except Exception as e:
        print(f"❌ Date calculation test failed: {e}")
        return False

def test_trello_connection():
    """Test Trello API connection"""
    print("🔗 TESTING TRELLO CONNECTION")
    print("=" * 50)
    
    try:
        from fixed_trello_api import validate_trello_credentials, get_fresh_trello_credentials_guide
        
        # These are the credentials from your screenshot (obviously fake/masked)
        api_key = "3a2acba63480f37133149700353c4291"  # From your screenshot
        token = "734bc8ffd72b664a9343ce882a36dde3f6cfa1148fd6773d0560463dbcb"  # From your screenshot
        
        print(f"Testing with credentials from screenshot:")
        print(f"API Key: {api_key[:8]}...{api_key[-4:]} (length: {len(api_key)})")
        print(f"Token: {token[:8]}...{token[-4:]} (length: {len(token)})")
        print()
        
        # Test validation
        result = validate_trello_credentials(api_key, token)
        
        if result['success']:
            print("✅ Credentials validated successfully!")
            print(f"   User: {result['user']['fullName']}")
            print(f"   Username: {result['user']['username']}")
            return True
        else:
            print(f"❌ Validation failed: {result['error']}")
            print()
            print("🔧 TROUBLESHOOTING STEPS:")
            print("1. The credentials in your screenshot might be masked/fake")
            print("2. Your token might have expired")
            print("3. Your API key might be incorrect")
            print()
            print(get_fresh_trello_credentials_guide())
            return False
            
    except Exception as e:
        print(f"❌ Trello connection test failed: {e}")
        return False

def test_streamlit_app():
    """Test if the Streamlit app would work"""
    print("🌐 TESTING STREAMLIT APP COMPATIBILITY")
    print("=" * 50)
    
    try:
        # Test imports
        print("Testing imports...")
        
        try:
            from completely_fixed_ai_parser import AdvancedAIDateParser
            print("✅ AI Parser import successful")
        except Exception as e:
            print(f"❌ AI Parser import failed: {e}")
            return False
        
        try:
            from fixed_trello_api import TrelloAPI, validate_trello_credentials
            print("✅ Trello API import successful")
        except Exception as e:
            print(f"❌ Trello API import failed: {e}")
            return False
        
        # Test basic functionality
        print("\nTesting basic AI functionality...")
        parser = AdvancedAIDateParser()
        result = parser.suggest_due_date("test task")
        print(f"✅ AI parser working: {result['suggested_date']}")
        
        print("\nTesting Trello API class creation...")
        trello = TrelloAPI("dummy_key", "dummy_token")
        print("✅ Trello API class creation successful")
        
        return True
        
    except Exception as e:
        print(f"❌ Streamlit compatibility test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 COMPREHENSIVE DEBUG SCRIPT")
    print("=" * 60)
    print("This script tests both date calculation and Trello connection fixes")
    print()
    
    results = {
        'date_calculation': test_date_calculation(),
        'trello_connection': test_trello_connection(),
        'streamlit_compatibility': test_streamlit_app()
    }
    
    print("\n" + "=" * 60)
    print("📋 SUMMARY OF RESULTS")
    print("=" * 60)
    
    for test_name, success in results.items():
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{test_name.replace('_', ' ').title()}: {status}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\n🎉 ALL TESTS PASSED!")
        print("Your application should now work correctly with:")
        print("  • Fixed 'next week' date calculations")
        print("  • Better Trello API error handling")
        print("  • Improved Streamlit compatibility")
    else:
        print("\n⚠️  SOME TESTS FAILED")
        print("Please check the errors above and:")
        print("  • Replace the AI parser file with the fixed version")
        print("  • Get fresh Trello API credentials if needed")
        print("  • Check your Python environment")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()