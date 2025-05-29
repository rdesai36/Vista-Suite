import streamlit as st
from supabase_client import get_supabase_client
import time

def _create_profile_if_not_exists(supabase, user_id, email, user_data):
    """Check for duplicate profile by user_id or email, insert if not exists. Ensures all required fields are present."""
    try:
        # Check for existing profile by user_id or email
        existing = supabase.from_("profiles").select("id").or_(f"id.eq.{user_id},email.eq.{email}").execute()
        if existing.data and len(existing.data) > 0:
            return False, "A profile already exists for this user or email."
        # Build complete profile_data with all required fields
        required_fields = ["id", "email", "name", "first_name", "last_name", "phone", "role"]  # adjust as per your table schema
        profile_data = {"id": user_id, "email": email}
        if user_data:
            profile_data.update(user_data)
        # Set defaults for missing required fields
        if not profile_data.get("name"):
            fname = profile_data.get("first_name", "")
            lname = profile_data.get("last_name", "")
            profile_data["name"] = (fname + " " + lname).strip() or email
        if not profile_data.get("first_name"):
            profile_data["first_name"] = "First"
        if not profile_data.get("last_name"):
            profile_data["last_name"] = "Last"
        if not profile_data.get("phone"):
            profile_data["phone"] = "N/A"
        if not profile_data.get("role"):
            profile_data["role"] = "user"
        # Insert the profile
        result = supabase.from_("profiles").insert(profile_data).execute()
        # supabase-py returns result as an object with .data and .status_code; error is in .data['error'] or .status_code >= 400
        error = None
        if hasattr(result, 'error') and result.error:
            error = result.error
        elif hasattr(result, 'data') and isinstance(result.data, dict) and result.data.get('error'):
            error = result.data['error']
        elif hasattr(result, 'status_code') and result.status_code and result.status_code >= 400:
            error = result.data if hasattr(result, 'data') else result
        if error:
            return False, f"Failed to create profile: {error}"
        return True, "Profile created successfully."
    except Exception as e:
        return False, f"Failed to create profile: {str(e)}"

def sign_up(email, password, user_data=None):
    """Register a new user with Supabase Auth and return the user object if successful."""
    try:
        supabase = get_supabase_client()
        response = supabase.auth.sign_up({
            "email": email,
            "password": password,
            "options": {"data": user_data or {}}
        })
        if response.user:
            return response.user
        return None
    except Exception as e:
        st.error(f"Sign up error: {str(e)}")
        return None

def sign_in(email, password, user_data=None):
    """Sign in a user with email and password and return the user object if successful. On first login, create user profile if missing."""
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
            # After login, check if profile exists, create if missing
            user_id = response.user.id if hasattr(response.user, 'id') else response.user.get('id')
            profile = get_user_profile(user_id)
            if not profile:
                # Use user_data if passed, else check session_state for pending_profile_data
                profile_data = user_data or st.session_state.get("pending_profile_data", {})
                # Add email to profile_data if not present
                if 'email' not in profile_data:
                    profile_data['email'] = email
                ok, msg = _create_profile_if_not_exists(supabase, user_id, email, profile_data)
                if not ok:
                    st.error(msg)
                    return None
                # Remove pending_profile_data after use
                if "pending_profile_data" in st.session_state:
                    del st.session_state["pending_profile_data"]
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
        response = supabase.from_("profiles").select("*").eq("id", user_id).execute()
        # response.data is a list; return first if exists, else None
        if response.data and isinstance(response.data, list) and len(response.data) == 1:
            return response.data[0]
        elif response.data and isinstance(response.data, list) and len(response.data) > 1:
            st.error(f"Multiple profiles found for user_id {user_id}.")
            return response.data[0]
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