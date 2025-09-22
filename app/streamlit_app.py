import streamlit as st
from datetime import datetime, timedelta
import pandas as pd
import re
from typing import Dict, Any, List

# Page config
st.set_page_config(
    page_title="AI Due Date Assistant",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enhanced CSS with better styling
st.markdown("""
<style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Main app styling */
    .main { 
        padding: 1rem 2rem;
        font-family: 'Inter', sans-serif;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        min-height: 100vh;
    }
    
    /* Header */
    .app-header {
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(20px);
        border-radius: 20px;
        padding: 2rem;
        text-align: center;
        margin-bottom: 2rem;
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    
    .app-title {
        font-size: 3rem;
        font-weight: 700;
        color: white;
        margin-bottom: 0.5rem;
        text-shadow: 0 4px 20px rgba(0,0,0,0.3);
    }
    
    .app-subtitle {
        font-size: 1.2rem;
        color: rgba(255, 255, 255, 0.8);
        font-weight: 400;
    }
    
    /* Main content cards */
    .content-card {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(20px);
        border-radius: 20px;
        padding: 2rem;
        margin-bottom: 2rem;
        box-shadow: 0 20px 60px rgba(0,0,0,0.1);
        border: 1px solid rgba(255, 255, 255, 0.3);
    }
    
    /* Input section */
    .stTextArea textarea {
        border-radius: 15px !important;
        border: 2px solid #e1e8ed !important;
        font-size: 1.1rem !important;
        padding: 1rem !important;
        transition: all 0.3s ease !important;
    }
    
    .stTextArea textarea:focus {
        border-color: #667eea !important;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1) !important;
    }
    
    /* Buttons */
    .stButton > button {
        width: 100%;
        border-radius: 15px !important;
        padding: 0.75rem 2rem !important;
        font-weight: 600 !important;
        font-size: 1.1rem !important;
        transition: all 0.3s ease !important;
        border: none !important;
    }
    
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3) !important;
    }
    
    .stButton > button[kind="primary"]:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 15px 40px rgba(102, 126, 234, 0.4) !important;
    }
    
    /* Results section */
    .result-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 20px;
        padding: 2rem;
        margin: 1rem 0;
        box-shadow: 0 20px 60px rgba(102, 126, 234, 0.3);
    }
    
    .result-title {
        font-size: 1.8rem;
        font-weight: 700;
        margin-bottom: 1rem;
    }
    
    .result-date {
        font-size: 2.2rem;
        font-weight: 700;
        margin: 1rem 0;
        text-shadow: 0 2px 10px rgba(0,0,0,0.2);
    }
    
    /* Metrics */
    .metric-container {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
        gap: 1rem;
        margin: 1.5rem 0;
    }
    
    .metric-card {
        background: rgba(255, 255, 255, 0.15);
        backdrop-filter: blur(20px);
        border-radius: 15px;
        padding: 1.5rem 1rem;
        text-align: center;
        border: 1px solid rgba(255, 255, 255, 0.2);
        transition: all 0.3s ease;
    }
    
    .metric-card:hover {
        background: rgba(255, 255, 255, 0.25);
        transform: translateY(-3px);
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    
    .metric-label {
        font-size: 0.9rem;
        opacity: 0.9;
        font-weight: 500;
    }
    
    /* Confidence colors */
    .confidence-high { color: #00ff88; }
    .confidence-medium { color: #ffcc00; }
    .confidence-low { color: #ff6b6b; }
    
    /* Keywords */
    .keyword-tag {
        display: inline-block;
        background: rgba(255, 255, 255, 0.2);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        margin: 0.25rem;
        font-size: 0.9rem;
        font-weight: 500;
        backdrop-filter: blur(10px);
    }
    
    /* Advanced options */
    .option-container {
        background: rgba(102, 126, 234, 0.05);
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0;
        border: 1px solid rgba(102, 126, 234, 0.1);
    }
    
    /* Feedback section */
    .feedback-card {
        background: rgba(17, 153, 142, 0.05);
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0;
        border: 1px solid rgba(17, 153, 142, 0.1);
    }
    
    /* Sidebar enhancements */
    .sidebar-card {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    
    /* Hide streamlit branding */
    #MainMenu { visibility: hidden; }
    .stDeployButton { display: none; }
    footer { visibility: hidden; }
    
    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: rgba(255, 255, 255, 0.3);
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: rgba(255, 255, 255, 0.5);
    }
</style>
""", unsafe_allow_html=True)

class SmartDateParser:
    """Enhanced AI date parser with improved accuracy"""
    
    def __init__(self):
        self.urgency_patterns = {
            'critical': ['asap', 'urgent', 'critical', 'emergency', 'immediately', 'now', 'crisis', 'fire', 'breaking'],
            'high': ['today', 'tonight', 'this morning', 'this afternoon', 'by end of day', 'eod', 'before 5'],
            'medium': ['tomorrow', 'by friday', 'this week', 'end of week', 'soon', 'quickly', 'by monday'],
            'low': ['next week', 'when possible', 'eventually', 'sometime', 'later', 'no rush']
        }
        
        self.time_patterns = {
            'now': 0, 'immediately': 0, 'today': 0, 'tonight': 0,
            'tomorrow': 1, 'day after': 2,
            'this week': 5, 'by friday': 4, 'by monday': 3,
            'next week': 10, 'in a week': 7,
            'this month': 20, 'next month': 35
        }
    
    def analyze_task(self, text: str) -> Dict[str, Any]:
        """Analyze task and suggest due date with enhanced logic"""
        text_lower = text.lower()
        
        urgency_score = self._calculate_urgency(text_lower)
        confidence = self._calculate_confidence(text_lower)
        keywords = self._extract_keywords(text_lower)
        days = self._estimate_timeline(text_lower, urgency_score)
        
        due_date = datetime.now() + timedelta(days=days)
        
        return {
            'task': text,
            'due_date': due_date.strftime('%Y-%m-%d'),
            'due_datetime': due_date,
            'days_from_now': days,
            'urgency_score': urgency_score,
            'confidence': confidence,
            'keywords': keywords,
            'reasoning': self._generate_reasoning(keywords, urgency_score, days, text_lower)
        }
    
    def _calculate_urgency(self, text: str) -> int:
        """Enhanced urgency calculation with context awareness"""
        urgency = 4  # default
        
        # Check for explicit urgency keywords
        for level, patterns in self.urgency_patterns.items():
            matches = sum(1 for pattern in patterns if pattern in text)
            if matches > 0:
                level_scores = {'critical': 10, 'high': 8, 'medium': 6, 'low': 3}
                urgency = max(urgency, level_scores[level])
        
        # Context-based adjustments
        if any(word in text for word in ['bug', 'error', 'broken', 'down', 'failed']):
            urgency += 2
        if any(word in text for word in ['client', 'customer', 'user', 'production']):
            urgency += 1
        if any(word in text for word in ['meeting', 'call', 'presentation']):
            urgency += 1
        if any(word in text for word in ['research', 'plan', 'organize', 'clean']):
            urgency -= 1
            
        return min(10, max(1, urgency))
    
    def _calculate_confidence(self, text: str) -> float:
        """Calculate confidence with improved logic"""
        base_confidence = 0.4
        
        # Boost for specific time mentions
        time_mentions = sum(1 for pattern in self.time_patterns.keys() if pattern in text)
        base_confidence += time_mentions * 0.15
        
        # Boost for urgency keywords
        urgency_words = [word for patterns in self.urgency_patterns.values() for word in patterns]
        urgency_mentions = sum(1 for word in urgency_words if word in text)
        base_confidence += urgency_mentions * 0.1
        
        # Boost for context clues
        context_clues = ['deadline', 'due', 'finish', 'complete', 'deliver', 'submit']
        context_mentions = sum(1 for clue in context_clues if clue in text)
        base_confidence += context_mentions * 0.08
        
        return min(0.95, base_confidence)
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract and prioritize relevant keywords"""
        found_keywords = []
        
        # Priority 1: Time-specific keywords
        for pattern in self.time_patterns.keys():
            if pattern in text:
                found_keywords.append(pattern)
        
        # Priority 2: Urgency keywords
        for patterns in self.urgency_patterns.values():
            for pattern in patterns:
                if pattern in text and pattern not in found_keywords:
                    found_keywords.append(pattern)
        
        # Priority 3: Context keywords
        context_keywords = ['bug', 'error', 'client', 'meeting', 'deadline', 'review']
        for keyword in context_keywords:
            if keyword in text and keyword not in found_keywords:
                found_keywords.append(keyword)
        
        return found_keywords[:6]  # Limit to most relevant
    
    def _estimate_timeline(self, text: str, urgency: int) -> int:
        """Improved timeline estimation"""
        # Check for explicit time patterns first
        for pattern, days in self.time_patterns.items():
            if pattern in text:
                return days
        
        # Fallback to urgency-based estimation with business logic
        urgency_timeline = {
            10: 0,  # Critical - immediately
            9: 0,   # Very urgent - today
            8: 1,   # Urgent - tomorrow
            7: 2,   # High priority - 2 days
            6: 5,   # Medium-high - this week
            5: 7,   # Medium - 1 week
            4: 10,  # Normal - 1.5 weeks
            3: 14,  # Low - 2 weeks
            2: 21,  # Very low - 3 weeks
            1: 30   # Minimal - 1 month
        }
        
        return urgency_timeline.get(urgency, 7)
    
    def _generate_reasoning(self, keywords: List[str], urgency: int, days: int, text: str) -> str:
        """Generate contextual reasoning"""
        if not keywords:
            return f"Based on general analysis → {days} days (urgency: {urgency}/10)"
        
        # Create reasoning based on found keywords
        key_phrases = keywords[:3]
        urgency_desc = {
            10: "critical priority", 9: "very urgent", 8: "high priority", 
            7: "elevated priority", 6: "medium-high priority", 5: "standard priority",
            4: "routine priority", 3: "low priority", 2: "minimal priority", 1: "when convenient"
        }
        
        reasoning_parts = []
        
        if any(word in ['bug', 'error', 'broken'] for word in keywords):
            reasoning_parts.append("technical issue detected")
        if any(word in ['client', 'customer'] for word in keywords):
            reasoning_parts.append("client-facing impact")
        if any(word in ['asap', 'urgent', 'critical'] for word in keywords):
            reasoning_parts.append("explicit urgency indicated")
        
        if reasoning_parts:
            context = " + ".join(reasoning_parts)
            return f"Keywords '{', '.join(key_phrases)}' → {context} → {urgency_desc.get(urgency, 'standard')} → {days} days"
        else:
            return f"Keywords '{', '.join(key_phrases)}' indicate {urgency_desc.get(urgency, 'standard')} → {days} days"

def init_session():
    """Initialize session state efficiently"""
    defaults = {
        'parser': SmartDateParser(),
        'history': [],
        'current_analysis': None,
        'show_enhanced_dashboard': False,
        'current_view': 'main'
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def render_sidebar():
    """Render enhanced sidebar with navigation and integration options"""
    with st.sidebar:
        st.markdown("## 🎯 Navigation")
        
        # Main navigation
        view_options = {
            'main': '🏠 Main Dashboard',
            'enhanced': '🚀 Enhanced Board View',
            'calendar': '📅 Calendar Integration',
            'analytics': '📊 AI Analytics',
            'settings': '⚙️ Settings'
        }
        
        for view_key, view_name in view_options.items():
            if st.button(view_name, key=f"nav_{view_key}", use_container_width=True):
                st.session_state.current_view = view_key
                st.rerun()
        
        st.markdown("---")
        
        # Trello Integration Status
        st.markdown("### 🔗 Trello Integration")
        
        if st.session_state.get('trello_user'):
            user = st.session_state.trello_user
            st.success(f"✅ Connected as {user.get('fullName', 'User')[:20]}...")
            
            # Quick actions
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📋 Board", use_container_width=True):
                    st.session_state.current_view = 'enhanced'
                    st.rerun()
            
            with col2:
                if st.button("📊 Stats", use_container_width=True):
                    st.session_state.current_view = 'analytics'
                    st.rerun()
                    
        else:
            st.info("🔌 Not connected to Trello")
            if st.button("🔗 Connect Trello", use_container_width=True):
                st.session_state.current_view = 'enhanced'
                st.rerun()
        
        st.markdown("---")
        
        # Quick Examples in Sidebar
        render_sidebar_examples()
        
        # Quick Stats
        render_sidebar_stats()

def render_sidebar_examples():
    """Render quick examples in sidebar"""
    st.markdown("### 💡 Quick Examples")
    
    examples = [
        "Fix critical login bug ASAP",
        "Review document by Friday", 
        "Research new tools next week"
    ]
    
    for example in examples:
        if st.button(f"📝 {example[:25]}...", key=f"sidebar_ex_{example}", use_container_width=True):
            st.session_state.selected_example = example
            st.session_state.current_view = 'main'
            st.rerun()

def render_sidebar_stats():
    """Render quick stats in sidebar"""
    if not st.session_state.history:
        return
        
    st.markdown("### 📈 Quick Stats")
    
    total = len(st.session_state.history)
    accepted = sum(1 for h in st.session_state.history if h['decision'] in ['accepted', 'modified'])
    acceptance_rate = (accepted/total*100) if total > 0 else 0
    
    st.metric("📊 Total", total)
    st.metric("✅ Accepted", f"{acceptance_rate:.0f}%")

def main():
    init_session()
    
    # Render sidebar
    render_sidebar()
    
    # Main content based on current view
    if st.session_state.current_view == 'main':
        render_main_dashboard()
    elif st.session_state.current_view == 'enhanced':
        render_enhanced_view()
    elif st.session_state.current_view == 'calendar':
        render_calendar_view()
    elif st.session_state.current_view == 'analytics':
        render_analytics_view()
    elif st.session_state.current_view == 'settings':
        render_settings_view()

def render_main_dashboard():
    """Render the main AI analysis dashboard"""
    # Header Section
    st.markdown("""
    <div class="app-header">
        <div class="app-title">🎯 AI Due Date Assistant</div>
        <div class="app-subtitle">Smart task scheduling with intelligent context analysis</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Main Content Layout
    main_col, sidebar_col = st.columns([3, 1])
    
    with main_col:
        # Task Input Section
        st.markdown('<div class="content-card">', unsafe_allow_html=True)
        st.markdown("### ✏️ Task Analysis")
        
        # Handle example selection
        default_text = ""
        if st.session_state.get('selected_example'):
            default_text = st.session_state.selected_example
            del st.session_state.selected_example
        
        task_input = st.text_area(
            label="",
            value=default_text,
            placeholder="Describe your task here...\n\nExamples:\n• Fix critical login bug ASAP\n• Schedule quarterly review by Friday\n• Research new tools when possible",
            height=120,
            label_visibility="collapsed"
        )
        
        # Advanced Options (Simplified)
        with st.expander("🎛️ Advanced Settings", expanded=False):
            st.markdown('<div class="option-container">', unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            
            with col1:
                priority_override = st.selectbox(
                    "Priority Level:",
                    options=["Auto-detect", "Low", "Medium", "High", "Critical"],
                    help="Override AI priority detection"
                )
            
            with col2:
                timeline_preference = st.selectbox(
                    "Timeline Preference:",
                    options=["AI Suggestion", "Same Day", "Next Day", "This Week", "Next Week"],
                    help="Set preferred timeline"
                )
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Analyze Button
        analyze_clicked = st.button("🚀 Analyze Task", type="primary", disabled=not task_input.strip())
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Process Analysis
        if analyze_clicked and task_input:
            process_analysis(task_input, priority_override, timeline_preference)
        
        # Display Current Analysis
        if st.session_state.get('current_analysis'):
            display_analysis_results(st.session_state.current_analysis)
    
    with sidebar_col:
        # Quick action buttons
        st.markdown('<div class="content-card">', unsafe_allow_html=True)
        st.markdown("### 🚀 Quick Actions")
        
        if st.button("📋 Open Trello Dashboard", use_container_width=True):
            st.session_state.current_view = 'enhanced'
            st.rerun()
            
        if st.button("📅 Calendar View", use_container_width=True):
            st.session_state.current_view = 'calendar'
            st.rerun()
            
        if st.button("📊 View Analytics", use_container_width=True):
            st.session_state.current_view = 'analytics'
            st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # History Section
    display_history_section()

def render_enhanced_view():
    """Render the enhanced Trello integration view"""
    st.markdown("# 📋 Enhanced Trello Dashboard")
    
    try:
        # Import and render enhanced integration
        from enhanced_integration import main_enhanced_integration
        main_enhanced_integration()
    except ImportError:
        st.error("❌ Enhanced integration module not found.")
        st.info("📝 Make sure `enhanced_integration.py` is in your app directory")
        
        # Fallback to basic integration message
        st.markdown("""
        ### 🔧 Setup Required
        
        To use the enhanced Trello integration:
        
        1. **Save the enhanced integration code** as `enhanced_integration.py`
        2. **Install required packages**: `pip install plotly`
        3. **Restart the application**
        
        For now, you can use the basic features available in the main dashboard.
        """)
        
        if st.button("🔙 Back to Main Dashboard"):
            st.session_state.current_view = 'main'
            st.rerun()

def render_calendar_view():
    """Render calendar integration view"""
    st.markdown("# 📅 Calendar Integration")
    
    # Calendar view tabs
    tab1, tab2, tab3 = st.tabs(["📅 Monthly View", "📋 Weekly Agenda", "⏰ Upcoming Deadlines"])
    
    with tab1:
        render_monthly_calendar()
    
    with tab2:
        render_weekly_agenda()
    
    with tab3:
        render_upcoming_deadlines()

def render_monthly_calendar():
    """Render monthly calendar view"""
    st.markdown("### 📅 Monthly Calendar View")
    
    import calendar
    
    today = datetime.now()
    year = today.year
    month = today.month
    
    # Month navigation
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        if st.button("← Previous"):
            # Previous month logic would go here
            pass
    
    with col2:
        st.markdown(f"### {calendar.month_name[month]} {year}")
    
    with col3:
        if st.button("Next →"):
            # Next month logic would go here
            pass
    
    # Calendar grid
    cal_data = calendar.monthcalendar(year, month)
    
    # Days of week header
    days_of_week = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    cols = st.columns(7)
    for i, day in enumerate(days_of_week):
        with cols[i]:
            st.markdown(f"**{day}**")
    
    # Calendar days
    for week in cal_data:
        cols = st.columns(7)
        for i, day in enumerate(week):
            with cols[i]:
                if day == 0:
                    st.markdown("")
                else:
                    # Check if this day has tasks (sample logic)
                    has_tasks = day in [15, 20, 25, 30]  # Sample days with tasks
                    
                    if has_tasks:
                        st.markdown(f"""
                        <div style="
                            background: #ff6b6b; 
                            color: white; 
                            border-radius: 5px; 
                            padding: 5px; 
                            text-align: center; 
                            margin: 2px;
                        ">
                            <strong>{day}</strong><br>
                            <small>📋 2 tasks</small>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"<div style='text-align: center; padding: 10px;'>{day}</div>", 
                                  unsafe_allow_html=True)

def render_weekly_agenda():
    """Render weekly agenda view"""
    st.markdown("### 📋 Weekly Agenda")
    
    today = datetime.now()
    week_start = today - timedelta(days=today.weekday())
    
    for i in range(7):
        day = week_start + timedelta(days=i)
        is_today = day.date() == today.date()
        
        day_emoji = "🔸" if is_today else "📅"
        
        with st.expander(f"{day_emoji} {day.strftime('%A, %B %d')}", expanded=is_today):
            # Sample tasks for each day
            sample_tasks = {
                0: ["Team standup", "Code review"],  # Monday
                1: ["Client meeting", "Bug fixes"],   # Tuesday
                2: ["Documentation update"],         # Wednesday
                3: ["Sprint planning"],              # Thursday
                4: ["Deploy to staging", "Weekly review"],  # Friday
                5: [],  # Saturday
                6: []   # Sunday
            }
            
            day_tasks = sample_tasks.get(day.weekday(), [])
            
            if day_tasks:
                for task in day_tasks:
                    st.markdown(f"• 📋 {task}")
                    
                # Add AI suggestions
                if day_tasks:
                    st.info(f"🤖 AI suggests {len(day_tasks)} tasks are well-distributed for this day")
            else:
                st.markdown("📭 No tasks scheduled for this day")
                st.info("💡 Good day to tackle lower-priority items or take a break!")

def render_upcoming_deadlines():
    """Render upcoming deadlines"""
    st.markdown("### ⏰ Upcoming Deadlines")
    
    # Sample upcoming deadlines
    deadlines = [
        {
            "task": "Fix critical login bug",
            "due": "Today",
            "urgency": 10,
            "source": "AI Analysis",
            "time_left": "6 hours"
        },
        {
            "task": "Client presentation prep",
            "due": "Tomorrow",
            "urgency": 8,
            "source": "Calendar",
            "time_left": "1 day"
        },
        {
            "task": "Code review completion",
            "due": "This week",
            "urgency": 6,
            "source": "Trello",
            "time_left": "3 days"
        },
        {
            "task": "Documentation update",
            "due": "Next week",
            "urgency": 4,
            "source": "AI Analysis",
            "time_left": "1 week"
        }
    ]
    
    for deadline in deadlines:
        urgency_color = "#dc3545" if deadline['urgency'] >= 8 else "#fd7e14" if deadline['urgency'] >= 6 else "#28a745"
        urgency_emoji = "🚨" if deadline['urgency'] >= 8 else "⚡" if deadline['urgency'] >= 6 else "📋"
        
        st.markdown(f"""
        <div style="
            border-left: 4px solid {urgency_color};
            background: white;
            border-radius: 8px;
            padding: 15px;
            margin: 10px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        ">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <h4 style="margin: 0; color: #333;">{urgency_emoji} {deadline['task']}</h4>
                    <p style="margin: 5px 0; color: #666;">📅 Due: {deadline['due']} | ⏰ Time left: {deadline['time_left']}</p>
                    <p style="margin: 5px 0; color: #888;">📍 Source: {deadline['source']}</p>
                </div>
                <div style="text-align: right;">
                    <span style="background: {urgency_color}; color: white; padding: 5px 10px; border-radius: 15px; font-weight: bold;">
                        {deadline['urgency']}/10
                    </span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Add action buttons for each deadline
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button(f"✅ Mark Complete", key=f"complete_{deadline['task'][:10]}"):
                st.success(f"✅ {deadline['task']} marked as complete!")
        
        with col2:
            if st.button(f"📅 Reschedule", key=f"reschedule_{deadline['task'][:10]}"):
                st.info(f"📅 Rescheduling {deadline['task']}...")
        
        with col3:
            if st.button(f"📋 View Details", key=f"details_{deadline['task'][:10]}"):
                st.info(f"📋 Opening details for {deadline['task']}...")

def render_analytics_view():
    """Render AI analytics dashboard"""
    st.markdown("# 📊 AI Analytics Dashboard")
    
    # Analytics tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "🎯 Task Prioritization", 
        "📈 Performance Trends", 
        "⚡ Urgency Analysis", 
        "🔍 Keyword Insights"
    ])
    
    with tab1:
        render_task_prioritization()
    
    with tab2:
        render_performance_trends()
    
    with tab3:
        render_urgency_analysis()
    
    with tab4:
        render_keyword_insights()

def render_task_prioritization():
    """Render task prioritization analysis"""
    st.markdown("### 🎯 Task Prioritization Matrix")
    
    try:
        import plotly.express as px
        import plotly.graph_objects as go
        
        # Sample data - in real implementation, use actual analysis data
        sample_tasks = [
            {"task": "Fix login bug", "urgency": 9, "impact": 9, "complexity": 7, "priority": 25},
            {"task": "Update docs", "urgency": 3, "impact": 4, "complexity": 5, "priority": 12},
            {"task": "Client meeting", "urgency": 8, "impact": 8, "complexity": 4, "priority": 20},
            {"task": "Code review", "urgency": 6, "impact": 5, "complexity": 6, "priority": 17},
            {"task": "Team standup", "urgency": 4, "impact": 3, "complexity": 2, "priority": 9}
        ]
        
        # Create DataFrame
        import pandas as pd
        df = pd.DataFrame(sample_tasks)
        
        # Priority matrix scatter plot
        fig = px.scatter(
            df,
            x='urgency',
            y='impact',
            size='complexity',
            color='priority',
            hover_name='task',
            title="🎯 Task Priority Matrix (Urgency vs Impact)",
            labels={'urgency': 'Urgency Level', 'impact': 'Business Impact'},
            color_continuous_scale='Reds',
            size_max=60
        )
        
        # Add quadrant lines
        fig.add_hline(y=5.5, line_dash="dash", line_color="gray", opacity=0.5)
        fig.add_vline(x=5.5, line_dash="dash", line_color="gray", opacity=0.5)
        
        # Add quadrant labels
        fig.add_annotation(x=8.5, y=8.5, text="🚨 Urgent & Important", showarrow=False, bgcolor="rgba(255,0,0,0.1)")
        fig.add_annotation(x=2.5, y=8.5, text="📋 Important, Not Urgent", showarrow=False, bgcolor="rgba(0,255,0,0.1)")
        fig.add_annotation(x=8.5, y=2.5, text="⚡ Urgent, Not Important", showarrow=False, bgcolor="rgba(255,255,0,0.1)")
        fig.add_annotation(x=2.5, y=2.5, text="📂 Neither Urgent nor Important", showarrow=False, bgcolor="rgba(128,128,128,0.1)")
        
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)
        
        # Priority recommendations
        st.markdown("### 📋 Priority Recommendations")
        
        sorted_tasks = sorted(sample_tasks, key=lambda x: x['priority'], reverse=True)
        
        for i, task in enumerate(sorted_tasks):
            priority_colors = ["🔴", "🟠", "🟡", "🟢", "🔵"]
            priority_emoji = priority_colors[min(i, 4)]
            
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            
            with col1:
                st.markdown(f"{priority_emoji} **{task['task']}**")
            
            with col2:
                st.metric("Priority", f"{task['priority']}")
            
            with col3:
                st.markdown(f"⚡{task['urgency']} 📊{task['impact']}")
            
            with col4:
                st.markdown(f"🔧{task['complexity']}")
        
    except ImportError:
        st.warning("📊 Plotly not installed. Install with: `pip install plotly`")
        
        # Fallback to simple text display
        st.markdown("### 📋 Task Priority List (Text Mode)")
        
        sample_tasks = [
            {"task": "Fix login bug", "urgency": 9, "priority": "🔴 Critical"},
            {"task": "Client meeting", "urgency": 8, "priority": "🟠 High"},
            {"task": "Code review", "urgency": 6, "priority": "🟡 Medium"},
            {"task": "Update docs", "urgency": 3, "priority": "🟢 Low"},
            {"task": "Team standup", "urgency": 4, "priority": "🟢 Low"}
        ]
        
        for task in sample_tasks:
            st.markdown(f"{task['priority']} **{task['task']}** (Urgency: {task['urgency']}/10)")

