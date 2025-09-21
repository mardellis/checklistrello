import streamlit as st
import pandas as pd
from datetime import datetime
from typing import List, Optional

from trello_api import TrelloAPI, validate_trello_credentials, ChecklistItem, get_trello_credentials_guide
from ai_parser import AdvancedAIDateParser as AIDateParser

def render_trello_integration():
    """Render the complete Trello integration section"""
    st.header("🔗 Trello Integration")
    st.markdown("Connect your Trello boards to automatically analyze checklist items with AI.")
    
    # API Credentials Section
    with st.expander("🔑 Trello API Setup", expanded=not _has_valid_credentials()):
        st.markdown(get_trello_credentials_guide())
        
        col1, col2 = st.columns(2)
        
        with col1:
            api_key = st.text_input(
                "API Key (32 characters)",
                type="password",
                value=st.session_state.get('trello_api_key', ''),
                help="Your Trello API Key from https://trello.com/app-key",
                placeholder="32-character API key..."
            )
        
        with col2:
            token = st.text_input(
                "Token (64+ characters)",
                type="password", 
                value=st.session_state.get('trello_token', ''),
                help="Your Trello Token from the same page",
                placeholder="64+ character token..."
            )
        
        col_test, col_clear = st.columns(2)
        
        with col_test:
            if st.button("🔍 Test Connection", type="primary", use_container_width=True):
                if api_key and token:
                    test_trello_connection(api_key, token)
                else:
                    st.warning("⚠️ Please enter both API Key and Token")
        
        with col_clear:
            if st.button("🗑️ Clear Credentials", use_container_width=True):
                clear_trello_credentials()
                st.success("🧹 Credentials cleared")
                st.rerun()
    
    # Connection Status & Main Interface
    if _has_valid_credentials():
        display_connection_status()
        render_main_trello_interface()
    else:
        display_connection_help()

def test_trello_connection(api_key: str, token: str):
    """Test Trello connection and save credentials if successful"""
    with st.spinner("🔄 Testing connection..."):
        result = validate_trello_credentials(api_key, token)
        
        if result['success']:
            # Save credentials
            st.session_state.trello_api_key = api_key
            st.session_state.trello_token = token
            st.session_state.trello_user = result['user']
            
            st.success(f"✅ Connected successfully as **{result['user']['fullName']}** (@{result['user']['username']})")
            st.balloons()
            st.rerun()
        else:
            st.error(f"❌ Connection failed: {result['error']}")
            
            # Provide specific help based on error
            if "invalid key" in result['error'].lower():
                st.info("💡 **Tip:** Make sure you copied the API Key correctly (32 characters)")
            elif "401" in result['error']:
                st.info("💡 **Tip:** Your token might have expired. Generate a new one.")
            elif "403" in result['error']:
                st.info("💡 **Tip:** Check token permissions. Make sure you authorized the token.")

def clear_trello_credentials():
    """Clear all Trello credentials and data"""
    keys_to_clear = [
        'trello_api_key', 'trello_token', 'trello_user', 'trello_boards',
        'selected_board_id', 'checklist_items', 'analyzed_items'
    ]
    
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]

def display_connection_status():
    """Display current connection status"""
    user = st.session_state.get('trello_user', {})
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.success(f"🟢 **Connected as:** {user.get('fullName', 'Unknown')} (@{user.get('username', 'unknown')})")
    
    with col2:
        if st.button("🔄 Refresh", help="Refresh connection"):
            # Clear cached data
            for key in ['trello_boards', 'checklist_items', 'analyzed_items']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
    
    with col3:
        if st.button("🚪 Disconnect", help="Clear credentials"):
            clear_trello_credentials()
            st.rerun()

def display_connection_help():
    """Display help when not connected"""
    st.info("👆 Please configure your Trello API credentials above to continue")
    
    with st.expander("❓ Need Help?"):
        st.markdown("""
        **Common Issues:**
        
        🔧 **API Key Problems:**
        - Make sure it's exactly 32 characters
        - Copy from https://trello.com/app-key
        - Don't include extra spaces
        
        🔧 **Token Problems:**  
        - Generate a fresh token (they can expire)
        - Make sure you clicked "Allow" when generating
        - Should be 64+ characters long
        
        🔧 **Connection Issues:**
        - Check your internet connection
        - Try refreshing the page
        - Make sure you're logged into Trello
        """)

