import re
import requests
import json
from datetime import datetime, timedelta, date
from typing import Optional, Dict, Any, List, Tuple
import logging
import spacy
from dateutil import parser as date_parser
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
                'patterns': ['asap', 'urgent', 'critical', 'emergency', 'now', 'immediately', 'right away'],
                'base_days': 0,
                'urgency': 10
            },
            # Today/tomorrow
            'today': {
                'patterns': ['today', 'by today', 'end of today'],
                'base_days': 0,
                'urgency': 9
            },
            'tomorrow': {
                'patterns': ['tomorrow', 'by tomorrow', 'next day'],
                'base_days': 1,
                'urgency': 8
            },
            # This week
            'this_week': {
                'patterns': ['this week', 'end of week', 'by friday', 'this friday'],
                'base_days': self._days_until_friday(),
                'urgency': 7
            },
            # Next week
            'next_week': {
                'patterns': ['next week', 'following week'],
                'base_days': 7 + self._days_until_friday(),
                'urgency': 6
            },
            # Specific days
            'end_of_month': {
                'patterns': ['end of month', 'month end', 'by month end'],
                'base_days': self._days_until_month_end(),
                'urgency': 4
            },
            # Longer terms
            'quarterly': {
                'patterns': ['quarterly', 'end of quarter', 'q1', 'q2', 'q3', 'q4'],
                'base_days': 90,
                'urgency': 2
            }
        }
        
        # Action urgency modifiers
        self.action_urgency = {
            'high': ['fix', 'bug', 'error', 'break', 'down', 'crash', 'fail', 'critical', 'block'],
            'medium': ['review', 'update', 'check', 'test', 'verify', 'complete'],
            'low': ['plan', 'research', 'consider', 'explore', 'document', 'organize']
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
        import re
        date_patterns = [
            r'\b(\d{1,2})/(\d{1,2})/(\d{2,4})\b',  # MM/DD/YYYY
            r'\b(\d{1,2})-(\d{1,2})-(\d{2,4})\b',  # MM-DD-YYYY
            r'\b(\d{4})-(\d{1,2})-(\d{1,2})\b',    # YYYY-MM-DD
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
        for urgency_level, actions in self.action_urgency.items():
            for action in actions:
                if action in text_lower:
                    if urgency_level == 'high':
                        action_modifier += 3
                    elif urgency_level == 'medium':
                        action_modifier += 1
                    else:
                        action_modifier -= 1
                    break
        
        # Calculate final metrics
        if matched_patterns:
            # Use the most urgent pattern
            max_urgency_idx = urgency_scores.index(max(urgency_scores))
            suggested_days = suggested_days_list[max_urgency_idx]
            base_urgency = urgency_scores[max_urgency_idx]
            confidence = 0.7 + (len(matched_patterns) * 0.1)
        else:
            # Default fallback
            suggested_days = 7
            base_urgency = 3
            confidence = 0.3
        
        # Apply action modifier
        final_urgency = min(10, max(0, base_urgency + action_modifier))
        
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
            'matched_patterns': matched_patterns[:5],  # Limit to 5 patterns
            'reasoning': self._generate_advanced_reasoning(text, matched_patterns, suggested_days, final_urgency)
        }
    
    def _generate_advanced_reasoning(self, text: str, patterns: List[str], days: int, urgency: int) -> str:
        """Generate detailed reasoning for the suggestion"""
        if not patterns:
            return f"No specific time indicators found. Using standard {days}-day timeline based on task complexity."
        
        pattern_str = ', '.join(patterns[:3])
        
        if days == 0:
            return f"Immediate action required based on: '{pattern_str}'. Suggested for today."
        elif days == 1:
            return f"High urgency detected from: '{pattern_str}'. Suggested for tomorrow."
        elif days <= 3:
            return f"Urgent timeline indicated by: '{pattern_str}'. Suggested within {days} days."
        elif days <= 7:
            return f"Week-based timeline from: '{pattern_str}'. Suggested within 1 week."
        else:
            return f"Longer-term planning based on: '{pattern_str}'. Suggested {days} days timeline."
    
    def suggest_due_date(self, checklist_item: str) -> Dict[str, Any]:
        """
        Main method to suggest due date with advanced analysis
        """
        try:
            if not checklist_item or not checklist_item.strip():
                raise ValueError("Empty checklist item")
            
            # Advanced text analysis
            analysis = self.analyze_text_advanced(checklist_item)
            
            # Calculate target date
            suggested_date = datetime.now() + timedelta(days=analysis['suggested_days'])
            
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
                'days_from_now': analysis['suggested_days']
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
                'days_from_now': 7
            }

# Backwards compatibility
AIDateParser = AdvancedAIDateParser

def test_advanced_parser():
    """Comprehensive test suite"""
    parser = AdvancedAIDateParser()
    
    test_cases = [
        # Immediate urgency
        ("Fix critical bug ASAP", 0, 10),
        ("Emergency server down", 0, 10),
        ("Urgent client call needed", 0, 9),
        
        # Specific timeframes
        ("Call client tomorrow", 1, 8),
        ("Meeting scheduled for Friday", None, 7),  # Variable days to Friday
        ("Next week review quarterly report", None, 6),
        
        # Complex cases
        ("NEXT WEEK EXACTLY TODAY I HAVE AN APPOINTMENT", None, None),  # Your example
        ("Plan team building event for next month", 30, 3),
        ("Review documentation when you have time", 7, 3),
        
        # Date parsing
        ("Deadline is 2025-09-25", 4, 8),
        ("Submit by 09/30/2025", None, 8),
    ]
    
    print("🧪 ADVANCED AI PARSER TEST SUITE")
    print("=" * 60)
    
    for i, (text, expected_days, expected_urgency) in enumerate(test_cases, 1):
        result = parser.suggest_due_date(text)
        
        print(f"\n{i}. Text: '{text}'")
        print(f"   📅 Suggested: {result['suggested_date']} ({result['days_from_now']} days)")
        print(f"   🎯 Confidence: {result['confidence']:.1%}")
        print(f"   ⚡ Urgency: {result['urgency_score']}/10")
        print(f"   🔍 Keywords: {result['keywords_found']}")
        print(f"   💭 Reasoning: {result['reasoning']}")
        
        # Validation
        if expected_days is not None and result['days_from_now'] != expected_days:
            print(f"   ⚠️  Expected {expected_days} days, got {result['days_from_now']}")
        
        if expected_urgency is not None and abs(result['urgency_score'] - expected_urgency) > 2:
            print(f"   ⚠️  Expected urgency ~{expected_urgency}, got {result['urgency_score']}")
        
        print("-" * 40)

if __name__ == "__main__":
    test_advanced_parser()