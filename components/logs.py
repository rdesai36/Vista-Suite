import streamlit as st
from datetime import datetime
import uuid

from supabase_client import supabase
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
    
    # Get all logs from Supabase
    try:
        response = supabase.from_('logs').select('*').order('timestamp', desc=True).execute()
        all_logs = response.data
    except Exception as e:
        st.error(f"Error fetching logs: {str(e)}")
        all_logs = []
    
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
        available_roles = set(log['author_role'] for log in all_logs if 'author_role' in log)
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
        filtered_logs = [log for log in filtered_logs if 'timestamp' in log and datetime.fromisoformat(log['timestamp']).date() == now.date()]
    elif time_filter == "Last 3 Days":
        three_days_ago = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=3)
        filtered_logs = [log for log in filtered_logs if 'timestamp' in log and datetime.fromisoformat(log['timestamp']) >= three_days_ago]
    elif time_filter == "Last Week":
        week_ago = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=7)
        filtered_logs = [log for log in filtered_logs if 'timestamp' in log and datetime.fromisoformat(log['timestamp']) >= week_ago]
    elif time_filter == "Last Month":
        month_ago = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=30) # Approximation
        filtered_logs = [log for log in filtered_logs if 'timestamp' in log and datetime.fromisoformat(log['timestamp']) >= month_ago]
    
    # Apply role filter
    if role_filter:
        filtered_logs = [log for log in filtered_logs if 'author_role' in log and log['author_role'] in role_filter]
    
    # Logs are already sorted by timestamp from the Supabase query

    # Display logs
    if filtered_logs:
        # Toggle to show/hide read logs
        show_read = st.checkbox("Show logs I've already read", value=True)
        
        # Apply read/unread filter
        if not show_read:
            filtered_logs = [log for log in filtered_logs if 'read_by' in log and current_user['id'] not in log['read_by']]
        
        # Render each log
        for log in filtered_logs:
            is_read = 'read_by' in log and current_user['id'] in log['read_by']
            
            with st.expander(
                f"{log.get('title', 'No Title')} - {format_timestamp(datetime.fromisoformat(log['timestamp']), '%b %d, %I:%M %p') if 'timestamp' in log else 'No Timestamp'}",
                expanded=not is_read
            ):
                # Display log details
                st.markdown(f"""
                **Author:** {log.get('author_name', 'Unknown')} {render_role_badge(log.get('author_role', 'Unknown'))}
                
                **Time:** {format_timestamp(datetime.fromisoformat(log['timestamp'])) if 'timestamp' in log else 'Unknown'}
                
                **Message:**
                {log.get('message', 'No Message')}
                """, unsafe_allow_html=True)
                
                # Mark as read button (if not already read)
                if not is_read:
                    if st.button("Mark as Read", key=f"mark_read_{log.get('log_id', uuid.uuid4())}"):
                        try:
                            # Add current user's ID to the read_by array
                            read_by_list = log.get('read_by', [])
                            if current_user['id'] not in read_by_list:
                                read_by_list.append(current_user['id'])
                                update_response = supabase.from_('logs').update({'read_by': read_by_list}).eq('log_id', log['log_id']).execute()
                                if update_response.data:
                                    st.success("Marked as read")
                                    st.rerun()
                                else:
                                    st.error(f"Error marking log as read: {update_response.error.message}")
                            else:
                                st.info("Log already marked as read.")
                        except Exception as e:
                            st.error(f"Error marking log as read: {str(e)}")
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
                # Create new log entry data
                new_log_data = {
                    "log_id": str(uuid.uuid4()),
                    "title": title,
                    "message": message,
                    "author_id": current_user['id'],
                    "author_name": current_user['name'],
                    "author_role": current_user['role'],
                    "timestamp": datetime.now().isoformat(),
                    "read_by": [current_user['id']] # Mark as read by author initially
                }
                
                # Add to log database using Supabase
                try:
                    insert_response = supabase.from_('logs').insert([new_log_data]).execute()
                    if insert_response.data:
                        st.success("Log entry created successfully!")
                        # Clear form fields by triggering a rerun
                        st.rerun()
                    else:
                        st.error(f"Error creating log entry: {insert_response.error.message}")
                except Exception as e:
                    st.error(f"Error creating log entry: {str(e)}")
            else:
                st.error("Please fill in both title and message fields.")
