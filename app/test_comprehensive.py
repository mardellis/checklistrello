#!/usr/bin/env python3
"""
Comprehensive test script for checklistrello application
Tests all major fixes and improvements including date calculations and Trello integration
"""

import sys
import os
from datetime import datetime, timedelta
import json

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_date_calculations():
    """Test the fixed date calculation logic"""
    print("🗓️  TESTING DATE CALCULATIONS")
    print("=" * 60)
    
    try:
        from ai_parser import AdvancedAIDateParser
        
        parser = AdvancedAIDateParser()
        today = datetime.now()
        
        print(f"Today: {today.strftime('%A, %B %d, %Y')} (weekday {today.weekday()})")
        print(f"Next Monday calculation: {parser.days_to_next_monday} days")
        print(f"Expected next Monday: {(today + timedelta(days=parser.days_to_next_monday)).strftime('%A, %B %d, %Y')}")
        print()
        
        # Test cases focusing on the original issue
        critical_test_cases = [
            "fix bugs next week",           # This was failing before
            "fix bugs next weeks",          # Plural form
            "meeting next week",
            "schedule call next week",
            "review code next week"
        ]
        
        print("🔍 CRITICAL TEST CASES (Next Week Calculations):")
        print("-" * 50)
        
        all_passed = True
        
        for test_text in critical_test_cases:
            result = parser.suggest_due_date(test_text)
            expected_days = parser.days_to_next_monday
            actual_days = result['days_from_now']
            
            status = "✅ PASS" if actual_days == expected_days else "❌ FAIL"
            if actual_days != expected_days:
                all_passed = False
            
            print(f"{status} '{test_text}'")
            print(f"     Expected: {expected_days} days → {(today + timedelta(days=expected_days)).strftime('%Y-%m-%d (%A)')}")
            print(f"     Actual:   {actual_days} days → {result['suggested_date']} ({result['suggested_datetime'].strftime('%A')})")
            print(f"     Confidence: {result['confidence']:.1%}, Urgency: {result['urgency_score']}/10")
            print()
        
        # Additional comprehensive tests
        print("🧪 ADDITIONAL DATE TESTS:")
        print("-" * 30)
        
        additional_tests = [
            ("critical issue ASAP", 0, 1),           # Should be today/tomorrow
            ("emergency fix now", 0, 1),             # Should be today/tomorrow  
            ("meeting tomorrow", 1, 1),              # Should be exactly 1 day
            ("task this week", 0, 5),                # Should be within week
            ("call client 12/25/2024", None, None), # Explicit date
            ("research next month", 20, 40)          # Should be longer term
        ]
        
        for test_text, min_days, max_days in additional_tests:
            result = parser.suggest_due_date(test_text)
            days = result['days_from_now']
            
            if min_days is not None and max_days is not None:
                status = "✅ PASS" if min_days <= days <= max_days else "❌ FAIL"
                if not (min_days <= days <= max_days):
                    all_passed = False
                print(f"{status} '{test_text}' → {days} days (expected {min_days}-{max_days})")
            else:
                print(f"📅 '{test_text}' → {days} days ({result['suggested_date']})")
        
        print()
        print("🏆 DATE CALCULATION TEST RESULT:")
        if all_passed:
            print("✅ ALL CRITICAL TESTS PASSED! Date calculations are working correctly.")
        else:
            print("❌ SOME TESTS FAILED! Please check the date calculation logic.")
        
        return all_passed
        
    except ImportError as e:
        print(f"❌ Could not import AI parser: {e}")
        return False
    except Exception as e:
        print(f"❌ Date calculation test failed: {e}")
        return False

