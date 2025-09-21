import re
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
import calendar

logger = logging.getLogger(__name__)

class AdvancedAIDateParser:
    """Advanced AI-powered date parser with urgency analysis"""
    
    def __init__(self):
        self.today = datetime.now()
        self.days_to_next_monday = self._calculate_days_to_next_monday()
        
        # Define urgency keywords with scores
        self.urgency_keywords = {
            'critical': 10, 'urgent': 9, 'asap': 9, 'immediately': 9,
            'emergency': 10, 'priority': 8, 'important': 7,
            'soon': 6, 'quickly': 6, 'fast': 6, 'rush': 7,
            'today': 10, 'now': 10, 'right now': 10,
            'tomorrow': 8, 'this week': 7, 'next week': 5,
            'deadline': 8, 'due': 7, 'overdue': 10, 'late': 9
        }
        
        # Time-specific patterns
        self.time_patterns = {
            'today': 0,
            'tomorrow': 1,
            'day after tomorrow': 2,
            'this week': 3,
            'next week': lambda: self.days_to_next_monday,
            'next weeks': lambda: self.days_to_next_monday,  # Handle plural
            'next monday': lambda: self.days_to_next_monday,
            'next tuesday': lambda: self.days_to_next_monday + 1,
            'next wednesday': lambda: self.days_to_next_monday + 2,
            'next thursday': lambda: self.days_to_next_monday + 3,
            'next friday': lambda: self.days_to_next_monday + 4,
            'in a week': 7,
            'in two weeks': 14,
            'in a month': 30,
            'end of week': lambda: self._days_to_end_of_week(),
            'end of month': lambda: self._days_to_end_of_month()
        }
        
        # Date format patterns
        self.date_patterns = [
            r'\b(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})\b',  # MM/DD/YYYY or DD/MM/YYYY
            r'\b(\d{4})[/-](\d{1,2})[/-](\d{1,2})\b',    # YYYY/MM/DD
            r'\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*\s+(\d{1,2})\b',  # Month DD
            r'\b(\d{1,2})\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*\b'   # DD Month
        ]
    
    def _calculate_days_to_next_monday(self) -> int:
        """Calculate days until next Monday"""
        current_weekday = self.today.weekday()  # Monday = 0, Sunday = 6
        if current_weekday == 6:  # Sunday
            return 1
        else:
            return 7 - current_weekday
    
    def _days_to_end_of_week(self) -> int:
        """Calculate days to end of current week (Friday)"""
        current_weekday = self.today.weekday()  # Monday = 0, Friday = 4
        if current_weekday <= 4:  # Monday to Friday
            return 4 - current_weekday
        else:  # Weekend, return next Friday
            return 4 + (7 - current_weekday)
    
    def _days_to_end_of_month(self) -> int:
        """Calculate days to end of current month"""
        last_day = calendar.monthrange(self.today.year, self.today.month)[1]
        return last_day - self.today.day
    
    def suggest_due_date(self, task_text: str) -> Dict[str, Any]:
        """Main function to suggest due date based on task text"""
        try:
            task_lower = task_text.lower().strip()
            
            # 1. Look for explicit dates first
            explicit_date = self._extract_explicit_date(task_lower)
            if explicit_date:
                return self._create_result(
                    explicit_date['date'],
                    explicit_date['days'],
                    0.9,
                    f"Explicit date found: {explicit_date['original']}",
                    task_text=task_text
                )
            
            # 2. Look for time-specific patterns
            time_match = self._find_time_patterns(task_lower)
            if time_match:
                urgency_analysis = self._analyze_urgency(task_lower)
                return self._create_result(
                    time_match['date'],
                    time_match['days'],
                    time_match['confidence'],
                    time_match['reasoning'],
                    keywords=urgency_analysis['keywords'],
                    urgency_score=max(urgency_analysis['score'], 5),  # Time patterns get min 5 urgency
                    task_text=task_text
                )
            
            # 3. Analyze urgency keywords
            urgency_analysis = self._analyze_urgency(task_lower)
            
            # 4. Generate suggestion based on urgency
            if urgency_analysis['score'] >= 9:
                # Extreme urgency - today
                days = 0
                reasoning = f"Extreme urgency detected (score: {urgency_analysis['score']}/10) - immediate action required"
            elif urgency_analysis['score'] >= 7:
                # High urgency - tomorrow
                days = 1
                reasoning = f"High urgency detected (score: {urgency_analysis['score']}/10) - quick turnaround needed"
            elif urgency_analysis['score'] >= 5:
                # Medium urgency - this week
                days = 3
                reasoning = f"Medium urgency detected (score: {urgency_analysis['score']}/10) - within week"
            elif urgency_analysis['score'] >= 2:
                # Low urgency - next week
                days = 7
                reasoning = f"Low urgency detected (score: {urgency_analysis['score']}/10) - standard timeline"
            else:
                # No urgency indicators - default timeline
                days = 7
                reasoning = "No specific urgency indicators found - using standard 1-week timeline"
            
            suggested_date = self.today + timedelta(days=days)
            confidence = 0.3 + (urgency_analysis['score'] / 10 * 0.5)  # 0.3 to 0.8 range
            
            return self._create_result(
                suggested_date,
                days,
                confidence,
                reasoning,
                urgency_analysis['keywords'],
                urgency_analysis['score'],
                task_text
            )
            
        except Exception as e:
            logger.error(f"Error in suggest_due_date: {e}")
            # Fallback result
            fallback_date = self.today + timedelta(days=7)
            return self._create_result(
                fallback_date,
                7,
                0.1,
                f"Error occurred, using fallback: {str(e)}",
                task_text=task_text
            )
    
    def _extract_explicit_date(self, text: str) -> Dict[str, Any]:
        """Extract explicit dates from text"""
        for pattern in self.date_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    date_obj = self._parse_date_match(match)
                    if date_obj and date_obj >= self.today.date():
                        days_diff = (date_obj - self.today.date()).days
                        return {
                            'date': datetime.combine(date_obj, datetime.min.time()),
                            'days': days_diff,
                            'original': match.group(0)
                        }
                except ValueError:
                    continue
        return None
    
    def _parse_date_match(self, match) -> datetime.date:
        """Parse regex match into date object"""
        groups = match.groups()
        text = match.group(0).lower()
        
        # Handle month name patterns
        if any(month in text for month in ['jan', 'feb', 'mar', 'apr', 'may', 'jun',
                                          'jul', 'aug', 'sep', 'oct', 'nov', 'dec']):
            return self._parse_month_day(text)
        
        # Handle numeric patterns
        if len(groups) == 3:
            if len(groups[0]) == 4:  # YYYY/MM/DD
                year, month, day = int(groups[0]), int(groups[1]), int(groups[2])
            else:  # MM/DD/YYYY or DD/MM/YYYY (assume MM/DD for US format)
                month, day, year = int(groups[0]), int(groups[1]), int(groups[2])
                if year < 100:
                    year += 2000
            
            return datetime(year, month, day).date()
        
        return None
    
    def _parse_month_day(self, text: str) -> datetime.date:
        """Parse month-day combinations"""
        months = {
            'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
            'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
        }
        
        for month_name, month_num in months.items():
            if month_name in text:
                # Extract day number
                day_match = re.search(r'\d{1,2}', text)
                if day_match:
                    day = int(day_match.group())
                    year = self.today.year
                    
                    # If date has passed this year, use next year
                    try:
                        date_obj = datetime(year, month_num, day).date()
                        if date_obj < self.today.date():
                            date_obj = datetime(year + 1, month_num, day).date()
                        return date_obj
                    except ValueError:
                        return None
        
        return None
    
    def _find_time_patterns(self, text: str) -> Dict[str, Any]:
        """Find time-specific patterns in text"""
        for pattern, days_func in self.time_patterns.items():
            if pattern in text:
                if callable(days_func):
                    days = days_func()
                else:
                    days = days_func
                
                suggested_date = self.today + timedelta(days=days)
                
                # Determine confidence based on specificity
                if pattern in ['today', 'tomorrow']:
                    confidence = 0.9
                elif pattern in ['this week', 'next week', 'next weeks']:
                    confidence = 0.8
                else:
                    confidence = 0.7
                
                return {
                    'date': suggested_date,
                    'days': days,
                    'confidence': confidence,
                    'reasoning': f"Time-specific pattern detected: '{pattern}' → {days} days from today"
                }
        
        return None
    
    def _analyze_urgency(self, text: str) -> Dict[str, Any]:
        """Analyze urgency level of task"""
        found_keywords = []
        total_score = 0
        
        for keyword, score in self.urgency_keywords.items():
            if keyword in text:
                found_keywords.append(keyword)
                total_score += score
        
        # Normalize score to 0-10 range with better scaling
        if total_score == 0:
            normalized_score = 0
        else:
            # Allow for keyword combinations to boost score
            max_single_keyword = max(self.urgency_keywords.values())
            normalized_score = min(10, int((total_score / max_single_keyword) * 8))
            
            # Boost for multiple keywords
            if len(found_keywords) > 1:
                normalized_score = min(10, normalized_score + len(found_keywords))
        
        return {
            'score': normalized_score,
            'keywords': found_keywords
        }
    
    def _create_result(self, date_obj: datetime, days_from_now: int, confidence: float, 
                      reasoning: str, keywords: List[str] = None, urgency_score: int = None,
                      task_text: str = '') -> Dict[str, Any]:
        """Create standardized result dictionary"""
        if keywords is None:
            keywords = []
        
        if urgency_score is None:
            # Calculate urgency based on days (inverse relationship)
            if days_from_now == 0:
                urgency_score = 10
            elif days_from_now == 1:
                urgency_score = 8
            elif days_from_now <= 3:
                urgency_score = 6
            elif days_from_now <= 7:
                urgency_score = 4
            else:
                urgency_score = max(1, int(10 - (days_from_now / 7)))
        
        return {
            'suggested_date': date_obj.strftime('%Y-%m-%d'),
            'suggested_datetime': date_obj,
            'days_from_now': days_from_now,
            'confidence': min(1.0, max(0.0, confidence)),
            'urgency_score': min(10, max(0, urgency_score)),
            'reasoning': reasoning,
            'keywords_found': keywords,
            'task_text': task_text,
        }

