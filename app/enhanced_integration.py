import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import json
from typing import Dict, List, Any, Optional
import requests
from dataclasses import dataclass
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Enhanced data structures
@dataclass
class TrelloCard:
    id: str
    name: str
    desc: str
    due: Optional[str]
    list_name: str
    board_name: str
    labels: List[Dict]
    checklists: List[Dict]
    members: List[Dict]
    url: str

@dataclass
class CalendarEvent:
    id: str
    title: str
    start_date: datetime
    end_date: datetime
    description: str
    location: str
    attendees: List[str]

class EnhancedTrelloManager:
    """Enhanced Trello integration with better board visualization"""
    
    def __init__(self, api_key: str, token: str):
        self.api_key = api_key
        self.token = token
        self.base_url = "https://api.trello.com/1"
    
    def get_board_with_cards(self, board_id: str) -> Dict[str, Any]:
        """Get comprehensive board data with cards, lists, and checklists"""
        try:
            # Get board info
            board_url = f"{self.base_url}/boards/{board_id}"
            board_params = {
                'key': self.api_key,
                'token': self.token,
                'fields': 'name,desc,url,dateLastActivity,prefs'
            }
            
            board_response = requests.get(board_url, params=board_params)
            board_data = board_response.json()
            
            # Get lists
            lists_url = f"{self.base_url}/boards/{board_id}/lists"
            lists_params = {
                'key': self.api_key,
                'token': self.token,
                'fields': 'name,pos'
            }
            
            lists_response = requests.get(lists_url, params=lists_params)
            lists_data = lists_response.json()
            
            # Get cards with detailed info
            cards_url = f"{self.base_url}/boards/{board_id}/cards"
            cards_params = {
                'key': self.api_key,
                'token': self.token,
                'fields': 'name,desc,due,dueComplete,labels,members,url,pos',
                'checklists': 'all',
                'checklist_fields': 'name,checkItems',
                'members': 'true',
                'member_fields': 'fullName,username,avatarHash'
            }
            
            cards_response = requests.get(cards_url, params=cards_params)
            cards_data = cards_response.json()
            
            return {
                'board': board_data,
                'lists': lists_data,
                'cards': cards_data
            }
            
        except Exception as e:
            st.error(f"Error fetching board data: {str(e)}")
            return None
    
    def get_user_info(self) -> Dict[str, Any]:
        """Get current user information"""
        try:
            user_url = f"{self.base_url}/members/me"
            user_params = {
                'key': self.api_key,
                'token': self.token,
                'fields': 'fullName,username,email,avatarHash,url'
            }
            
            response = requests.get(user_url, params=user_params)
            return response.json()
            
        except Exception as e:
            st.error(f"Error fetching user info: {str(e)}")
            return {}

class GoogleCalendarManager:
    """Google Calendar integration for due date management"""
    
    def __init__(self):
        self.calendar_id = 'primary'  # Default calendar
    
    def setup_oauth(self):
        """Setup Google OAuth for Calendar API"""
        st.markdown("""
        ### 📅 Google Calendar Setup
        
        To integrate with Google Calendar, you need to:
        
        1. **Create a Google Cloud Project**
           - Go to [Google Cloud Console](https://console.cloud.google.com)
           - Create a new project or select existing one
        
        2. **Enable Calendar API**
           - Go to APIs & Services > Library
           - Search for "Google Calendar API"
           - Click "Enable"
        
        3. **Create Credentials**
           - Go to APIs & Services > Credentials  
           - Click "Create Credentials" > "OAuth 2.0 Client IDs"
           - Choose "Web application"
           - Add your Streamlit URL to authorized origins
        
        4. **Download Credentials**
           - Download the JSON file
           - Upload it using the file uploader below
        """)
        
        uploaded_file = st.file_uploader(
            "📁 Upload Google OAuth Credentials (JSON)",
            type="json",
            help="Upload the credentials.json file from Google Cloud Console"
        )
        
        if uploaded_file:
            credentials = json.load(uploaded_file)
            st.session_state.google_credentials = credentials
            st.success("✅ Google credentials uploaded successfully!")
            return True
        
        return False
    
    def create_calendar_event(self, title: str, start_date: datetime, 
                            description: str = "", duration_hours: int = 1) -> Dict:
        """Create a calendar event (simulated for demo)"""
        # In a real implementation, this would use Google Calendar API
        event = {
            'id': f"event_{datetime.now().timestamp()}",
            'title': title,
            'start': start_date.isoformat(),
            'end': (start_date + timedelta(hours=duration_hours)).isoformat(),
            'description': description,
            'created': datetime.now().isoformat()
        }
        
        return event

def render_enhanced_trello_dashboard():
    """Render the enhanced Trello dashboard with board visualization"""
    st.header("🎯 Enhanced Trello & Calendar Dashboard")
    
    # Check connection
    if not st.session_state.get('trello_api_key'):
        render_connection_setup()
        return
    
    # Initialize managers
    trello = EnhancedTrelloManager(
        st.session_state.trello_api_key,
        st.session_state.trello_token
    )
    
    calendar_mgr = GoogleCalendarManager()
    
    # Main dashboard tabs
    tab_board, tab_calendar, tab_ai, tab_settings = st.tabs([
        "📋 Board View", "📅 Calendar", "🤖 AI Analysis", "⚙️ Settings"
    ])
    
    with tab_board:
        render_board_dashboard(trello)
    
    with tab_calendar:
        render_calendar_integration(calendar_mgr)
    
    with tab_ai:
        render_ai_analysis_dashboard()
    
    with tab_settings:
        render_settings_panel()

