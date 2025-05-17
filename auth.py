import bcrypt
from database import db_manager
from models_db import User
import streamlit as st
from supabase_client import get_supabase_client, get_admin_client
import time
from datetime import datetime, timedelta

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))

# Authenticate user
def authenticate(username, password):
    user = db_manager.db.query(User).filter_by(username=username).first()
    if user and verify_password(password, user.hashed_password):
        return user
    return None

def sign_up(email, password, user_data=None):
    """
    Register a new user with Supabase Auth.
    
    Args:
        email: User's email
        password: User's password
        user_data: Optional dictionary with additional user data
    
    Returns:
        User data if successful, None if failed
    """
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
            return response.user
        return None
    except Exception as e:
        st.error(f"Sign up error: {str(e)}")
        return None

def sign_in(email, password):
    """
    Sign in a user with email and password.
    
    Args:
        email: User's email
        password: User's password
    
    Returns:
        User data if successful, None if failed
    """
    try:
        supabase = get_supabase_client()
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        
        if response.user:
            # Store session in streamlit session state
            st.session_state.user = response.user
            st.session_state.access_token = response.session.access_token
            st.session_state.refresh_token = response.session.refresh_token
            st.session_state.expires_at = time.time() + response.session.expires_in
            
            # Get user profile data from the database
            profile = get_user_profile(response.user.id)
            if profile:
                st.session_state.user_profile = profile
            
            return response.user
        return None
    except Exception as e:
        st.error(f"Sign in error: {str(e)}")
        return None

def sign_out():
    """Sign out the current user"""
    try:
        supabase = get_supabase_client()
        supabase.auth.sign_out()
        
        # Clear session state
        for key in ['user', 'access_token', 'refresh_token', 'expires_at', 'user_profile']:
            if key in st.session_state:
                del st.session_state[key]
                
        return True
    except Exception as e:
        st.error(f"Sign out error: {str(e)}")
        return False

def get_current_user():
    """
    Get the current authenticated user.
    Handles token refresh if needed.
    
    Returns:
        User object if authenticated, None otherwise
    """
    if "user" not in st.session_state:
        return None
    
    # Check if token needs refresh
    if "expires_at" in st.session_state and time.time() > st.session_state.expires_at - 300:  # 5 min buffer
        try:
            supabase = get_supabase_client()
            response = supabase.auth.refresh_session({
                "refresh_token": st.session_state.refresh_token
            })
            
            if response.session:
                st.session_state.access_token = response.session.access_token
                st.session_state.refresh_token = response.session.refresh_token
                st.session_state.expires_at = time.time() + response.session.expires_in
        except Exception as e:
            # If refresh fails, sign out
            sign_out()
            return None
    
    return st.session_state.user

def get_user_profile(user_id):
    """
    Get user profile data from the profiles table
    
    Args:
        user_id: The user's UUID
        
    Returns:
        User profile data or None
    """
    try:
        supabase = get_supabase_client()
        response = supabase.table('profiles').select('*').eq('id', user_id).execute()
        
        if response.data and len(response.data) > 0:
            return response.data[0]
        return None
    except Exception as e:
        st.error(f"Error getting user profile: {str(e)}")
        return None

def update_user_profile(user_id, profile_data):
    """
    Update a user's profile in the profiles table
    
    Args:
        user_id: The user's UUID
        profile_data: Dictionary of profile data to update
        
    Returns:
        Updated profile data or None
    """
    try:
        supabase = get_supabase_client()
        response = supabase.table('profiles').update(profile_data).eq('id', user_id).execute()
        
        if response.data and len(response.data) > 0:
            return response.data[0]
        return None
    except Exception as e:
        st.error(f"Error updating user profile: {str(e)}")
        return None

def require_auth():
    """
    Decorator-like function to require authentication.
    If user is not authenticated, redirects to login page.
    
    Usage:
        user = require_auth()
        if not user:
            return
    """
    user = get_current_user()
    if not user:
        st.session_state.page = "login"
        st.rerun()
    return user