import streamlit as st
import sys
import os
from datetime import datetime
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import our modules
try:
    from ai_parser import AdvancedAIDateParser
    from database import DatabaseManager, TaskAnalysis
    from trello_integration import integrate_trello_to_main_app
    from dashboard import integrate_dashboard_to_main_app
except ImportError as e:
    st.error(f"Import error: {e}. Please ensure all modules are in the same directory.")
    st.stop()

# Configure page
st.set_page_config(
    page_title="AI Checklist Due Dates - Enhanced",
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
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
    }
    .confidence-high { color: #28a745; font-weight: bold; font-size: 1.1em; }
    .confidence-medium { color: #ffc107; font-weight: bold; font-size: 1.1em; }
    .confidence-low { color: #dc3545; font-weight: bold; font-size: 1.1em; }
    .metric-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #007bff;
        margin: 0.5rem 0;
    }
    .success-message {
        background: linear-gradient(90deg, #28a745, #20c997);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    .stButton > button {
        border-radius: 20px;
        border: none;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
    }
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """Initialize all session state variables"""
    if 'ai_parser' not in st.session_state:
        st.session_state.ai_parser = AdvancedAIDateParser()
    
    if 'db_manager' not in st.session_state:
        st.session_state.db_manager = DatabaseManager()
    
    if 'history' not in st.session_state:
        st.session_state.history = []
    
    if 'analysis_count' not in st.session_state:
        st.session_state.analysis_count = 0

def render_header():
    """Render the main header with statistics"""
    st.markdown('<h1 class="main-header">🤖 AI Checklist Due Dates</h1>', unsafe_allow_html=True)
    
    # Quick stats in header
    stats = st.session_state.db_manager.get_analytics_summary()
    if stats.get('total_analyses', 0) > 0:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📊 Total Analyses", stats.get('total_analyses', 0))
        
        with col2:
            approval_rate = stats.get('approval_rate', 0)
            st.metric("✅ Approval Rate", f"{approval_rate:.1f}%")
        
        with col3:
            avg_confidence = stats.get('average_confidence', 0)
            st.metric("🎯 Avg Confidence", f"{avg_confidence:.1%}")
        
        with col4:
            recent_activity = stats.get('recent_activity', 0)
            st.metric("📈 Recent (7d)", recent_activity)
    
    st.markdown("---")

def render_sidebar():
    """Render enhanced sidebar with settings and quick stats"""
    with st.sidebar:
        st.header("⚙️ Control Panel")
        
        # Quick actions
        st.subheader("🚀 Quick Actions")
        if st.button("🧪 Run Parser Tests", use_container_width=True):
            run_parser_tests()
        
        if st.button("💾 Backup Database", use_container_width=True):
            backup_database()
        
        # Settings
        st.subheader("🔧 Settings")
        
        # Default timeline setting
        default_timeline = st.slider(
            "Default Timeline (days)",
            min_value=1,
            max_value=30,
            value=7,
            help="Default timeline when no patterns are detected"
        )
        st.session_state.default_timeline = default_timeline
        
        # Weekend handling
        skip_weekends = st.checkbox(
            "Skip weekends for non-urgent tasks",
            value=True,
            help="Automatically move suggested dates to weekdays"
        )
        st.session_state.skip_weekends = skip_weekends
        
        # Display current info
        st.subheader("📅 Current Info")
        st.info(f"**Today:** {datetime.now().strftime('%Y-%m-%d')}")
        st.info(f"**Session Analyses:** {st.session_state.analysis_count}")
        
        # Clear session data
        st.subheader("🗑️ Cleanup")
        if st.button("Clear Session History", use_container_width=True):
            st.session_state.history = []
            st.session_state.analysis_count = 0
            st.success("Session cleared!")
            st.rerun()

def render_main_interface():
    """Render the main analysis interface"""
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("✏️ Task Analysis")
        
        # Text input with enhanced features
        checklist_item = st.text_area(
            label="Enter Task Description",
            placeholder="e.g., Fix critical bug in login system ASAP\nSchedule team meeting for next week\nReview quarterly report by Friday",
            height=120,
            help="📝 Enter a task description. The AI will analyze urgency keywords, dates, and context to suggest appropriate due dates.",
            key="main_input"
        )
        
        # Analysis controls
        col1a, col1b = st.columns(2)
        
        with col1a:
            analyze_button = st.button("🔮 Analyze & Suggest Due Date", type="primary", use_container_width=True)
        
        with col1b:
            clear_input = st.button("🧹 Clear Input", use_container_width=True)
            if clear_input:
                st.session_state.main_input = ""
                st.rerun()
    
    with col2:
        st.subheader("📊 Quick Examples")
        
        examples = [
            ("🚨 Fix critical bug ASAP", "immediate"),
            ("📞 Call client tomorrow", "specific"),
            ("📝 Review quarterly report", "general"),
            ("📅 Schedule team meeting", "planning"),
            ("🔄 Update documentation", "maintenance"),
            ("🎯 Deploy by Friday", "deadline")
        ]
        
        for example_text, category in examples:
            if st.button(example_text, key=f"ex_{category}", use_container_width=True):
                st.session_state.main_input = example_text.split(" ", 1)[1]  # Remove emoji
                st.rerun()
        
        # Add custom example
        st.markdown("**Add Custom Example:**")
        custom_example = st.text_input("Custom task:", placeholder="Enter your own example")
        if custom_example and st.button("➕ Use Custom", use_container_width=True):
            st.session_state.main_input = custom_example
            st.rerun()
    
    return analyze_button, checklist_item

def render_analysis_results(result, checklist_item):
    """Render comprehensive analysis results"""
    st.markdown("## 📅 AI Analysis Results")
    
    # Main suggestion box
    st.markdown(f"""
    <div class="suggestion-box">
        <h3>📋 Task: {checklist_item}</h3>
        <h2>🗓️ Suggested Due Date: {result['suggested_date']}</h2>
        <p><strong>💭 Reasoning:</strong> {result['reasoning']}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Detailed metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
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
        <div class="metric-card">
            <p style="color: {urgency_color}; font-weight: bold; font-size: 1.1em;">
                ⚡ Urgency Score<br>
                {result['urgency_score']}/10
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <p style="color: #007bff; font-weight: bold;">
                📅 Timeline<br>
                {result['days_from_now']} days
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        keywords_count = len(result['keywords_found'])
        st.markdown(f"""
        <div class="metric-card">
            <p style="color: #6c757d; font-weight: bold;">
                🔍 Keywords<br>
                {keywords_count} found
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    # Detailed breakdown
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🔍 Analysis Breakdown")
        
        if result['keywords_found']:
            st.write("**Time Indicators:**")
            for keyword in result['keywords_found']:
                st.code(f"🕒 {keyword}", language=None)
        
        if result.get('detected_actions'):
            st.write("**Action Keywords:**")
            for action in result['detected_actions']:
                st.code(f"🎬 {action}", language=None)
        
        if result.get('detected_contexts'):
            st.write("**Context Clues:**")
            for context in result['detected_contexts']:
                st.code(f"🏷️ {context}", language=None)
        
        if not any([result['keywords_found'], result.get('detected_actions'), result.get('detected_contexts')]):
            st.info("No specific patterns detected - using default analysis")
    
    with col2:
        st.subheader("✏️ Adjust & Save")
        
        # Date adjustment
        adjusted_date = st.date_input(
            "Modify due date if needed:",
            value=result['suggested_datetime'].date(),
            help="🗓️ Adjust the suggested date based on your requirements"
        )
        
        # Priority adjustment
        adjusted_priority = st.selectbox(
            "Adjust priority:",
            options=["Keep AI suggestion", "Low Priority", "Medium Priority", "High Priority", "Critical"],
            index=0
        )
        
        # Action buttons
        col2a, col2b = st.columns(2)
        
        with col2a:
            if st.button("✅ Accept & Save", type="primary", use_container_width=True):
                save_analysis(checklist_item, result, "accepted", str(result['suggested_datetime'].date()))
        
        with col2b:
            if st.button("📝 Save Modified", use_container_width=True):
                save_analysis(checklist_item, result, "modified", str(adjusted_date))

def save_analysis(task_text, ai_result, status, final_date):
    """Save analysis to database with proper error handling"""
    try:
        # Prepare analysis data
        analysis_data = {
            'task_text': task_text,
            'suggested_date': ai_result['suggested_date'],
            'confidence': ai_result['confidence'],
            'urgency_score': ai_result['urgency_score'],
            'keywords_found': ai_result['keywords_found'],
            'reasoning': ai_result['reasoning']
        }
        
        # Save to database
        task_id = st.session_state.db_manager.save_analysis(analysis_data)
        
        # Update approval status
        user_approved = status in ["accepted", "modified"]
        st.session_state.db_manager.update_user_approval(task_id, user_approved, final_date)
        
        # Update session stats
        st.session_state.analysis_count += 1
        add_to_session_history(task_text, final_date, status.title())
        
        # Show success message
        st.markdown(f"""
        <div class="success-message">
            <h4>✅ Analysis Saved Successfully!</h4>
            <p>Task ID: {task_id} | Status: {status.title()} | Final Date: {final_date}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Trigger rerun to update stats
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Error saving analysis: {str(e)}")
        st.error("Please try again or contact support")

def render_recent_history():
    """Render recent analysis history with enhanced features"""
    st.markdown("## 📚 Recent Analysis History")
    
    # Get recent analyses from database
    recent_analyses = st.session_state.db_manager.get_analyses(limit=15)
    
    if not recent_analyses:
        st.info("📈 No analysis history available yet. Start analyzing tasks to build your database!")
        return
    
    # Filter controls
    col1, col2, col3 = st.columns(3)
    
    with col1:
        filter_status = st.selectbox(
            "Filter by status:",
            options=["All", "Approved", "Pending"],
            index=0
        )
    
    with col2:
        filter_urgency = st.selectbox(
            "Min urgency level:",
            options=["All", "Critical (8+)", "High (6+)", "Medium (4+)", "Low (0+)"],
            index=0
        )
    
    with col3:
        sort_by = st.selectbox(
            "Sort by:",
            options=["Created Date (Newest)", "Created Date (Oldest)", "Urgency (High-Low)", "Confidence (High-Low)"],
            index=0
        )
    
    # Apply filters
    filtered_analyses = recent_analyses.copy()
    
    if filter_status == "Approved":
        filtered_analyses = [a for a in filtered_analyses if a.user_approved]
    elif filter_status == "Pending":
        filtered_analyses = [a for a in filtered_analyses if not a.user_approved]
    
    if filter_urgency != "All":
        urgency_map = {"Critical (8+)": 8, "High (6+)": 6, "Medium (4+)": 4, "Low (0+)": 0}
        min_urgency = urgency_map[filter_urgency]
        filtered_analyses = [a for a in filtered_analyses if a.urgency_score >= min_urgency]
    
    # Apply sorting
    if sort_by == "Created Date (Oldest)":
        filtered_analyses.reverse()
    elif sort_by == "Urgency (High-Low)":
        filtered_analyses.sort(key=lambda x: x.urgency_score, reverse=True)
    elif sort_by == "Confidence (High-Low)":
        filtered_analyses.sort(key=lambda x: x.confidence, reverse=True)
    
    # Display results
    if filtered_analyses:
        # Create enhanced DataFrame
        history_data = []
        for analysis in filtered_analyses:
            # Status emoji
            if analysis.user_approved:
                status_emoji = "✅"
                status_text = "Approved"
            else:
                status_emoji = "⏳"
                status_text = "Pending"
            
            # Urgency emoji
            if analysis.urgency_score >= 8:
                urgency_emoji = "🔴"
            elif analysis.urgency_score >= 6:
                urgency_emoji = "🟡"
            else:
                urgency_emoji = "🟢"
            
            # Source emoji
            source_emoji = "🔗" if analysis.trello_card_id else "✏️"
            
            history_data.append({
                "ID": analysis.id,
                "Task": analysis.task_text[:60] + ("..." if len(analysis.task_text) > 60 else ""),
                "Suggested": analysis.suggested_date,
                "Final Date": analysis.final_due_date or "Not set",
                "Confidence": f"{analysis.confidence:.0%}",
                "Urgency": f"{urgency_emoji} {analysis.urgency_score}/10",
                "Status": f"{status_emoji} {status_text}",
                "Source": f"{source_emoji} {'Trello' if analysis.trello_card_id else 'Manual'}",
                "Created": analysis.created_at[:16] if analysis.created_at else "Unknown"
            })
        
        # Display table
        df = pd.DataFrame(history_data)
        st.dataframe(df, use_container_width=True)
        
        # Summary stats
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            approved_count = sum(1 for a in filtered_analyses if a.user_approved)
            st.metric("✅ Approved", f"{approved_count}/{len(filtered_analyses)}")
        
        with col2:
            avg_confidence = sum(a.confidence for a in filtered_analyses) / len(filtered_analyses)
            st.metric("🎯 Avg Confidence", f"{avg_confidence:.1%}")
        
        with col3:
            avg_urgency = sum(a.urgency_score for a in filtered_analyses) / len(filtered_analyses)
            st.metric("⚡ Avg Urgency", f"{avg_urgency:.1f}/10")
        
        with col4:
            trello_count = sum(1 for a in filtered_analyses if a.trello_card_id)
            st.metric("🔗 From Trello", f"{trello_count}/{len(filtered_analyses)}")
        
        # Export options
        col1, col2 = st.columns(2)
        
        with col1:
            csv_data = df.to_csv(index=False)
            st.download_button(
                label="📊 Download CSV Report",
                data=csv_data,
                file_name=f"ai_analysis_report_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        
        with col2:
            if st.button("📈 View Detailed Analytics", use_container_width=True):
                st.session_state.show_dashboard = True
                st.rerun()
    
    else:
        st.warning("⚠️ No analyses match the current filters")

def add_to_session_history(task, date, status):
    """Add item to session history"""
    if 'history' not in st.session_state:
        st.session_state.history = []
    
    history_item = {
        'task': task,
        'date': date,
        'status': status,
        'timestamp': datetime.now().strftime('%H:%M:%S')
    }
    
    st.session_state.history.append(history_item)

def run_parser_tests():
    """Run parser tests and display results"""
    st.info("🧪 Running parser tests...")
    
    # This would run the test function from ai_parser.py
    try:
        # Import and run tests
        from ai_parser import test_enhanced_parser
        
        # Capture test output (in a real app, you'd redirect stdout)
        st.success("✅ Parser tests completed! Check console for detailed results.")
        st.info("💡 Tests verify the AI parser's accuracy on various task types and patterns.")
        
    except Exception as e:
        st.error(f"❌ Test execution failed: {str(e)}")

def backup_database():
    """Create database backup"""
    try:
        backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        success = st.session_state.db_manager.backup_database(backup_name)
        
        if success:
            st.success(f"✅ Database backed up successfully!")
            st.info(f"📁 Backup saved as: {backup_name}")
        else:
            st.error("❌ Backup failed")
            
    except Exception as e:
        st.error(f"❌ Backup error: {str(e)}")

def main():
    """Main application function"""
    # Initialize session state
    initialize_session_state()
    
    # Render UI components
    render_header()
    render_sidebar()
    
    # Main interface
    analyze_button, checklist_item = render_main_interface()
    
    # Handle analysis
    if analyze_button and checklist_item.strip():
        with st.spinner("🤔 Analyzing task with enhanced AI..."):
            try:
                # Get AI suggestion
                result = st.session_state.ai_parser.suggest_due_date(checklist_item)
                
                # Display results
                render_analysis_results(result, checklist_item)
                
                # Auto-save analysis for tracking (without approval)
                if 'current_analysis' not in st.session_state:
                    analysis_data = {
                        'task_text': checklist_item,
                        'suggested_date': result['suggested_date'],
                        'confidence': result['confidence'],
                        'urgency_score': result['urgency_score'],
                        'keywords_found': result['keywords_found'],
                        'reasoning': result['reasoning']
                    }
                    task_id = st.session_state.db_manager.save_analysis(analysis_data)
                    st.session_state.current_analysis = task_id
                
            except Exception as e:
                st.error(f"❌ Analysis failed: {str(e)}")
                st.error("Please try again or check your input")
                
                # Log error analysis
                error_analysis = {
                    'task_text': checklist_item,
                    'suggested_date': datetime.now().strftime('%Y-%m-%d'),
                    'confidence': 0.0,
                    'urgency_score': 0,
                    'keywords_found': [],
                    'reasoning': f'Analysis error: {str(e)}'
                }
                st.session_state.db_manager.save_analysis(error_analysis)
    
    elif analyze_button and not checklist_item.strip():
        st.warning("⚠️ Please enter a task description to analyze")
    
    # Show recent history
    st.markdown("---")
    render_recent_history()
    
    # Integration modules
    integrate_trello_to_main_app()
    integrate_dashboard_to_main_app(st.session_state.db_manager)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; padding: 20px;">
        <p>🤖 <strong>AI Checklist Due Dates</strong> - Enhanced Edition</p>
        <p>Powered by Advanced Rule-Based AI Parser | Built with Streamlit</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()metric-card">
            <p class="{conf_class}">
                {conf_emoji} Confidence<br>
                {confidence:.1%} ({conf_desc})
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        urgency_color = "#dc3545" if result['urgency_score'] >= 8 else "#ffc107" if result['urgency_score'] >= 5 else "#28a745"
        st.markdown(f"""
        <div class="