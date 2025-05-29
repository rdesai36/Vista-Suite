import streamlit as st
from datetime import datetime
from auth import sign_in, sign_up
from supabase_client import get_supabase_client



def show_login():
    """Display login page with email/password authentication"""
    st.image("newvista-narrow.png", width=500)
    tab1, tab2 = st.tabs(["Login", "Sign Up"])
    st.markdown("----")

    # LOGIN TAB
    with tab1:
        st.subheader("Login", )
        email = st.text_input("Email", key="login_email").strip().lower()
        password = st.text_input("Password", type="password", key="login_password")

        if st.button("Login", key="login_button"):
            if email and password:
                user = sign_in(email, password, None)  # No user_data on normal login
                if user:
                    st.session_state["supabase_user"] = user  # use consistent session key
                    st.session_state["page"] = "home"
                    st.success("Login successful!")
                    st.rerun()
            else:
                st.warning("Please enter both email and password.")

    # SIGN UP TAB
    with tab2:
        st.subheader("Create Account")
        first_name = st.text_input("First Name", key="signup_first_name").strip()
        last_name = st.text_input("Last Name", key="signup_last_name").strip()
        email = st.text_input("Email", key="signup_email").strip().lower()
        phone = st.text_input("Phone Number", key="signup_phone").strip()
        password = st.text_input("Password", type="password", key="signup_password")
        confirm_password = st.text_input("Confirm Password", type="password", key="signup_confirm_password")

        if st.button("Sign Up", key="signup_button"):
            # Validate all required fields for profiles table
            missing_fields = []
            if not first_name:
                missing_fields.append("First Name")
            if not last_name:
                missing_fields.append("Last Name")
            if not email:
                missing_fields.append("Email")
            if not phone:
                missing_fields.append("Phone Number")
            if not password:
                missing_fields.append("Password")
            if not confirm_password:
                missing_fields.append("Confirm Password")
            if missing_fields:
                st.warning(f"Please fill in all required fields: {', '.join(missing_fields)}.")
            elif password != confirm_password:
                st.error("Passwords do not match.")
            else:
                user_data = {"first_name": first_name, "last_name": last_name, "phone": phone}
                user = sign_up(email, password, user_data)
                if user:
                    # Store user_data in session for use on first login
                    st.session_state["pending_profile_data"] = user_data
                    st.success("Account created! Please check your email and verify your email address before logging in.")
                else:
                    st.error("Failed to create account. Please try again.")
