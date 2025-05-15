import streamlit as st
from datetime import datetime
import uuid

from models import data_manager, LogEntry
from styles import render_role_badge, format_timestamp

def show_logs(current_user=None):
    """Display logs and notes page"""
    if not current_user:
        st.warning("No user profile found. Please log in or create a profile.")
        return
    
    st.header("Logs & Notes")
    
    # Create tabs for viewing and creating logs
    tab1, tab2 = st.tabs(["Recent Logs", "Create New Log"])
    
    with tab1:
        show_recent_logs(current_user)
    
    with tab2:
        create_new_log(current_user)


def show_recent_logs(current_user):
    """Display recent logs with filtering options"""
    st.subheader("Recent Logs")
    
    # Get all logs
    all_logs = data_manager.logs
    
    # Filter options
    col1, col2 = st.columns(2)
    
    with col1:
        # Filter by time period
        time_filter = st.selectbox(
            "Time Period",
            ["All Time", "Today", "Last 3 Days", "Last Week", "Last Month"],
            index=0
        )
    
    with col2:
        # Filter by department/role
        available_roles = set(log.author_role for log in all_logs)
        role_filter = st.multiselect(
            "Department/Role",
            options=list(available_roles),
            default=[]
        )
    
    # Apply filters
    filtered_logs = all_logs
    
    # Apply time filter
    now = datetime.now()
    if time_filter == "Today":
        filtered_logs = [log for log in filtered_logs if log.timestamp.date() == now.date()]
    elif time_filter == "Last 3 Days":
        three_days_ago = now.replace(hour=0, minute=0, second=0, microsecond=0)
        three_days_ago = three_days_ago.replace(day=three_days_ago.day - 3)
        filtered_logs = [log for log in filtered_logs if log.timestamp >= three_days_ago]
    elif time_filter == "Last Week":
        week_ago = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_ago = week_ago.replace(day=week_ago.day - 7)
        filtered_logs = [log for log in filtered_logs if log.timestamp >= week_ago]
    elif time_filter == "Last Month":
        month_ago = now.replace(hour=0, minute=0, second=0, microsecond=0)
        month_ago = month_ago.replace(month=month_ago.month-1 if month_ago.month > 1 else 12)
        if month_ago.month == 12:
            month_ago = month_ago.replace(year=month_ago.year-1)
        filtered_logs = [log for log in filtered_logs if log.timestamp >= month_ago]
    
    # Apply role filter
    if role_filter:
        filtered_logs = [log for log in filtered_logs if log.author_role in role_filter]
    
    # Sort logs by timestamp (newest first)
    filtered_logs = sorted(filtered_logs, key=lambda log: log.timestamp, reverse=True)
    
    # Display logs
    if filtered_logs:
        # Toggle to show/hide read logs
        show_read = st.checkbox("Show logs I've already read", value=True)
        
        # Apply read/unread filter
        if not show_read:
            filtered_logs = [log for log in filtered_logs if current_user.id not in log.read_by]
        
        # Render each log
        for log in filtered_logs:
            is_read = current_user.id in log.read_by
            
            with st.expander(
                f"{log.title} - {format_timestamp(log.timestamp, '%b %d, %I:%M %p')}",
                expanded=not is_read
            ):
                # Display log details
                st.markdown(f"""
                **Author:** {log.author_name} {render_role_badge(log.author_role)}
                
                **Time:** {format_timestamp(log.timestamp)}
                
                **Message:**
                {log.message}
                """, unsafe_allow_html=True)
                
                # Mark as read button (if not already read)
                if not is_read:
                    if st.button("Mark as Read", key=f"mark_read_{log.log_id}"):
                        data_manager.mark_log_as_read(log.log_id, current_user.id)
                        st.success("Marked as read")
                        st.rerun()
    else:
        st.info("No logs found matching the selected filters.")


def create_new_log(current_user):
    """Form for creating a new log entry"""
    st.subheader("Create New Log Entry")
    
    # Log form
    with st.form("new_log_form"):
        title = st.text_input("Title", placeholder="Log entry title")
        message = st.text_area("Message", placeholder="Enter your log message here", height=150)
        
        submitted = st.form_submit_button("Submit Log Entry")
        
        if submitted:
            if title and message:
                # Create new log entry
                log_id = str(uuid.uuid4())
                new_log = LogEntry(
                    log_id=log_id,
                    title=title,
                    message=message,
                    author_id=current_user.id,
                    author_name=current_user.name,
                    author_role=current_user.role
                )
                
                # Add to log database
                data_manager.add_log(new_log)
                
                st.success("Log entry created successfully!")
                # Clear form fields by triggering a rerun
                st.rerun()
            else:
                st.error("Please fill in both title and message fields.")