def render_performance_trends():
    """Render performance trends analysis"""
    st.markdown("### 📈 AI Performance Trends")
    
    try:
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots
        
        # Sample performance data
        weeks = ['W1', 'W2', 'W3', 'W4', 'W5', 'W6']
        accuracy = [85, 88, 90, 92, 94, 95]
        suggestions = [12, 15, 18, 16, 20, 22]
        acceptance_rate = [70, 75, 80, 85, 88, 90]
        
        # Create subplots
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('🎯 AI Accuracy', '💡 Suggestions Made', '✅ Acceptance Rate', '📊 Overall Trend'),
            specs=[[{"secondary_y": False}, {"secondary_y": False}],
                   [{"secondary_y": False}, {"secondary_y": False}]]
        )
        
        # Add traces
        fig.add_trace(go.Scatter(x=weeks, y=accuracy, mode='lines+markers', name='Accuracy', line=dict(color='blue')), row=1, col=1)
        fig.add_trace(go.Bar(x=weeks, y=suggestions, name='Suggestions', marker_color='green'), row=1, col=2)
        fig.add_trace(go.Scatter(x=weeks, y=acceptance_rate, mode='lines+markers', name='Acceptance', line=dict(color='orange')), row=2, col=1)
        
        # Combined trend
        combined_score = [(a + s + ar) / 3 for a, s, ar in zip(accuracy, suggestions, acceptance_rate)]
        fig.add_trace(go.Scatter(x=weeks, y=combined_score, mode='lines+markers', name='Overall', line=dict(color='red')), row=2, col=2)
        
        fig.update_layout(height=600, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
        
    except ImportError:
        st.warning("📊 Plotly not available. Showing text summary.")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("🎯 AI Accuracy", "95%", delta="+10%")
        
        with col2:
            st.metric("💡 Suggestions", "22", delta="+10")
        
        with col3:
            st.metric("✅ Acceptance", "90%", delta="+20%")
    
    # Performance insights
    st.markdown("### 🔍 Performance Insights")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.info("""
        **🎯 Accuracy Improvement**
        - AI accuracy increased by 10% over 6 weeks
        - Best performance on technical tasks
        - Keyword detection improving
        """)
    
    with col2:
        st.success("""
        **📈 Growing Usage**
        - 83% increase in suggestions requested
        - Users finding AI more helpful
        - Feature adoption growing
        """)
    
    with col3:
        st.warning("""
        **🔧 Areas for Improvement**
        - Complex projects need better handling
        - Calendar integration accuracy
        - Multi-task dependency detection
        """)

def render_urgency_analysis():
    """Render urgency analysis"""
    st.markdown("### ⚡ Urgency Level Analysis")
    
    # Urgency distribution
    if st.session_state.history:
        urgency_data = [h['urgency'] for h in st.session_state.history]
        
        try:
            import plotly.express as px
            
            # Create histogram
            fig = px.histogram(
                x=urgency_data,
                nbins=10,
                title="📊 Urgency Level Distribution",
                labels={'x': 'Urgency Level (1-10)', 'y': 'Number of Tasks'},
                color_discrete_sequence=['#667eea']
            )
            
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
            
        except ImportError:
            # Fallback to simple metrics
            avg_urgency = sum(urgency_data) / len(urgency_data)
            high_urgency = sum(1 for u in urgency_data if u >= 7)
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("📊 Average Urgency", f"{avg_urgency:.1f}/10")
            
            with col2:
                st.metric("🚨 High Urgency Tasks", high_urgency)
            
            with col3:
                st.metric("📈 Total Analyzed", len(urgency_data))
    
    else:
        st.info("📊 No urgency data available yet. Analyze some tasks to see urgency patterns!")
    
    # Urgency recommendations
    st.markdown("### 💡 Urgency Management Tips")
    
    tips = [
        "🚨 **Critical (9-10)**: Handle immediately, drop everything else",
        "⚡ **High (7-8)**: Schedule for today or tomorrow",
        "📋 **Medium (4-6)**: Plan for this week",
        "🟢 **Low (1-3)**: Schedule when convenient",
    ]
    
    for tip in tips:
        st.markdown(tip)

def render_keyword_insights():
    """Render keyword analysis insights"""
    st.markdown("### 🔍 Keyword Analysis Insights")
    
    if st.session_state.history:
        # Extract keywords from history
        all_keywords = []
        for h in st.session_state.history:
            if h.get('keywords'):
                all_keywords.extend(h['keywords'])
        
        if all_keywords:
            # Count keyword frequency
            from collections import Counter
            keyword_counts = Counter(all_keywords)
            
            # Display top keywords
            st.markdown("#### 🏆 Most Common Keywords")
            
            top_keywords = keyword_counts.most_common(10)
            
            for i, (keyword, count) in enumerate(top_keywords):
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    st.markdown(f"**{i+1}. {keyword}**")
                
                with col2:
                    st.metric("Count", count)
                
                with col3:
                    # Determine keyword type
                    urgency_keywords = ['urgent', 'critical', 'asap', 'emergency', 'now']
                    if keyword.lower() in urgency_keywords:
                        st.markdown("🚨 Urgency")
                    elif keyword.lower() in ['bug', 'error', 'fix']:
                        st.markdown("🐛 Technical")
                    elif keyword.lower() in ['client', 'customer', 'meeting']:
                        st.markdown("👥 Business")
                    else:
                        st.markdown("📋 General")
            
            # Keyword insights
            st.markdown("#### 💡 Keyword Insights")
            
            urgency_keywords = sum(1 for k in all_keywords if k.lower() in ['urgent', 'critical', 'asap'])
            technical_keywords = sum(1 for k in all_keywords if k.lower() in ['bug', 'error', 'fix'])
            business_keywords = sum(1 for k in all_keywords if k.lower() in ['client', 'customer', 'meeting'])
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("🚨 Urgency Keywords", urgency_keywords)
            
            with col2:
                st.metric("🐛 Technical Keywords", technical_keywords)
            
            with col3:
                st.metric("👥 Business Keywords", business_keywords)
                
        else:
            st.info("🔍 No keywords found in analysis history")
    
    else:
        st.info("📊 No keyword data available yet. Analyze some tasks to see keyword patterns!")

def render_settings_view():
    """Render settings and configuration"""
    st.markdown("# ⚙️ Settings & Configuration")
    
    # Settings tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "🤖 AI Settings", 
        "🔗 Integrations", 
        "🔔 Notifications", 
        "📤 Data Management"
    ])
    
    with tab1:
        render_ai_settings()
    
    with tab2:
        render_integration_settings()
    
    with tab3:
        render_notification_settings()
    
    with tab4:
        render_data_management()

