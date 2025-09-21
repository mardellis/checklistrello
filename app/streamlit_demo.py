import streamlit as st
import sys
from datetime import datetime
import pandas as pd

# Import our modules
from ai_parser import AdvancedAIDateParser
from trello_integration import integrate_trello_to_main_app
from database import DatabaseManager
from dashboard import integrate_dashboard_to_main_app

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
    }
    .suggestion-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        margin: 1rem 0;
    }
    .confidence-high { color: #28a745; font-weight: bold; }
    .confidence-medium { color: #ffc107; font-weight: bold; }
    .confidence-low { color: #dc3545; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

def main():
    # Header
    st.markdown('<h1 class="main-header">🤖 AI Checklist Due Dates</h1>', unsafe_allow_html=True)
    st.markdown("---")
    
    # Initialize components
    if 'ai_parser' not in st.session_state:
        st.session_state.ai_parser = AdvancedAIDateParser()
    
    if 'db_manager' not in st.session_state:
        st.session_state.db_manager = DatabaseManager()
    
    # Sidebar for settings and stats
    with st.sidebar:
        st.header("⚙️ Settings")
        
        # Show current stats
        stats = st.session_state.db_manager.get_analytics_summary()
        if stats.get('total_analyses', 0) > 0:
            st.success(f"📊 **{stats['total_analyses']}** analyses completed")
            st.info(f"✅ **{stats.get('approval_rate', 0):.1f}%** approval rate")
        
        st.info("Currently using advanced rule-based AI parser with date extraction capabilities.")
        
        # Display current date
        st.write(f"**Current Date:** {datetime.now().strftime('%Y-%m-%d')}")
        
        # Clear history button
        if st.button("🗑️ Clear Session History"):
            if 'history' in st.session_state:
                st.session_state.history = []
            st.rerun() = []
            st.rerun()
    
    # Main input area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("✏️ Enter Checklist Item")
        
        # Text input for checklist item
        checklist_item = st.text_area(
            label="Checklist Item Description",
            placeholder="e.g., Fix critical bug in login system ASAP",
            height=100,
            help="Enter a task description. The AI will analyze urgency keywords to suggest appropriate due dates."
        )
        
        # Analyze button
        analyze_button = st.button("🔮 Analyze & Suggest Due Date", type="primary")
    
    with col2:
        st.subheader("📊 Quick Examples")
        example_items = [
            "Fix critical bug ASAP",
            "Review quarterly report",
            "Schedule team meeting",
            "Update documentation",
            "Call client tomorrow"
        ]
        
        for example in example_items:
            if st.button(f"📝 {example}", key=f"ex_{example}"):
                st.session_state.current_item = example
                st.rerun()
    
    # Use example if selected
    if 'current_item' in st.session_state:
        checklist_item = st.session_state.current_item
        st.session_state.pop('current_item', None)
    
    # Analysis results
    if analyze_button and checklist_item:
        with st.spinner("🤔 Analyzing task urgency..."):
            try:
                # Get AI suggestion
                result = st.session_state.ai_parser.suggest_due_date(checklist_item)
                
                # Display results
                st.markdown("## 📅 AI Suggestion")
                
                # Create columns for better layout
                res_col1, res_col2, res_col3 = st.columns([2, 1, 1])
                
                with res_col1:
                    st.markdown(f"""
                    <div class="suggestion-box">
                        <h3>📋 Task: {checklist_item}</h3>
                        <h2>🗓️ Suggested Due Date: {result['suggested_date']}</h2>
                        <p><strong>Reasoning:</strong> {result['reasoning']}</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with res_col2:
                    # Confidence indicator
                    confidence = result['confidence']
                    if confidence >= 0.7:
                        conf_class = "confidence-high"
                        conf_emoji = "🎯"
                    elif confidence >= 0.5:
                        conf_class = "confidence-medium"
                        conf_emoji = "⚠️"
                    else:
                        conf_class = "confidence-low"
                        conf_emoji = "❓"
                    
                    st.markdown(f"""
                    <p class="{conf_class}">
                        {conf_emoji} Confidence<br>
                        {confidence:.1%}
                    </p>
                    """, unsafe_allow_html=True)
                    
                    st.metric("Urgency Score", f"{result['urgency_score']}/10")
                
                with res_col3:
                    st.write("**Keywords Found:**")
                    if result['keywords_found']:
                        for keyword in result['keywords_found']:
                            st.code(keyword, language=None)
                    else:
                        st.write("None")
                
                # User feedback section
                st.markdown("## ✏️ Adjust & Save Suggestion")
                
                feedback_col1, feedback_col2 = st.columns(2)
                
                with feedback_col1:
                    # Date picker for adjustment
                    adjusted_date = st.date_input(
                        "Adjust due date if needed:",
                        value=result['suggested_datetime'].date(),
                        help="Modify the suggested date based on your needs"
                    )
                
                with feedback_col2:
                    # Action buttons
                    if st.button("✅ Accept & Save Suggestion"):
                        # Save to database
                        analysis_data = {
                            'task_text': checklist_item,
                            'suggested_date': result['suggested_date'],
                            'confidence': result['confidence'],
                            'urgency_score': result['urgency_score'],
                            'keywords_found': result['keywords_found'],
                            'reasoning': result['reasoning']
                        }
                        
                        task_id = st.session_state.db_manager.save_analysis(analysis_data)
                        st.session_state.db_manager.update_user_approval(task_id, True, result['suggested_date'])
                        
                        st.success(f"✅ Accepted and saved to database (ID: {task_id})")
                        add_to_history(checklist_item, result['suggested_date'], "Accepted & Saved")
                    
                    if st.button("📝 Accept Modified & Save"):
                        # Save to database with modified date
                        analysis_data = {
                            'task_text': checklist_item,
                            'suggested_date': str(adjusted_date),
                            'confidence': result['confidence'],
                            'urgency_score': result['urgency_score'],
                            'keywords_found': result['keywords_found'],
                            'reasoning': result['reasoning'] + f" (User modified to {adjusted_date})"
                        }
                        
                        task_id = st.session_state.db_manager.save_analysis(analysis_data)
                        st.session_state.db_manager.update_user_approval(task_id, True, str(adjusted_date))
                        
                        st.success(f"✅ Modified date accepted and saved (ID: {task_id})")
                        add_to_history(checklist_item, str(adjusted_date), "Modified & Saved")
                
                # Save analysis even if not approved (for learning)
                if 'analysis_saved' not in st.session_state:
                    analysis_data = {
                        'task_text': checklist_item,
                        'suggested_date': result['suggested_date'],
                        'confidence': result['confidence'],
                        'urgency_score': result['urgency_score'],
                        'keywords_found': result['keywords_found'],
                        'reasoning': result['reasoning']
                    }
                    task_id = st.session_state.db_manager.save_analysis(analysis_data)
                    st.session_state.analysis_saved = True
                    add_to_history(checklist_item, result['suggested_date'], "Analyzed")
                
            except Exception as e:
                st.error(f"❌ Error analyzing task: {str(e)}")
                st.write("Please try again or contact support.")
                # Log error for debugging
                st.session_state.db_manager.save_analysis({
                    'task_text': checklist_item,
                    'suggested_date': datetime.now().strftime('%Y-%m-%d'),
                    'confidence': 0.0,
                    'urgency_score': 0,
                    'keywords_found': [],
                    'reasoning': f'Analysis failed: {str(e)}'
                })
    
    # Recent analyses from database
    st.markdown("## 📚 Recent Analysis History")
    recent_analyses = st.session_state.db_manager.get_analyses(limit=10)
    
    if recent_analyses:
        # Create DataFrame for display
        history_data = []
        for analysis in recent_analyses:
            history_data.append({
                "ID": analysis.id,
                "Task": analysis.task_text[:50] + ("..." if len(analysis.task_text) > 50 else ""),
                "Suggested Date": analysis.suggested_date,
                "Final Date": analysis.final_due_date or "Not set",
                "Confidence": f"{analysis.confidence:.1%}",
                "Urgency": f"{analysis.urgency_score}/10",
                "Status": "✅ Approved" if analysis.user_approved else "⏳ Pending",
                "Source": "🔗 Trello" if analysis.trello_card_id else "✏️ Manual",
                "Created": analysis.created_at[:16] if analysis.created_at else "Unknown"
            })
        
        df = pd.DataFrame(history_data)
        st.dataframe(df, use_container_width=True)
        
        # Quick stats
        col1, col2, col3 = st.columns(3)
        with col1:
            approved_count = sum(1 for a in recent_analyses if a.user_approved)
            st.metric("Approved", f"{approved_count}/{len(recent_analyses)}")
        with col2:
            avg_confidence = sum(a.confidence for a in recent_analyses) / len(recent_analyses)
            st.metric("Avg Confidence", f"{avg_confidence:.1%}")
        with col3:
            avg_urgency = sum(a.urgency_score for a in recent_analyses) / len(recent_analyses)
            st.metric("Avg Urgency", f"{avg_urgency:.1f}/10")
    else:
        st.info("No analysis history available yet. Start analyzing tasks to build your database!")
    
    # Integration modules
    integrate_trello_to_main_app()
    integrate_dashboard_to_main_app(st.session_state.db_manager)

def add_to_history(task, date, status, result=None):
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

if __name__ == "__main__":
    main()