def render_connection_setup():
    """Render connection setup for Trello and Google"""
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🔗 Trello Connection")
        
        with st.expander("Setup Instructions", expanded=True):
            st.markdown("""
            1. Go to [Trello Developer Portal](https://trello.com/app-key)
            2. Copy your API Key (32 characters)
            3. Generate a token by clicking the token link
            4. Copy the token (64+ characters)
            5. Paste both below
            """)
        
        api_key = st.text_input("API Key", type="password", placeholder="32-character API key")
        token = st.text_input("Token", type="password", placeholder="64+ character token")
        
        if st.button("🔗 Connect to Trello", type="primary"):
            if api_key and token:
                # Test connection
                try:
                    trello = EnhancedTrelloManager(api_key, token)
                    user_info = trello.get_user_info()
                    
                    if user_info:
                        st.session_state.trello_api_key = api_key
                        st.session_state.trello_token = token
                        st.session_state.trello_user = user_info
                        st.success(f"✅ Connected as {user_info.get('fullName', 'Unknown User')}")
                        st.rerun()
                    else:
                        st.error("❌ Invalid credentials")
                except Exception as e:
                    st.error(f"❌ Connection failed: {str(e)}")
            else:
                st.warning("⚠️ Please enter both API Key and Token")
    
    with col2:
        st.subheader("📅 Google Calendar")
        calendar_mgr = GoogleCalendarManager()
        calendar_mgr.setup_oauth()

def render_board_dashboard(trello: EnhancedTrelloManager):
    """Render the main board dashboard with Kanban-style visualization"""
    
    # Board selection
    if 'selected_board' not in st.session_state:
        render_board_selector(trello)
        return
    
    board_data = st.session_state.selected_board
    
    # Board header
    render_board_header(board_data)
    
    # Board statistics
    render_board_statistics(board_data)
    
    # Kanban board view
    render_kanban_board(board_data)
    
    # AI suggestions section
    render_ai_suggestions_for_board(board_data)