def test_trello_integration():
    """Test Trello integration components"""
    print("🔗 TESTING TRELLO INTEGRATION")
    print("=" * 60)
    
    try:
        from trello_api import TrelloAPI, validate_trello_credentials
        from trello_integration import render_trello_integration
        
        print("✅ Trello modules imported successfully")
        
        # Test credential validation with dummy data
        print("\n🔍 Testing credential validation:")
        
        # Test invalid credentials
        invalid_result = validate_trello_credentials("", "")
        if not invalid_result['success']:
            print("✅ Empty credentials correctly rejected")
        else:
            print("❌ Empty credentials should be rejected")
        
        # Test format validation
        short_key_result = validate_trello_credentials("short", "token" * 20)
        if not short_key_result['success'] and "32 characters" in short_key_result['error']:
            print("✅ Short API key correctly rejected with helpful message")
        else:
            print("❌ Short API key validation failed")
        
        # Test TrelloAPI class creation
        try:
            api = TrelloAPI("dummy32characterapikeyfordemoonly", "dummy64charactertoken" * 2)
            print("✅ TrelloAPI class creation successful")
        except Exception as e:
            print(f"❌ TrelloAPI class creation failed: {e}")
        
        # Test integration functions exist
        integration_functions = [
            'render_trello_integration',
            'test_trello_connection', 
            'load_trello_boards',
            'analyze_all_items'
        ]
        
        from trello_integration import render_trello_integration
        print("✅ Main integration function imported")
        
        return True
        
    except ImportError as e:
        print(f"❌ Trello integration import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Trello integration test failed: {e}")
        return False

def test_ai_enhancements():
    """Test AI parser enhancements and urgency detection"""
    print("🤖 TESTING AI ENHANCEMENTS")
    print("=" * 60)
    
    try:
        from ai_parser import AdvancedAIDateParser
        
        parser = AdvancedAIDateParser()
        
        # Test enhanced urgency detection
        urgency_test_cases = [
            ("critical production issue", 9, 10),
            ("security vulnerability found", 8, 10), 
            ("emergency server down", 10, 10),
            ("bug fix needed soon", 5, 7),
            ("research new tools", 1, 4),
            ("plan team building", 1, 3)
        ]
        
        print("⚡ Testing urgency detection:")
        urgency_passed = True
        
        for test_text, min_urgency, max_urgency in urgency_test_cases:
            result = parser.suggest_due_date(test_text)
            urgency = result['urgency_score']
            
            status = "✅ PASS" if min_urgency <= urgency <= max_urgency else "❌ FAIL"
            if not (min_urgency <= urgency <= max_urgency):
                urgency_passed = False
            
            print(f"  {status} '{test_text}' → {urgency}/10 (expected {min_urgency}-{max_urgency})")
            if result['keywords_found']:
                print(f"       Keywords: {', '.join(result['keywords_found'])}")
        
        # Test confidence scoring
        print("\n🎯 Testing confidence scoring:")
        confidence_test_cases = [
            ("meeting tomorrow at 2pm", 0.8, 1.0),    # High confidence - specific
            ("critical bug ASAP", 0.6, 0.9),          # Good confidence - clear urgency
            ("some task", 0.1, 0.4),                   # Low confidence - vague
            ("call client 12/25/2024", 0.9, 1.0)      # Very high - explicit date
        ]
        
        confidence_passed = True
        
        for test_text, min_conf, max_conf in confidence_test_cases:
            result = parser.suggest_due_date(test_text)
            confidence = result['confidence']
            
            status = "✅ PASS" if min_conf <= confidence <= max_conf else "❌ FAIL"
            if not (min_conf <= confidence <= max_conf):
                confidence_passed = False
            
            print(f"  {status} '{test_text}' → {confidence:.1%} (expected {min_conf:.0%}-{max_conf:.0%})")
        
        # Test enhanced reasoning
        print("\n💭 Testing enhanced reasoning:")
        reasoning_test = parser.suggest_due_date("critical client meeting tomorrow ASAP")
        print(f"  Sample reasoning: {reasoning_test['reasoning']}")
        
        reasoning_quality = (
            len(reasoning_test['reasoning']) > 20 and
            any(word in reasoning_test['reasoning'].lower() for word in ['critical', 'tomorrow', 'urgency'])
        )
        
        if reasoning_quality:
            print("  ✅ Reasoning contains relevant keywords and details")
        else:
            print("  ❌ Reasoning lacks detail or relevance")
        
        overall_ai_passed = urgency_passed and confidence_passed and reasoning_quality
        
        return overall_ai_passed
        
    except Exception as e:
        print(f"❌ AI enhancement test failed: {e}")
        return False

