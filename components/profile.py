import streamlit as st
from datetime import datetime

from models import data_manager
from styles import render_role_badge, format_timestamp

def show_profile(current_user=None, user_id=None):
    """Display user profile, either current user or another user"""
    if not current_user:
        st.warning("No user profile found. Please log in or create a profile.")
        return

    # Determine which profile to show
    if user_id and user_id != current_user.id:
        # Viewing someone else's profile
        profile_user = data_manager.get_user(user.id)
        if not profile_user:
            st.error(f"User profile not found.")
            return

        show_read_only_profile(profile_user, current_user)
    else:
        # Viewing own profile
        show_editable_profile(current_user)


def show_editable_profile(user):
    """Display and allow editing of current user's profile"""
    st.header("My Profile")

    # Profile display and edit form
    col1, col2 = st.columns([1, 3])

    with col1:
        # Display avatar
        st.image(user.avatar, width=150)

        # Display role badge
        st.markdown(f"""
        <div style="text-align: center; margin-top: 10px;">
            {render_role_badge(user.role)}
        </div>
        """, unsafe_allow_html=True)

        # Last active display
        st.markdown(f"""
        <div style="text-align: center; margin-top: 10px; font-size: 0.8rem; color: var(--text-secondary-color);">
            Last active: {format_timestamp(user.last_active)}
        </div>
        """, unsafe_allow_html=True)

    with col2:
        with st.form("edit_profile_form"):
            name = st.text_input("Name", user.name)

            # Only managers can change roles
            if user.role == "Manager":
                role_options = ["Manager", "Front Desk", "Housekeeping", "Maintenance", "Sales", "Inspector"]
                role = st.selectbox("Role", options=role_options, index=role_options.index(user.role))
            else:
                role = user.role
                st.markdown(f"**Role:** {role} *(Only managers can change roles)*")

            email = st.text_input("Email", user.email or "")
            phone = st.text_input("Phone", user.phone or "")
            bio = st.text_area("Bio", user.bio, height=150)
            avatar_url = st.text_input("Avatar URL (optional)", user.avatar)

            submitted = st.form_submit_button("Save Changes")

            if submitted:
                # Update user profile
                user.name = name
                if user.role == "Manager":  # Only managers can change roles
                    user.role = role
                user.email = email
                user.phone = phone
                user.bio = bio
                if avatar_url:
                    user.avatar = avatar_url

                # Update in data manager
                data_manager.update_user(user)

                st.success("Profile updated successfully!")

    # Messaging section - display recent messages
    st.header("My Messages")

    # Get messages for current user
    messages = data_manager.get_messages(user.id)

    if messages:
        messages = sorted(messages, key=lambda msg: msg.timestamp, reverse=True)

        for message in messages[:5]:  # Show only most recent 5 messages
            # Determine if sent or received
            if message.sender_id == user.id:
                other_user = data_manager.get_user(message.recipient_id)
                is_sent = True
            else:
                other_user = data_manager.get_user(message.sender_id)
                is_sent = False

            other_name = other_user.name if other_user else "Unknown User"

            with st.expander(
                f"{'To' if is_sent else 'From'}: {other_name} - {format_timestamp(message.timestamp, '%b %d, %I:%M %p')}",
                expanded=not message.is_read and not is_sent
            ):
                st.markdown(f"""
                **{'Sent' if is_sent else 'Received'}:** {format_timestamp(message.timestamp)}

                {message.content}
                """)

                # Mark as read if it's a received message and not already read
                if not is_sent and not message.is_read:
                    if st.button("Mark as Read", key=f"msg_read_{message.message_id}"):
                        data_manager.mark_message_as_read(message.message_id)
                        st.success("Marked as read")
                        st.rerun()
    else:
        st.info("No messages to display.")

    # Form to send a new message
    st.subheader("Send New Message")

    # Get all users except current user
    other_users = [u for u in data_manager.users if u.id != user.id]

    if other_users:
        with st.form("send_message_form"):
            recipient_options = [(u.id, f"{u.name} ({u.role})") for u in other_users]
            recipient_ids = [u[0] for u in recipient_options]
            recipient_labels = [u[1] for u in recipient_options]

            recipient_index = st.selectbox(
                "Recipient", 
                options=range(len(recipient_options)),
                format_func=lambda x: recipient_labels[x]
            )

            message_content = st.text_area("Message", "", height=100)

            send_submitted = st.form_submit_button("Send Message")

            if send_submitted:
                if message_content:
                    recipient_id = recipient_ids[recipient_index]

                    # Send message
                    data_manager.send_message(user.id, recipient_id, message_content)

                    st.success("Message sent successfully!")
                    st.rerun()  # Reset form
                else:
                    st.error("Please enter a message.")
    else:
        st.info("No other users available to message.")


def show_read_only_profile(profile_user, current_user):
    """Display read-only view of another user's profile"""
    st.header(f"{profile_user.name}'s Profile")

    col1, col2 = st.columns([1, 3])

    with col1:
        # Display avatar
        st.image(profile_user.avatar, width=150)

        # Display role badge
        st.markdown(f"""
        <div style="text-align: center; margin-top: 10px;">
            {render_role_badge(profile_user.role)}
        </div>
        """, unsafe_allow_html=True)

        # Last active display
        st.markdown(f"""
        <div style="text-align: center; margin-top: 10px; font-size: 0.8rem; color: var(--text-secondary-color);">
            Last active: {format_timestamp(profile_user.last_active)}
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"**Email:** {profile_user.email or 'Not provided'}")
        st.markdown(f"**Phone:** {profile_user.phone or 'Not provided'}")

        if profile_user.bio:
            st.markdown("**Bio:**")
            st.markdown(profile_user.bio)
        else:
            st.markdown("**Bio:** No bio provided.")

    # Option to send a message to this user
    st.subheader(f"Send Message to {profile_user.name}")

    with st.form("send_direct_message_form"):
        message_content = st.text_area("Message", "", height=100)

        send_submitted = st.form_submit_button("Send Message")

        if send_submitted:
            if message_content:
                # Send message
                data_manager.send_message(current_user.id, profile_user.id, message_content)

                st.success("Message sent successfully!")
            else:
                st.error("Please enter a message.")