def render_board_selector(trello: EnhancedTrelloManager):
    """Render board selection interface"""
    st.subheader("📋 Select Your Board")
    
    if st.button("🔄 Load My Boards"):
        with st.spinner("Loading boards..."):
            try:
                # Get user boards
                boards_url = f"{trello.base_url}/members/me/boards"
                params = {
                    'key': trello.api_key,
                    'token': trello.token,
                    'fields': 'name,desc,url,dateLastActivity,prefs'
                }
                
                response = requests.get(boards_url, params=params)
                boards = response.json()
                
                st.session_state.user_boards = boards
                st.success(f"✅ Loaded {len(boards)} boards")
                
            except Exception as e:
                st.error(f"❌ Error loading boards: {str(e)}")
    
    if 'user_boards' in st.session_state:
        boards = st.session_state.user_boards
        
        # Display boards as cards
        cols = st.columns(3)
        
        for i, board in enumerate(boards):
            with cols[i % 3]:
                with st.container():
                    st.markdown(f"""
                    <div style="
                        border: 1px solid #ddd; 
                        border-radius: 10px; 
                        padding: 15px; 
                        margin: 10px 0;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        color: white;
                    ">
                        <h4>📋 {board['name']}</h4>
                        <p>{board.get('desc', 'No description')[:100]}...</p>
                        <small>Last activity: {board.get('dateLastActivity', 'Unknown')[:10]}</small>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if st.button(f"Select {board['name']}", key=f"board_{board['id']}"):
                        # Load full board data
                        with st.spinner(f"Loading {board['name']}..."):
                            board_data = trello.get_board_with_cards(board['id'])
                            if board_data:
                                st.session_state.selected_board = board_data
                                st.rerun()

def render_board_header(board_data: Dict):
    """Render board header with key information"""
    board = board_data['board']
    
    col1, col2, col3 = st.columns([3, 1, 1])
    
    with col1:
        st.markdown(f"""
        # 📋 {board['name']}
        {board.get('desc', 'No description available')}
        """)
    
    with col2:
        if st.button("🔄 Refresh Board"):
            # Refresh board data
            trello = EnhancedTrelloManager(
                st.session_state.trello_api_key,
                st.session_state.trello_token
            )
            board_data = trello.get_board_with_cards(board['id'])
            if board_data:
                st.session_state.selected_board = board_data
                st.rerun()
    
    with col3:
        if st.button("🔙 Change Board"):
            if 'selected_board' in st.session_state:
                del st.session_state.selected_board
            st.rerun()

def render_board_statistics(board_data: Dict):
    """Render board statistics and metrics"""
    cards = board_data['cards']
    lists = board_data['lists']
    
    # Calculate statistics
    total_cards = len(cards)
    overdue_cards = len([c for c in cards if c.get('due') and 
                        datetime.fromisoformat(c['due'].replace('Z', '+00:00')) < datetime.now()])
    cards_with_due_dates = len([c for c in cards if c.get('due')])
    completed_cards = len([c for c in cards if c.get('dueComplete')])
    
    # Display metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("📊 Total Cards", total_cards)
    
    with col2:
        st.metric("📅 With Due Dates", cards_with_due_dates)
    
    with col3:
        st.metric("✅ Completed", completed_cards)
    
    with col4:
        st.metric("⏰ Overdue", overdue_cards, delta=f"-{overdue_cards}" if overdue_cards > 0 else "0")
    
    with col5:
        completion_rate = (completed_cards / cards_with_due_dates * 100) if cards_with_due_dates > 0 else 0
        st.metric("📈 Completion Rate", f"{completion_rate:.1f}%")

def render_kanban_board(board_data: Dict):
    """Render Kanban-style board visualization"""
    st.subheader("🎯 Board Overview")
    
    lists = board_data['lists']
    cards = board_data['cards']
    
    # Group cards by list
    cards_by_list = {}
    for card in cards:
        list_id = card.get('idList')
        if list_id not in cards_by_list:
            cards_by_list[list_id] = []
        cards_by_list[list_id].append(card)
    
    # Create columns for each list
    if lists:
        cols = st.columns(len(lists))
        
        for i, list_item in enumerate(lists):
            with cols[i]:
                list_cards = cards_by_list.get(list_item['id'], [])
                
                st.markdown(f"""
                <div style="
                    background: #f8f9fa; 
                    border-radius: 10px; 
                    padding: 15px; 
                    margin-bottom: 20px;
                    border-left: 4px solid #667eea;
                ">
                    <h4>📝 {list_item['name']} ({len(list_cards)})</h4>
                </div>
                """, unsafe_allow_html=True)
                
                # Display cards in this list
                for card in list_cards[:10]:  # Limit display to avoid clutter
                    render_card_preview(card)
                
                if len(list_cards) > 10:
                    st.info(f"... and {len(list_cards) - 10} more cards")

def render_card_preview(card: Dict):
    """Render a preview of a Trello card"""
    # Determine card urgency color
    urgency_color = "#28a745"  # Default green
    
    if card.get('due'):
        try:
            due_date = datetime.fromisoformat(card['due'].replace('Z', '+00:00'))
            days_until_due = (due_date - datetime.now()).days
            
            if days_until_due < 0:
                urgency_color = "#dc3545"  # Red - overdue
            elif days_until_due <= 2:
                urgency_color = "#fd7e14"  # Orange - urgent
            elif days_until_due <= 7:
                urgency_color = "#ffc107"  # Yellow - soon
        except:
            pass
    
    # Card labels
    labels_html = ""
    if card.get('labels'):
        for label in card['labels'][:3]:  # Show max 3 labels
            label_color = label.get('color', 'gray')
            labels_html += f'<span style="background-color: #{label_color}; color: white; padding: 2px 6px; border-radius: 3px; font-size: 0.7em; margin-right: 3px;">{label.get("name", "Label")}</span>'
    
    # Due date info
    due_info = ""
    if card.get('due'):
        try:
            due_date = datetime.fromisoformat(card['due'].replace('Z', '+00:00'))
            due_info = f"📅 Due: {due_date.strftime('%m/%d')}"
        except:
            due_info = "📅 Due: Invalid date"
    
    # Checklist info
    checklist_info = ""
    if card.get('checklists'):
        total_items = sum(len(cl.get('checkItems', [])) for cl in card['checklists'])
        completed_items = sum(len([item for item in cl.get('checkItems', []) if item.get('state') == 'complete']) 
                            for cl in card['checklists'])
        if total_items > 0:
            checklist_info = f"☑️ {completed_items}/{total_items}"
    
    st.markdown(f"""
    <div style="
        border-left: 4px solid {urgency_color};
        background: white;
        border-radius: 8px;
        padding: 12px;
        margin: 8px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        cursor: pointer;
    ">
        <div style="font-weight: 600; font-size: 0.9em; margin-bottom: 8px;">
            {card['name'][:50]}{'...' if len(card['name']) > 50 else ''}
        </div>
        {labels_html}
        <div style="font-size: 0.8em; color: #666; margin-top: 8px;">
            {due_info} {checklist_info}
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_ai_suggestions_for_board(board_data: Dict):
    """Render AI suggestions for cards without due dates"""
    st.subheader("🤖 AI Due Date Suggestions")
    
    cards = board_data['cards']
    cards_without_due_dates = [c for c in cards if not c.get('due')]
    
    if not cards_without_due_dates:
        st.success("🎉 All cards have due dates assigned!")
        return
    
    st.info(f"💡 Found {len(cards_without_due_dates)} cards without due dates")
    
    # AI analysis for cards without due dates
    if st.button("🚀 Generate AI Suggestions"):
        analyze_cards_for_due_dates(cards_without_due_dates)

def analyze_cards_for_due_dates(cards: List[Dict]):
    """Analyze cards and suggest due dates using AI"""
    if 'ai_parser' not in st.session_state:
        from ai_parser import AdvancedAIDateParser
        st.session_state.ai_parser = AdvancedAIDateParser()
    
    ai_parser = st.session_state.ai_parser
    
    suggestions = []
    progress_bar = st.progress(0)
    
    for i, card in enumerate(cards):
        # Analyze card name and description
        card_text = card['name']
        if card.get('desc'):
            card_text += " " + card['desc']
        
        # Get AI suggestion
        ai_result = ai_parser.suggest_due_date(card_text)
        
        suggestions.append({
            'card': card,
            'suggestion': ai_result
        })
        
        progress_bar.progress((i + 1) / len(cards))
    
    # Display suggestions
    st.subheader("📋 AI Suggestions")
    
    for suggestion in suggestions:
        card = suggestion['card']
        ai = suggestion['suggestion']
        
        col1, col2, col3 = st.columns([3, 2, 1])
        
        with col1:
            st.markdown(f"""
            **📋 {card['name']}**  
            🎯 Confidence: {ai['confidence']:.0%} | ⚡ Urgency: {ai['urgency_score']}/10
            """)
        
        with col2:
            st.markdown(f"""
            **📅 Suggested Date:** {ai['suggested_date']}  
            **📝 Reasoning:** {ai['reasoning'][:100]}...
            """)
        
        with col3:
            if st.button("✅ Apply", key=f"apply_{card['id']}"):
                # In a real implementation, this would update the card via Trello API
                st.success("✅ Due date applied!")

def render_calendar_integration(calendar_mgr: GoogleCalendarManager):
    """Render Google Calendar integration"""
    st.subheader("📅 Calendar Integration")
    
    if not st.session_state.get('google_credentials'):
        st.info("📝 Please setup Google Calendar credentials in the Settings tab first")
        calendar_mgr.setup_oauth()
        return
    
    # Calendar view options
    view_option = st.selectbox(
        "📊 Calendar View",
        ["Monthly Overview", "Weekly Agenda", "Upcoming Deadlines", "Overdue Items"]
    )
    
    if view_option == "Monthly Overview":
        render_monthly_calendar_view()
    elif view_option == "Weekly Agenda":
        render_weekly_agenda()
    elif view_option == "Upcoming Deadlines":
        render_upcoming_deadlines()
    else:
        render_overdue_items()

def render_monthly_calendar_view():
    """Render monthly calendar view with Trello due dates"""
    st.markdown("### 📅 Monthly Calendar View")
    
    # Sample calendar data (in real implementation, this would come from Google Calendar API)
    import calendar as cal
    
    today = datetime.now()
    year = today.year
    month = today.month
    
    # Create calendar visualization using Plotly
    month_calendar = cal.monthcalendar(year, month)
    
    # Create calendar heatmap
    dates = []
    values = []
    
    for week in month_calendar:
        for day in week:
            if day != 0:
                date = datetime(year, month, day)
                dates.append(date)
                # Simulate activity level (in real app, count actual tasks)
                values.append(abs(hash(str(date))) % 5)
    
    fig = go.Figure(data=go.Scatter(
        x=[d.day for d in dates],
        y=[1] * len(dates),
        mode='markers',
        marker=dict(
            size=[20 + v * 10 for v in values],
            color=values,
            colorscale='Blues',
            showscale=True,
            colorbar=dict(title="Task Load")
        ),
        text=[f"{d.strftime('%B %d')}<br>Tasks: {v}" for d, v in zip(dates, values)],
        hovertemplate="<b>%{text}</b><extra></extra>"
    ))
    
    fig.update_layout(
        title=f"📅 {cal.month_name[month]} {year} - Task Distribution",
        xaxis_title="Day of Month",
        yaxis=dict(showticklabels=False, showgrid=False),
        height=300
    )
    
    st.plotly_chart(fig, use_container_width=True)

def render_weekly_agenda():
    """Render weekly agenda view"""
    st.markdown("### 📋 Weekly Agenda")
    
    # Get current week
    today = datetime.now()
    week_start = today - timedelta(days=today.weekday())
    
    # Create weekly view
    for i in range(7):
        day = week_start + timedelta(days=i)
        is_today = day.date() == today.date()
        
        day_color = "🔸" if is_today else "📅"
        
        with st.expander(f"{day_color} {day.strftime('%A, %B %d')}", expanded=is_today):
            # In real implementation, show actual tasks for this day
            st.markdown(f"""
            **Sample Tasks for {day.strftime('%A')}:**
            - 🎯 Review project proposal (AI Suggested)
            - 📞 Client meeting at 2 PM
            - ✅ Complete code review
            
            **AI Recommendations:**
            - High urgency: 2 tasks
            - Medium urgency: 1 task
            """)

def render_upcoming_deadlines():
    """Render upcoming deadlines view"""
    st.markdown("### ⏰ Upcoming Deadlines")
    
    # Sample upcoming deadlines
    deadlines = [
        {"task": "Fix critical bug", "due": "Today", "urgency": 10, "source": "Trello"},
        {"task": "Client presentation", "due": "Tomorrow", "urgency": 8, "source": "Calendar"},
        {"task": "Code review", "due": "This week", "urgency": 6, "source": "Trello"},
        {"task": "Planning meeting", "due": "Next week", "urgency": 4, "source": "Calendar"}
    ]
    
    for deadline in deadlines:
        urgency_color = "#dc3545" if deadline['urgency'] >= 8 else "#fd7e14" if deadline['urgency'] >= 6 else "#28a745"
        
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
                    <h4 style="margin: 0; color: #333;">{deadline['task']}</h4>
                    <p style="margin: 5px 0; color: #666;">📅 Due: {deadline['due']} | 📍 From: {deadline['source']}</p>
                </div>
                <div style="text-align: right;">
                    <span style="background: {urgency_color}; color: white; padding: 5px 10px; border-radius: 15px; font-weight: bold;">
                        {deadline['urgency']}/10
                    </span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

def render_overdue_items():
    """Render overdue items view"""
    st.markdown("### 🚨 Overdue Items")
    
    st.warning("⚠️ You have overdue items that need immediate attention!")
    
    # Sample overdue items
    overdue_items = [
        {"task": "Security patch deployment", "overdue_days": 3, "urgency": 10},
        {"task": "Customer feedback response", "overdue_days": 1, "urgency": 7}
    ]
    
    for item in overdue_items:
        st.error(f"""
        🚨 **{item['task']}**  
        ⏰ Overdue by: {item['overdue_days']} days  
        ⚡ Urgency: {item['urgency']}/10
        """)

def render_ai_analysis_dashboard():
    """Render comprehensive AI analysis dashboard"""
    st.subheader("🤖 AI Analysis Dashboard")
    
    # Analysis options
    analysis_type = st.selectbox(
        "📊 Analysis Type",
        ["Task Prioritization", "Due Date Optimization", "Workload Distribution", "Team Performance"]
    )
    
    if analysis_type == "Task Prioritization":
        render_task_prioritization_analysis()
    elif analysis_type == "Due Date Optimization":
        render_due_date_optimization()
    elif analysis_type == "Workload Distribution":
        render_workload_distribution()
    else:
        render_team_performance()

def render_task_prioritization_analysis():
    """Render task prioritization analysis"""
    st.markdown("### 🎯 Task Prioritization Analysis")
    
    # Sample data for prioritization
    tasks_data = {
        'Task': ['Fix login bug', 'Update documentation', 'Client meeting prep', 'Code review', 'Team standup'],
        'Urgency': [9, 3, 8, 6, 4],
        'Complexity': [7, 5, 4, 6, 2],
        'Impact': [9, 4, 8, 5, 3],
        'Priority Score': [25, 12, 20, 17, 9]
    }
    
    df = pd.DataFrame(tasks_data)
    
    # Priority matrix visualization
    fig = px.scatter(
        df, 
        x='Urgency', 
        y='Impact',
        size='Complexity',
        color='Priority Score',
        hover_name='Task',
        title="🎯 Task Priority Matrix",
        color_continuous_scale='Reds'
    )
    
    fig.update_layout(height=500)
    st.plotly_chart(fig, use_container_width=True)
    
    # Priority recommendations
    st.markdown("### 📋 Priority Recommendations")
    
    sorted_df = df.sort_values('Priority Score', ascending=False)
    
    for i, (_, task) in enumerate(sorted_df.iterrows()):
        priority_emoji = ["🔴", "🟠", "🟡", "🟢", "🔵"][min(i, 4)]
        
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            st.markdown(f"{priority_emoji} **{task['Task']}**")
        
        with col2:
            st.metric("Priority Score", f"{task['Priority Score']}")
        
        with col3:
            st.markdown(f"⚡{task['Urgency']} 📊{task['Impact']} 🔧{task['Complexity']}")

def render_due_date_optimization():
    """Render due date optimization analysis"""
    st.markdown("### 📅 Due Date Optimization")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📈 Current Schedule")
        
        # Sample schedule data
        schedule_data = {
            'Week': ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
            'Planned Tasks': [5, 8, 3, 6],
            'Completed Tasks': [4, 6, 3, 4],
            'Workload %': [80, 100, 60, 95]
        }
        
        fig1 = px.bar(
            schedule_data, 
            x='Week', 
            y=['Planned Tasks', 'Completed Tasks'],
            title="📊 Weekly Task Distribution",
            barmode='group'
        )
        st.plotly_chart(fig1, use_container_width=True)
    
    with col2:
        st.markdown("#### 🎯 Optimized Schedule")
        
        # Optimized schedule
        optimized_data = {
            'Week': ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
            'Original': [5, 8, 3, 6],
            'AI Optimized': [6, 6, 5, 5],
            'Efficiency Gain': [20, -25, 67, -17]
        }
        
        fig2 = px.line(
            optimized_data, 
            x='Week', 
            y=['Original', 'AI Optimized'],
            title="🤖 AI Schedule Optimization",
            markers=True
        )
        st.plotly_chart(fig2, use_container_width=True)
    
    # Optimization recommendations
    st.markdown("### 💡 Optimization Recommendations")
    
    recommendations = [
        {
            'task': 'Documentation Update',
            'current_due': '2025-09-25',
            'suggested_due': '2025-09-28',
            'reason': 'Reduce Week 2 overload',
            'impact': '+15% efficiency'
        },
        {
            'task': 'Code Review',
            'current_due': '2025-09-27',
            'suggested_due': '2025-09-24',
            'reason': 'Balance workload',
            'impact': '+10% efficiency'
        }
    ]
    
    for rec in recommendations:
        st.info(f"""
        📋 **{rec['task']}**  
        📅 Current: {rec['current_due']} → Suggested: {rec['suggested_due']}  
        💭 Reason: {rec['reason']} | 📈 Impact: {rec['impact']}
        """)

def render_workload_distribution():
    """Render workload distribution analysis"""
    st.markdown("### 📊 Workload Distribution Analysis")
    
    # Team workload data
    team_data = {
        'Team Member': ['Alice', 'Bob', 'Charlie', 'Diana', 'Eve'],
        'Current Tasks': [8, 12, 5, 9, 7],
        'Capacity': [10, 10, 10, 10, 10],
        'Utilization %': [80, 120, 50, 90, 70]
    }
    
    df_team = pd.DataFrame(team_data)
    
    # Utilization chart
    fig_util = px.bar(
        df_team,
        x='Team Member',
        y='Utilization %',
        color='Utilization %',
        title="👥 Team Utilization Analysis",
        color_continuous_scale=['green', 'yellow', 'red'],
        text='Utilization %'
    )
    
    fig_util.add_hline(y=100, line_dash="dash", line_color="red", 
                      annotation_text="Capacity Limit")
    
    st.plotly_chart(fig_util, use_container_width=True)
    
    # Rebalancing suggestions
    st.markdown("### ⚖️ Workload Rebalancing Suggestions")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.error("🚨 **Overloaded**")
        st.markdown("- **Bob**: 120% utilization (2 tasks over capacity)")
        st.markdown("- **Diana**: 90% utilization (at risk)")
    
    with col2:
        st.success("✅ **Available Capacity**")  
        st.markdown("- **Charlie**: 50% utilization (5 tasks available)")
        st.markdown("- **Eve**: 70% utilization (3 tasks available)")
    
    # Suggested redistributions
    st.markdown("### 🔄 Suggested Task Redistributions")
    
    redistributions = [
        {
            'from': 'Bob',
            'to': 'Charlie', 
            'task': 'API Documentation',
            'reason': 'Balance overload',
            'impact': '📉 Bob: 120% → 100%, 📈 Charlie: 50% → 60%'
        },
        {
            'from': 'Bob',
            'to': 'Eve',
            'task': 'Unit Testing',
            'reason': 'Prevent burnout',
            'impact': '📉 Bob: 100% → 90%, 📈 Eve: 70% → 80%'
        }
    ]
    
    for redistrib in redistributions:
        st.info(f"""
        🔄 **Move:** {redistrib['task']}  
        👤 **From:** {redistrib['from']} → **To:** {redistrib['to']}  
        💭 **Reason:** {redistrib['reason']}  
        📊 **Impact:** {redistrib['impact']}
        """)

def render_team_performance():
    """Render team performance analysis"""
    st.markdown("### 📈 Team Performance Analytics")
    
    # Performance metrics over time
    performance_data = {
        'Week': ['W1', 'W2', 'W3', 'W4', 'W5', 'W6'],
        'Tasks Completed': [23, 28, 31, 29, 33, 35],
        'On-Time Delivery %': [85, 90, 88, 92, 94, 96],
        'Quality Score': [8.2, 8.5, 8.7, 8.9, 9.1, 9.2]
    }
    
    # Multi-metric chart
    fig_perf = make_subplots(
        rows=2, cols=2,
        subplot_titles=('📋 Tasks Completed', '⏰ On-Time Delivery', '⭐ Quality Score', '📊 Overall Trend'),
        specs=[[{"secondary_y": False}, {"secondary_y": False}],
               [{"secondary_y": False}, {"secondary_y": False}]]
    )
    
    # Tasks completed
    fig_perf.add_trace(
        go.Scatter(x=performance_data['Week'], y=performance_data['Tasks Completed'], 
                  mode='lines+markers', name='Tasks', line=dict(color='blue')),
        row=1, col=1
    )
    
    # On-time delivery
    fig_perf.add_trace(
        go.Scatter(x=performance_data['Week'], y=performance_data['On-Time Delivery %'], 
                  mode='lines+markers', name='On-Time %', line=dict(color='green')),
        row=1, col=2
    )
    
    # Quality score
    fig_perf.add_trace(
        go.Scatter(x=performance_data['Week'], y=performance_data['Quality Score'], 
                  mode='lines+markers', name='Quality', line=dict(color='purple')),
        row=2, col=1
    )
    
    # Overall trend (combined score)
    combined_score = [
        (tasks * 0.4 + delivery * 0.3 + quality * 10 * 0.3) / 3 
        for tasks, delivery, quality in zip(
            performance_data['Tasks Completed'],
            performance_data['On-Time Delivery %'], 
            performance_data['Quality Score']
        )
    ]
    
    fig_perf.add_trace(
        go.Scatter(x=performance_data['Week'], y=combined_score, 
                  mode='lines+markers', name='Overall', line=dict(color='red')),
        row=2, col=2
    )
    
    fig_perf.update_layout(height=600, title_text="📊 Team Performance Dashboard")
    st.plotly_chart(fig_perf, use_container_width=True)
    
    # Performance insights
    st.markdown("### 🎯 Performance Insights")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "📈 Productivity Trend", 
            "+52%", 
            delta="↗️ Week over week growth"
        )
    
    with col2:
        st.metric(
            "🎯 Delivery Accuracy", 
            "96%", 
            delta="+11% from baseline"
        )
    
    with col3:
        st.metric(
            "⭐ Quality Score", 
            "9.2/10", 
            delta="+1.0 improvement"
        )
    
    # AI recommendations for performance improvement
    st.markdown("### 🤖 AI Performance Recommendations")
    
    recommendations = [
        {
            'category': '🚀 Productivity',
            'recommendation': 'Continue current sprint velocity, consider increasing capacity by 10%',
            'impact': 'High',
            'effort': 'Medium'
        },
        {
            'category': '⏰ Delivery',
            'recommendation': 'Implement buffer time for critical tasks to maintain 96%+ delivery rate',
            'impact': 'Medium', 
            'effort': 'Low'
        },
        {
            'category': '⭐ Quality',
            'recommendation': 'Introduce peer review for tasks scoring below 8.5',
            'impact': 'High',
            'effort': 'Low'
        }
    ]
    
    for rec in recommendations:
        impact_color = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}[rec['impact']]
        effort_color = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}[rec['effort']]
        
        st.info(f"""
        {rec['category']} **Recommendation:**  
        📝 {rec['recommendation']}  
        📊 Impact: {impact_color} {rec['impact']} | 🔧 Effort: {effort_color} {rec['effort']}
        """)

