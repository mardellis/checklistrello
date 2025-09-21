import re
import json
from datetime import datetime, timedelta, date
from typing import Optional, Dict, Any, List, Tuple
import logging
import calendar

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AdvancedAIDateParser:
    def __init__(self):
        """Initialize the advanced AI date parser"""
        self.today = datetime.now().date()
        
        # Enhanced patterns with better logic
        self.time_patterns = {
            # Immediate urgency
            'immediate': {
                'patterns': ['asap', 'urgent', 'critical', 'emergency', 'now', 'immediately', 'right away', 'urgent!'],
                'base_days': 0,
                'urgency': 10
            },
            # Today/tomorrow
            'today': {
                'patterns': ['today', 'by today', 'end of today', 'eod', 'end of day'],
                'base_days': 0,
                'urgency': 9
            },
            'tomorrow': {
                'patterns': ['tomorrow', 'by tomorrow', 'next day', 'tmrw'],
                'base_days': 1,
                'urgency': 8
            },
            # This week
            'this_week': {
                'patterns': ['this week', 'end of week', 'by friday', 'this friday', 'eow'],
                'base_days': self._days_until_friday(),
                'urgency': 7
            },
            # Next week
            'next_week': {
                'patterns': ['next week', 'following week', 'next monday'],
                'base_days': 7 + self._days_until_monday(),
                'urgency': 6
            },
            # Biweekly
            'biweekly': {
                'patterns': ['in two weeks', 'biweekly', '2 weeks', 'two weeks'],
                'base_days': 14,
                'urgency': 5
            },
            # Monthly
            'end_of_month': {
                'patterns': ['end of month', 'month end', 'by month end', 'eom'],
                'base_days': self._days_until_month_end(),
                'urgency': 4
            },
            'next_month': {
                'patterns': ['next month', 'following month'],
                'base_days': 30,
                'urgency': 3
            },
            # Quarterly
            'quarterly': {
                'patterns': ['quarterly', 'end of quarter', 'q1', 'q2', 'q3', 'q4', 'quarter end'],
                'base_days': 90,
                'urgency': 2
            },
            # Longer terms
            'long_term': {
                'patterns': ['someday', 'eventually', 'when possible', 'low priority', 'nice to have'],
                'base_days': 30,
                'urgency': 1
            }
        }
        
        # Action urgency modifiers
        self.action_urgency = {
            'high': ['fix', 'bug', 'error', 'break', 'broken', 'down', 'crash', 'fail', 'critical', 'block', 'blocking', 'hotfix', 'security'],
            'medium': ['review', 'update', 'check', 'test', 'verify', 'complete', 'finish', 'implement', 'deploy'],
            'low': ['plan', 'research', 'consider', 'explore', 'document', 'organize', 'brainstorm', 'think about']
        }
        
        # Context modifiers
        self.context_modifiers = {
            'client': ['client', 'customer', 'user', 'stakeholder'],
            'meeting': ['meeting', 'call', 'standup', 'sync', 'demo', 'presentation'],
            'deadline': ['deadline', 'due', 'submit', 'deliver', 'launch', 'release'],
            'maintenance': ['maintenance', 'cleanup', 'refactor', 'optimize']
        }
        
        # Weekday mapping
        self.weekdays = {
            'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
            'friday': 4, 'saturday': 5, 'sunday': 6,
            'mon': 0, 'tue': 1, 'wed': 2, 'thu': 3, 'fri': 4, 'sat': 5, 'sun': 6
        }
    
    def _days_until_friday(self) -> int:
        """Calculate days until next Friday"""
        days_ahead = 4 - self.today.weekday()  # Friday is weekday 4
        if days_ahead <= 0:  # Target day already happened this week
            days_ahead += 7
        return days_ahead
    
    def _days_until_monday(self) -> int:
        """Calculate days until next Monday"""
        days_ahead = 0 - self.today.weekday()  # Monday is weekday 0
        if days_ahead <= 0:  # Target day already happened this week
            days_ahead += 7
        return days_ahead
    
    def _days_until_month_end(self) -> int:
        """Calculate days until end of current month"""
        last_day = calendar.monthrange(self.today.year, self.today.month)[1]
        return last_day - self.today.day
    
    def _extract_specific_dates(self, text: str) -> Optional[Tuple[datetime, float]]:
        """Extract specific dates from text using advanced parsing"""
        text_lower = text.lower()
        
        # Try to extract specific weekdays
        for day_name, day_num in self.weekdays.items():
            if day_name in text_lower:
                days_ahead = day_num - self.today.weekday()
                if days_ahead <= 0:
                    days_ahead += 7
                
                # Check if it's "next" weekday
                if 'next' in text_lower and day_name in text_lower:
                    days_ahead += 7
                
                target_date = datetime.now() + timedelta(days=days_ahead)
                return target_date, 0.8
        
        # Try to parse actual dates
        date_patterns = [
            r'\b(\d{1,2})/(\d{1,2})/(\d{2,4})\b',  # MM/DD/YYYY
            r'\b(\d{1,2})-(\d{1,2})-(\d{2,4})\b',  # MM-DD-YYYY
            r'\b(\d{4})-(\d{1,2})-(\d{1,2})\b',    # YYYY-MM-DD
            r'\b(\d{1,2})\.(\d{1,2})\.(\d{2,4})\b',  # MM.DD.YYYY
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, text)
            if matches:
                try:
                    match = matches[0]
                    if len(match[0]) == 4:  # YYYY-MM-DD format
                        year, month, day = int(match[0]), int(match[1]), int(match[2])
                    else:  # MM/DD/YYYY or MM-DD-YYYY
                        month, day, year = int(match[0]), int(match[1]), int(match[2])
                        if year < 100:
                            year += 2000
                    
                    target_date = datetime(year, month, day)
                    return target_date, 0.9
                except ValueError:
                    continue
        
        return None
    
    def analyze_text_advanced(self, text: str) -> Dict[str, Any]:
        """Advanced text analysis with multiple factors"""
        text_lower = text.lower().strip()
        
        # First try to extract specific dates
        specific_date = self._extract_specific_dates(text)
        if specific_date:
            date_obj, confidence = specific_date
            days_diff = (date_obj.date() - self.today).days
            return {
                'suggested_days': max(0, days_diff),
                'confidence': confidence,
                'reasoning': f"Specific date detected: {date_obj.strftime('%Y-%m-%d')}",
                'urgency_score': 8 if days_diff <= 1 else 6 if days_diff <= 7 else 4,
                'matched_patterns': ['specific_date']
            }
        
        # Analyze time patterns
        matched_patterns = []
        urgency_scores = []
        suggested_days_list = []
        
        for pattern_name, pattern_data in self.time_patterns.items():
            for pattern in pattern_data['patterns']:
                if pattern in text_lower:
                    matched_patterns.append(pattern)
                    urgency_scores.append(pattern_data['urgency'])
                    suggested_days_list.append(pattern_data['base_days'])
        
        # Analyze action urgency
        action_modifier = 0
        detected_actions = []
        for urgency_level, actions in self.action_urgency.items():
            for action in actions:
                if action in text_lower:
                    detected_actions.append(action)
                    if urgency_level == 'high':
                        action_modifier += 3
                    elif urgency_level == 'medium':
                        action_modifier += 1
                    else:
                        action_modifier -= 1
        
        # Analyze context modifiers
        context_modifier = 0
        detected_contexts = []
        for context_type, contexts in self.context_modifiers.items():
            for context in contexts:
                if context in text_lower:
                    detected_contexts.append(context)
                    if context_type == 'client':
                        context_modifier += 2
                    elif context_type == 'meeting':
                        context_modifier += 1
                    elif context_type == 'deadline':
                        context_modifier += 2
        
        # Calculate final metrics
        if matched_patterns:
            # Use the most urgent pattern
            max_urgency_idx = urgency_scores.index(max(urgency_scores))
            suggested_days = suggested_days_list[max_urgency_idx]
            base_urgency = urgency_scores[max_urgency_idx]
            confidence = 0.7 + (len(matched_patterns) * 0.05)
        else:
            # Default fallback based on text length and complexity
            word_count = len(text_lower.split())
            if word_count < 3:
                suggested_days = 7
                base_urgency = 3
            elif word_count < 10:
                suggested_days = 5
                base_urgency = 4
            else:
                suggested_days = 3
                base_urgency = 5
            confidence = 0.3
        
        # Apply modifiers
        final_urgency = min(10, max(0, base_urgency + action_modifier + context_modifier))
        
        # Adjust days based on final urgency
        if final_urgency >= 9:
            suggested_days = min(suggested_days, 1)
        elif final_urgency >= 7:
            suggested_days = min(suggested_days, 3)
        elif final_urgency >= 5:
            suggested_days = min(suggested_days, 7)
        
        return {
            'suggested_days': max(0, suggested_days),
            'confidence': min(0.95, confidence),
            'urgency_score': final_urgency,
            'matched_patterns': matched_patterns[:5],
            'detected_actions': detected_actions[:3],
            'detected_contexts': detected_contexts[:3],
            'reasoning': self._generate_advanced_reasoning(text, matched_patterns, suggested_days, final_urgency, detected_actions, detected_contexts)
        }
    
    def _generate_advanced_reasoning(self, text: str, patterns: List[str], days: int, urgency: int, actions: List[str], contexts: List[str]) -> str:
        """Generate detailed reasoning for the suggestion"""
        reasoning_parts = []
        
        if patterns:
            pattern_str = ', '.join(patterns[:3])
            reasoning_parts.append(f"Time indicators: '{pattern_str}'")
        
        if actions:
            action_str = ', '.join(actions[:3])
            reasoning_parts.append(f"Action keywords: '{action_str}'")
        
        if contexts:
            context_str = ', '.join(contexts[:3])
            reasoning_parts.append(f"Context clues: '{context_str}'")
        
        if not reasoning_parts:
            reasoning_parts.append("No specific indicators found, using default timeline")
        
        # Add urgency explanation
        if urgency >= 9:
            urgency_text = "Immediate action required"
        elif urgency >= 7:
            urgency_text = "High priority task"
        elif urgency >= 5:
            urgency_text = "Medium priority task"
        elif urgency >= 3:
            urgency_text = "Standard timeline task"
        else:
            urgency_text = "Low priority task"
        
        base_reasoning = "; ".join(reasoning_parts)
        
        if days == 0:
            return f"{base_reasoning}. {urgency_text} - suggested for today."
        elif days == 1:
            return f"{base_reasoning}. {urgency_text} - suggested for tomorrow."
        elif days <= 7:
            return f"{base_reasoning}. {urgency_text} - suggested within {days} days."
        else:
            return f"{base_reasoning}. {urgency_text} - suggested {days}-day timeline."
    
    def suggest_due_date(self, checklist_item: str) -> Dict[str, Any]:
        """Main method to suggest due date with advanced analysis"""
        try:
            if not checklist_item or not checklist_item.strip():
                raise ValueError("Empty checklist item")
            
            # Advanced text analysis
            analysis = self.analyze_text_advanced(checklist_item)
            
            # Calculate target date
            suggested_date = datetime.now() + timedelta(days=analysis['suggested_days'])
            
            # Ensure it's not a weekend for work tasks (optional logic)
            if analysis['urgency_score'] < 8 and suggested_date.weekday() >= 5:  # Weekend
                # Move to next Monday if it's weekend and not urgent
                days_to_monday = 7 - suggested_date.weekday()
                suggested_date += timedelta(days=days_to_monday)
                analysis['reasoning'] += " (Moved to next weekday)"
            
            # Ensure it's not a past date
            if suggested_date.date() < self.today:
                suggested_date = datetime.now() + timedelta(days=1)
                analysis['suggested_days'] = 1
                analysis['reasoning'] += " (Adjusted to avoid past date)"
            
            return {
                'suggested_date': suggested_date.strftime('%Y-%m-%d'),
                'suggested_datetime': suggested_date,
                'confidence': analysis['confidence'],
                'reasoning': analysis['reasoning'],
                'urgency_score': analysis['urgency_score'],
                'keywords_found': analysis['matched_patterns'],
                'days_from_now': analysis['suggested_days'],
                'detected_actions': analysis.get('detected_actions', []),
                'detected_contexts': analysis.get('detected_contexts', [])
            }
            
        except Exception as e:
            logger.error(f"Error in suggest_due_date: {str(e)}")
            # Robust fallback
            fallback_date = datetime.now() + timedelta(days=7)
            return {
                'suggested_date': fallback_date.strftime('%Y-%m-%d'),
                'suggested_datetime': fallback_date,
                'confidence': 0.3,
                'reasoning': f'Default 7-day suggestion due to analysis error: {str(e)[:50]}',
                'urgency_score': 3,
                'keywords_found': [],
                'days_from_now': 7,
                'detected_actions': [],
                'detected_contexts': []
            }