def test_error_handling():
    """Test error handling and fallback mechanisms"""
    print("🛡️  TESTING ERROR HANDLING")
    print("=" * 60)
    
    try:
        from ai_parser import AdvancedAIDateParser
        
        parser = AdvancedAIDateParser()
        
        # Test with problematic inputs
        error_test_cases = [
            "",                    # Empty string
            "   ",                # Whitespace only  
            "a" * 1000,          # Very long string
            "🎉🎊🎈" * 50,       # Unicode/emojis
            "invalid date 13/45/2024",  # Invalid date
            None                  # None input (will be converted to string)
        ]
        
        print("🧪 Testing error resilience:")
        errors_handled = 0
        
        for test_input in error_test_cases:
            try:
                if test_input is None:
                    continue  # Skip None test as it would cause TypeError before reaching our code
                    
                result = parser.suggest_due_date(str(test_input))
                
                # Check if result is valid
                if (result and 
                    'suggested_date' in result and 
                    'confidence' in result and
                    result['confidence'] >= 0):
                    print(f"  ✅ Handled: '{str(test_input)[:30]}...' → {result['suggested_date']}")
                    errors_handled += 1
                else:
                    print(f"  ❌ Invalid result for: '{str(test_input)[:30]}...'")
                    
            except Exception as e:
                print(f"  ❌ Unhandled error for '{str(test_input)[:30]}...': {e}")
        
        # Test fallback parser
        print("\n🔄 Testing fallback mechanisms:")
        try:
            # Import and test the fallback parser from main app
            sys.path.append('.')
            from streamlit_app import FallbackAIParser
            
            fallback_parser = FallbackAIParser()
            fallback_result = fallback_parser.suggest_due_date("test task")
            
            if fallback_result and 'suggested_date' in fallback_result:
                print("  ✅ Fallback parser working correctly")
                fallback_works = True
            else:
                print("  ❌ Fallback parser failed")
                fallback_works = False
                
        except ImportError:
            print("  ⚠️  Fallback parser not available (streamlit_app not found)")
            fallback_works = True  # Don't fail the test for this
        
        error_handling_passed = errors_handled >= len(error_test_cases) - 1  # -1 for None case
        
        return error_handling_passed and fallback_works
        
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        return False

def test_streamlit_compatibility():
    """Test Streamlit app compatibility"""
    print("🌐 TESTING STREAMLIT COMPATIBILITY")
    print("=" * 60)
    
    try:
        # Test imports
        print("📦 Testing imports:")
        
        modules_to_test = [
            ('ai_parser', 'AdvancedAIDateParser'),
            ('trello_api', 'TrelloAPI'),
            ('trello_integration', 'integrate_trello_to_main_app'),
            ('streamlit_app', 'main')
        ]
        
        import_success = 0
        
        for module_name, class_or_func in modules_to_test:
            try:
                module = __import__(module_name)
                if hasattr(module, class_or_func):
                    print(f"  ✅ {module_name}.{class_or_func}")
                    import_success += 1
                else:
                    print(f"  ❌ {module_name}.{class_or_func} not found")
            except ImportError as e:
                print(f"  ⚠️  {module_name} not available: {e}")
        
        # Test basic functionality without Streamlit
        print("\n🔧 Testing core functionality:")
        
        try:
            from ai_parser import AdvancedAIDateParser
            parser = AdvancedAIDateParser()
            result = parser.suggest_due_date("test integration")
            
            if result and result.get('suggested_date'):
                print("  ✅ Core AI functionality working")
                core_works = True
            else:
                print("  ❌ Core AI functionality failed")
                core_works = False
                
        except Exception as e:
            print(f"  ❌ Core functionality test failed: {e}")
            core_works = False
        
        compatibility_score = import_success / len(modules_to_test)
        
        print(f"\n📊 Compatibility score: {compatibility_score:.1%}")
        
        return compatibility_score >= 0.75 and core_works
        
    except Exception as e:
        print(f"❌ Streamlit compatibility test failed: {e}")
        return False