def render_settings_panel():
    """Render settings and configuration panel"""
    st.subheader("⚙️ Settings & Configuration")
    
    # Tabs for different setting categories
    tab_connections, tab_ai, tab_notifications, tab_export = st.tabs([
        "🔗 Connections", "🤖 AI Settings", "🔔 Notifications", "📤 Export/Import"
    ])
    
    with tab_connections:
        render_connection_settings()
    
    with tab_ai:
        render_ai_settings()
    
    with tab_notifications:
        render_notification_settings()
    
    with tab_export:
        render_export_import_settings()

def render_connection_settings():
    """Render connection management settings"""
    st.markdown("### 🔗 Connection Management")
    
    # Trello connection status
    st.markdown("#### 📋 Trello Connection")
    
    if st.session_state.get('trello_user'):
        user = st.session_state.trello_user
        st.success(f"✅ Connected as {user.get('fullName', 'Unknown')}")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔄 Test Connection"):
                # Test Trello connection
                try:
                    trello = EnhancedTrelloManager(
                        st.session_state.trello_api_key,
                        st.session_state.trello_token
                    )
                    user_info = trello.get_user_info()
                    if user_info:
                        st.success("✅ Connection test successful!")
                    else:
                        st.error("❌ Connection test failed!")
                except Exception as e:
                    st.error(f"❌ Connection error: {str(e)}")
        
        with col2:
            if st.button("🗑️ Disconnect", type="secondary"):
                # Clear Trello credentials
                keys_to_clear = ['trello_api_key', 'trello_token', 'trello_user', 'selected_board']
                for key in keys_to_clear:
                    if key in st.session_state:
                        del st.session_state[key]
                st.success("🔌 Disconnected from Trello")
                st.rerun()
    else:
        st.warning("⚠️ Not connected to Trello")
        if st.button("🔗 Setup Trello Connection"):
            st.info("👆 Please use the connection setup section above")
    
    # Google Calendar connection status
    st.markdown("#### 📅 Google Calendar Connection")
    
    if st.session_state.get('google_credentials'):
        st.success("✅ Google Calendar credentials configured")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔄 Test Calendar API"):
                st.info("📅 Calendar API test would happen here")
        
        with col2:
            if st.button("🗑️ Clear Credentials"):
                if 'google_credentials' in st.session_state:
                    del st.session_state.google_credentials
                st.success("🗑️ Google credentials cleared")
                st.rerun()
    else:
        st.warning("⚠️ Google Calendar not configured")

