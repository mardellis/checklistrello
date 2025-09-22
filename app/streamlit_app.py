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
    initial_sidebar_state="collapsed"
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
    
    /* Example buttons */
    .example-btn {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.75rem 1rem;
        margin: 0.25rem;
        cursor: pointer;
        font-weight: 500;
        font-size: 0.9rem;
        transition: all 0.3s ease;
        width: 100%;
        text-align: left;
    }
    
    .example-btn:hover {
        transform: translateY(-1px);
        box-shadow: 0 8px 25px rgba(17, 153, 142, 0.3);
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
    
    /* History table */
    .stDataFrame {
        border-radius: 15px !important;
        overflow: hidden !important;
        box-shadow: 0 10px 40px rgba(0,0,0,0.1) !important;
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
    
    /* Remove default streamlit styling */
    .block-container { 
        padding-top: 1rem;
        max-width: none;
    }
    
    /* Sidebar styling */
    .css-1d391kg { 
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(20px);
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
        'current_analysis': None
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def main():
    init_session()
    
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
        
        task_input = st.text_area(
            label="",
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
        
        # Handle example selection
        if hasattr(st.session_state, 'selected_example'):
            task_input = st.session_state.selected_example
            del st.session_state.selected_example
            st.rerun()
        
        # Process Analysis
        if analyze_clicked and task_input:
            process_analysis(task_input, priority_override, timeline_preference)
        
        # Display Current Analysis
        if st.session_state.get('current_analysis'):
            display_analysis_results(st.session_state.current_analysis)
    
    with sidebar_col:
        # Quick Examples
        st.markdown('<div class="content-card">', unsafe_allow_html=True)
        st.markdown("### 💡 Quick Examples")
        
        examples = {
            "🔴 Critical": [
                "Server is down fix immediately",
                "Critical bug in production ASAP",
                "Emergency client call needed"
            ],
            "🟡 Medium": [
                "Review document by Friday",
                "Update project status this week",
                "Schedule team meeting soon"
            ],
            "🟢 Low": [
                "Research new tools",
                "Organize project files",
                "Plan next quarter when possible"
            ]
        }
        
        for category, example_list in examples.items():
            st.markdown(f"**{category}**")
            for example in example_list:
                if st.button(f"📝 {example}", key=f"ex_{example}", help="Click to analyze"):
                    st.session_state.selected_example = example
                    st.rerun()
            st.markdown("")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Quick Stats
        display_quick_stats()
    
    # History Section
    display_history_section()

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

def display_quick_stats():
    """Display quick statistics in sidebar"""
    if not st.session_state.history:
        return
    
    st.markdown('<div class="content-card">', unsafe_allow_html=True)
    st.markdown("### 📈 Quick Stats")
    
    total = len(st.session_state.history)
    accepted = sum(1 for h in st.session_state.history if h['decision'] in ['accepted', 'modified'])
    avg_rating = sum(h['rating'] for h in st.session_state.history) / total if total > 0 else 0
    avg_confidence = sum(h['confidence'] for h in st.session_state.history) / total if total > 0 else 0
    
    st.metric("📊 Total Analyses", total)
    st.metric("✅ Acceptance Rate", f"{(accepted/total*100) if total > 0 else 0:.0f}%")
    st.metric("⭐ Avg Rating", f"{avg_rating:.1f}/5")
    st.metric("🎯 Avg Confidence", f"{avg_confidence:.0%}")
    
    if st.button("🗑️ Clear History", help="Clear all history"):
        st.session_state.history = []
        st.success("History cleared!")
        st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

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

# At the top with other imports
from trello_integration import integrate_trello_to_main_app as integrate_trello_calendar_to_app

# In your main() function, add:
if st.session_state.get('show_integrations', False):
    integrate_trello_calendar_to_app()

# Add a button to show/hide integrations
if st.button("🔗 Toggle Trello/Calendar Integration"):
    st.session_state.show_integrations = not st.session_state.get('show_integrations', False)
    st.rerun()
    
if __name__ == "__main__":
    main()