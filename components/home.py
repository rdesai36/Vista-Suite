import streamlit as st
from supabase_client import get_supabase_client

supabase = get_supabase_client()

def show_home(current_user):
    """
    Display the home page with today's overview, recent logs, and role-based quick actions.
    Args:
        current_user (dict): The current user's profile information.
    """
    st.markdown("---")
    user_email = st.session_state.get('email', current_user.get('email', ''))
    st.header(f"Welcome, {current_user.get('first_name', user_email)}!")
    st.markdown(f":orange-badge[{current_user.get('role', 'N/A')}]")
    st.markdown("\n")

    # Today’s Overview Section
    st.subheader("Today’s Overview")

    # 1. Number of check-ins today (fake for now, since bookings not implemented)
    checkins_today = "-"
    checkouts_today = "-"
    rooms_available = "-"

    # TODO: Replace with actual booking/room queries when available

    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        with st.container(border=True):
            st.metric("Check-Ins Today", checkins_today)
    with col2:
        with st.container(border=True):
            st.metric("Check-Outs Today", checkouts_today)
    with col3:
        with st.container(border=True):
            st.metric("Rooms Available", rooms_available)
    st.info("Once your property is connected to HotelKey, quick stats will appear here.")
    st.markdown("---")

    # Recent Activity Logs
    st.subheader("Recent Logbook Entries")
    logs_query = supabase.from_("logs").select("*").order("timestamp", desc=True).limit(5)
    logs_response = logs_query.execute()
    logs = logs_response.data if logs_response and logs_response.data else []

    # Standardized empty state handling
    if logs:
        for log in logs:
            with st.expander(f"{log['title']} — {log['timestamp']}"):
                st.write(f"**Author:** {log['author_id']}")
                st.write(log['message'])
                st.write(f"**Type:** {log['type']}")
    else:
        st.warning("No recent logs available.")
        st.info("Once your property is connected to HotelKey, quick stats will appear here.")
    st.markdown("---")

    # Management Dashboard (role-based section)
    if current_user.get("role") == "Manager":
        st.subheader("Management Dashboard")
        st.info("Revenue snapshot, staff performance, etc. — coming soon!", icon="ℹ️")
        st.caption("This section will display management KPIs and team analytics in a future release.")
    else:
        st.subheader("Housekeeping Status")
        st.info("Housekeeping overview coming soon.", icon="🧹")
        st.caption("This section will show room cleaning schedules and task assignments in the future.")
        st.markdown("---")
        st.subheader("Maintenance Requests")
        st.info("Maintenance request overview coming soon.", icon="🛠️")
        st.caption("This section will show open maintenance tickets and status updates in a future release.")
        st.markdown("---")

    # If you want to show custom content for other roles, add here.