import streamlit as st
from supabase_client import get_supabase_client

supabase = get_supabase_client()

def show_home(current_user):
    st.title(f"Welcome, {current_user.get('name', 'User')}!")
    st.markdown(f"**Role:** {current_user.get('role', 'N/A')}")

    # Today’s Overview Section
    st.subheader("Today’s Overview")
    property_id = st.session_state.get('selected_property', None)

    # 1. Number of check-ins today (fake for now, since bookings not implemented)
    checkins_today = "-"
    checkouts_today = "-"
    rooms_available = "-"
    new_notifications = "-"

    # TODO: Replace with actual booking/room queries when available

    st.markdown(
        f"""
        | Check-Ins Today | Check-Outs Today | Rooms Available | New Notifications |
        | :------------: | :--------------: | :-------------: | :---------------: |
        | {checkins_today} | {checkouts_today} | {rooms_available} | {new_notifications} |
        """
    )

    # Recent Activity Logs (for managers/front desk)
    st.subheader("Recent Activity Logs")
    logs_query = supabase.from_("logs").select("*").order("timestamp", desc=True).limit(5)
    if property_id:
        logs_query = logs_query.eq("property_id", property_id)

    logs_response = logs_query.execute()
    logs = logs_response.data if logs_response and logs_response.data else []

    if logs:
        for log in logs:
            with st.expander(f"{log['title']} — {log['timestamp']}"):
                st.write(f"**Author:** {log['author_id']}")
                st.write(log['content'])
                st.write(f"**Type:** {log['type']}")
    else:
        st.info("No recent logs available.")

    # Management Dashboard (role-based section)
    if current_user.get("role") == "Manager":
        st.subheader("Management Dashboard")
        st.info("Revenue snapshot, staff performance, etc. — coming soon!")

    # Quick Actions/Shortcuts for Front Desk
    if current_user.get("role") == "Front Desk":
        st.subheader("Quick Actions")
        st.button("Check-in Guest (Coming Soon)", disabled=True)
        st.button("Check-out Guest (Coming Soon)", disabled=True)

    # Housekeeping status for Housekeeping role
    if current_user.get("role") == "Housekeeping":
        st.subheader("Housekeeping Status")
        st.info("Housekeeping overview coming soon.")

    # Maintenance status for Maintenance role
    if current_user.get("role") == "Maintenance":
        st.subheader("Maintenance Requests")
        st.info("Maintenance request overview coming soon.")

    # If you want to show custom content for other roles, add here.

