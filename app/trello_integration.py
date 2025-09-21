import streamlit as st
import pandas as pd
from datetime import datetime
from typing import List, Optional

from trello_api import TrelloAPI, validate_trello_credentials, ChecklistItem
from ai_parser import AIDateParser

def render_trello_integration():
    """Render the Trello integration section"""
    st.header("🔗 Trello Integration")
    
    # API Credentials Section
    with st.expander("🔑 Trello API Setup", expanded=not _has_valid_credentials()):
        st.markdown("""
        **How to get your Trello API credentials:**
        1. Go to [Trello Developer API Keys](https://trello.com/app-key)
        2. Copy your **API Key**
        3. Click "Generate a Token" for a **Token**
        4. Paste both below
        """)
        
        col1, col2 = st.columns(2)
        
        with col1:
            api_key = st.text_input(
                "API Key",
                type="password",
                value=st.session_state.get('trello_api_key', ''),
                help="32-character API key from Trello"
            )
        
        with col2:
            token = st.text_input(
                "Token",
                type="password", 
                value=st.session_state.get('trello_token', ''),
                help="64-character token from Trello"
            )
        
        if st.button("🔍 Test Connection", type="primary"):
            if api_key and token:
                with st.spinner("Testing connection..."):
                    result = validate_trello_credentials(api_key, token)
                    
                    if result['success']:
                        st.success(f"✅ Connected successfully as {result['user']['fullName']}")
                        st.session_state.trello_api_key = api_key
                        st.session_state.trello_token = token
                        st.session_state.trello_user = result['user']
                        st.rerun()
                    else:
                        st.error(f"❌ Connection failed: {result['error']}")
            else:
                st.warning("Please enter both API Key and Token")
    
    # Show connection status
    if _has_valid_credentials():
        user = st.session_state.get('trello_user', {})
        st.success(f"🟢 Connected as **{user.get('fullName', 'Unknown User')}**")
        
        # Board Selection
        _render_board_selection()
        
        # Show checklist items if board selected
        if st.session_state.get('selected_board_id'):
            _render_checklist_items()
    else:
        st.info("👆 Please configure your Trello API credentials above to continue")

def _has_valid_credentials() -> bool:
    """Check if valid Trello credentials are stored"""
    return bool(
        st.session_state.get('trello_api_key') and 
        st.session_state.get('trello_token') and 
        st.session_state.get('trello_user')
    )

def _render_board_selection():
    """Render board selection interface"""
    st.subheader("📋 Select Board")
    
    # Load boards button
    if st.button("🔄 Load My Boards"):
        with st.spinner("Loading boards..."):
            trello = TrelloAPI(
                st.session_state.trello_api_key,
                st.session_state.trello_token
            )
            
            boards = trello.get_user_boards()
            if boards:
                st.session_state.trello_boards = boards
                st.success(f"✅ Loaded {len(boards)} boards")
            else:
                st.error("❌ No boards found or error loading boards")
    
    # Display boards
    if 'trello_boards' in st.session_state and st.session_state.trello_boards:
        boards = st.session_state.trello_boards
        
        # Create board selection
        board_options = {f"{board['name']} ({board['id'][:8]}...)": board['id'] for board in boards}
        
        selected_board_display = st.selectbox(
            "Choose a board:",
            options=list(board_options.keys()),
            key="board_selector"
        )
        
        if selected_board_display:
            selected_board_id = board_options[selected_board_display]
            st.session_state.selected_board_id = selected_board_id
            
            # Find selected board details
            selected_board = next(b for b in boards if b['id'] == selected_board_id)
            
            col1, col2 = st.columns([3, 1])
            with col1:
                st.info(f"📌 Selected: **{selected_board['name']}**")
            with col2:
                if st.button("📊 Analyze Board"):
                    _load_checklist_items(selected_board_id)

def _load_checklist_items(board_id: str):
    """Load checklist items from selected board"""
    with st.spinner("Loading checklist items..."):
        trello = TrelloAPI(
            st.session_state.trello_api_key,
            st.session_state.trello_token
        )
        
        checklist_items = trello.get_checklist_items(board_id)
        
        if checklist_items:
            st.session_state.checklist_items = checklist_items
            st.success(f"✅ Found {len(checklist_items)} checklist items")
        else:
            st.warning("⚠️ No checklist items found in this board")
            st.session_state.checklist_items = []

