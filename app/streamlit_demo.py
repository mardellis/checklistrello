import streamlit as st
import sys
from datetime import datetime
import pandas as pd
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import our modules with error handling
try:
    from ai_parser import AdvancedAIDateParser, AIDateParser
    logger.info("AI parser loaded successfully")
except ImportError as e:
    logger.error(f"ai_parser import failed: {e}")
    AdvancedAIDateParser = None
    AIDateParser = None

try:
    from trello_integration import integrate_trello_to_main_app
    logger.info("Trello integration loaded successfully")
except ImportError as e:
    logger.info(f"Trello integration not loaded: {e}")
    integrate_trello_to_main_app = None

try:
    from database import DatabaseManager
    from dashboard import integrate_dashboard_to_main_app
    logger.info("Database modules loaded successfully")
except ImportError as e:
    logger.info(f"Database/dashboard modules not loaded: {e}")
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
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 2rem;
    }
    .suggestion-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 15px;
        color: white;
        margin: 1rem 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .confidence-high { color: #28a745; font-weight: bold; font-size: 1.1em; }
    .confidence-medium { color: #ffc107; font-weight: bold; font-size: 1.1em; }
    .confidence-low { color: #dc3545; font-weight: bold; font-size: 1.1em; }
    .urgency-high { background: #dc3545; color: white; padding: 5px 10px; border-radius: 15px; }
    .urgency-medium { background: #ffc107; color: black; padding: 5px 10px; border-radius: 15px; }
    .urgency-low { background: #28a745; color: white; padding: 5px 10px; border-radius: 15px; }
    .stats-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #667eea;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

def main():
    # Header
    st.markdown('<h1 class="main-header">🤖 AI Checklist Due Dates</h1>', unsafe_allow_html=True)
    st.markdown("---")
    
    # Initialize components
    if 'ai_parser' not in st.session_state:
        if AdvancedAIDateParser:
            st.session_state.ai_parser = AdvancedAIDateParser()
            logger.info("AI parser initialized")
        else:
            st.error("⚠️ AI Parser not available. Please check your ai_parser.py file.")
            st.stop()
    
    if DatabaseManager and 'db_manager' not in st.session_state:
        try:
            st.session_state.db_manager = DatabaseManager()
            logger.info("Database manager initialized")
        except Exception as e:
            st.warning(f"⚠️ Database not available: {e}")
    
    # Sidebar for settings and stats
    with st.sidebar:
        st.header("⚙️ Settings & Stats")
        
        # Show current stats
        if st.session_state.get('db_manager'):
            try:
                stats = st.session_state.db_manager.get_analytics_summary()
                if stats.get('total_analyses', 0) > 0:
                    st.markdown(f"""
                    <div class="stats-card">
                        <h4>📊 Quick Stats</h4>
                        <p><strong>{stats['total_analyses']}</strong> analyses completed</p>
                        <p><strong>{stats.get('approval_rate', 0):.1f}%</strong> approval rate</p>
                        <p><strong>{stats.get('average_confidence', 0):.1%}</strong> avg confidence</p>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.info("📈 No analyses yet - start by entering a task!")
            except Exception as e:
                logger.error(f"Stats error: {e}")
        
        # System info
        st.markdown(f"""
        <div class="stats-card">
            <h4>🔧 System Info</h4>
            <p><strong>AI Parser:</strong> {'✅ Active' if AdvancedAIDateParser else '❌ Error'}</p>
            <p><strong>Database:</strong> {'✅ Active' if DatabaseManager else '❌ Disabled'}</p>
            <p><strong>Trello:</strong> {'✅ Available' if integrate_trello_to_main_app else '❌ Disabled'}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Display current date and time info
        now = datetime.now()
        st.write(f"**Today:** {now.strftime('%A, %B %d, %Y')}")
        st.write(f"**Time:** {now.strftime('%I:%M %p')}")
        
        # Calculate next Monday for reference
        if st.session_state.get('ai_parser'):
            next_monday_days = st.session_state.ai_parser.days_to_next_monday
            next_monday_date = now + pd.Timedelta(days=next_monday_days)
            st.write(f"**Next Monday:** {next_monday_date.strftime('%B %d')} ({next_monday_days} days)")
        
        st.markdown("---")
        
        # Clear history button
        if st.button("🗑️ Clear Session History", help="Clear all session data"):
            for key in ['history', 'analysis_saved']:
                if key in st.session_state:
                    del st.session_state[key]
            st.success("Session cleared!")
            st.rerun()
    
    # Main content area
    create_main_interface()
    
    # Show recent history
    display_recent_history()
    
    # Integration modules
    integrate_external_modules()

def create_main_interface():
    """Create the main task analysis interface"""
    # Main input area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("✏️ Enter Your Task")
        
        # Text input for checklist item
        checklist_item = st.text_area(
            label="Task Description",
            placeholder="Example: Fix critical login bug ASAP\nExample: Schedule team meeting next week\nExample: Review quarterly report by Friday",
            height=120,
            help="💡 Tip: Include urgency words (urgent, ASAP, critical) and time references (today, next week, etc.) for better suggestions",
            key="main_task_input"
        )
        
        # Analysis button
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            analyze_button = st.button("🔮 Analyze & Suggest Due Date", type="primary", use_container_width=True)
        with col_btn2:
            if st.button("🎲 Try Random Example", use_container_width=True):
                examples = [
                    "Critical database backup needed ASAP",
                    "Plan quarterly team meeting next week", 
                    "Review client proposal by tomorrow",
                    "Update project documentation this week",
                    "Emergency server maintenance tonight",
                    "Schedule annual performance reviews",
                    "Fix urgent login bug immediately",
                    "Submit monthly report end of week"
                ]
                import random
                st.session_state.current_item = random.choice(examples)
                st.rerun()
    
    with col2:
        st.subheader("📊 Quick Examples")
        
        example_categories = {
            "🚨 Urgent Tasks": [
                "Fix critical bug ASAP",
                "Emergency server restart",
                "Call client immediately"
            ],
            "📅 Scheduled Tasks": [
                "Team meeting next Monday",
                "Review report this week", 
                "Project deadline Friday"
            ],
            "📝 Regular Tasks": [
                "Update documentation",
                "Plan vacation time",
                "Organize desk space"
            ]
        }
        
        for category, examples in example_categories.items():
            with st.expander(category):
                for example in examples:
                    if st.button(f"📝 {example}", key=f"ex_{example}", use_container_width=True):
                        st.session_state.current_item = example
                        st.rerun()
    
    # Use example if selected
    if 'current_item' in st.session_state:
        checklist_item = st.session_state.current_item
        st.session_state.pop('current_item', None)
        # Update the text area
        st.session_state.main_task_input = checklist_item
        st.rerun()
    
    # Analysis results
    if analyze_button and checklist_item:
        analyze_task(checklist_item)

def analyze_task(checklist_item: str):
    """Analyze the given task and display results"""
    with st.spinner("🤔 Analyzing task urgency and timeline..."):
        try:
            # Get AI suggestion
            result = st.session_state.ai_parser.suggest_due_date(checklist_item)
            
            # Display results with enhanced UI
            st.markdown("## 📅 AI Analysis Results")
            
            # Create columns for better layout
            res_col1, res_col2, res_col3 = st.columns([3, 1, 1])
            
            with res_col1:
                # Determine day of week for display
                day_name = result['suggested_datetime'].strftime('%A')
                
                st.markdown(f"""
                <div class="suggestion-box">
                    <h3>📋 Task: {checklist_item}</h3>
                    <h2>🗓️ Suggested Due Date: {result['suggested_date']}</h2>
                    <h3>📆 {day_name} ({result['days_from_now']} days from today)</h3>
                    <p><strong>💭 AI Reasoning:</strong> {result['reasoning']}</p>
                </div>
                """, unsafe_allow_html=True)
            
            with res_col2:
                # Confidence indicator with better styling
                confidence = result['confidence']
                if confidence >= 0.7:
                    conf_class = "confidence-high"
                    conf_emoji = "🎯"
                    conf_desc = "High"
                elif confidence >= 0.5:
                    conf_class = "confidence-medium"
                    conf_emoji = "⚠️"
                    conf_desc = "Medium"
                else:
                    conf_class = "confidence-low"
                    conf_emoji = "❓"
                    conf_desc = "Low"
                
                st.markdown(f"""
                <div style="text-align: center;">
                    <p class="{conf_class}">
                        {conf_emoji} Confidence<br>
                        {confidence:.1%}<br>
                        <small>({conf_desc})</small>
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
                # Urgency score with color coding
                urgency = result['urgency_score']
                if urgency >= 8:
                    urgency_class = "urgency-high"
                    urgency_emoji = "🚨"
                elif urgency >= 5:
                    urgency_class = "urgency-medium" 
                    urgency_emoji = "⚡"
                else:
                    urgency_class = "urgency-low"
                    urgency_emoji = "📅"
                
                st.markdown(f"""
                <div style="text-align: center; margin-top: 1rem;">
                    <span class="{urgency_class}">
                        {urgency_emoji} {urgency}/10
                    </span>
                </div>
                """, unsafe_allow_html=True)
            
            with res_col3:
                st.write("**🔍 Keywords Found:**")
                if result['keywords_found']:
                    for keyword in result['keywords_found']:
                        st.code(keyword, language=None)
                else:
                    st.write("*None detected*")
                
                # Additional info
                st.write("**📊 Analysis:**")
                st.write(f"• Days ahead: {result['days_from_now']}")
                st.write(f"• Confidence: {confidence:.0%}")
                st.write(f"• Urgency: {urgency}/10")
            
            # User feedback section with improved UI
            display_feedback_section(checklist_item, result)
            
        except Exception as e:
            st.error(f"❌ Error analyzing task: {str(e)}")
            logger.error(f"Analysis error: {e}")
            
            # Offer manual input as fallback
            st.warning("🔧 Analysis failed, but you can still set a due date manually:")
            manual_date = st.date_input("Select due date:", value=datetime.now().date())
            if st.button("💾 Save Manual Entry"):
                add_to_history(checklist_item, str(manual_date), "Manual Entry")
                st.success(f"✅ Manual entry saved: {manual_date}")

def display_feedback_section(checklist_item: str, result: dict):
    """Display user feedback and save options"""
    st.markdown("## ✏️ Review & Save")
    
    feedback_col1, feedback_col2 = st.columns(2)
    
    with feedback_col1:
        st.write("**📅 Adjust date if needed:**")
        adjusted_date = st.date_input(
            "Fine-tune the due date:",
            value=result['suggested_datetime'].date(),
            help="Modify the AI suggestion based on your specific needs"
        )
        
        # Show the difference if date was changed
        if str(adjusted_date) != result['suggested_date']:
            days_diff = (adjusted_date - result['suggested_datetime'].date()).days
            if days_diff > 0:
                st.info(f"📈 Moved {days_diff} days later")
            else:
                st.warning(f"📉 Moved {abs(days_diff)} days earlier")
    
    with feedback_col2:
        st.write("**💾 Save your decision:**")
        
        # Action buttons with better styling
        col_accept, col_modify = st.columns(2)
        
        with col_accept:
            if st.button("✅ Accept AI Suggestion", type="primary", use_container_width=True):
                save_analysis_result(checklist_item, result, result['suggested_date'], "Accepted AI Suggestion")
                st.success("✅ AI suggestion accepted and saved!")
                st.balloons()  # Celebration effect
        
        with col_modify:
            if st.button("📝 Save Modified Date", use_container_width=True):
                modified_result = result.copy()
                modified_result['final_date'] = str(adjusted_date)
                save_analysis_result(checklist_item, modified_result, str(adjusted_date), "Modified & Saved")
                st.success(f"✅ Modified date saved: {adjusted_date}")
        
        # Quick action buttons
        st.write("**⚡ Quick Actions:**")
        quick_col1, quick_col2 = st.columns(2)
        
        with quick_col1:
            if st.button("📌 Save for Later", use_container_width=True):
                add_to_history(checklist_item, result['suggested_date'], "Saved for Later")
                st.info("📌 Task saved for later review")
        
        with quick_col2:
            if st.button("❌ Skip This Task", use_container_width=True):
                add_to_history(checklist_item, "N/A", "Skipped")
                st.info("⏭️ Task skipped")

def save_analysis_result(task_text: str, result: dict, final_date: str, status: str):
    """Save analysis result to database and session"""
    # Save to database if available
    if st.session_state.get('db_manager'):
        try:
            analysis_data = {
                'task_text': task_text,
                'suggested_date': result['suggested_date'],
                'confidence': result['confidence'],
                'urgency_score': result['urgency_score'],
                'keywords_found': result['keywords_found'],
                'reasoning': result['reasoning']
            }
            
            task_id = st.session_state.db_manager.save_analysis(analysis_data)
            st.session_state.db_manager.update_user_approval(task_id, True, final_date)
            
            logger.info(f"Analysis saved to database with ID: {task_id}")
            
        except Exception as e:
            logger.error(f"Database save error: {e}")
            st.warning("⚠️ Could not save to database, but saved to session")
    
    # Always save to session history
    add_to_history(task_text, final_date, status, result)

def display_recent_history():
    """Display recent analysis history"""
    st.markdown("## 📚 Recent Analysis History")
    
    # Try to get history from database first
    if st.session_state.get('db_manager'):
        display_database_history()
    else:
        display_session_history()

def display_database_history():
    """Display history from database"""
    try:
        recent_analyses = st.session_state.db_manager.get_analyses(limit=15)
        
        if recent_analyses:
            # Create enhanced DataFrame for display
            history_data = []
            for analysis in recent_analyses:
                history_data.append({
                    "🆔 ID": analysis.id,
                    "📋 Task": analysis.task_text[:60] + ("..." if len(analysis.task_text) > 60 else ""),
                    "📅 Suggested": analysis.suggested_date,
                    "✅ Final": analysis.final_due_date or "Not set",
                    "🎯 Confidence": f"{analysis.confidence:.0%}",
                    "⚡ Urgency": f"{analysis.urgency_score}/10",
                    "📊 Status": "✅ Approved" if analysis.user_approved else "⏳ Pending",
                    "📍 Source": "🔗 Trello" if analysis.trello_card_id else "✏️ Manual",
                    "🕒 Created": analysis.created_at[:16] if analysis.created_at else "Unknown"
                })
            
            df = pd.DataFrame(history_data)
            
            # Display with filters
            col1, col2, col3 = st.columns(3)
            with col1:
                show_all = st.checkbox("Show all entries", value=True)
            with col2:
                if not show_all:
                    max_rows = st.number_input("Max rows to show", min_value=5, max_value=50, value=10)
                else:
                    max_rows = len(df)
            with col3:
                st.write(f"**Total: {len(recent_analyses)} analyses**")
            
            # Display the dataframe
            display_df = df.head(max_rows) if not show_all else df
            st.dataframe(display_df, use_container_width=True)
            
            # Summary statistics
            display_history_stats(recent_analyses)
            
            # Export option
            if st.button("📊 Export History as CSV"):
                csv_data = df.to_csv(index=False)
                st.download_button(
                    label="⬇️ Download CSV",
                    data=csv_data,
                    file_name=f"ai_analysis_history_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv"
                )
        else:
            st.info("📈 No analysis history yet. Start analyzing tasks to build your database!")
            
    except Exception as e:
        st.error(f"Error loading database history: {e}")
        display_session_history()  # Fallback

def display_session_history():
    """Display session-based history as fallback"""
    if 'history' in st.session_state and st.session_state.history:
        history_data = []
        for item in st.session_state.history[-15:]:  # Show last 15
            history_data.append({
                "📋 Task": item['task'][:60] + ("..." if len(item['task']) > 60 else ""),
                "📅 Date": item['date'],
                "📊 Status": item['status'],
                "🕒 Time": item['timestamp']
            })
        
        if history_data:
            df = pd.DataFrame(history_data)
            st.dataframe(df, use_container_width=True)
            st.info(f"📱 Session history: {len(history_data)} items (database not available)")
    else:
        st.info("📈 No history available. Start analyzing tasks to see your progress!")

def display_history_stats(analyses):
    """Display summary statistics for analyses"""
    if not analyses:
        return
        
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        approved_count = sum(1 for a in analyses if a.user_approved)
        st.metric(
            "✅ Approved", 
            f"{approved_count}/{len(analyses)}", 
            f"{approved_count/len(analyses)*100:.0f}%"
        )
    
    with col2:
        avg_confidence = sum(a.confidence for a in analyses) / len(analyses)
        st.metric("🎯 Avg Confidence", f"{avg_confidence:.0%}")
    
    with col3:
        avg_urgency = sum(a.urgency_score for a in analyses) / len(analyses)
        st.metric("⚡ Avg Urgency", f"{avg_urgency:.1f}/10")
    
    with col4:
        trello_count = sum(1 for a in analyses if a.trello_card_id)
        st.metric("🔗 From Trello", f"{trello_count}")

def integrate_external_modules():
    """Integrate external modules (Trello, Dashboard)"""
    try:
        # Trello integration
        if integrate_trello_to_main_app:
            integrate_trello_to_main_app()
    except Exception as e:
        logger.error(f"Trello integration error: {e}")
    
    try:
        # Dashboard integration  
        if integrate_dashboard_to_main_app and st.session_state.get('db_manager'):
            integrate_dashboard_to_main_app(st.session_state.db_manager)
    except Exception as e:
        logger.error(f"Dashboard integration error: {e}")

def add_to_history(task: str, date: str, status: str, result: dict = None):
    """Add item to session analysis history"""
    if 'history' not in st.session_state:
        st.session_state.history = []
    
    history_item = {
        'task': task,
        'date': date,
        'status': status,
        'timestamp': datetime.now().strftime('%H:%M:%S'),
        'result': result
    }
    
    st.session_state.history.append(history_item)
    
    # Keep only last 50 items in session
    if len(st.session_state.history) > 50:
        st.session_state.history = st.session_state.history[-50:]

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"🚨 Application Error: {str(e)}")
        st.error("Please check the logs and refresh the page.")
        logger.error(f"Main application error: {e}", exc_info=True)
        
        # Emergency fallback interface
        st.markdown("---")
        st.subheader("🔧 Emergency Mode")
        st.write("The main application encountered an error. You can still use basic functionality:")
        
        emergency_task = st.text_input("Enter task:")
        emergency_date = st.date_input("Select due date:")
        
        if st.button("Save Emergency Entry") and emergency_task:
            st.success(f"Emergency entry saved: {emergency_task} → {emergency_date}")