def render_main_trello_interface():
    """Render the main Trello interface after successful connection"""
    # Board Selection
    render_board_selection()
    
    # Show checklist items if board selected
    if st.session_state.get('selected_board_id'):
        render_checklist_interface()

def render_board_selection():
    """Render board selection interface"""
    st.subheader("📋 Select Trello Board")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Load boards button
        if st.button("🔄 Load My Boards", help="Fetch boards from your Trello account"):
            load_trello_boards()
    
    with col2:
        # Show board count if available
        if 'trello_boards' in st.session_state:
            st.info(f"📊 {len(st.session_state.trello_boards)} boards loaded")
    
    # Display boards if loaded
    if 'trello_boards' in st.session_state and st.session_state.trello_boards:
        display_board_selector()

def load_trello_boards():
    """Load boards from Trello API"""
    with st.spinner("🔄 Loading boards..."):
        try:
            trello = TrelloAPI(
                st.session_state.trello_api_key,
                st.session_state.trello_token
            )
            
            boards = trello.get_user_boards()
            if boards:
                st.session_state.trello_boards = boards
                st.success(f"✅ Loaded {len(boards)} boards successfully!")
            else:
                st.warning("⚠️ No boards found. Make sure you have access to Trello boards.")
                
        except Exception as e:
            st.error(f"❌ Error loading boards: {str(e)}")

def display_board_selector():
    """Display the board selection dropdown"""
    boards = st.session_state.trello_boards
    
    # Create board options for selectbox
    board_options = ["Select a board..."] + [
        f"📋 {board['name']}" + (f" ({board['desc'][:30]}...)" if board.get('desc') else "")
        for board in boards
    ]
    
    selected_index = st.selectbox(
        "Choose a board to analyze:",
        options=range(len(board_options)),
        format_func=lambda x: board_options[x],
        key="board_selector"
    )
    
    if selected_index > 0:  # Not "Select a board..."
        selected_board = boards[selected_index - 1]
        st.session_state.selected_board_id = selected_board['id']
        st.session_state.selected_board = selected_board
        
        # Display selected board info
        display_selected_board_info(selected_board)

def display_selected_board_info(board):
    """Display information about the selected board"""
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.info(f"📌 **Selected:** {board['name']}")
        if board.get('desc'):
            st.caption(f"📝 {board['desc']}")
    
    with col2:
        if st.button("🔍 Analyze Board", type="primary", use_container_width=True):
            load_checklist_items(board['id'])

def load_checklist_items(board_id: str):
    """Load checklist items from the selected board"""
    with st.spinner("🔄 Loading checklist items..."):
        try:
            trello = TrelloAPI(
                st.session_state.trello_api_key,
                st.session_state.trello_token
            )
            
            checklist_items = trello.get_checklist_items(board_id)
            
            if checklist_items:
                st.session_state.checklist_items = checklist_items
                st.success(f"✅ Found {len(checklist_items)} checklist items!")
                
                # Show breakdown by state
                completed = sum(1 for item in checklist_items if item.state == 'complete')
                incomplete = len(checklist_items) - completed
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("📝 Total Items", len(checklist_items))
                with col2:
                    st.metric("✅ Completed", completed)
                with col3:
                    st.metric("⏳ Incomplete", incomplete)
                    
            else:
                st.warning("⚠️ No checklist items found in this board.")
                st.info("💡 Make sure your cards have checklists with items.")
                
        except Exception as e:
            st.error(f"❌ Error loading checklist items: {str(e)}")

def render_checklist_interface():
    """Render the checklist items interface"""
    if 'checklist_items' not in st.session_state:
        st.info("👆 Click 'Analyze Board' to load checklist items")
        return
    
    checklist_items = st.session_state.checklist_items
    
    if not checklist_items:
        st.warning("📭 No checklist items found in the selected board")
        return
    
    st.subheader(f"📝 Checklist Items Analysis")
    
    # Filter and analysis controls
    render_filter_controls(checklist_items)
    
    # Apply filters
    filtered_items = apply_filters(checklist_items)
    
    # AI Analysis section
    render_ai_analysis_section(filtered_items)
    
    # Display items table
    if filtered_items:
        display_checklist_table(filtered_items)
    else:
        st.info("🔍 No items match the selected filters")