# Backwards compatibility
AIDateParser = AdvancedAIDateParser

def test_enhanced_parser():
    """Comprehensive test suite for enhanced parser"""
    parser = AdvancedAIDateParser()
    
    test_cases = [
        # Immediate urgency
        ("Fix critical security bug ASAP", 0, 10),
        ("Emergency server maintenance NOW", 0, 10),
        ("Urgent client call needed today", 0, 9),
        
        # Specific timeframes
        ("Schedule team meeting tomorrow", 1, 8),
        ("Review code by Friday", None, 7),
        ("Deploy to production next week", None, 6),
        ("Plan Q2 strategy quarterly review", 90, 2),
        
        # Complex cases with context
        ("Fix login bug for client demo tomorrow", 1, 9),
        ("Research new framework when possible", 30, 1),
        ("Complete user documentation by month end", None, 4),
        
        # Date parsing
        ("Submit report by 2025-09-25", 3, 8),
        ("Meeting scheduled for 09/30/2025", None, 8),
        
        # Edge cases
        ("", 7, 3),  # Empty string
        ("Very long detailed task description with multiple clauses and complex requirements", 3, 5),
        ("a", 7, 3),  # Single character
    ]
    
    print("🧪 ENHANCED AI PARSER TEST SUITE")
    print("=" * 70)
    
    passed = 0
    total = len(test_cases)
    
    for i, (text, expected_days, expected_urgency) in enumerate(test_cases, 1):
        try:
            result = parser.suggest_due_date(text)
            
            print(f"\n{i}. Text: '{text[:50]}{'...' if len(text) > 50 else ''}'")
            print(f"   📅 Suggested: {result['suggested_date']} ({result['days_from_now']} days)")
            print(f"   🎯 Confidence: {result['confidence']:.1%}")
            print(f"   ⚡ Urgency: {result['urgency_score']}/10")
            print(f"   🔍 Keywords: {result['keywords_found']}")
            print(f"   🎬 Actions: {result.get('detected_actions', [])}")
            print(f"   🏷️  Contexts: {result.get('detected_contexts', [])}")
            print(f"   💭 Reasoning: {result['reasoning'][:100]}{'...' if len(result['reasoning']) > 100 else ''}")
            
            # Validation
            test_passed = True
            if expected_days is not None and result['days_from_now'] != expected_days:
                print(f"   ⚠️  Expected {expected_days} days, got {result['days_from_now']}")
                test_passed = False
            
            if expected_urgency is not None and abs(result['urgency_score'] - expected_urgency) > 2:
                print(f"   ⚠️  Expected urgency ~{expected_urgency}, got {result['urgency_score']}")
                test_passed = False
            
            if test_passed:
                print(f"   ✅ Test passed")
                passed += 1
            else:
                print(f"   ❌ Test failed")
                
            print("-" * 50)
            
        except Exception as e:
            print(f"   💥 Exception: {str(e)}")
            print("-" * 50)
    
    print(f"\n🎉 TEST RESULTS: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🏆 All tests passed! Parser is working correctly.")
    elif passed >= total * 0.8:
        print("✅ Most tests passed. Parser is functioning well.")
    else:
        print("⚠️  Some tests failed. Review parser logic.")

if __name__ == "__main__":
    test_enhanced_parser()