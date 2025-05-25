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
    cookie_manager = stx.CookieManager() # Use stx.CookieManager()
    cookies = cookie_manager.get_all()
    token = None
    # Try to find the access token first
    for key, value in cookies.items():
        if key.startswith('sb-') and key.endswith('-auth-token'): # Standard Supabase cookie name pattern
            token = value
            break

    if token:
        try:
            supabase = get_supabase_client()
            response = supabase.auth.get_user(token) # Validate token and get user
            if response and response.user:
                st.session_state.supabase_user = response.user
                st.session_state.supabase_access_token = token # Store the token that was validated
                st.session_state.email = response.user.email

                # Attempt to get full session details including refresh token and expiry
                # This might be optimistic as get_user(token) primarily validates the access token.
                # A full session might require re-authentication or a separate cookie for refresh token.
                session = supabase.auth.get_session()
                if session and session.refresh_token and session.expires_at:
                    st.session_state.supabase_refresh_token = session.refresh_token
                    st.session_state.supabase_expires_at = session.expires_at
                else:
                    # If full session details aren't available, clear potentially stale ones
                    # or rely on what might already be in other cookies if handled elsewhere.
                    # For now, we'll clear them if not directly part of the get_user or subsequent get_session response.
                    st.session_state.pop('supabase_refresh_token', None)
                    st.session_state.pop('supabase_expires_at', None)
                return True
            else:
                # Token was invalid or user could not be fetched
                st.session_state.pop('supabase_user', None)
                st.session_state.pop('email', None)
                st.session_state.pop('supabase_access_token', None)
                st.session_state.pop('supabase_refresh_token', None)
                st.session_state.pop('supabase_expires_at', None)
                print("Failed to restore session: No user from token.")
                return False
        except Exception as e:
            # Handle any exception during Supabase client call
            print(f"Error restoring Supabase session from cookie: {e}")
            st.session_state.pop('supabase_user', None)
            st.session_state.pop('email', None)
            st.session_state.pop('supabase_access_token', None)
            st.session_state.pop('supabase_refresh_token', None)
            st.session_state.pop('supabase_expires_at', None)
            return False
    return False

def get_email_from_cookies():
    # For backward compatibility, call the new restore logic
    # This function will now use the updated restore_supabase_session_from_cookie
    restore_supabase_session_from_cookie()
    # It might be better to return the email if found, or None
    # return st.session_state.get('email') # Optional: make it return the email


get_email_from_cookies()