def render_filter_controls(checklist_items):
    """Render filtering controls"""
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.session_state.filter_state = st.selectbox(
            "Filter by completion:",
            options=["All", "incomplete", "complete"],
            index=0,
            key="state_filter"
        )
    
    with col2:
        cards = list(set(item.card_name for item in checklist_items))
        st.session_state.filter_card = st.selectbox(
            "Filter by card:",
            options=["All"] + sorted(cards),
            index=0,
            key="card_filter"
        )
    
    with col3:
        st.session_state.filter_checklist = st.selectbox(
            "Filter by checklist:",
            options=["All"] + sorted(list(set(item.checklist_name for item in checklist_items))),
            index=0,
            key="checklist_filter"
        )

def apply_filters(checklist_items):
    """Apply selected filters to checklist items"""
    filtered = checklist_items
    
    # State filter
    if st.session_state.get('filter_state', 'All') != 'All':
        filtered = [item for item in filtered if item.state == st.session_state.filter_state]
    
    # Card filter
    if st.session_state.get('filter_card', 'All') != 'All':
        filtered = [item for item in filtered if item.card_name == st.session_state.filter_card]
    
    # Checklist filter
    if st.session_state.get('filter_checklist', 'All') != 'All':
        filtered = [item for item in filtered if item.checklist_name == st.session_state.filter_checklist]
    
    return filtered

def render_ai_analysis_section(filtered_items):
    """Render AI analysis controls and options"""
    st.markdown("### 🤖 AI Analysis")
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.write(f"**Items to analyze:** {len(filtered_items)}")
        if len(filtered_items) > 50:
            st.warning("⚠️ Large number of items. Analysis may take a while.")
    
    with col2:
        analyze_incomplete_only = st.checkbox(
            "📋 Incomplete items only",
            value=True,
            help="Only analyze incomplete checklist items"
        )
    
    with col3:
        if st.button("🚀 Analyze All Items", type="primary", use_container_width=True):
            items_to_analyze = filtered_items
            if analyze_incomplete_only:
                items_to_analyze = [item for item in filtered_items if item.state == 'incomplete']
            
            if items_to_analyze:
                analyze_all_items(items_to_analyze)
            else:
                st.warning("⚠️ No items to analyze with current filters")

def analyze_all_items(items_to_analyze):
    """Analyze all checklist items with AI"""
    if 'ai_parser' not in st.session_state:
        st.session_state.ai_parser = AIDateParser()
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    analyzed_items = []
    
    try:
        for i, item in enumerate(items_to_analyze):
            status_text.text(f"🔍 Analyzing item {i+1}/{len(items_to_analyze)}: {item.name[:40]}...")
            
            # Get AI suggestion
            ai_result = st.session_state.ai_parser.suggest_due_date(item.name)
            
            # Combine item data with AI result
            item_data = {
                'item': item,
                'ai_suggestion': ai_result
            }
            analyzed_items.append(item_data)
            
            # Update progress
            progress_bar.progress((i + 1) / len(items_to_analyze))
        
        # Save results
        st.session_state.analyzed_items = analyzed_items
        
        # Clear status
        status_text.text("✅ Analysis complete!")
        progress_bar.progress(1.0)
        
        # Show summary
        st.success(f"🎯 Successfully analyzed {len(analyzed_items)} items!")
        
        # Analysis summary
        display_analysis_summary(analyzed_items)
        
    except Exception as e:
        st.error(f"❌ Error during analysis: {str(e)}")
        status_text.text("❌ Analysis failed")

def display_analysis_summary(analyzed_items):
    """Display summary of AI analysis results"""
    if not analyzed_items:
        return
    
    st.markdown("#### 📊 Analysis Summary")
    
    # Calculate statistics
    urgency_scores = [item['ai_suggestion']['urgency_score'] for item in analyzed_items]
    confidence_scores = [item['ai_suggestion']['confidence'] for item in analyzed_items]
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        avg_urgency = sum(urgency_scores) / len(urgency_scores)
        st.metric("⚡ Avg Urgency", f"{avg_urgency:.1f}/10")
    
    with col2:
        high_urgency = sum(1 for score in urgency_scores if score >= 7)
        st.metric("🚨 High Urgency", f"{high_urgency}")
    
    with col3:
        avg_confidence = sum(confidence_scores) / len(confidence_scores)
        st.metric("🎯 Avg Confidence", f"{avg_confidence:.0%}")
    
    with col4:
        keywords_found = sum(1 for item in analyzed_items if item['ai_suggestion']['keywords_found'])
        st.metric("🔍 With Keywords", f"{keywords_found}")

