import streamlit as st
from datetime import datetime, timedelta
import os

# Import components
from components.dashboard import show_dashboard
from components.occupancy import show_occupancy
from components.revenue import show_revenue
from components.front_office import show_front_office
from components.room_status import show_room_status
from components.reports import show_reports

# Import new components for user system
from components.home import show_home
from components.logs import show_logs
from components.messaging import show_messaging
from components.profile import show_profile
from components.team import show_team
from components.settings import show_settings

# Import models and styling
from models import data_manager
from database import db_manager
from styles import load_theme_settings, apply_theme, apply_mobile_styles, render_mobile_nav
from auth import authenticate

# Page configuration
st.set_page_config(
    page_title="Vista Suite",
    page_icon="logobg.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

# === Auth Gate ===
if "user" not in st.session_state:
    if "page" not in st.session_state:
        st.session_state.page = "login"

    if st.session_state.page == "login":
        st.title("Vista Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Login"):
                user = authenticate(username, password)
                if user:
                    st.session_state.user = user
                    st.rerun()
                else:
                    st.error("Invalid login credentials")

        with col2:
            if st.button("Sign Up"):
                st.session_state.page = "signup"
                st.rerun()

        st.stop()

    elif st.session_state.page == "signup":
        st.title("Vista Signup")
        name = st.text_input("Full Name")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        property_code = st.text_input("Property Code")
        invite_code = st.text_input("Invite Code")

        if st.button("Create Account"):
            from models_db import User, Property, InviteCode
            from database import db_manager
            from auth import hash_password

            prop = db_manager.db.query(Property).filter_by(code=property_code.upper()).first()
            invite = db_manager.db.query(InviteCode).filter_by(code=invite_code.upper()).first()

            if not prop:
                st.error("Invalid property code.")
            elif not invite or not invite.code.startswith(prop.company):
                st.error("Invalid or mismatched invite code.")
            else:
                role_map = {
                    "E": "Executive",
                    "F": "Frontline",
                    "M": "Manager",
                    "A": "Accounting"
                }
                role_letter = invite.code.split("-")[-1].upper()
                role = role_map.get(role_letter)

                if not role:
                    st.error("Invalid role in invite code.")
                else:
                    if db_manager.db.query(User).filter_by(username=username).first():
                        st.error("Username already exists.")
                    else:
                        user = User(
                            username=username,
                            name=name,
                            hashed_password=hash_password(password),
                            role=role
                        )
                        db_manager.db.add(user)
                        db_manager.db.commit()
                        st.success("Account created successfully. Please login.")
                        st.session_state.page = "login"
                        st.rerun()

        if st.button("Back to Login"):
            st.session_state.page = "login"
            st.rerun()

        # ✅ Stop here so dashboard doesn't render under signup
        st.stop()

# Initialize session state for navigation and settings
if 'page' not in st.session_state:
    st.session_state.page = "home"  # Default to home page

if 'start_date' not in st.session_state:
    st.session_state.start_date = datetime.now().date() - timedelta(days=30)
if 'end_date' not in st.session_state:
    st.session_state.end_date = datetime.now().date()

# Initialize or get database manager from session state
if 'db_manager' not in st.session_state:
    st.session_state.db_manager = db_manager

# Initialize or get current user from session state
if 'current_user_id' not in st.session_state:
    # For demo purposes, use the first user or a default
    try:
        users = data_manager.users if hasattr(data_manager, 'users') else []
        if users:
            st.session_state.current_user_id = users[0].user_id
        else:
            st.session_state.current_user_id = "user1"  # Default fallback
    except Exception as e:
        st.error(f"Error loading users: {str(e)}")
        st.session_state.current_user_id = "user1"  # Default fallback

# Get current user profile
try:
    current_user = data_manager.get_user(st.session_state.current_user_id)
except Exception as e:
    st.error(f"Error getting user: {str(e)}")
    current_user = None

# Create a default user if none exists (for demonstration)
if current_user is None:
    from models import UserProfile
    current_user = UserProfile(
    user_id="rdesai",
    name="Rishikesh Desai",
    role="Developer",
    email="rrd0363@gmail.com",
    avatar="https://ui-avatars.com/api/?name=Rishikesh+Desai&background=0D8ABC&color=fff"
    )

# Update user's last active timestamp
if current_user and hasattr(current_user, 'user_id'):
    try:
        db_manager.update_user_last_active(current_user.user_id)
    except Exception as e:
        st.warning(f"Could not update last active timestamp: {str(e)}")

# Handle mobile navigation (receives message from JavaScript)
if 'mobile_nav' in st.session_state:
    try:
        import json
        nav_data = json.loads(st.session_state.mobile_nav)
        if 'page' in nav_data:
            st.session_state.page = nav_data['page']
            # Clear the message to prevent loops
            del st.session_state.mobile_nav
    except:
        pass

# Sidebar for navigation and filters
with st.sidebar:
    # User profile summary in sidebar
    if current_user:
        st.image(current_user.avatar, width=100)
        st.subheader(current_user.name)
        st.caption(current_user.role)
    
    st.header("Navigation")
    
    # Primary Navigation
    if st.button("🏠 Home", use_container_width=True, 
                 type="primary" if st.session_state.page == "home" else "secondary"):
        st.session_state.page = "home"
        st.rerun()
    
    if st.button("📝 Logs & Notes", use_container_width=True,
                 type="primary" if st.session_state.page == "logs" else "secondary"):
        st.session_state.page = "logs"
        st.rerun()
    
    if st.button("👤 My Profile", use_container_width=True,
                 type="primary" if st.session_state.page == "profile" else "secondary"):
        st.session_state.page = "profile"
        st.rerun()
    
    if st.button("👥 Team Directory", use_container_width=True,
                 type="primary" if st.session_state.page == "team" else "secondary"):
        st.session_state.page = "team"
        st.rerun()
        
    if st.button("💬 Messages", use_container_width=True,
                 type="primary" if st.session_state.page == "messaging" else "secondary"):
        st.session_state.page = "messaging"
        st.rerun()

    if st.button("Logout"):
        st.session_state.clear()
        st.rerun()
    
    st.markdown("---")
    
    # Hotel Metrics Navigation
    st.subheader("Hotel Metrics")
    
    if st.button("📊 Dashboard", use_container_width=True,
                 type="primary" if st.session_state.page == "dashboard" else "secondary"):
        st.session_state.page = "dashboard"
        st.rerun()
    
    if st.button("🏢 Occupancy", use_container_width=True,
                 type="primary" if st.session_state.page == "occupancy" else "secondary"):
        st.session_state.page = "occupancy"
        st.rerun()
    
    if st.button("💰 Revenue", use_container_width=True,
                 type="primary" if st.session_state.page == "revenue" else "secondary"):
        st.session_state.page = "revenue"
        st.rerun()
    
    if st.button("🔑 Front Office", use_container_width=True,
                 type="primary" if st.session_state.page == "front_office" else "secondary"):
        st.session_state.page = "front_office"
        st.rerun()
    
    if st.button("🛏️ Room Status", use_container_width=True,
                 type="primary" if st.session_state.page == "room_status" else "secondary"):
        st.session_state.page = "room_status"
        st.rerun()
    
    if st.button("📑 Reports", use_container_width=True,
                 type="primary" if st.session_state.page == "reports" else "secondary"):
        st.session_state.page = "reports"
        st.rerun()
    
    # Only show date filters for pages that need them
    if st.session_state.page in ["dashboard", "occupancy", "revenue", "reports"]:
        st.markdown("---")
        st.subheader("Date Range")
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input(
                "Start Date",
                value=st.session_state.start_date,
                key="sidebar_start_date"
            )
        with col2:
            end_date = st.date_input(
                "End Date",
                value=st.session_state.end_date,
                key="sidebar_end_date"
            )
        
        # Update session state with new date values
        if start_date != st.session_state.start_date or end_date != st.session_state.end_date:
            st.session_state.start_date = start_date
            st.session_state.end_date = end_date
        
        # Validate date range
        if st.session_state.start_date > st.session_state.end_date:
            st.error("Error: End date must be after start date")
            st.session_state.start_date = st.session_state.end_date - timedelta(days=1)
    
    st.markdown("---")
    
    # Settings button at bottom of sidebar
    if st.button("⚙️ Settings", use_container_width=True,
                 type="primary" if st.session_state.page == "settings" else "secondary"):
        st.session_state.page = "settings"
        st.rerun()

# Render mobile navigation bar
render_mobile_nav(st.session_state.page)

# Display the selected page
if st.session_state.page == "home":
    show_home(current_user)
elif st.session_state.page == "logs":
    show_logs(current_user)
elif st.session_state.page == "profile":
    # Check if we're viewing another user's profile
    view_user_id = st.session_state.get("view_user_id")
    show_profile(current_user, view_user_id)
    # Reset view_user_id after displaying the profile
    if "view_user_id" in st.session_state:
        del st.session_state.view_user_id
elif st.session_state.page == "team":
    show_team(current_user)
elif st.session_state.page == "messaging":
    show_messaging(current_user)
elif st.session_state.page == "settings":
    show_settings(current_user)
# Original metrics pages
elif st.session_state.page == "dashboard":
    show_dashboard(st.session_state.start_date, st.session_state.end_date)
elif st.session_state.page == "occupancy":
    show_occupancy(st.session_state.start_date, st.session_state.end_date)
elif st.session_state.page == "revenue":
    show_revenue(st.session_state.start_date, st.session_state.end_date)
elif st.session_state.page == "front_office":
    show_front_office()
elif st.session_state.page == "room_status":
    show_room_status()
elif st.session_state.page == "reports":
    show_reports(st.session_state.start_date, st.session_state.end_date)
else:
    # Default to home if page not found
    show_home(current_user)

    if "selected_property" not in st.session_state:
        st.session_state.selected_property = user_properties[0]

# This is just for now — should be fetched from user-property relationships later
user_properties = ["BOKOH", "CLELW", "CLEMF"]

selected_property = st.selectbox("Select Property", user_properties)
st.session_state.selected_property = selected_property