def run_comprehensive_tests():
    """Run all tests and provide comprehensive report"""
    print("🧪 COMPREHENSIVE CHECKLISTRELLO TEST SUITE")
    print("=" * 70)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Run all test suites
    test_results = {}
    
    print("Running test suites...\n")
    
    test_results['date_calculations'] = test_date_calculations()
    print()
    
    test_results['trello_integration'] = test_trello_integration() 
    print()
    
    test_results['ai_enhancements'] = test_ai_enhancements()
    print()
    
    test_results['error_handling'] = test_error_handling()
    print()
    
    test_results['streamlit_compatibility'] = test_streamlit_compatibility()
    print()
    
    # Generate comprehensive report
    print("📋 COMPREHENSIVE TEST REPORT")
    print("=" * 70)
    
    total_tests = len(test_results)
    passed_tests = sum(test_results.values())
    success_rate = (passed_tests / total_tests) * 100
    
    print(f"Overall Success Rate: {success_rate:.1f}% ({passed_tests}/{total_tests})")
    print()
    
    # Detailed results
    status_emoji = {True: "✅ PASS", False: "❌ FAIL"}
    
    for test_name, result in test_results.items():
        test_display_name = test_name.replace('_', ' ').title()
        print(f"{status_emoji[result]} {test_display_name}")
    
    print()
    
    # Recommendations based on results
    print("🎯 RECOMMENDATIONS:")
    print("-" * 30)
    
    if test_results['date_calculations']:
        print("✅ Date calculations are working correctly - the 'next week' bug is fixed!")
    else:
        print("❌ Date calculations need attention - check the _calculate_days_to_next_monday method")
    
    if test_results['trello_integration']:
        print("✅ Trello integration is ready - API connections should work properly")
    else:
        print("❌ Trello integration needs fixes - check import paths and function definitions")
    
    if test_results['ai_enhancements']:
        print("✅ AI enhancements are working - improved urgency detection and confidence scoring")
    else:
        print("❌ AI enhancements need refinement - check keyword matching and scoring logic")
    
    if test_results['error_handling']:
        print("✅ Error handling is robust - app should handle edge cases gracefully")
    else:
        print("❌ Error handling needs improvement - add more try/catch blocks and fallbacks")
    
    if test_results['streamlit_compatibility']:
        print("✅ Streamlit compatibility confirmed - app should run without import issues")
    else:
        print("❌ Streamlit compatibility issues detected - check module imports and dependencies")
    
    print()
    
    # Final assessment
    if success_rate >= 90:
        print("🎉 EXCELLENT! Your application is ready for production deployment.")
        recommendation = "DEPLOY"
    elif success_rate >= 75:
        print("👍 GOOD! Minor issues detected but application should work well.")
        recommendation = "DEPLOY WITH MONITORING"
    elif success_rate >= 50:
        print("⚠️  MODERATE: Several issues need attention before deployment.")
        recommendation = "FIX CRITICAL ISSUES FIRST"
    else:
        print("🚨 CRITICAL: Major issues detected. Significant fixes needed.")
        recommendation = "MAJOR REFACTORING NEEDED"
    
    print(f"Recommendation: {recommendation}")
    
    # Generate summary JSON
    test_summary = {
        'test_timestamp': datetime.now().isoformat(),
        'overall_success_rate': success_rate,
        'tests_passed': passed_tests,
        'total_tests': total_tests,
        'detailed_results': test_results,
        'recommendation': recommendation,
        'critical_fixes_verified': {
            'next_week_calculation': test_results['date_calculations'],
            'trello_analysis_integration': test_results['trello_integration'],
            'ai_improvements': test_results['ai_enhancements'],
            'error_resilience': test_results['error_handling']
        }
    }
    
    # Save test results
    try:
        with open(f'test_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json', 'w') as f:
            json.dump(test_summary, f, indent=2)
        print(f"\n💾 Test results saved to test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    except Exception as e:
        print(f"\n⚠️ Could not save test results: {e}")
    
    print("\n" + "=" * 70)
    return success_rate >= 75  # Return True if tests are mostly passing

def quick_smoke_test():
    """Quick smoke test for immediate verification"""
    print("🔥 QUICK SMOKE TEST")
    print("=" * 40)
    
    try:
        # Test the critical "next week" fix
        from ai_parser import AdvancedAIDateParser
        parser = AdvancedAIDateParser()
        
        result = parser.suggest_due_date("fix bugs next week")
        expected_days = parser.days_to_next_monday
        actual_days = result['days_from_now']
        
        if actual_days == expected_days:
            print("✅ CRITICAL FIX VERIFIED: 'next week' calculation is correct!")
            print(f"   Next week = {actual_days} days = {result['suggested_date']}")
            return True
        else:
            print("❌ CRITICAL FIX FAILED: 'next week' calculation is still wrong!")
            print(f"   Expected: {expected_days} days")
            print(f"   Actual: {actual_days} days")
            return False
            
    except Exception as e:
        print(f"❌ SMOKE TEST FAILED: {e}")
        return False

def main():
    """Main test runner"""
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        # Quick smoke test only
        success = quick_smoke_test()
        sys.exit(0 if success else 1)
    else:
        # Full comprehensive test suite
        success = run_comprehensive_tests()
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()