def display_checklist_table(items: List[ChecklistItem]):
    """Display checklist items in an enhanced table format"""
    st.markdown("#### 📋 Checklist Items")
    
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
        
        # Status emoji
        status_emoji = '✅' if item.state == 'complete' else '⏳'
        
        # Urgency emoji based on AI analysis
        urgency_emoji = "📅"  # default
        if ai_data:
            urgency = ai_data['urgency_score']
            if urgency >= 8:
                urgency_emoji = "🚨"
            elif urgency >= 6:
                urgency_emoji = "⚡"
        
        row = {
            '📋 Item': item.name[:60] + ("..." if len(item.name) > 60 else ""),
            '🏷️ Card': item.card_name[:30] + ("..." if len(item.card_name) > 30 else ""),
            '📝 Checklist': item.checklist_name,
            '📊 Status': status_emoji,
            '📅 AI Date': ai_data['suggested_date'] if ai_data else 'Not analyzed',
            '🎯 Confidence': f"{ai_data['confidence']:.0%}" if ai_data else 'N/A',
            f'{urgency_emoji} Urgency': f"{ai_data['urgency_score']}/10" if ai_data else 'N/A'
        }
        table_data.append(row)
    
    # Display table
    if table_data:
        df = pd.DataFrame(table_data)
        
        # Make table interactive
        st.dataframe(
            df, 
            use_container_width=True,
            height=min(400, len(table_data) * 35 + 100)  # Dynamic height
        )
        
        # Export and action buttons
        render_action_buttons(df, items)

def render_action_buttons(df, items):
    """Render action buttons for export and further actions"""
    st.markdown("#### 🔧 Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # CSV Export
        csv_data = df.to_csv(index=False)
        st.download_button(
            label="📊 Download as CSV",
            data=csv_data,
            file_name=f"trello_analysis_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    with col2:
        # Save to Database
        if st.button("💾 Save to Database", use_container_width=True):
            save_trello_analysis_to_db(items)
    
    with col3:
        # Calendar Export (placeholder)
        if st.button("📅 Export to Calendar", use_container_width=True):
            st.info("📅 Calendar export feature coming soon!")
            # This would integrate with calendar APIs

def save_trello_analysis_to_db(items):
    """Save Trello analysis results to database"""
    if not st.session_state.get('db_manager'):
        st.warning("⚠️ Database not available")
        return
    
    if 'analyzed_items' not in st.session_state:
        st.warning("⚠️ No analysis results to save")
        return
    
    try:
        saved_count = 0
        
        for analyzed_item in st.session_state.analyzed_items:
            item = analyzed_item['item']
            ai_result = analyzed_item['ai_suggestion']
            
            # Prepare analysis data
            analysis_data = {
                'task_text': item.name,
                'suggested_date': ai_result['suggested_date'],
                'confidence': ai_result['confidence'],
                'urgency_score': ai_result['urgency_score'],
                'keywords_found': ai_result['keywords_found'],
                'reasoning': ai_result['reasoning']
            }
            
            # Prepare Trello data
            trello_data = {
                'card_id': item.card_id,
                'checklist_id': item.checklist_id,
                'item_id': item.id,
                'board_name': item.board_name,
                'card_name': item.card_name
            }
            
            # Save to database
            task_id = st.session_state.db_manager.save_analysis(analysis_data, trello_data)
            saved_count += 1
        
        st.success(f"✅ Saved {saved_count} analyses to database!")
        
    except Exception as e:
        st.error(f"❌ Error saving to database: {str(e)}")

def _has_valid_credentials() -> bool:
    """Check if valid Trello credentials are stored"""
    return bool(
        st.session_state.get('trello_api_key') and 
        st.session_state.get('trello_token') and 
        st.session_state.get('trello_user')
    )

# Integration function for main app
def integrate_trello_to_main_app():
    """Integrate Trello functionality into the main Streamlit app"""
    with st.sidebar:
        st.markdown("---")
        st.markdown("### 🔗 Trello Integration")
        
        if _has_valid_credentials():
            user = st.session_state.get('trello_user', {})
            st.success(f"Connected: {user.get('fullName', 'Unknown')}")
            
            if st.button("🔗 Open Trello Panel", use_container_width=True):
                st.session_state.show_trello = True
        else:
            st.info("Not connected to Trello")
            if st.button("🔗 Connect Trello", use_container_width=True):
                st.session_state.show_trello = True
    
    # Show Trello integration panel if requested
    if st.session_state.get('show_trello', False):
        st.markdown("---")
        render_trello_integration()
        
        # Close button
        if st.button("❌ Close Trello Integration", type="secondary"):
            st.session_state.show_trello = False
            st.rerun()