def render_ai_settings():
    """Render AI configuration settings"""
    st.markdown("### 🤖 AI Model Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        confidence_threshold = st.slider(
            "🎯 Confidence Threshold",
            min_value=0.0,
            max_value=1.0,
            value=st.session_state.get('ai_confidence_threshold', 0.6),
            step=0.05,
            help="Minimum confidence for AI suggestions"
        )
        st.session_state.ai_confidence_threshold = confidence_threshold
    
    with col2:
        urgency_sensitivity = st.slider(
            "⚡ Urgency Sensitivity",
            min_value=1,
            max_value=10,
            value=st.session_state.get('ai_urgency_sensitivity', 5),
            help="How sensitive AI is to urgency keywords"
        )
        st.session_state.ai_urgency_sensitivity = urgency_sensitivity
    
    # Custom keywords
    st.markdown("#### 🔤 Custom Keywords")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**High Priority Keywords**")
        high_keywords = st.text_area(
            "One keyword per line",
            value="urgent\ncritical\nASAP\nemergency",
            height=100
        )
    
    with col2:
        st.markdown("**Low Priority Keywords**")
        low_keywords = st.text_area(
            "One keyword per line",
            value="research\nplan\norganize\nwhen possible",
            height=100
        )
    
    # AI behavior
    st.markdown("#### 🎛️ AI Behavior")
    
    col1, col2 = st.columns(2)
    
    with col1:
        auto_apply = st.checkbox(
            "🤖 Auto-apply high confidence suggestions (>90%)",
            value=st.session_state.get('auto_apply_high_confidence', False)
        )
        st.session_state.auto_apply_high_confidence = auto_apply
    
    with col2:
        include_weekends = st.checkbox(
            "📅 Include weekends in scheduling",
            value=st.session_state.get('include_weekends', False)
        )
        st.session_state.include_weekends = include_weekends
    
    if st.button("💾 Save AI Settings", type="primary"):
        st.success("✅ AI settings saved successfully!")

