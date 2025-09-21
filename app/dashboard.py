import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import List, Dict, Any

from database import DatabaseManager, TaskAnalysis

def render_analytics_dashboard(db_manager: DatabaseManager):
    """Render comprehensive analytics dashboard"""
    st.header("📊 Analytics Dashboard")
    
    # Get analytics data
    stats = db_manager.get_analytics_summary()
    analyses = db_manager.get_analyses(limit=1000)  # Get more data for analytics
    
    if not analyses:
        st.info("📈 No data available yet. Start analyzing tasks to see insights!")
        return
    
    # Key metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Analyses", 
            stats.get('total_analyses', 0),
            delta=stats.get('recent_activity', 0),
            delta_color="normal"
        )
    
    with col2:
        approval_rate = stats.get('approval_rate', 0)
        st.metric(
            "Approval Rate", 
            f"{approval_rate:.1f}%",
            delta=None
        )
    
    with col3:
        avg_confidence = stats.get('average_confidence', 0)
        st.metric(
            "Avg. Confidence", 
            f"{avg_confidence:.1%}",
            delta=None
        )
    
    with col4:
        exported_count = stats.get('exported_count', 0)
        st.metric(
            "Exported to Calendar", 
            exported_count,
            delta=None
        )
    
    st.markdown("---")
    
    # Charts row
    col1, col2 = st.columns(2)
    
    with col1:
        _render_urgency_distribution(stats.get('urgency_distribution', {}))
    
    with col2:
        _render_confidence_over_time(analyses)
    
    # Second row of charts
    col1, col2 = st.columns(2)
    
    with col1:
        _render_approval_timeline(analyses)
    
    with col2:
        _render_task_sources(analyses)
    
    # Detailed analysis table
    st.markdown("---")
    _render_detailed_table(analyses)

def _render_urgency_distribution(urgency_dist: Dict[int, int]):
    """Render urgency score distribution chart"""
    st.subheader("⚡ Urgency Score Distribution")
    
    if not urgency_dist:
        st.info("No urgency data available")
        return
    
    # Prepare data
    urgency_scores = list(range(1, 11))  # 1-10 scale
    counts = [urgency_dist.get(score, 0) for score in urgency_scores]
    
    # Create bar chart
    fig = go.Figure(data=[
        go.Bar(
            x=urgency_scores,
            y=counts,
            marker_color=px.colors.sequential.Reds_r,
            text=counts,
            textposition='auto'
        )
    ])
    
    fig.update_layout(
        title="Task Distribution by Urgency Level",
        xaxis_title="Urgency Score (1-10)",
        yaxis_title="Number of Tasks",
        height=400,
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True)

def _render_confidence_over_time(analyses: List[TaskAnalysis]):
    """Render confidence trends over time"""
    st.subheader("🎯 AI Confidence Trends")
    
    if not analyses:
        st.info("No confidence data available")
        return
    
    # Prepare data
    df_data = []
    for analysis in analyses:
        if analysis.created_at:
            df_data.append({
                'date': analysis.created_at[:10],  # Extract date part
                'confidence': analysis.confidence,
                'urgency_score': analysis.urgency_score
            })
    
    if not df_data:
        st.info("No timestamped data available")
        return
    
    df = pd.DataFrame(df_data)
    df['date'] = pd.to_datetime(df['date'])
    
    # Group by date and calculate average confidence
    daily_stats = df.groupby('date').agg({
        'confidence': 'mean',
        'urgency_score': 'mean'
    }).reset_index()
    
    # Create line chart
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=daily_stats['date'],
        y=daily_stats['confidence'],
        mode='lines+markers',
        name='Average Confidence',
        line=dict(color='#1f77b4', width=3),
        marker=dict(size=8)
    ))
    
    fig.update_layout(
        title="AI Confidence Over Time",
        xaxis_title="Date",
        yaxis_title="Confidence Level",
        height=400,
        yaxis=dict(tickformat='.0%')
    )
    
    st.plotly_chart(fig, use_container_width=True)