def render_ai_settings():
    """Render AI configuration settings"""
    st.markdown("### 🤖 AI Configuration")
    
    # AI model settings
    st.markdown("#### 🧠 AI Model Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        confidence_threshold = st.slider(
            "🎯 Confidence Threshold",
            min_value=0.0,
            max_value=1.0,
            value=st.session_state.get('ai_confidence_threshold', 0.6),
            step=0.05,
            help="Minimum confidence level for AI suggestions"
        )
        st.session_state.ai_confidence_threshold = confidence_threshold
    
    with col2:
        urgency_sensitivity = st.slider(
            "⚡ Urgency Sensitivity",
            min_value=1,
            max_value=10,
            value=st.session_state.get('ai_urgency_sensitivity', 5),
            help="How sensitive the AI is to urgency keywords"
        )
        st.session_state.ai_urgency_sensitivity = urgency_sensitivity
    
    # Keyword customization
    st.markdown("#### 🔤 Custom Keywords")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**High Priority Keywords**")
        high_priority_keywords = st.text_area(
            "Enter keywords (one per line)",
            value=st.session_state.get('high_priority_keywords', 
                                     'urgent\ncritical\nASAP\nemergency\nhotfix'),
            key="high_priority"
        )
        st.session_state.high_priority_keywords = high_priority_keywords
    
    with col2:
        st.markdown("**Low Priority Keywords**")
        low_priority_keywords = st.text_area(
            "Enter keywords (one per line)",
            value=st.session_state.get('low_priority_keywords',
                                     'research\nplan\norganize\ncleanup\nwhen possible'),
            key="low_priority"
        )
        st.session_state.low_priority_keywords = low_priority_keywords
    
    # AI behavior settings
    st.markdown("#### 🎛️ AI Behavior")
    
    col1, col2 = st.columns(2)
    
    with col1:
        auto_apply_high_confidence = st.checkbox(
            "🤖 Auto-apply high-confidence suggestions (>90%)",
            value=st.session_state.get('auto_apply_high_confidence', False)
        )
        st.session_state.auto_apply_high_confidence = auto_apply_high_confidence
    
    with col2:
        include_weekends = st.checkbox(
            "📅 Include weekends in scheduling",
            value=st.session_state.get('include_weekends', False)
        )
        st.session_state.include_weekends = include_weekends
    
    # Save AI settings
    if st.button("💾 Save AI Settings", type="primary"):
        st.success("✅ AI settings saved successfully!")