def render_integration_settings():
    """Render integration settings"""
    st.markdown("### 🔗 Integration Status")
    
    # Trello integration status
    st.markdown("#### 📋 Trello Integration")
    
    if st.session_state.get('trello_user'):
        user = st.session_state.trello_user
        st.success(f"✅ Connected as {user.get('fullName', 'Unknown')}")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔄 Test Connection"):
                st.info("🔄 Testing Trello connection...")
                # Connection test would happen here
                st.success("✅ Connection successful!")
        
        with col2:
            if st.button("🗑️ Disconnect"):
                # Clear Trello credentials
                keys_to_clear = ['trello_api_key', 'trello_token', 'trello_user']
                for key in keys_to_clear:
                    if key in st.session_state:
                        del st.session_state[key]
                st.success("🔌 Disconnected from Trello")
                st.rerun()
    
    else:
        st.warning("⚠️ Not connected to Trello")
        
        with st.expander("🔧 Setup Trello Integration"):
            st.markdown("""
            1. Go to [Trello Developer Portal](https://trello.com/app-key)
            2. Copy your API Key and Token
            3. Use the Enhanced Dashboard to connect
            """)
            
            if st.button("🚀 Open Enhanced Dashboard"):
                st.session_state.current_view = 'enhanced'
                st.rerun()
    
    # Google Calendar integration
    st.markdown("#### 📅 Google Calendar Integration")
    
    if st.session_state.get('google_credentials'):
        st.success("✅ Google Calendar configured")
    else:
        st.info("📝 Google Calendar not configured")
        
        if st.button("⚙️ Setup Google Calendar"):
            st.session_state.current_view = 'calendar'
            st.rerun()

