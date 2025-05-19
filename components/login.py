import streamlit as st
from auth import sign_in, sign_up
from supabase_client import get_supabase_client

def show_login():
    """Display login page with email/password authentication"""
    st.title("Welcome to Vista Suite")

    tab1, tab2 = st.tabs(["Login", "Sign Up"])

    # LOGIN TAB
    with tab1:
        st.subheader("Login")
        email = st.text_input("Email", key="login_email").strip().lower()
        password = st.text_input("Password", type="password", key="login_password")

        if st.button("Login", key="login_button"):
            if email and password:
                user = sign_in(email, password)
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
        name = st.text_input("Full Name", key="signup_name").strip()
        email = st.text_input("Email", key="signup_email").strip().lower()
        password = st.text_input("Password", type="password", key="signup_password")
        confirm_password = st.text_input("Confirm Password", type="password", key="signup_confirm_password")

        if st.button("Sign Up", key="signup_button"):
            if not all([name, email, password, confirm_password]):
                st.warning("Please fill in all fields.")
            elif password != confirm_password:
                st.error("Passwords do not match.")
            else:
                user_data = {"name": name}
                user = sign_up(email, password, user_data)
                if user:
                    # OPTIONAL: Add to your profiles table as well (only if not handled automatically)
                    supabase = get_supabase_client()
                    supabase.from_("profiles").insert({
                        "id": user.id,
                        "name": name,
                        "email": email,
                        "role": "Front Desk",    # Or whatever your default is
                    }).execute()

                    st.success("Account created successfully! Please log in.")
                    st.session_state["page"] = "login"
                    st.rerun()
                else:
                    st.error("Failed to create account. Please try again.")