import streamlit as st
from datetime import datetime
from supabase_client import get_supabase_client
from styles import toggle_theme

def show_settings(current_user=None):
    """Display settings page with theme toggle and app preferences"""
    if not current_user:
        st.warning("No user profile found. Please log in or create a profile.")
        return
    
    st.header("Settings")
    
    st.markdown("---")
    
    # Notification settings
    st.subheader("Notifications")
    
 # TODO: These would eventually save to user preferences
 #   receive_email = st.checkbox("Receive email notifications", value=True)
 #   receive_sms = st.checkbox("Receive SMS notifications", value=False)
    
 #   notification_types = st.multiselect(
 #       "Notification Types",
 #       options=["Shift Logs", "Direct Messages", "System Alerts", "Housekeeping", "Maintenance"],
 #       default=["Shift Logs", "Direct Messages", "System Alerts"]
 #   )
    
 #   if st.button("Save Notification Preferences"):
 #       st.success("Notification preferences saved.")
        
    st.markdown("---")
    
    # TODO: Account settings with logout
    st.subheader("Account")
    
    st.markdown("---")
    
    # App information
    st.subheader("About")
    
    st.markdown("""
    **Vista Hotel Management System**
    
    Version: 0.2.0
    """)