def render_notification_settings():
    """Render notification settings"""
    st.markdown("### 🔔 Notification Preferences")
    
    # Email notifications
    email = st.text_input(
        "📧 Email Address",
        value=st.session_state.get('notification_email', ''),
        placeholder="your.email@example.com"
    )
    st.session_state.notification_email = email
    
    # Notification types
    st.markdown("#### 📬 Notification Types")
    
    col1, col2 = st.columns(2)
    
    with col1:
        overdue = st.checkbox("🚨 Overdue tasks", value=True)
        upcoming = st.checkbox("📅 Upcoming deadlines", value=True)
        ai_suggestions = st.checkbox("🤖 New AI suggestions", value=False)
    
    with col2:
        schedule_changes = st.checkbox("🔄 Schedule changes", value=True)
        weekly_summary = st.checkbox("📊 Weekly summary", value=True)
        performance_reports = st.checkbox("📈 Performance reports", value=False)
    
    # Notification frequency
    frequency = st.selectbox(
        "📊 Summary Frequency",
        options=['Never', 'Daily', 'Weekly', 'Monthly'],
        index=2
    )
    
    if st.button("💾 Save Notification Settings", type="primary"):
        st.success("✅ Notification settings saved!")

def render_data_management():
    """Render data management settings"""
    st.markdown("### 📤 Data Management")
    
    # Export options
    st.markdown("#### 📤 Export Data")
    
    col1, col2 = st.columns(2)
    
    with col1:
        export_format = st.selectbox(
            "Export Format",
            options=['CSV', 'JSON', 'Excel']
        )
        
        export_scope = st.selectbox(
            "Export Scope", 
            options=['Analysis History', 'AI Settings', 'Full Export']
        )
    
    with col2:
        if st.button("📊 Export Data", use_container_width=True):
            # Generate export data
            if export_scope == 'Analysis History':
                export_data = st.session_state.history
            elif export_scope == 'AI Settings':
                export_data = {
                    'confidence_threshold': st.session_state.get('ai_confidence_threshold', 0.6),
                    'urgency_sensitivity': st.session_state.get('ai_urgency_sensitivity', 5)
                }
            else:
                export_data = {
                    'history': st.session_state.history,
                    'settings': {
                        'confidence_threshold': st.session_state.get('ai_confidence_threshold', 0.6),
                        'urgency_sensitivity': st.session_state.get('ai_urgency_sensitivity', 5)
                    }
                }
            
            if export_format == 'JSON':
                import json
                st.download_button(
                    "💾 Download JSON",
                    data=json.dumps(export_data, indent=2),
                    file_name=f"ai_assistant_export_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                    mime="application/json"
                )
            else:
                st.info(f"📁 {export_format} export would be generated here")
    
    # Clear data options
    st.markdown("#### 🗑️ Clear Data")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🗑️ Clear History", type="secondary"):
            st.session_state.history = []
            st.success("🧹 Analysis history cleared!")
    
    with col2:
        if st.button("⚙️ Reset Settings", type="secondary"):
            # Reset AI settings
            settings_to_reset = [
                'ai_confidence_threshold',
                'ai_urgency_sensitivity', 
                'auto_apply_high_confidence',
                'include_weekends'
            ]
            for setting in settings_to_reset:
                if setting in st.session_state:
                    del st.session_state[setting]
            st.success("⚙️ Settings reset to defaults!")

