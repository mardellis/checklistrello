import streamlit as st
import sys
from datetime import datetime, timedelta
import pandas as pd
import json
import logging
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import our modules with error handling
try:
    from ai_parser import AdvancedAIDateParser
except ImportError:
    logger.warning("ai_parser not available, using fallback")
    AdvancedAIDateParser = None

try:
    from trello_integration import integrate_trello_to_main_app
except ImportError:
    logger.warning("trello_integration not available")
    integrate_trello_to_main_app = None

try:
    from database import DatabaseManager
    from dashboard import integrate_dashboard_to_main_app
except ImportError:
    logger.warning("database/dashboard modules not available")
    DatabaseManager = None
    integrate_dashboard_to_main_app = None

# Configure page
st.set_page_config(
    page_title="AI Checklist Due Dates",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better aesthetics
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    
    .suggestion-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 15px;
        color: white;
        margin: 1rem 0;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        border: 1px solid rgba(255,255,255,0.1);
    }
    
    .metric-card {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        box-shadow: 0 4px 16px rgba(0,0,0,0.1);
        margin: 0.5rem 0;
    }
    
    .confidence-high { 
        color: #28a745; 
        font-weight: bold; 
        font-size: 1.2rem;
    }
    .confidence-medium { 
        color: #ffc107; 
        font-weight: bold; 
        font-size: 1.2rem;
    }
    .confidence-low { 
        color: #dc3545; 
        font-weight: bold; 
        font-size: 1.2rem;
    }
    
    .example-button {
        margin: 0.25rem 0;
        width: 100%;
    }
    
    .status-approved { color: #28a745; font-weight: bold; }
    .status-pending { color: #ffc107; font-weight: bold; }
    .status-rejected { color: #dc3545; font-weight: bold; }
    
    .feature-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 4px 16px rgba(0,0,0,0.05);
        border-left: 4px solid #1f77b4;
        margin: 1rem 0;
    }
    
    .stDataFrame {
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 4px 16px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

class SimpleAIParser:
    """Fallback AI parser if advanced version not available"""
    
    def __init__(self):
        self.today = datetime.now().date()
        
    def suggest_due_date(self, text: str) -> Dict[str, Any]:
        """Simple rule-based date suggestion"""
        text_lower = text.lower()
        
        # Simple keyword detection
        if any(word in text_lower for word in ['asap', 'urgent', 'critical', 'emergency']):
            days = 0
            urgency = 10
            confidence = 0.8
        elif any(word in text_lower for word in ['today', 'now']):
            days = 0
            urgency = 9
            confidence = 0.9
        elif any(word in text_lower for word in ['tomorrow']):
            days = 1
            urgency = 8
            confidence = 0.9
        elif any(word in text_lower for word in ['week', 'friday']):
            days = 7
            urgency = 6
            confidence = 0.7
        else:
            days = 7
            urgency = 5
            confidence = 0.3
        
        suggested_date = datetime.now() + timedelta(days=days)
        
        return {
            'suggested_date': suggested_date.strftime('%Y-%m-%d'),
            'suggested_datetime': suggested_date,
            'confidence': confidence,
            'reasoning': f'Simple analysis suggests {days} days based on keywords',
            'urgency_score': urgency,
            'keywords_found': [],
            'days_from_now': days
        }

def main():
    # Header with animation
    st.markdown("""
    <div class="main-header">
        🤖 AI Checklist Due Dates
        <div style="font-size: 1rem; font-weight: 400; color: #666; margin-top: 0.5rem;">
            Intelligent task scheduling powered by AI analysis
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Initialize components with error handling
    try:
        if 'ai_parser' not in st.session_state:
            if AdvancedAIDateParser:
                st.session_state.ai_parser = AdvancedAIDateParser()
            else:
                st.session_state.ai_parser = SimpleAIParser()
        
        if DatabaseManager and 'db_manager' not in st.session_state:
            st.session_state.db_manager = DatabaseManager()
    except Exception as e:
        logger.error(f"Component initialization error: {e}")
        st.error(f"⚠️ Some features may be limited: {str(e)}")
    
    # Sidebar for settings and stats
    with st.sidebar:
        st.markdown("""
        <div class="feature-card">
            <h3>⚙️ Settings & Stats</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # Show current stats if database available
        if st.session_state.get('db_manager'):
            try:
                stats = st.session_state.db_manager.get_analytics_summary()
                if stats.get('total_analyses', 0) > 0:
                    st.markdown(f"""
                    <div class="metric-card">
                        <h4>📊 Analysis Stats</h4>
                        <p><strong>{stats['total_analyses']}</strong> tasks analyzed</p>
                        <p><strong>{stats.get('approval_rate', 0):.1f}%</strong> approval rate</p>
                    </div>
                    """, unsafe_allow_html=True)
            except Exception as e:
                logger.error(f"Stats error: {e}")
        
        # System info
        ai_type = "Advanced AI Parser" if AdvancedAIDateParser else "Simple Parser"
        db_status = "✅ Connected" if st.session_state.get('db_manager') else "❌ Not Available"
        
        st.markdown(f"""
        <div class="feature-card">
            <h4>🔧 System Status</h4>
            <p><strong>AI Engine:</strong> {ai_type}</p>
            <p><strong>Database:</strong> {db_status}</p>
            <p><strong>Date:</strong> {datetime.now().strftime('%Y-%m-%d')}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Clear history button
        if st.button("🗑️ Clear Session History", help="Clear current session data"):
            clear_session_data()
            st.success("✅ Session cleared!")
            st.rerun()
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("✏️ Enter Checklist Item")
        
        # Text input for checklist item
        checklist_item = st.text_area(
            label="Task Description",
            placeholder="e.g., Fix critical bug in login system ASAP\nSchedule quarterly review meeting\nUpdate project documentation",
            height=120,
            help="Enter a task description. The AI will analyze urgency keywords and context to suggest appropriate due dates."
        )
        
        # Additional options
        with st.expander("🎛️ Advanced Options"):
            col_opt1, col_opt2 = st.columns(2)
            with col_opt1:
                priority_override = st.selectbox(
                    "Priority Override:",
                    options=["Auto-detect", "Low", "Medium", "High", "Critical"],
                    help="Override AI priority detection"
                )
            with col_opt2:
                date_range_preference = st.selectbox(
                    "Preferred Timeline:",
                    options=["AI Suggestion", "Same Day", "Next Day", "This Week", "Next Week", "Custom"],
                    help="Set your preferred timeline preference"
                )
        
        # Analyze button
        analyze_button = st.button("🔮 Analyze & Suggest Due Date", type="primary", use_container_width=True)
    
    with col2:
        st.subheader("📊 Quick Examples")
        
        example_categories = {
            "🔴 High Priority": [
                "Fix critical bug ASAP",
                "Emergency server maintenance",
                "Call client immediately"
            ],
            "🟡 Medium Priority": [
                "Review quarterly report",
                "Update documentation",
                "Schedule team meeting"
            ],
            "🟢 Low Priority": [
                "Research new tools",
                "Organize project files",
                "Plan next quarter"
            ]
        }
        
        for category, examples in example_categories.items():
            st.markdown(f"**{category}**")
            for example in examples:
                if st.button(f"📝 {example}", key=f"ex_{example}", help=f"Use example: {example}"):
                    st.session_state.current_item = example
                    st.rerun()
            st.markdown("")
    
    # Use example if selected
    if 'current_item' in st.session_state:
        checklist_item = st.session_state.current_item
        st.session_state.pop('current_item', None)
    
    # Analysis results
    if analyze_button and checklist_item:
        perform_task_analysis(checklist_item, priority_override, date_range_preference)
    
    # Display recent analyses
    display_recent_analyses()
    
    # Integration modules (if available)
    try:
        if integrate_trello_to_main_app:
            integrate_trello_to_main_app()
        
        if integrate_dashboard_to_main_app and st.session_state.get('db_manager'):
            integrate_dashboard_to_main_app(st.session_state.db_manager)
    except Exception as e:
        logger.error(f"Integration error: {e}")

def perform_task_analysis(checklist_item: str, priority_override: str, date_range_preference: str):
    """Perform AI analysis on the task"""
    with st.spinner("🤔 Analyzing task urgency and context..."):
        try:
            # Get AI suggestion
            result = st.session_state.ai_parser.suggest_due_date(checklist_item)
            
            # Apply overrides
            result = apply_user_preferences(result, priority_override, date_range_preference)
            
            # Display results
            st.markdown("## 📅 AI Analysis Results")
            
            # Main suggestion box
            st.markdown(f"""
            <div class="suggestion-box">
                <h3>📋 Task: {checklist_item}</h3>
                <h2>🗓️ Suggested Due Date: {result['suggested_date']}</h2>
                <p><strong>💭 AI Reasoning:</strong> {result['reasoning']}</p>
                <p><strong>⏱️ Timeline:</strong> {result['days_from_now']} days from now</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Metrics row
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                confidence = result['confidence']
                conf_class, conf_emoji = get_confidence_display(confidence)
                st.markdown(f"""
                <div class="metric-card">
                    <div class="{conf_class}">
                        {conf_emoji}<br>
                        {confidence:.1%}
                    </div>
                    <small>Confidence</small>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                urgency = result['urgency_score']
                urgency_color = get_urgency_color(urgency)
                st.markdown(f"""
                <div class="metric-card">
                    <div style="color: {urgency_color}; font-weight: bold; font-size: 1.5rem;">
                        {urgency}/10
                    </div>
                    <small>Urgency Score</small>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                st.markdown(f"""
                <div class="metric-card">
                    <div style="font-weight: bold; font-size: 1.2rem; color: #1f77b4;">
                        {result['days_from_now']}
                    </div>
                    <small>Days Away</small>
                </div>
                """, unsafe_allow_html=True)
            
            with col4:
                keyword_count = len(result.get('keywords_found', []))
                st.markdown(f"""
                <div class="metric-card">
                    <div style="font-weight: bold; font-size: 1.2rem; color: #28a745;">
                        {keyword_count}
                    </div>
                    <small>Keywords Found</small>
                </div>
                """, unsafe_allow_html=True)
            
            # Keywords section
            if result.get('keywords_found'):
                st.subheader("🔍 Detected Keywords")
                cols = st.columns(min(len(result['keywords_found']), 5))
                for i, keyword in enumerate(result['keywords_found'][:5]):
                    with cols[i % len(cols)]:
                        st.code(keyword)
            
            # User feedback section
            st.markdown("## ✏️ Review & Adjust")
            
            feedback_col1, feedback_col2 = st.columns(2)
            
            with feedback_col1:
                # Date picker for adjustment
                adjusted_date = st.date_input(
                    "📅 Adjust due date if needed:",
                    value=result['suggested_datetime'].date(),
                    help="Modify the suggested date based on your specific needs"
                )
                
                # Feedback rating
                user_rating = st.slider(
                    "⭐ Rate this AI suggestion (1-5 stars):",
                    min_value=1, max_value=5, value=3,
                    help="Help improve AI accuracy with your feedback"
                )
            
            with feedback_col2:
                st.markdown("**📝 Actions:**")
                
                # Action buttons
                if st.button("✅ Accept AI Suggestion", type="primary", use_container_width=True):
                    handle_user_decision(checklist_item, result['suggested_date'], "accepted", result, user_rating)
                
                if st.button("📝 Accept Modified Date", type="secondary", use_container_width=True):
                    handle_user_decision(checklist_item, str(adjusted_date), "modified", result, user_rating)
                
                if st.button("❌ Reject Suggestion", use_container_width=True):
                    handle_user_decision(checklist_item, None, "rejected", result, user_rating)
            
            # Save analysis for learning (if database available)
            save_analysis_to_database(checklist_item, result)
            
        except Exception as e:
            st.error(f"❌ Error analyzing task: {str(e)}")
            logger.error(f"Analysis error: {e}")
            
            # Show fallback suggestion
            fallback_date = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
            st.warning(f"🔄 Fallback suggestion: {fallback_date} (7 days from now)")

def apply_user_preferences(result: Dict[str, Any], priority_override: str, date_range_preference: str) -> Dict[str, Any]:
    """Apply user preferences to AI result"""
    modified_result = result.copy()
    
    # Apply priority override
    if priority_override != "Auto-detect":
        priority_map = {"Low": 2, "Medium": 5, "High": 8, "Critical": 10}
        if priority_override in priority_map:
            modified_result['urgency_score'] = priority_map[priority_override]
            modified_result['reasoning'] += f" (Priority manually set to {priority_override})"
    
    # Apply date range preference
    if date_range_preference != "AI Suggestion":
        range_map = {
            "Same Day": 0,
            "Next Day": 1, 
            "This Week": 7,
            "Next Week": 14
        }
        if date_range_preference in range_map:
            new_days = range_map[date_range_preference]
            new_date = datetime.now() + timedelta(days=new_days)
            modified_result['suggested_date'] = new_date.strftime('%Y-%m-%d')
            modified_result['suggested_datetime'] = new_date
            modified_result['days_from_now'] = new_days
            modified_result['reasoning'] += f" (Timeline preference: {date_range_preference})"
    
    return modified_result

def get_confidence_display(confidence: float) -> tuple:
    """Get confidence display class and emoji"""
    if confidence >= 0.7:
        return "confidence-high", "🎯"
    elif confidence >= 0.5:
        return "confidence-medium", "⚠️"
    else:
        return "confidence-low", "❓"

def get_urgency_color(urgency: int) -> str:
    """Get color for urgency score"""
    if urgency >= 8:
        return "#dc3545"  # Red
    elif urgency >= 6:
        return "#fd7e14"  # Orange
    elif urgency >= 4:
        return "#ffc107"  # Yellow
    else:
        return "#28a745"  # Green

def handle_user_decision(task: str, date: Optional[str], decision: str, result: Dict[str, Any], rating: int):
    """Handle user decision on AI suggestion"""
    decision_messages = {
        "accepted": f"✅ AI suggestion accepted! Due date: {date}",
        "modified": f"📝 Modified suggestion accepted! Due date: {date}",
        "rejected": "❌ Suggestion rejected. No due date set."
    }
    
    st.success(decision_messages[decision])
    
    # Add to history
    add_to_history(task, date or "Not set", decision.title(), result, rating)
    
    # Update database if available
    if st.session_state.get('db_manager') and decision in ["accepted", "modified"]:
        try:
            analysis_data = {
                'task_text': task,
                'suggested_date': date or result['suggested_date'],
                'confidence': result['confidence'],
                'urgency_score': result['urgency_score'],
                'keywords_found': result.get('keywords_found', []),
                'reasoning': result['reasoning'] + f" (User {decision}, Rating: {rating}/5)"
            }
            
            task_id = st.session_state.db_manager.save_analysis(analysis_data)
            st.session_state.db_manager.update_user_approval(task_id, True, date)
            st.info(f"💾 Saved to database (ID: {task_id})")
            
        except Exception as e:
            logger.error(f"Database save error: {e}")

def save_analysis_to_database(task: str, result: Dict[str, Any]):
    """Save analysis to database for learning"""
    if st.session_state.get('db_manager') and 'analysis_saved' not in st.session_state:
        try:
            analysis_data = {
                'task_text': task,
                'suggested_date': result['suggested_date'],
                'confidence': result['confidence'],
                'urgency_score': result['urgency_score'],
                'keywords_found': result.get('keywords_found', []),
                'reasoning': result['reasoning']
            }
            st.session_state.db_manager.save_analysis(analysis_data)
            st.session_state.analysis_saved = True
        except Exception as e:
            logger.error(f"Database save error: {e}")

def display_recent_analyses():
    """Display recent analyses from database or session"""
    st.markdown("## 📚 Analysis History")
    
    if st.session_state.get('db_manager'):
        display_database_history()
    else:
        display_session_history()

def display_database_history():
    """Display recent analyses from database"""
    try:
        recent_analyses = st.session_state.db_manager.get_analyses(limit=10)
        
        if recent_analyses:
            # Create DataFrame for display
            history_data = []
            for analysis in recent_analyses:
                history_data.append({
                    "ID": analysis.id,
                    "Task": truncate_text(analysis.task_text, 50),
                    "Suggested Date": analysis.suggested_date,
                    "Final Date": analysis.final_due_date or "Not set",
                    "Confidence": f"{analysis.confidence:.1%}",
                    "Urgency": f"{analysis.urgency_score}/10",
                    "Status": format_status(analysis.user_approved),
                    "Source": "🔗 Trello" if analysis.trello_card_id else "✏️ Manual",
                    "Created": analysis.created_at[:16] if analysis.created_at else "Unknown"
                })
            
            df = pd.DataFrame(history_data)
            st.dataframe(df, use_container_width=True, height=300)
            
            # Quick stats
            col1, col2, col3 = st.columns(3)
            with col1:
                approved_count = sum(1 for a in recent_analyses if a.user_approved)
                st.metric("✅ Approved", f"{approved_count}/{len(recent_analyses)}")
            with col2:
                avg_confidence = sum(a.confidence for a in recent_analyses) / len(recent_analyses)
                st.metric("🎯 Avg Confidence", f"{avg_confidence:.1%}")
            with col3:
                avg_urgency = sum(a.urgency_score for a in recent_analyses) / len(recent_analyses)
                st.metric("⚡ Avg Urgency", f"{avg_urgency:.1f}/10")
        else:
            st.info("📈 No analysis history yet. Start analyzing tasks to build your database!")
            
    except Exception as e:
        logger.error(f"Database history error: {e}")
        display_session_history()

def display_session_history():
    """Display session history as fallback"""
    if 'history' in st.session_state and st.session_state.history:
        # Create DataFrame from session history
        history_data = []
        for item in st.session_state.history[-10:]:  # Show last 10
            history_data.append({
                "Task": truncate_text(item['task'], 50),
                "Date": item['date'],
                "Status": item['status'],
                "Rating": f"{item.get('rating', 'N/A')}/5",
                "Time": item['timestamp']
            })
        
        if history_data:
            df = pd.DataFrame(history_data)
            st.dataframe(df, use_container_width=True)
    else:
        st.info("📋 No session history available. Analyze some tasks to see them here!")

def truncate_text(text: str, max_length: int) -> str:
    """Truncate text to specified length"""
    return text[:max_length] + ("..." if len(text) > max_length else "")

def format_status(approved: bool) -> str:
    """Format approval status with styling"""
    return "✅ Approved" if approved else "⏳ Pending"

def add_to_history(task: str, date: str, status: str, result: Optional[Dict] = None, rating: Optional[int] = None):
    """Add item to session analysis history"""
    if 'history' not in st.session_state:
        st.session_state.history = []
    
    history_item = {
        'task': task,
        'date': date,
        'status': status,
        'timestamp': datetime.now().strftime('%H:%M:%S'),
        'result': result,
        'rating': rating
    }
    
    st.session_state.history.append(history_item)

def clear_session_data():
    """Clear session data"""
    keys_to_clear = ['history', 'analysis_saved', 'current_item']
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"🚨 Application Error: {str(e)}")
        logger.error(f"Main application error: {e}")
        
        # Show basic fallback interface
        st.markdown("## 🔧 Basic Mode")
        st.info("Running in basic mode due to system error. Some features may be limited.")
        
        task = st.text_input("Enter a task:")
        if task and st.button("Simple Analysis"):
            parser = SimpleAIParser()
            result = parser.suggest_due_date(task)
            st.success(f"📅 Suggested date: {result['suggested_date']}")
            st.info(f"💭 Reasoning: {result['reasoning']}")