import streamlit as st
from supabase_client import get_supabase_client
import time
from streamlit.server.server import Server
import extra_streamlit_components as stx
from tornado import httputil #Handle Headers

def sign_up(email, password, user_data=None):
    """Register a new user with Supabase Auth and return the user object if successful."""
    try:
        supabase = get_supabase_client()
        response = supabase.auth.sign_up({
            "email": email,
            "password": password,
            "options": {
                "data": user_data or {}
            }
        })
        if response.user:
            return response.user  # Return user object
        return None
    except Exception as e:
        st.error(f"Sign up error: {str(e)}")
        return None

def sign_in(email, password):
    """Sign in a user with email and password and return the user object if successful."""
    try:
        supabase = get_supabase_client()
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        if response.user:
            # Store session in streamlit session state
            st.session_state["supabase_user"] = response.user
            st.session_state["supabase_access_token"] = response.session.access_token
            st.session_state["supabase_refresh_token"] = response.session.refresh_token
            st.session_state["supabase_expires_at"] = time.time() + response.session.expires_in
            return response.user
        return None
    except Exception as e:
        st.error(f"Sign in error: {str(e)}")
        return None

def sign_out():
    """Sign out the current user and clear session state."""
    try:
        supabase = get_supabase_client()
        supabase.auth.sign_out()
        for key in [
            "supabase_user", "supabase_access_token", 
            "supabase_refresh_token", "supabase_expires_at", "user_profile"
        ]:
            if key in st.session_state:
                del st.session_state[key]
        return True
    except Exception as e:
        st.error(f"Sign out error: {str(e)}")
        return False

def get_current_user():
    """
    Get the current authenticated user from session state.
    Handles token refresh if needed.
    """
    if "supabase_user" not in st.session_state:
        return None
    # Optionally refresh token here if needed
    return st.session_state["supabase_user"]

def get_user_profile(user_id):
    """Get user profile data from the profiles table."""
    try:
        supabase = get_supabase_client()
        response = supabase.from_("profiles").select("*").eq("id", user_id).single().execute()
        if response.data:
            return response.data
        return None
    except Exception as e:
        st.error(f"Error getting user profile: {str(e)}")
        return None

def update_user_profile(user_id, profile_data):
    """Update a user's profile in the profiles table."""
    try:
        supabase = get_supabase_client()
        response = supabase.from_("profiles").update(profile_data).eq('id', user_id).execute()
        if response.data:
            return response.data
        return None
    except Exception as e:
        st.error(f"Error updating user profile: {str(e)}")
        return None

def require_auth():
    """
    Require authentication. If not authenticated, redirect to login page.
    """
    user = get_current_user()
    if not user:
        st.session_state.page = "login"
        st.rerun()
    return user

def get_headers():
    # Hack to get the session object from Streamlit.
    headers=[]
    current_server = Server.get_current()
    if hasattr(current_server, '_session_infos'):
        # Streamlit < 0.56
        session_infos = Server.get_current()._session_infos.values()
    else:
        session_infos = Server.get_current()._session_info_by_id.values()
    # Multiple Session Objects?
    for session_info in session_infos:
        headers.append(session_info.ws.request.headers)

def restore_supabase_session_from_cookie():
    import base64, json, time
    cookie_manager = get_manager()
    cookies = cookie_manager.get_all()
    token = None
    for key in cookies:
        if key.startswith('sb-') and key.endswith('-auth-token'):
            token = cookies[key]
            break
    if token:
        try:
            # JWT format: header.payload.signature
            payload_b64 = token.split('.')[1]
            padding = '=' * (4 - (len(payload_b64) % 4)) if len(payload_b64) % 4 else ''
            payload_b64 += padding
            payload_json = base64.urlsafe_b64decode(payload_b64)
            payload = json.loads(payload_json)
            email = payload.get('email')
            exp = payload.get('exp')  # expiry timestamp (seconds since epoch)
            now = int(time.time())
            if exp and now < exp:
                # Session is still valid
                st.session_state['email'] = email
                # Simulate a minimal supabase_user object for session restoration
                st.session_state['supabase_user'] = type('User', (), {})()
                st.session_state['supabase_user'].id = payload.get('sub', '')
                st.session_state['supabase_user'].email = email
                # Optionally: st.session_state['supabase_access_token'] = token
                return True
            else:
                # Token expired - clear session
                st.session_state.pop('supabase_user', None)
                st.session_state.pop('email', None)
                return False
        except Exception as e:
            print(f"Error decoding/restoring Supabase session from JWT: {e}")
            st.session_state.pop('supabase_user', None)
            st.session_state.pop('email', None)
            return False
    return False

def get_email_from_cookies():
    # For backward compatibility, call the new restore logic
    restore_supabase_session_from_cookie()


get_email_from_cookies()