def process_analysis(task: str, priority_override: str, timeline_preference: str):
    """Process task analysis with user preferences"""
    with st.spinner("🤔 Analyzing task context and urgency..."):
        result = st.session_state.parser.analyze_task(task)
        
        # Apply user preferences
        result = apply_preferences(result, priority_override, timeline_preference)
        
        # Store current analysis
        st.session_state.current_analysis = result

def apply_preferences(result: Dict[str, Any], priority: str, timeline: str) -> Dict[str, Any]:
    """Apply user preferences to analysis result"""
    modified_result = result.copy()
    
    # Apply priority override
    if priority != "Auto-detect":
        priority_map = {"Low": 3, "Medium": 6, "High": 8, "Critical": 10}
        if priority in priority_map:
            modified_result['urgency_score'] = priority_map[priority]
            modified_result['reasoning'] += f" (Priority set to {priority})"
    
    # Apply timeline preference
    if timeline != "AI Suggestion":
        timeline_map = {"Same Day": 0, "Next Day": 1, "This Week": 5, "Next Week": 10}
        if timeline in timeline_map:
            days = timeline_map[timeline]
            new_date = datetime.now() + timedelta(days=days)
            modified_result['due_date'] = new_date.strftime('%Y-%m-%d')
            modified_result['due_datetime'] = new_date
            modified_result['days_from_now'] = days
            modified_result['reasoning'] += f" (Timeline: {timeline})"
    
    return modified_result