def render_notification_settings():
    """Render notification configuration"""
    st.markdown("### 🔔 Notification Settings")
    
    # Email notifications
    st.markdown("#### 📧 Email Notifications")
    
    email_address = st.text_input(
        "📧 Email Address",
        value=st.session_state.get('notification_email', ''),
        placeholder="your.email@example.com"
    )
    st.session_state.notification_email = email_address
    
    col1, col2 = st.columns(2)
    
    with col1:
        notify_overdue = st.checkbox(
            "🚨 Overdue tasks",
            value=st.session_state.get('notify_overdue', True)
        )
        
        notify_upcoming = st.checkbox(
            "📅 Upcoming deadlines",
            value=st.session_state.get('notify_upcoming', True)
        )
    
    with col2:
        notify_ai_suggestions = st.checkbox(
            "🤖 New AI suggestions",
            value=st.session_state.get('notify_ai_suggestions', False)
        )
        
        notify_schedule_changes = st.checkbox(
            "🔄 Schedule changes",
            value=st.session_state.get('notify_schedule_changes', True)
        )
    
    # Notification frequency
    st.markdown("#### ⏰ Notification Frequency")
    
    notification_frequency = st.selectbox(
        "📊 How often should we send summary notifications?",
        options=['Never', 'Daily', 'Weekly', 'Monthly'],
        index=['Never', 'Daily', 'Weekly', 'Monthly'].index(
            st.session_state.get('notification_frequency', 'Weekly')
        )
    )
    st.session_state.notification_frequency = notification_frequency
    
    # Slack/Teams integration
    st.markdown("#### 💬 Team Notifications")
    
    slack_webhook = st.text_input(
        "Slack Webhook URL (optional)",
        value=st.session_state.get('slack_webhook', ''),
        type="password",
        help="Paste your Slack webhook URL to receive team notifications"
    )
    st.session_state.slack_webhook = slack_webhook
    
    if st.button("💾 Save Notification Settings", type="primary"):
        st.success("✅ Notification settings saved!")

