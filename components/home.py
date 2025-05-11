import streamlit as st
from datetime import datetime
import random

from data_handler import hotel_data
from models import data_manager
from styles import render_role_badge, format_timestamp, render_card
from utils import format_currency, format_percentage, display_metric_card

def show_home(current_user=None):
    """Display home dashboard with welcome message and key metrics"""
    if not current_user:
        st.warning("No user profile found. Please log in or create a profile.")
        return
    
    # Update last active timestamp
    current_user.last_active = datetime.now()
    
    # Welcome header with user name and role
    st.markdown(f"""
    # Welcome, {current_user.name}
    {render_role_badge(current_user.role)}
    """, unsafe_allow_html=True)
    
    # Last refresh timestamp and refresh button
    col1, col2 = st.columns([3, 1])
    with col1:
        last_refresh = datetime.now()
        st.markdown(f"""
        <div class="last-updated">
            Last refreshed: {format_timestamp(last_refresh)}
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        if st.button("🔄 Refresh"):
            st.rerun()
    
    # Quick stats row
    st.subheader("Today's Overview")
    
    # Load data for metrics
    hotel_data.load_data()
    
    # Get check-in/check-out stats
    checkins, checkouts = hotel_data.get_checkin_checkout_today()
    
    # Get room status stats
    room_data = hotel_data.get_room_status_data()
    
    # Get recent logs (shown to authorized roles)
    recent_logs = data_manager.get_recent_logs(5)
    
    # Display key metrics in 4 columns
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Check-ins Today",
            value=len(checkins)
        )
    
    with col2:
        st.metric(
            label="Check-outs Today",
            value=len(checkouts)
        )
    
    with col3:
        # Count rooms by status if data is available
        if not room_data.empty and 'status' in room_data.columns:
            vacant_count = len(room_data[room_data['status'] == 'Vacant'])
            total_rooms = len(room_data)
            vacancy_pct = (vacant_count / total_rooms * 100) if total_rooms > 0 else 0
            
            st.metric(
                label="Rooms Available",
                value=vacant_count,
                delta=f"{vacancy_pct:.1f}%"
            )
        else:
            st.metric(label="Rooms Available", value="N/A")
    
    with col4:
        # Count unread logs for current user
        unread_count = sum(1 for log in recent_logs if current_user.user_id not in log.read_by)
        
        st.metric(
            label="New Notifications",
            value=unread_count
        )
    
    # Display recent logs if user role has access
    if current_user.role in ["Manager", "Front Desk"]:
        st.subheader("Recent Activity Logs")
        
        if recent_logs:
            for log in recent_logs:
                is_read = current_user.user_id in log.read_by
                
                # Create a card for each log entry
                log_html = f"""
                <div class="log-entry" style="opacity: {'0.7' if is_read else '1'};">
                    <div class="log-entry-header">
                        <span class="log-entry-title">{log.title}</span>
                        <span class="log-entry-meta">
                            {format_timestamp(log.timestamp)} by {log.author_name} 
                            ({render_role_badge(log.author_role)})
                        </span>
                    </div>
                    <div class="log-entry-message">
                        {log.message}
                    </div>
                </div>
                """
                
                st.markdown(log_html, unsafe_allow_html=True)
                
                if not is_read:
                    if st.button("Mark as Read", key=f"read_{log.log_id}"):
                        data_manager.mark_log_as_read(log.log_id, current_user.user_id)
                        st.rerun()
        else:
            st.info("No recent activity logs.")
    
    # Quick links section
    st.subheader("Quick Access")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        report_card = st.container()
        report_card.button("📊 Reports", key="reports_btn", use_container_width=True)
        report_card.caption("Access daily and monthly reports")
    
    with col2:
        guest_card = st.container()
        guest_card.button("📝 Guest Services", key="guest_services_btn", use_container_width=True)
        guest_card.caption("Manage guest requests and feedback")
    
    with col3:
        room_card = st.container()
        room_card.button("🔑 Room Management", key="room_mgmt_btn", use_container_width=True)
        room_card.caption("View and update room status")
    
    # Role-specific content
    if current_user.role == "Manager":
        st.subheader("Management Dashboard")
        
        # Manager-specific metrics
        col1, col2 = st.columns(2)
        
        with col1:
            # Simulated revenue chart placeholder
            st.markdown(render_card("""
                <h3>Revenue Snapshot</h3>
                <p>View monthly and YTD revenue metrics</p>
            """), unsafe_allow_html=True)
        
        with col2:
            # Staff performance metrics placeholder
            st.markdown(render_card("""
                <h3>Staff Performance</h3>
                <p>Monitor team productivity and guest satisfaction</p>
            """), unsafe_allow_html=True)
    
    elif current_user.role == "Front Desk":
        st.subheader("Front Desk Quick Actions")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.button("Check-in Guest")
            st.button("Check-out Guest")
        
        with col2:
            st.button("Room Assignment")
            st.button("Guest Lookup")
    
    elif current_user.role == "Housekeeping":
        st.subheader("Housekeeping Status")
        
        # Display rooms that need cleaning if data is available
        if not room_data.empty and 'status' in room_data.columns:
            dirty_rooms = room_data[room_data['status'] == 'Dirty']
            
            if not dirty_rooms.empty:
                st.markdown("### Rooms Pending Cleaning")
                st.dataframe(dirty_rooms, hide_index=True)
            else:
                st.success("No rooms pending cleaning at this time.")
        else:
            st.info("No room data available.")
    
    # Display custom message for other roles
    elif current_user.role == "Maintenance":
        st.subheader("Maintenance Requests")
        
        # Placeholder for maintenance requests
        st.info("No pending maintenance requests at this time.")
        
        if st.button("Create Maintenance Request"):
            st.session_state.page = "maintenance"
            st.rerun()