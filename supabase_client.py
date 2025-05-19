import os
import supabase
from supabase import create_client, Client
from dotenv import load_dotenv
import streamlit as st

# Load environment variables
load_dotenv()

def get_supabase_client() -> Client:
    """
    Get a Supabase client instance.
    Uses cached client if available in session state.
    """
    if "supabase" not in st.session_state:
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_ANON_KEY")
        st.session_state.supabase = create_client(url, key)
    
    return st.session_state.supabase

def get_admin_client() -> Client:
    """
    Get a Supabase admin client with service role permissions.
    Only use for admin operations that require elevated privileges.
    """
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_KEY")
    return create_client(url, key)