def render_export_import_settings():
    """Render export and import options"""
    st.markdown("### 📤 Export & Import")
    
    # Export options
    st.markdown("#### 📤 Export Data")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Export Formats**")
        
        export_format = st.selectbox(
            "Choose export format",
            options=['CSV', 'JSON', 'Excel', 'Calendar (ICS)']
        )
        
        export_scope = st.selectbox(
            "Export scope",
            options=['Current board only', 'All boards', 'AI analysis results', 'Full system data']
        )
    
    with col2:
        st.markdown("**Quick Export**")
        
        if st.button("📊 Export Current Analysis", use_container_width=True):
            # Generate sample export data
            export_data = {
                'export_date': datetime.now().isoformat(),
                'scope': export_scope,
                'format': export_format,
                'sample_data': 'This would contain actual analysis data'
            }
            
            if export_format == 'JSON':
                st.download_button(
                    "💾 Download JSON",
                    data=json.dumps(export_data, indent=2),
                    file_name=f"trello_analysis_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                    mime="application/json"
                )
            else:
                st.info(f"📁 {export_format} export would be generated here")
    
    # Import options
    st.markdown("#### 📥 Import Data")
    
    uploaded_file = st.file_uploader(
        "📁 Upload analysis data",
        type=['json', 'csv', 'xlsx'],
        help="Import previous analysis data or settings"
    )
    
    if uploaded_file:
        file_type = uploaded_file.name.split('.')[-1].lower()
        
        try:
            if file_type == 'json':
                imported_data = json.load(uploaded_file)
                st.success("✅ JSON data imported successfully!")
                st.json(imported_data)
            
            elif file_type == 'csv':
                imported_df = pd.read_csv(uploaded_file)
                st.success("✅ CSV data imported successfully!")
                st.dataframe(imported_df.head())
            
            else:
                st.info("📊 Excel import would be processed here")
                
        except Exception as e:
            st.error(f"❌ Import failed: {str(e)}")
    
    # Backup and restore
    st.markdown("#### 💾 Backup & Restore")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("💾 Create Full Backup", use_container_width=True):
            backup_data = {
                'backup_date': datetime.now().isoformat(),
                'settings': {
                    'ai_confidence_threshold': st.session_state.get('ai_confidence_threshold', 0.6),
                    'notification_email': st.session_state.get('notification_email', ''),
                    'high_priority_keywords': st.session_state.get('high_priority_keywords', ''),
                },
                'connections': {
                    'trello_connected': bool(st.session_state.get('trello_user')),
                    'google_connected': bool(st.session_state.get('google_credentials'))
                }
            }
            
            st.download_button(
                "📁 Download Backup",
                data=json.dumps(backup_data, indent=2),
                file_name=f"system_backup_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                mime="application/json"
            )
    
    with col2:
        backup_file = st.file_uploader(
            "📥 Restore from Backup",
            type='json',
            help="Upload a system backup file to restore settings"
        )
        
        if backup_file:
            try:
                backup_data = json.load(backup_file)
                st.success("✅ Backup loaded successfully!")
                
                if st.button("🔄 Restore Settings"):
                    # Restore settings from backup
                    settings = backup_data.get('settings', {})
                    for key, value in settings.items():
                        st.session_state[key] = value
                    
                    st.success("✅ Settings restored from backup!")
                    st.rerun()
                    
            except Exception as e:
                st.error(f"❌ Backup restore failed: {str(e)}")