# Alias for backward compatibility
AIDateParser = AdvancedAIDateParser

def test_ai_parser():
    """Test the AI parser with various inputs"""
    print("🤖 AI DATE PARSER TEST")
    print("=" * 40)
    
    parser = AdvancedAIDateParser()
    
    test_cases = [
        "fix bugs next week",
        "send mail next weeks",
        "critical issue ASAP", 
        "meeting tomorrow at 2pm",
        "review document this week",
        "call client 12/25/2024",
        "urgent priority task",
        "plan vacation in a month",
        "submit report end of week",
        "emergency fix needed now",
        "schedule team meeting next Monday"
    ]
    
    print(f"Today: {parser.today.strftime('%A, %B %d, %Y')}")
    print(f"Days to next Monday: {parser.days_to_next_monday}")
    print()
    
    for test_text in test_cases:
        print(f"Testing: '{test_text}'")
        result = parser.suggest_due_date(test_text)
        
        print(f"  📅 Date: {result['suggested_date']} ({result['suggested_datetime'].strftime('%A')})")
        print(f"  📊 Days from now: {result['days_from_now']}")
        print(f"  🎯 Confidence: {result['confidence']:.1%}")
        print(f"  ⚡ Urgency: {result['urgency_score']}/10")
        print(f"  💭 Reasoning: {result['reasoning']}")
        if result['keywords_found']:
            print(f"  🔍 Keywords: {', '.join(result['keywords_found'])}")
        print()

if __name__ == "__main__":
    test_ai_parser()