def _render_approval_timeline(analyses: List[TaskAnalysis]):
    """Render approval patterns over time"""
    st.subheader("✅ Approval Patterns")
    
    if not analyses:
        st.info("No approval data available")
        return
    
    # Prepare data
    df_data = []
    for analysis in analyses:
        if analysis.created_at:
            df_data.append({
                'date': analysis.created_at[:10],
                'approved': analysis.user_approved,
                'confidence': analysis.confidence
            })
    
    if not df_data:
        st.info("No timestamped approval data")
        return
    
    df = pd.DataFrame(df_data)
    df['date'] = pd.to_datetime(df['date'])
    
    # Group by date
    daily_approvals = df.groupby('date').agg({
        'approved': ['sum', 'count'],
        'confidence': 'mean'
    }).reset_index()
    
    daily_approvals.columns = ['date', 'approved_count', 'total_count', 'avg_confidence']
    daily_approvals['approval_rate'] = daily_approvals['approved_count'] / daily_approvals['total_count']
    
    # Create stacked bar chart
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=daily_approvals['date'],
        y=daily_approvals['approved_count'],
        name='Approved',
        marker_color='#2ca02c'
    ))
    
    fig.add_trace(go.Bar(
        x=daily_approvals['date'],
        y=daily_approvals['total_count'] - daily_approvals['approved_count'],
        name='Not Approved',
        marker_color='#d62728'
    ))
    
    fig.update_layout(
        title="Daily Task Approvals",
        xaxis_title="Date",
        yaxis_title="Number of Tasks",
        height=400,
        barmode='stack'
    )
    
    st.plotly_chart(fig, use_container_width=True)

def _render_task_sources(analyses: List[TaskAnalysis]):
    """Render task sources (Trello vs manual entry)"""
    st.subheader("📋 Task Sources")
    
    if not analyses:
        st.info("No source data available")
        return
    
    # Categorize sources
    trello_count = sum(1 for a in analyses if a.trello_card_id)
    manual_count = len(analyses) - trello_count
    
    # Create pie chart
    labels = ['Trello Integration', 'Manual Entry']
    values = [trello_count, manual_count]
    colors = ['#ff7f0e', '#1f77b4']
    
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        marker_colors=colors,
        textinfo='label+percent',
        textposition='inside'
    )])
    
    fig.update_layout(
        title="Task Entry Methods",
        height=400,
        showlegend=True
    )
    
    st.plotly_chart(fig, use_container_width=True)