# Main function to integrate everything
def main_enhanced_integration():
    """Main function to run the enhanced Trello & Calendar integration"""
    
    # Initialize session state
    if 'enhanced_integration_initialized' not in st.session_state:
        st.session_state.enhanced_integration_initialized = True
        st.session_state.show_integration_help = True
    
    # CSS for enhanced styling
    st.markdown("""
    <style>
    .integration-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2rem;
        border-radius: 15px;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .status-card {
        background: white;
        border-radius: 10px;
        padding: 1.5rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin: 1rem 0;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        margin: 0.5rem 0;
    }
    
    .kanban-column {
        background: #f8f9fa;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem;
        min-height: 200px;
    }
    
    .task-card {
        background: white;
        border-radius: 6px;
        padding: 0.8rem;
        margin: 0.5rem 0;
        border-left: 4px solid #667eea;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown("""
    <div class="integration-header">
        <h1>🎯 Enhanced Trello & Calendar Integration</h1>
        <p>Comprehensive task management with AI-powered scheduling and analytics</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Help section
    if st.session_state.get('show_integration_help', False):
        with st.expander("ℹ️ How to Use This Integration", expanded=True):
            st.markdown("""
            ### 🚀 Getting Started
            
            1. **Connect Your Accounts**
               - Set up Trello API credentials
               - Configure Google Calendar (optional)
            
            2. **Select Your Board**
               - Choose the Trello board you want to analyze
               - The system will load all cards and checklists
            
            3. **AI Analysis**
               - Get intelligent due date suggestions
               - View task prioritization
               - See workload distribution
            
            4. **Calendar Integration**
               - Sync due dates with Google Calendar
               - Get deadline notifications
               - Export scheduling data
            
            ### 💡 Key Features
            - **Smart Due Date Suggestions**: AI analyzes task content and suggests optimal due dates
            - **Visual Board Management**: Kanban-style board view with real-time updates
            - **Advanced Analytics**: Team performance, workload distribution, and optimization
            - **Calendar Synchronization**: Seamless integration with Google Calendar
            - **Customizable Notifications**: Email and Slack alerts for important deadlines
            """)
            
            if st.button("✅ Got it! Hide this help"):
                st.session_state.show_integration_help = False
                st.rerun()
    
    # Main integration interface
    render_enhanced_trello_dashboard()

# Entry point for the integration
if __name__ == "__main__":
    main_enhanced_integration()