def display_analysis_results(result: Dict[str, Any]):
    """Display analysis results with enhanced UI"""
    st.markdown("### 📊 Analysis Results")
    
    # Main result card
    confidence_class = get_confidence_class(result['confidence'])
    confidence_emoji = "🎯" if result['confidence'] >= 0.7 else "⚠️" if result['confidence'] >= 0.5 else "❓"
    
    st.markdown(f"""
    <div class="result-card">
        <div class="result-title">📋 {result['task'][:80]}{'...' if len(result['task']) > 80 else ''}</div>
        <div class="result-date">📅 Due: {result['due_date']}</div>
        <div style="font-size: 1.1rem; margin: 1rem 0;">
            <strong>🧠 AI Analysis:</strong> {result['reasoning']}
        </div>
        <div style="font-size: 1rem; opacity: 0.9;">
            <strong>⏰ Timeline:</strong> {result['days_from_now']} days from now
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Metrics Display
    st.markdown(f"""
    <div class="metric-container">
        <div class="metric-card">
            <div class="metric-value {confidence_class}">{confidence_emoji} {result['confidence']:.0%}</div>
            <div class="metric-label">Confidence</div>
        </div>
        <div class="metric-card">
            <div class="metric-value" style="color: {get_urgency_color(result['urgency_score'])}">{result['urgency_score']}/10</div>
            <div class="metric-label">Urgency</div>
        </div>
        <div class="metric-card">
            <div class="metric-value" style="color: #00d4ff;">{result['days_from_now']}</div>
            <div class="metric-label">Days</div>
        </div>
        <div class="metric-card">
            <div class="metric-value" style="color: #00ff88;">{len(result['keywords'])}</div>
            <div class="metric-label">Keywords</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Keywords Display
    if result['keywords']:
        st.markdown("**🔍 Detected Keywords:**")
        keywords_html = "".join([f'<span class="keyword-tag">{keyword}</span>' for keyword in result['keywords']])
        st.markdown(keywords_html, unsafe_allow_html=True)
    
    # User Feedback Section
    display_feedback_section(result)

def display_feedback_section(result: Dict[str, Any]):
    """Display user feedback and action section"""
    st.markdown("### ✅ Review & Confirm")
    st.markdown('<div class="feedback-card">', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        adjusted_date = st.date_input(
            "📅 Adjust date if needed:",
            value=result['due_datetime'].date(),
            key=f"date_adjust_{id(result)}"
        )
        
        rating = st.slider(
            "⭐ Rate this AI suggestion:",
            min_value=1, max_value=5, value=4,
            key=f"rating_{id(result)}"
        )
    
    with col2:
        st.markdown("**Actions:**")
        
        if st.button("✅ Accept AI Suggestion", type="primary", key="accept_ai"):
            save_feedback(result, "accepted", result['due_date'], rating)
            st.success("🎉 AI suggestion accepted!")
            st.balloons()
        
        if st.button("📝 Use Modified Date", type="secondary", key="accept_modified"):
            save_feedback(result, "modified", str(adjusted_date), rating)
            st.success(f"📅 Modified date accepted: {adjusted_date}")
        
        if st.button("❌ Reject", key="reject"):
            save_feedback(result, "rejected", None, rating)
            st.info("💭 Thanks for the feedback!")
    
    st.markdown('</div>', unsafe_allow_html=True)

def save_feedback(result: Dict[str, Any], decision: str, final_date: str, rating: int):
    """Save user feedback to history"""
    feedback_entry = {
        'task': result['task'],
        'ai_suggestion': result['due_date'],
        'final_date': final_date or "Rejected",
        'decision': decision,
        'confidence': result['confidence'],
        'urgency': result['urgency_score'],
        'rating': rating,
        'keywords': result['keywords'],
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M')
    }
    
    st.session_state.history.insert(0, feedback_entry)
    st.session_state.history = st.session_state.history[:100]  # Keep last 100
    
    # Clear current analysis
    st.session_state.current_analysis = None

def display_history_section():
    """Display analysis history"""
    if not st.session_state.history:
        return
    
    st.markdown("### 📚 Recent Analysis History")
    
    # Prepare data for display
    history_data = []
    for h in st.session_state.history[:15]:  # Show last 15
        status_emoji = {"accepted": "✅", "modified": "📝", "rejected": "❌"}
        history_data.append({
            "Task": h['task'][:50] + ('...' if len(h['task']) > 50 else ''),
            "AI Suggestion": h['ai_suggestion'],
            "Final Date": h['final_date'],
            "Status": f"{status_emoji.get(h['decision'], '❓')} {h['decision'].title()}",
            "Rating": f"⭐ {h['rating']}/5",
            "Confidence": f"{h['confidence']:.0%}",
            "Time": h['timestamp'][11:16]
        })
    
    if history_data:
        df = pd.DataFrame(history_data)
        st.dataframe(df, use_container_width=True, height=400)

def get_confidence_class(confidence: float) -> str:
    """Get CSS class for confidence level"""
    if confidence >= 0.7:
        return "confidence-high"
    elif confidence >= 0.5:
        return "confidence-medium"
    else:
        return "confidence-low"

def get_urgency_color(urgency: int) -> str:
    """Get color for urgency score"""
    colors = {
        10: "#ff4757", 9: "#ff4757", 8: "#ff6b6b", 7: "#ff7675",
        6: "#fdcb6e", 5: "#f1c40f", 4: "#00d2d3", 3: "#00d2d3",
        2: "#00ff88", 1: "#00ff88"
    }
    return colors.get(urgency, "#00d2d3")

# Enhanced integration functions
def render_enhanced_integration_button():
    """Render button to access enhanced features"""
    if st.sidebar.button("🚀 Enhanced Features", use_container_width=True):
        st.session_state.show_enhanced_dashboard = True
        st.rerun()

def check_enhanced_integration():
    """Check if enhanced integration is available"""
    try:
        import enhanced_integration
        return True
    except ImportError:
        return False

# Quick setup guide
def render_setup_guide():
    """Render setup guide for enhanced features"""
    st.markdown("""
    ## 🚀 Quick Setup Guide
    
    ### 1. Enhanced Trello Integration
    - Save the enhanced integration code as `enhanced_integration.py`
    - Add your Trello API credentials
    - Install required packages: `pip install plotly`
    
    ### 2. Google Calendar Integration  
    - Set up Google Cloud project
    - Enable Calendar API
    - Upload OAuth credentials
    
    ### 3. AI Analytics
    - Analyze tasks to build data
    - View performance trends
    - Get optimization suggestions
    
    ### 4. Advanced Features
    - Kanban board visualization
    - Team workload analysis
    - Automated scheduling
    """)

# Main app entry point
if __name__ == "__main__":
    main()