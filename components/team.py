import streamlit as st
from datetime import datetime

from models import data_manager
from styles import render_role_badge, format_timestamp

def show_team(current_user=None):
    """Display team directory page with user listing and filtering"""
    if not current_user:
        st.warning("No user profile found. Please log in or create a profile.")
        return

    st.header("Team Directory")

    # Get all users
    all_users = data_manager.users

    # Filter options
    col1, col2 = st.columns(2)

    with col1:
        # Search by name
        search_term = st.text_input("Search by Name", "")

    with col2:
        # Filter by role
        available_roles = sorted(set(user.role for user in all_users))
        role_filter = st.multiselect(
            "Filter by Role",
            options=["All"] + available_roles,
            default=["All"]
        )

    # Apply filters
    filtered_users = all_users

    # Apply name search
    if search_term:
        filtered_users = [user for user in filtered_users 
                         if search_term.lower() in user.name.lower()]

    # Apply role filter
    if role_filter and "All" not in role_filter:
        filtered_users = [user for user in filtered_users 
                         if user.role in role_filter]

    # Sort users by name
    filtered_users = sorted(filtered_users, key=lambda user: user.name)

    # Display user cards in a grid
    if filtered_users:
        # Create a 3-column layout
        cols = st.columns(3)

        # Display each user in a card
        for i, user in enumerate(filtered_users):
            with cols[i % 3]:
                # Don't show current user in the directory
                if user.id == current_user.id:
                    continue

                # Create a card for this user
                with st.container():
                    st.markdown(f"""
                    <div style="
                        background-color: var(--surface-color);
                        border-radius: 10px;
                        padding: 1rem;
                        border: 1px solid var(--border-color);
                        margin-bottom: 1rem;
                        text-align: center;
                    ">
                        <img src="{user.avatar}" width="100" style="border-radius: 50%; margin-bottom: 10px;">
                        <h3 style="margin: 5px 0;">{user.name}</h3>
                        <div>{render_role_badge(user.role)}</div>
                        <p style="font-size: 0.8rem; color: var(--text-secondary-color); margin-top: 10px;">
                            Last active: {format_timestamp(user.last_active, '%b %d')}
                        </p>
                    </div>
                    """, unsafe_allow_html=True)

                    # Add buttons to view profile or send message
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("View Profile", key=f"view_{user.id}"):
                            # Store the user ID in session state and navigate to profile page
                            st.session_state.view_user_id = user.id
                            st.session_state.page = "profile"
                            st.rerun()

                    with col2:
                        if st.button("Message", key=f"msg_{user.id}"):
                            # Show message form
                            st.session_state.message_user_id = user.id
                            st.session_state.page = "message"
                            st.rerun()
    else:
        st.info("No team members found matching your filters.")

    # Add a separator before the quick message form
    st.markdown("---")

    # Quick message form
    if "message_user_id" in st.session_state:
        recipient = data_manager.get_user(st.session_state.message_user_id)
        if recipient:
            st.subheader(f"Send Message to {recipient.name}")

            with st.form("quick_message_form"):
                message_content = st.text_area("Message", "", height=100)

                col1, col2 = st.columns([1, 4])
                with col1:
                    send_submitted = st.form_submit_button("Send Message")

                with col2:
                    if st.form_submit_button("Cancel"):
                        if "message_user_id" in st.session_state:
                            del st.session_state.message_user_id
                        st.rerun()

                if send_submitted:
                    if message_content:
                        # Send message
                        data_manager.send_message(current_user.id, recipient.id, message_content)

                        st.success("Message sent successfully!")

                        # Clear the message_user_id
                        if "message_user_id" in st.session_state:
                            del st.session_state.message_user_id

                        st.rerun()
                    else:
                        st.error("Please enter a message.")