def _render_detailed_table(analyses: List[TaskAnalysis]):
    """Render detailed analysis table with filters"""
    st.subheader("🔍 Detailed Analysis History")
    
    if not analyses:
        st.info("No analysis history available")
        return
    
    # Filter controls
    col1, col2, col3 = st.columns(3)
    
    with col1:
        filter_approved = st.selectbox(
            "Filter by Status:",
            options=["All", "Approved Only", "Not Approved"],
            index=0
        )
    
    with col2:
        min_confidence = st.slider(
            "Minimum Confidence:",
            min_value=0.0,
            max_value=1.0,
            value=0.0,
            step=0.1,
            format="%.1f"
        )
    
    with col3:
        min_urgency = st.slider(
            "Minimum Urgency:",
            min_value=0,
            max_value=10,
            value=0,
            step=1
        )
    
    # Apply filters
    filtered_analyses = analyses
    
    if filter_approved == "Approved Only":
        filtered_analyses = [a for a in filtered_analyses if a.user_approved]
    elif filter_approved == "Not Approved":
        filtered_analyses = [a for a in filtered_analyses if not a.user_approved]
    
    filtered_analyses = [a for a in filtered_analyses if a.confidence >= min_confidence]
    filtered_analyses = [a for a in filtered_analyses if a.urgency_score >= min_urgency]
    
    # Prepare table data
    table_data = []
    for analysis in filtered_analyses[:50]:  # Limit to 50 most recent
        table_data.append({
            'ID': analysis.id,
            'Task': analysis.task_text[:60] + ("..." if len(analysis.task_text) > 60 else ""),
            'Suggested Date': analysis.suggested_date,
            'Final Date': analysis.final_due_date or "Not set",
            'Confidence': f"{analysis.confidence:.1%}",
            'Urgency': f"{analysis.urgency_score}/10",
            'Approved': "✅" if analysis.user_approved else "⏳",
            'Source': "🔗 Trello" if analysis.trello_card_id else "✏️ Manual",
            'Exported': "📅" if analysis.exported_to_calendar else "❌",
            'Created': analysis.created_at[:10] if analysis.created_at else "Unknown"
        })
    
    if table_data:
        df = pd.DataFrame(table_data)
        st.dataframe(df, use_container_width=True)
        
        # Export options
        col1, col2 = st.columns(2)
        with col1:
            csv_data = df.to_csv(index=False)
            st.download_button(
                label="📊 Download Filtered Data (CSV)",
                data=csv_data,
                file_name=f"ai_analysis_report_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        
        with col2:
            st.info(f"Showing {len(table_data)} of {len(analyses)} total analyses")
    else:
        st.warning("No analyses match the current filters")

def render_database_management(db_manager: DatabaseManager):
    """Render database management interface"""
    st.header("🗄️ Database Management")
    
    # Database info
    db_info = db_manager.get_database_size()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Database Size", f"{db_info.get('file_size_mb', 0):.2f} MB")
    
    with col2:
        total_records = sum(db_info.get('table_counts', {}).values())
        st.metric("Total Records", total_records)
    
    with col3:
        st.metric("Tables", len(db_info.get('table_counts', {})))
    
    # Table details
    if db_info.get('table_counts'):
        st.subheader("📊 Table Statistics")
        table_df = pd.DataFrame([
            {'Table': table, 'Records': count}
            for table, count in db_info['table_counts'].items()
        ])
        st.dataframe(table_df, use_container_width=True)
    
    # Management actions
    st.subheader("🔧 Management Actions")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🗑️ Clear All Data", type="secondary"):
            st.warning("⚠️ This will permanently delete ALL data!")
            if st.button("⚠️ Confirm Delete All", type="secondary"):
                # This would implement data deletion
                st.error("Data deletion not implemented in demo")
    
    with col2:
        backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        if st.button("💾 Create Backup"):
            success = db_manager.backup_database(backup_name)
            if success:
                st.success(f"✅ Backup created: {backup_name}")
            else:
                st.error("❌ Backup failed")
    
    # Search functionality
    st.subheader("🔍 Search Analysis History")
    search_term = st.text_input("Search tasks, reasoning, or card names:")
    
    if search_term:
        search_results = db_manager.search_analyses(search_term)
        if search_results:
            st.success(f"Found {len(search_results)} matching analyses")
            
            # Display search results
            results_data = []
            for result in search_results[:20]:  # Limit to 20 results
                results_data.append({
                    'Task': result.task_text[:50] + ("..." if len(result.task_text) > 50 else ""),
                    'Date': result.suggested_date,
                    'Confidence': f"{result.confidence:.1%}",
                    'Approved': "✅" if result.user_approved else "⏳",
                    'Created': result.created_at[:10] if result.created_at else "Unknown"
                })
            
            if results_data:
                search_df = pd.DataFrame(results_data)
                st.dataframe(search_df, use_container_width=True)
        else:
            st.info("No matching analyses found")

# Integration function for main app
def integrate_dashboard_to_main_app(db_manager: DatabaseManager):
    """Integrate dashboard into main app"""
    with st.sidebar:
        st.markdown("---")
        if st.button("📊 View Analytics"):
            st.session_state.show_dashboard = True
        
        if st.button("🗄️ Database Manager"):
            st.session_state.show_db_manager = True
    
    # Show dashboard if requested
    if st.session_state.get('show_dashboard', False):
        st.markdown("---")
        render_analytics_dashboard(db_manager)
        
        if st.button("❌ Close Dashboard"):
            st.session_state.show_dashboard = False
            st.rerun()
    
    # Show database manager if requested
    if st.session_state.get('show_db_manager', False):
        st.markdown("---")
        render_database_management(db_manager)
        
        if st.button("❌ Close Database Manager"):
            st.session_state.show_db_manager = False
            st.rerun()