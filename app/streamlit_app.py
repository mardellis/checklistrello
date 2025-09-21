import streamlit as st
import sys
from datetime import datetime
import pandas as pd

# Import our AI parser
from ai_parser import AIDateParser

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
    
    # Initialize AI parser
    if 'ai_parser' not in st.session_state:
        st.session_state.ai_parser = AIDateParser()
    
    # Sidebar for settings
    with st.sidebar:
        st.header("⚙️ Settings")
        st.info("Currently using rule-based AI parser. Future versions will integrate advanced ML models.")
        
        # Display current date
        st.write(f"**Current Date:** {datetime.now().strftime('%Y-%m-%d')}")
        
        # Clear history button
        if st.button("🗑️ Clear History"):
            if 'history' in st.session_state:
                st.session_state.history = []
            st.experimental_rerun()
    
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
                st.experimental_rerun()
    
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
                st.markdown("## ✏️ Adjust Suggestion")
                
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
                    if st.button("✅ Accept Suggestion"):
                        st.success(f"✅ Accepted due date: {result['suggested_date']}")
                        add_to_history(checklist_item, result['suggested_date'], "Accepted")
                    
                    if st.button("📝 Accept Modified Date"):
                        st.success(f"✅ Accepted modified date: {adjusted_date}")
                        add_to_history(checklist_item, str(adjusted_date), "Modified")
                
                # Save to history
                add_to_history(checklist_item, result['suggested_date'], "Analyzed", result)
                
            except Exception as e:
                st.error(f"❌ Error analyzing task: {str(e)}")
                st.write("Please try again or contact support.")
    
    # History section
    if 'history' in st.session_state and st.session_state.history:
        st.markdown("## 📚 Analysis History")
        
        # Create DataFrame for better display
        history_data = []
        for item in st.session_state.history[-10:]:  # Show last 10
            history_data.append({
                "Task": item['task'][:50] + "..." if len(item['task']) > 50 else item['task'],
                "Suggested Date": item['date'],
                "Status": item['status'],
                "Timestamp": item['timestamp']
            })
        
        if history_data:
            df = pd.DataFrame(history_data)
            st.dataframe(df, use_container_width=True)

def add_to_history(task, date, status, result=None):
    """Add item to analysis history"""
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