import streamlit as st
from components.dashboard import show_dashboard
from components.reports import show_reports
from datetime import datetime, timedelta
from styles import load_theme_settings, apply_theme, apply_mobile_styles, render_mobile_nav
from components.home import show_home
from components.front_office import show_front_office
from components.occupancy import show_occupancy
from data_handler import hotel_data
from components.settings import show_settings
from components.messaging import show_messaging
from components.logs import show_logs
from components.revenue import show_revenue
from components.room_status import show_room_status
from components.profile import show_profile
from components.team import show_team
from components.login import show_login
from supabase_client import get_supabase_client
from auth import require_auth

# Page configuration
st.set_page_config(
    page_title="Vista Suite",
    page_icon="logobg.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply custom theme and styles
load_theme_settings()
apply_theme()
apply_mobile_styles()

# Initialize session state for navigation and settings
if 'page' not in st.session_state:
    st.session_state.page = "login"  # Default to login page

if 'start_date' not in st.session_state:
    st.session_state.start_date = datetime.now().date() - timedelta(days=30)
if 'end_date' not in st.session_state:
    st.session_state.end_date = datetime.now().date()

# --- MAIN ROUTING ---

if st.session_state.page == "login":
    show_login()
else:
    # === AUTH GATE (Supabase Auth enforced) ===
    if "supabase_user" not in st.session_state:
        st.session_state.page = "login"
        st.rerun()

    supabase = get_supabase_client()

    # Use the authenticated Supabase user's ID
    user_id = st.session_state['supabase_user'].id

    # --- Load (or create) current_user *first* ---
    try:
        user_response = supabase.from_('profiles').select('*').eq('id', user_id).execute()
        profiles = user_response.data if user_response and user_response.data else []
        if profiles and len(profiles) == 1:
            current_user = profiles[0]
        else:
            user_email = getattr(st.session_state['supabase_user'], "email", "")
            user_name = user_email.split("@")[0] if user_email else "Unknown"
            supabase.from_('profiles').insert({
                "id": user_id,
                "name": user_name,
                "email": user_email,
                "role": "Front Desk"
            }).execute()
            user_response = supabase.from_('profiles').select('*').eq('id', user_id).execute()
            profiles = user_response.data if user_response and user_response.data else []
            if profiles and len(profiles) == 1:
                current_user = profiles[0]
            else:
                st.error("Failed to auto-create user profile. Contact admin.")
                st.stop()
    except Exception as e:
        st.error(f"Error getting or creating user profile: {str(e)}")
        st.stop()

    # --- NOW: Define user name variables after current_user is loaded ---
    first_name = current_user.get("first_name", "")
    last_name = current_user.get("last_name", "")
    full_name = (first_name + " " + last_name).strip()
    sidebar_name = (first_name + " " + (last_name[:1] + ".") if last_name else "").strip() or current_user.get("name", "")

    # Update user's last active timestamp (don't fail hard if it breaks)
    try:
        supabase.from_('profiles').update({'last_active': datetime.now().isoformat()}).eq('id', user_id).execute()
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
            avatar_url = current_user.get("avatar_url", "")
            if avatar_url:
                st.image(avatar_url, width=100)
            st.subheader(sidebar_name or current_user.get("email", ""))
            st.caption(current_user.get("role", ""))

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

    # This is just for now — should be fetched from user-property relationships later
    user_properties = ["BOKOH", "CLELW", "CLEMF"]

    if "selected_property" not in st.session_state:
        st.session_state.selected_property = user_properties[0]

    selected_property = st.selectbox("Select Property", user_properties)
    st.session_state.selected_property = selected_property