import re
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple, Optional, Union
import calendar
from dateutil.relativedelta import relativedelta
from enum import Enum

logger = logging.getLogger(__name__)

class UrgencyLevel(Enum):
    CRITICAL = 10
    HIGH = 8
    MEDIUM = 6
    LOW = 4
    NONE = 2

class AdvancedAIDateParser:
    """Advanced AI-powered date parser with urgency analysis and fixed date calculations"""
    
    def __init__(self):
        self.today = datetime.now()
        self.current_date = self.today.date()
        self.days_to_next_monday = self._calculate_days_to_next_monday()
        
        # Enhanced urgency keywords with scores and categories
        self.urgency_keywords = {
            # Critical urgency (9-10)
            'critical': 10, 'urgent': 9, 'asap': 9, 'immediately': 9,
            'emergency': 10, 'priority': 8, 'important': 7, 'blocker': 10,
            'hotfix': 10, 'breaking': 10, 'outage': 10, 'down': 9,
            'stat': 9, 'now': 10, 'right now': 10,
            
            # Time-sensitive (7-9)
            'soon': 6, 'quickly': 6, 'fast': 6, 'rush': 7, 'hurry': 7,
            'today': 10, 'immediate': 9, 'tomorrow': 8,
            
            # Deadline-related (7-8)
            'deadline': 8, 'due': 7, 'overdue': 10, 'late': 9,
            'expires': 8, 'expiring': 8, 'cutoff': 8, 'timeline': 6,
            
            # Time frames (5-7)
            'this week': 7, 'end of week': 7, 'eow': 7,
            'next week': 5, 'weekly': 4, 'monthly': 3,
            'this month': 5, 'end of month': 6, 'eom': 6,
            'next month': 4, 'quarterly': 3, 'yearly': 2,
            
            # Business priority (6-8)
            'client': 7, 'customer': 7, 'boss': 8, 'manager': 7,
            'meeting': 6, 'presentation': 7, 'demo': 7, 'review': 6,
            'stakeholder': 7, 'executive': 8, 'vp': 8, 'director': 7,
            
            # Development urgency (5-9)
            'bug': 7, 'fix': 6, 'patch': 6, 'deploy': 7, 'release': 7,
            'production': 8, 'prod': 8, 'live': 8, 'staging': 6,
            'test': 5, 'qa': 6, 'security': 9, 'vulnerability': 9,
            'performance': 7, 'optimization': 5, 'refactor': 4,
            
            # Project management (4-6)
            'milestone': 6, 'deliverable': 6, 'sprint': 6,
            'backlog': 3, 'research': 4, 'investigate': 4,
            'planning': 4, 'design': 5, 'documentation': 4,
            'estimate': 4, 'budget': 5, 'roadmap': 4
        }
        
        # Time-specific patterns with FIXED calculations
        self.time_patterns = {
            'today': 0,
            'tonight': 0,
            'tomorrow': 1,
            'day after tomorrow': 2,
            'this week': lambda: self._days_to_end_of_week(),
            'end of week': lambda: self._days_to_end_of_week(),
            'eow': lambda: self._days_to_end_of_week(),
            
            # FIXED: These now properly calculate to next Monday
            'next week': lambda: self.days_to_next_monday,
            'next weeks': lambda: self.days_to_next_monday,  # Handle plural typo
            
            # Specific weekdays (next occurrence)
            'next monday': lambda: self.days_to_next_monday,
            'next tuesday': lambda: (self.days_to_next_monday + 1) % 7 or 7,
            'next wednesday': lambda: (self.days_to_next_monday + 2) % 7 or 7,
            'next thursday': lambda: (self.days_to_next_monday + 3) % 7 or 7,
            'next friday': lambda: (self.days_to_next_monday + 4) % 7 or 7,
            'next saturday': lambda: (self.days_to_next_monday + 5) % 7 or 7,
            'next sunday': lambda: (self.days_to_next_monday + 6) % 7 or 7,
            
            # This week days
            'monday': lambda: self._days_to_weekday(0),
            'tuesday': lambda: self._days_to_weekday(1),
            'wednesday': lambda: self._days_to_weekday(2),
            'thursday': lambda: self._days_to_weekday(3),
            'friday': lambda: self._days_to_weekday(4),
            'saturday': lambda: self._days_to_weekday(5),
            'sunday': lambda: self._days_to_weekday(6),
            
            # Relative timeframes
            'in a week': 7,
            'in 1 week': 7,
            'in two weeks': 14,
            'in 2 weeks': 14,
            'in a month': 30,
            'in 1 month': 30,
            'in two months': 60,
            'in 2 months': 60,
            'end of month': lambda: self._days_to_end_of_month(),
            'eom': lambda: self._days_to_end_of_month(),
            'next month': lambda: self._days_to_next_month(),
            'in a year': 365,
            'in 1 year': 365
        }
        
        # Date format patterns
        self.date_patterns = [
            r'\b(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})\b',  # MM/DD/YYYY or DD/MM/YYYY
            r'\b(\d{4})[/-](\d{1,2})[/-](\d{1,2})\b',    # YYYY/MM/DD
            r'\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*\s+(\d{1,2})(?:st|nd|rd|th)?\b',  # Month DD
            r'\b(\d{1,2})(?:st|nd|rd|th)?\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*\b',   # DD Month
            r'\b(\d{1,2})[/.-](\d{1,2})\b',  # MM/DD (current year assumed)
            r'\b(\d{1,2})(?:st|nd|rd|th)?\s+(of\s+)?(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*\b',  # DD of Month
        ]
        
        # Context patterns for better analysis
        self.context_patterns = {
            'work_related': ['meeting', 'client', 'project', 'task', 'deadline', 'presentation', 
                            'report', 'email', 'call', 'review', 'approval', 'team', 'manager',
                            'business', 'office', 'work', 'corporate', 'company'],
            'meeting_related': ['meeting', 'call', 'presentation', 'demo', 'standup', 'sync', 
                               'discussion', 'conference', 'appointment', 'interview', 'briefing'],
            'development_related': ['bug', 'fix', 'code', 'deploy', 'test', 'feature', 'api', 
                                   'database', 'server', 'application', 'website', 'build', 
                                   'release', 'software', 'program', 'script', 'develop'],
            'personal_related': ['buy', 'shopping', 'appointment', 'doctor', 'dentist', 'personal', 
                                'home', 'family', 'vacation', 'travel', 'grocery', 'birthday',
                                'anniversary', 'holiday', 'party', 'event', 'dinner', 'lunch']
        }
    
    def _calculate_days_to_next_monday(self) -> int:
        """Calculate days until next Monday - FIXED VERSION"""
        current_weekday = self.today.weekday()  # Monday = 0, Sunday = 6
        return (7 - current_weekday) % 7 or 7
    
    def _days_to_weekday(self, target_weekday: int) -> int:
        """Calculate days to a specific weekday in the current week"""
        current_weekday = self.today.weekday()
        if current_weekday <= target_weekday:
            return target_weekday - current_weekday
        else:
            return 7 - (current_weekday - target_weekday)
    
    def _days_to_end_of_week(self) -> int:
        """Calculate days to end of current week (Friday)"""
        current_weekday = self.today.weekday()  # Monday = 0, Friday = 4
        return (4 - current_weekday) % 7 or 7
    
    def _days_to_end_of_month(self) -> int:
        """Calculate days to end of current month"""
        last_day = calendar.monthrange(self.today.year, self.today.month)[1]
        return last_day - self.today.day
    
    def _days_to_next_month(self) -> int:
        """Calculate days to the same day next month"""
        next_month = self.today + relativedelta(months=1)
        return (next_month - self.today).days
    
    def suggest_due_date(self, task_text: str) -> Dict[str, Any]:
        """Main function to suggest due date based on task text - ENHANCED VERSION"""
        try:
            task_lower = task_text.lower().strip()
            
            # 1. Look for explicit dates first (highest priority)
            explicit_date = self._extract_explicit_date(task_lower)
            if explicit_date:
                return self._create_result(
                    explicit_date['date'],
                    explicit_date['days'],
                    0.95,  # Very high confidence for explicit dates
                    f"Explicit date found: {explicit_date['original']}",
                    task_text=task_text
                )
            
            # 2. Look for time-specific patterns (second priority)
            time_match = self._find_time_patterns(task_lower)
            if time_match:
                urgency_analysis = self._analyze_urgency(task_lower)
                # Combine time pattern urgency with keyword urgency
                combined_urgency = max(urgency_analysis['score'], time_match.get('base_urgency', 5))
                
                return self._create_result(
                    time_match['date'],
                    time_match['days'],
                    time_match['confidence'],
                    time_match['reasoning'],
                    keywords=urgency_analysis['keywords'],
                    urgency_score=combined_urgency,
                    task_text=task_text
                )
            
            # 3. Analyze urgency keywords and context
            urgency_analysis = self._analyze_urgency(task_lower)
            context_analysis = self._analyze_context(task_lower)
            
            # 4. Generate suggestion based on combined analysis
            final_urgency = max(urgency_analysis['score'], context_analysis['urgency_boost'])
            
            if final_urgency >= 9:
                # Extreme urgency - today or tomorrow
                days = 0 if final_urgency == 10 else 1
                reasoning = f"Extreme urgency detected (score: {final_urgency}/10) - immediate action required"
            elif final_urgency >= 7:
                # High urgency - within 2-3 days
                days = 2 if final_urgency >= 8 else 3
                reasoning = f"High urgency detected (score: {final_urgency}/10) - quick turnaround needed"
            elif final_urgency >= 5:
                # Medium urgency - this week (3-5 days)
                days = 5 if context_analysis['is_work_related'] else 4
                reasoning = f"Medium urgency detected (score: {final_urgency}/10) - within week"
            elif final_urgency >= 3:
                # Low urgency - next week
                days = self.days_to_next_monday
                reasoning = f"Low urgency detected (score: {final_urgency}/10) - next week timeline"
            else:
                # No urgency indicators - standard timeline
                days = 7
                reasoning = "No specific urgency indicators found - using standard 1-week timeline"
            
            # Apply context adjustments
            if context_analysis['is_meeting_related']:
                days = min(days, 3)  # Meetings need more advance notice
                reasoning += " (Meeting-related: adjusted for scheduling needs)"
            
            if context_analysis['is_development_related']:
                days = max(days, 2)  # Development tasks need realistic timeframes
                reasoning += " (Development task: realistic timeline applied)"
            
            if context_analysis['is_personal_related']:
                days = min(days, 5)  # Personal tasks often have shorter deadlines
                reasoning += " (Personal task: adjusted timeline)"
            
            suggested_date = self.today + timedelta(days=days)
            
            # Calculate confidence based on keyword matches and context
            base_confidence = 0.4
            keyword_confidence_boost = min(0.3, len(urgency_analysis['keywords']) * 0.1)
            context_confidence_boost = context_analysis['confidence_boost']
            
            confidence = base_confidence + keyword_confidence_boost + context_confidence_boost
            confidence = min(0.9, confidence)  # Cap at 90% for keyword-based analysis
            
            return self._create_result(
                suggested_date,
                days,
                confidence,
                reasoning,
                urgency_analysis['keywords'],
                final_urgency,
                task_text
            )
            
        except Exception as e:
            logger.error(f"Error in suggest_due_date: {e}")
            # Improved fallback
            fallback_days = 3  # More reasonable than 7 days
            fallback_date = self.today + timedelta(days=fallback_days)
            return self._create_result(
                fallback_date,
                fallback_days,
                0.1,
                f"Error occurred, using fallback: {str(e)}",
                task_text=task_text
            )
    
    def _analyze_context(self, text: str) -> Dict[str, Any]:
        """Analyze task context for better urgency and confidence assessment"""
        context_info = {
            'is_work_related': False,
            'is_meeting_related': False,
            'is_development_related': False,
            'is_personal_related': False,
            'urgency_boost': 0,
            'confidence_boost': 0
        }
        
        # Check each context category
        for category, keywords in self.context_patterns.items():
            if any(keyword in text for keyword in keywords):
                context_info[f'is_{category}'] = True
                
                # Apply boosts based on category
                if category == 'work_related':
                    context_info['confidence_boost'] += 0.1
                elif category == 'meeting_related':
                    context_info['urgency_boost'] += 2
                    context_info['confidence_boost'] += 0.15
                elif category == 'development_related':
                    context_info['confidence_boost'] += 0.1
                elif category == 'personal_related':
                    context_info['urgency_boost'] += 1
        
        return context_info
    
    def _extract_explicit_date(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract explicit dates from text - IMPROVED VERSION"""
        for pattern in self.date_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    date_obj = self._parse_date_match(match)
                    if date_obj and date_obj >= self.current_date:
                        days_diff = (date_obj - self.current_date).days
                        return {
                            'date': datetime.combine(date_obj, datetime.min.time()),
                            'days': days_diff,
                            'original': match.group(0)
                        }
                except (ValueError, TypeError) as e:
                    logger.debug(f"Date parsing failed for {match.group(0)}: {e}")
                    continue
        return None
    
    def _parse_date_match(self, match) -> Optional[datetime.date]:
        """Parse regex match into date object - IMPROVED VERSION"""
        groups = match.groups()
        text = match.group(0).lower()
        
        # Handle month name patterns
        if any(month in text for month in ['jan', 'feb', 'mar', 'apr', 'may', 'jun',
                                          'jul', 'aug', 'sep', 'oct', 'nov', 'dec']):
            return self._parse_month_day(text)
        
        # Handle numeric patterns
        if len(groups) >= 2:
            # Handle MM/DD without year (assume current year or next year if date has passed)
            if len(groups) == 2:
                month, day = int(groups[0]), int(groups[1])
                year = self.today.year
                
                try:
                    date_obj = datetime(year, month, day).date()
                    if date_obj < self.current_date:
                        date_obj = datetime(year + 1, month, day).date()
                    return date_obj
                except ValueError:
                    return None
            
            # Handle 3-part dates (with year)
            elif len(groups) == 3:
                # Determine format based on string length
                part1, part2, part3 = groups
                
                if len(part1) == 4:  # YYYY/MM/DD
                    year, month, day = int(part1), int(part2), int(part3)
                else:  # Assume MM/DD/YYYY or DD/MM/YYYY
                    # Try both formats and see which one makes sense
                    try:
                        # Try MM/DD/YYYY first
                        month, day, year = int(part1), int(part2), int(part3)
                        if year < 100:
                            year += 2000
                        
                        # Validate the date
                        datetime(year, month, day)
                        return datetime(year, month, day).date()
                    except ValueError:
                        # Try DD/MM/YYYY
                        try:
                            day, month, year = int(part1), int(part2), int(part3)
                            if year < 100:
                                year += 2000
                            datetime(year, month, day)
                            return datetime(year, month, day).date()
                        except ValueError:
                            return None
        
        return None
    
    def _parse_month_day(self, text: str) -> Optional[datetime.date]:
        """Parse month-day combinations - IMPROVED VERSION"""
        months = {
            'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
            'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12,
            'january': 1, 'february': 2, 'march': 3, 'april': 4, 'may': 5, 'june': 6,
            'july': 7, 'august': 8, 'september': 9, 'october': 10, 'november': 11, 'december': 12
        }
        
        # Find month in text
        for month_name, month_num in months.items():
            if month_name in text:
                # Extract day number
                day_match = re.search(r'\b(\d{1,2})(?:st|nd|rd|th)?\b', text)
                if day_match:
                    day = int(day_match.group(1))
                    year = self.today.year
                    
                    # If date has passed this year, use next year
                    try:
                        date_obj = datetime(year, month_num, day).date()
                        if date_obj < self.current_date:
                            date_obj = datetime(year + 1, month_num, day).date()
                        return date_obj
                    except ValueError:
                        return None
        
        return None
    
    def _find_time_patterns(self, text: str) -> Optional[Dict[str, Any]]:
        """Find time-specific patterns in text - ENHANCED VERSION"""
        for pattern, days_func in self.time_patterns.items():
            if re.search(r'\b' + pattern + r'\b', text):  # Use word boundaries for exact matching
                if callable(days_func):
                    days = days_func()
                else:
                    days = days_func
                
                suggested_date = self.today + timedelta(days=days)
                
                # Determine confidence and base urgency based on specificity
                if pattern in ['today', 'tonight', 'tomorrow']:
                    confidence = 0.95
                    base_urgency = 9
                elif pattern in ['this week', 'end of week', 'eow']:
                    confidence = 0.85
                    base_urgency = 7
                elif pattern in ['next week', 'next weeks']:
                    confidence = 0.8
                    base_urgency = 5
                elif pattern.startswith('next '):
                    confidence = 0.9
                    base_urgency = 6
                elif pattern in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']:
                    confidence = 0.85
                    base_urgency = 6
                else:
                    confidence = 0.75
                    base_urgency = 4
                
                return {
                    'date': suggested_date,
                    'days': days,
                    'confidence': confidence,
                    'base_urgency': base_urgency,
                    'reasoning': f"Time-specific pattern detected: '{pattern}' → {days} days from today"
                }
        
        return None
    
    def _analyze_urgency(self, text: str) -> Dict[str, Any]:
        """Analyze urgency level of task - ENHANCED VERSION"""
        found_keywords = []
        total_score = 0
        max_single_score = 0
        
        # Check for each urgency keyword
        for keyword, score in self.urgency_keywords.items():
            if re.search(r'\b' + keyword + r'\b', text):  # Use word boundaries for exact matching
                found_keywords.append(keyword)
                total_score += score
                max_single_score = max(max_single_score, score)
        
        # Enhanced scoring algorithm
        if total_score == 0:
            normalized_score = 0
        else:
            # Use the highest single keyword score as base
            normalized_score = max_single_score
            
            # Add bonus for multiple keywords (but cap the bonus)
            if len(found_keywords) > 1:
                bonus = min(2, len(found_keywords) - 1)  # Max +2 bonus
                normalized_score = min(10, normalized_score + bonus)
        
        # Context-based urgency boosters
        if any(word in text for word in ['!', '!!', 'asap', 'now']):
            normalized_score = min(10, normalized_score + 1)
        
        if any(word in text for word in ['critical', 'emergency', 'urgent']):
            normalized_score = max(8, normalized_score)  # Ensure minimum urgency
        
        return {
            'score': normalized_score,
            'keywords': found_keywords
        }
    
    def _create_result(self, date_obj: datetime, days_from_now: int, confidence: float, 
                      reasoning: str, keywords: List[str] = None, urgency_score: int = None,
                      task_text: str = '') -> Dict[str, Any]:
        """Create standardized result dictionary - ENHANCED VERSION"""
        if keywords is None:
            keywords = []
        
        if urgency_score is None:
            # Calculate urgency based on days (inverse relationship) - IMPROVED
            if days_from_now == 0:
                urgency_score = 10
            elif days_from_now == 1:
                urgency_score = 9
            elif days_from_now <= 2:
                urgency_score = 8
            elif days_from_now <= 3:
                urgency_score = 7
            elif days_from_now <= 5:
                urgency_score = 6
            elif days_from_now <= 7:
                urgency_score = 5
            elif days_from_now <= 14:
                urgency_score = 4
            else:
                urgency_score = max(1, int(10 - (days_from_now / 7)))
        
        # Determine urgency level
        if urgency_score >= 9:
            urgency_level = UrgencyLevel.CRITICAL.name
        elif urgency_score >= 7:
            urgency_level = UrgencyLevel.HIGH.name
        elif urgency_score >= 5:
            urgency_level = UrgencyLevel.MEDIUM.name
        elif urgency_score >= 3:
            urgency_level = UrgencyLevel.LOW.name
        else:
            urgency_level = UrgencyLevel.NONE.name
        
        return {
            'suggested_date': date_obj.strftime('%Y-%m-%d'),
            'suggested_datetime': date_obj,
            'days_from_now': days_from_now,
            'confidence': min(1.0, max(0.0, confidence)),
            'urgency_score': min(10, max(0, urgency_score)),
            'urgency_level': urgency_level,
            'reasoning': reasoning,
            'keywords_found': keywords,
            'task_text': task_text,
        }

# Alias for backward compatibility
AIDateParser = AdvancedAIDateParser

def test_ai_parser():
    """Test the AI parser with various inputs - ENHANCED TEST"""
    print("🤖 ENHANCED AI DATE PARSER TEST")
    print("=" * 50)
    
    parser = AdvancedAIDateParser()
    
    test_cases = [
        # Time pattern tests (including the failing case)
        "fix bugs next week",
        "fix bugs next weeks",  # This was the failing case
        "meeting tomorrow at 2pm",
        "review document this week",
        "urgent priority task",
        
        # Critical urgency tests
        "critical issue ASAP", 
        "emergency fix needed now",
        "production server is down",
        "security vulnerability found",
        
        # Development-related tests
        "deploy to production next Monday",
        "fix login bug before release",
        "code review for API changes",
        
        # Meeting-related tests
        "schedule team meeting next week",
        "client presentation this week",
        
        # Date-specific tests
        "call client 12/25/2024",
        "submit report end of week",
        "plan vacation in a month",
        
        # Context tests
        "buy groceries and milk",
        "doctor appointment needed",
        "research new frameworks",
        
        # Edge cases
        "meeting on Monday",
        "deadline next Friday",
        "important: fix critical bug ASAP!",
        "quarterly review next month"
    ]
    
    print(f"Today: {parser.today.strftime('%A, %B %d, %Y')}")
    print(f"Current weekday: {parser.today.weekday()} (Monday=0)")
    print(f"Days to next Monday: {parser.days_to_next_monday}")
    print(f"Expected next Monday: {(parser.today + timedelta(days=parser.days_to_next_monday)).strftime('%A, %B %d, %Y')}")
    print()
    
    for test_text in test_cases:
        print(f"Testing: '{test_text}'")
        result = parser.suggest_due_date(test_text)
        
        print(f"  📅 Date: {result['suggested_date']} ({result['suggested_datetime'].strftime('%A')})")
        print(f"  📊 Days from now: {result['days_from_now']}")
        print(f"  🎯 Confidence: {result['confidence']:.1%}")
        print(f"  ⚡ Urgency: {result['urgency_score']}/10 ({result['urgency_level']})")
        print(f"  💭 Reasoning: {result['reasoning']}")
        if result['keywords_found']:
            print(f"  🔍 Keywords: {', '.join(result['keywords_found'])}")
        
        # Special validation for "next week" cases
        if "next week" in test_text.lower():
            expected_days = parser.days_to_next_monday
            if result['days_from_now'] == expected_days:
                print("  ✅ NEXT WEEK CALCULATION: CORRECT!")
            else:
                print(f"  ❌ NEXT WEEK CALCULATION: WRONG! Expected {expected_days}, got {result['days_from_now']}")
        
        print()

if __name__ == "__main__":
    test_ai_parser()