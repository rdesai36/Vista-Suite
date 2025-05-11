import streamlit as st
from datetime import datetime

from styles import toggle_theme

def show_settings(current_user=None):
    """Display settings page with theme toggle and app preferences"""
    if not current_user:
        st.warning("No user profile found. Please log in or create a profile.")
        return
    
    st.header("Settings")
    
    # Display theme settings
    st.subheader("Appearance")
    
    # Get current theme from session state
    current_theme = st.session_state.theme
    
    # Theme toggle
    col1, col2 = st.columns([1, 4])
    
    with col1:
        theme_emoji = "🌙" if current_theme == "dark" else "☀️"
        st.write(f"Theme: {theme_emoji} {current_theme.capitalize()}")
    
    with col2:
        if st.button("Toggle Theme"):
            toggle_theme()
            st.rerun()
    
    # Notification settings
    st.subheader("Notifications")
    
    # These would eventually save to user preferences
    receive_email = st.checkbox("Receive email notifications", value=True)
    receive_sms = st.checkbox("Receive SMS notifications", value=False)
    
    notification_types = st.multiselect(
        "Notification Types",
        options=["Shift Logs", "Direct Messages", "System Alerts", "Housekeeping", "Maintenance"],
        default=["Shift Logs", "Direct Messages", "System Alerts"]
    )
    
    if st.button("Save Notification Preferences"):
        st.success("Notification preferences saved.")
    
    # Display settings
    st.subheader("Display Settings")
    
    default_page = st.selectbox(
        "Default Landing Page",
        options=["Home", "Logs", "Team", "Profile", "Dashboard"],
        index=0
    )
    
    items_per_page = st.slider(
        "Items Per Page",
        min_value=5,
        max_value=50,
        value=10,
        step=5
    )
    
    if st.button("Save Display Preferences"):
        st.success("Display preferences saved.")
    
    # Account settings with mock logout
    st.subheader("Account")
    
    if st.button("Logout"):
        # In a real app, this would log the user out
        st.info("This would log you out in a complete app.")
        
        # Reset theme to default (light)
        st.session_state.theme = "light"
        
        # For demo purposes, redirect to home
        st.session_state.page = "home"
        st.rerun()
    
    # App information
    st.subheader("About")
    
    st.markdown("""
    **Hotel Management System**
    
    Version: 1.0.0
    
    This application provides a comprehensive suite of tools for hotel management, 
    including front office operations, housekeeping, maintenance tracking, and 
    staff communication.
    
    Last updated: May 2025
    """)