def _render_checklist_items():
    """Render checklist items with AI analysis"""
    if 'checklist_items' not in st.session_state:
        st.info("👆 Click 'Analyze Board' to load checklist items")
        return
    
    checklist_items = st.session_state.checklist_items
    
    if not checklist_items:
        st.warning("No checklist items found in the selected board")
        return
    
    st.subheader(f"📝 Checklist Items ({len(checklist_items)} found)")
    
    # Filter controls
    col1, col2, col3 = st.columns(3)
    
    with col1:
        filter_state = st.selectbox(
            "Filter by state:",
            options=["All", "incomplete", "complete"],
            index=0
        )
    
    with col2:
        filter_card = st.selectbox(
            "Filter by card:",
            options=["All"] + list(set(item.card_name for item in checklist_items)),
            index=0
        )
    
    with col3:
        if st.button("🤖 Analyze All Items"):
            _analyze_all_items()
    
    # Apply filters
    filtered_items = checklist_items
    if filter_state != "All":
        filtered_items = [item for item in filtered_items if item.state == filter_state]
    if filter_card != "All":
        filtered_items = [item for item in filtered_items if item.card_name == filter_card]
    
    # Display items
    if filtered_items:
        _display_checklist_table(filtered_items)
    else:
        st.info("No items match the selected filters")

def _analyze_all_items():
    """Analyze all checklist items with AI"""
    if 'ai_parser' not in st.session_state:
        st.session_state.ai_parser = AIDateParser()
    
    checklist_items = st.session_state.checklist_items
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    analyzed_items = []
    
    for i, item in enumerate(checklist_items):
        status_text.text(f"Analyzing item {i+1}/{len(checklist_items)}: {item.name[:30]}...")
        
        # Get AI suggestion
        ai_result = st.session_state.ai_parser.suggest_due_date(item.name)
        
        # Combine item data with AI result
        item_data = {
            'item': item,
            'ai_suggestion': ai_result
        }
        analyzed_items.append(item_data)
        
        progress_bar.progress((i + 1) / len(checklist_items))
    
    st.session_state.analyzed_items = analyzed_items
    status_text.text("✅ Analysis complete!")
    st.success(f"🎯 Analyzed {len(analyzed_items)} items successfully")

def _display_checklist_table(items: List[ChecklistItem]):
    """Display checklist items in a table format"""
    # Prepare data for display
    table_data = []
    
    for item in items:
        # Check if we have AI analysis for this item
        ai_data = None
        if 'analyzed_items' in st.session_state:
            ai_data = next(
                (a['ai_suggestion'] for a in st.session_state.analyzed_items 
                 if a['item'].id == item.id), 
                None
            )
        
        row = {
            'Item': item.name[:50] + ("..." if len(item.name) > 50 else ""),
            'Card': item.card_name,
            'Checklist': item.checklist_name,
            'State': '✅' if item.state == 'complete' else '⏳',
            'AI Suggestion': ai_data['suggested_date'] if ai_data else 'Not analyzed',
            'Confidence': f"{ai_data['confidence']:.0%}" if ai_data else 'N/A',
            'Urgency': f"{ai_data['urgency_score']}/10" if ai_data else 'N/A'
        }
        table_data.append(row)
    
    # Display table
    if table_data:
        df = pd.DataFrame(table_data)
        st.dataframe(df, use_container_width=True)
        
        # Export options
        if 'analyzed_items' in st.session_state:
            st.subheader("💾 Export Options")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("📅 Export to Calendar (Coming Soon)"):
                    st.info("Calendar export will be available in the next step!")
            
            with col2:
                # Download as CSV
                csv_data = df.to_csv(index=False)
                st.download_button(
                    label="📊 Download as CSV",
                    data=csv_data,
                    file_name=f"trello_analysis_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv"
                )
    else:
        st.info("No items to display")

# Integration with main app
def integrate_trello_to_main_app():
    """Add Trello integration to the main Streamlit app"""
    # Add to sidebar
    with st.sidebar:
        st.markdown("---")
        if st.button("🔗 Configure Trello"):
            st.session_state.show_trello = True
    
    # Show Trello integration if requested
    if st.session_state.get('show_trello', False):
        st.markdown("---")
        render_trello_integration()
        
        if st.button("❌ Close Trello Integration"):
            st.session_state.show_trello = False
            st.rerun()