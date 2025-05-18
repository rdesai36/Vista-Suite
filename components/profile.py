import streamlit as st
from datetime import datetime
from styles import render_role_badge, format_timestamp
from supabase_client import supabase # Import supabase client


def show_profile(current_user=None, user_id=None):
    """Display user profile, either current user or another user"""
    if not current_user:
        st.warning("No user profile found. Please log in or create a profile.")
        return

    # Determine which profile to show
    if user_id and user_id != current_user['id']:
        # Viewing someone else's profile
        profile_user = get_user_profile_from_supabase(user_id)
        if not profile_user:
            st.error(f"User profile not found.")
            return

        show_read_only_profile(profile_user, current_user)
    else:
        # Viewing own profile
        show_editable_profile(current_user)


def get_user_profile_from_supabase(user_id):
    """Fetch user profile from Supabase"""
    try:
        response = supabase.from_('profiles').select('*').eq('id', user_id).single().execute()
        return response.data
    except Exception as e:
        st.error(f"Error fetching user profile {user_id}: {str(e)}")
        return None


def show_editable_profile(user):
    """Display and allow editing of current user's profile"""
    st.header("My Profile")

    # Fetch the latest profile data for editing
    profile_data = get_user_profile_from_supabase(user['id'])
    if not profile_data:
        st.error("Could not load your profile data.")
        return

    col1, col2 = st.columns([1, 3])

    with col1:
        # Display avatar
        st.image(profile_data.get('avatar', 'https://ui-avatars.com/api/?name=User&background=0D8ABC&color=fff'), width=150)

        # Display role badge
        st.markdown(f"""
        <div style="text-align: center; margin-top: 10px;">
            {render_role_badge(profile_data.get('role', 'Unknown'))}
        </div>
        """, unsafe_allow_html=True)

        # Last active display
        last_active_time = profile_data.get('last_active')
        formatted_last_active = format_timestamp(datetime.fromisoformat(last_active_time)) if last_active_time else 'Never'
        st.markdown(f"""
        <div style="text-align: center; margin-top: 10px; font-size: 0.8rem; color: var(--text-secondary-color);">
            Last active: {formatted_last_active}
        </div>
        """, unsafe_allow_html=True)


    with col2:
        with st.form("edit_profile_form"):
            name = st.text_input("Name", profile_data.get('name', ''))

            # Only managers can change roles
            # Assuming role is stored in the 'profiles' table
            current_role = profile_data.get('role', 'Unknown')
            if current_role == "Manager":
                role_options = ["Manager", "Front Desk", "Housekeeping", "Maintenance", "Sales", "Inspector"]
                role = st.selectbox("Role", options=role_options, index=role_options.index(current_role) if current_role in role_options else 0)
            else:
                role = current_role
                st.markdown(f"**Role:** {role} *(Only managers can change roles)*")

            email = st.text_input("Email", profile_data.get('email', ''))
            phone = st.text_input("Phone", profile_data.get('phone', ''))
            bio = st.text_area("Bio", profile_data.get('bio', ''), height=150)
            avatar_url = st.text_input("Avatar URL (optional)", profile_data.get('avatar', ''))

            submitted = st.form_submit_button("Save Changes")

            if submitted:
                # Update user profile in Supabase
                update_data = {
                    'name': name,
                    'email': email,
                    'phone': phone,
                    'bio': bio,
                    'avatar': avatar_url if avatar_url else None # Store None if empty
                }
                if current_role == "Manager": # Only managers can update role
                     update_data['role'] = role

                try:
                    response = supabase.from_('profiles').update(update_data).eq('id', user['id']).execute()
                    if response.data:
                        st.success("Profile updated successfully!")
                        st.rerun() # Rerun to show updated profile
                    else:
                         st.error(f"Error updating profile: {response.error.message}")
                except Exception as e:
                    st.error(f"Error updating profile: {str(e)}")


    # Messaging section - display recent messages
    st.header("My Messages")

    # Get messages for current user (sent or received)
    try:
        sent_messages_response = supabase.from_('messages').select('*, threads(title)').eq('sender_id', user['id']).order('timestamp', desc=True).limit(5).execute()
        received_messages_response = supabase.from_('messages').select('*, threads(title)').eq('recipient_id', user['id']).order('timestamp', desc=True).limit(5).execute()

        sent_messages = sent_messages_response.data if sent_messages_response.data else []
        received_messages = received_messages_response.data if received_messages_response.data else []

        # Combine and sort messages
        messages = sorted(sent_messages + received_messages, key=lambda msg: msg.get('timestamp', ''), reverse=True)

    except Exception as e:
        st.error(f"Error fetching messages: {str(e)}")
        messages = []


    if messages:
        for message in messages:
            is_sent = message.get('sender_id') == user['id']
            other_user_id = message.get('recipient_id') if is_sent else message.get('sender_id')

            # Fetch the other user's profile to get their name
            other_user_profile = get_user_profile_from_supabase(other_user_id)
            other_name = other_user_profile.get('name', 'Unknown User') if other_user_profile else 'Unknown User'

            # Assuming 'is_read' column exists in messages table
            is_read = message.get('is_read', False)

            with st.expander(
                f"{'To' if is_sent else 'From'}: {other_name} - {format_timestamp(datetime.fromisoformat(message.get('timestamp')), '%b %d, %I:%M %p') if message.get('timestamp') else 'No Timestamp'}",
                expanded=not is_read and not is_sent # Expand unread received messages
            ):
                st.markdown(f"""
                **{'Sent' if is_sent else 'Received'}:** {format_timestamp(datetime.fromisoformat(message.get('timestamp'))) if message.get('timestamp') else 'Unknown Time'}

                {message.get('content', 'No Content')}
                """)

                # Mark as read if it's a received message and not already read
                if not is_sent and not is_read:
                    if st.button("Mark as Read", key=f"msg_read_{message.get('id', uuid.uuid4())}"): # Assuming message has an 'id'
                        try:
                            update_response = supabase.from_('messages').update({'is_read': True}).eq('id', message['id']).execute()
                            if update_response.data:
                                st.success("Marked as read")
                                st.rerun()
                            else:
                                st.error(f"Error marking message as read: {update_response.error.message}")
                        except Exception as e:
                            st.error(f"Error marking message as read: {str(e)}")
    else:
        st.info("No messages to display.")

    # Form to send a new message
    st.subheader("Send New Message")

    # Get all users except current user
    try:
        all_users_response = supabase.from_('users').select('id, name, role').execute()
        all_users = all_users_response.data if all_users_response.data else []
        other_users = [u for u in all_users if u['id'] != user['id']]
    except Exception as e:
        st.error(f"Error fetching users for new message: {str(e)}")
        other_users = []


    if other_users:
        with st.form("send_message_form"):
            recipient_options = [(u['id'], f"{u['name']} ({u['role']})") for u in other_users]
            recipient_ids = [u[0] for u in recipient_options]
            recipient_labels = [u[1] for u in recipient_options]

            # Handle case where there are no other users after filtering
            if not recipient_ids:
                 st.info("No other users available to message.")
                 return

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

                    # Send message using Supabase
                    try:
                        message_data = {
                            'sender_id': user['id'],
                            'recipient_id': recipient_id,
                            'content': message_content,
                            'timestamp': datetime.now().isoformat(),
                            'is_read': False # Mark as unread initially
                        }
                        insert_response = supabase.from_('messages').insert([message_data]).execute()

                        if insert_response.data:
                            st.success("Message sent successfully!")
                            st.rerun()  # Reset form
                        else:
                            st.error(f"Error sending message: {insert_response.error.message}")
                    except Exception as e:
                        st.error(f"Error sending message: {str(e)}")
                else:
                    st.error("Please enter a message.")
    else:
        st.info("No other users available to message.")


def show_read_only_profile(profile_user, current_user):
    """Display read-only view of another user's profile"""
    st.header(f"{profile_user.get('name', 'Unknown User')}'s Profile")

    col1, col2 = st.columns([1, 3])

    with col1:
        # Display avatar
        st.image(profile_user.get('avatar', 'https://ui-avatars.com/api/?name=User&background=0D8ABC&color=fff'), width=150)

        # Display role badge
        st.markdown(f"""
        <div style="text-align: center; margin-top: 10px;">
            {render_role_badge(profile_user.get('role', 'Unknown'))}
        </div>
        """, unsafe_allow_html=True)

        # Last active display
        last_active_time = profile_user.get('last_active')
        formatted_last_active = format_timestamp(datetime.fromisoformat(last_active_time)) if last_active_time else 'Never'
        st.markdown(f"""
        <div style="text-align: center; margin-top: 10px; font-size: 0.8rem; color: var(--text-secondary-color);">
            Last active: {formatted_last_active}
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"**Email:** {profile_user.get('email', 'Not provided') or 'Not provided'}")
        st.markdown(f"**Phone:** {profile_user.get('phone', 'Not provided') or 'Not provided'}")

        if profile_user.get('bio'):
            st.markdown("**Bio:**")
            st.markdown(profile_user.get('bio'))
        else:
            st.markdown("**Bio:** No bio provided.")

    # Option to send a message to this user
    st.subheader(f"Send Message to {profile_user.get('name', 'Unknown User')}")

    with st.form("send_direct_message_form"):
        message_content = st.text_area("Message", "", height=100)

        send_submitted = st.form_submit_button("Send Message")

        if send_submitted:
            if message_content:
                # Send message using Supabase
                try:
                    message_data = {
                        'sender_id': current_user['id'],
                        'recipient_id': profile_user['id'],
                        'content': message_content,
                        'timestamp': datetime.now().isoformat(),
                        'is_read': False # Mark as unread initially
                    }
                    insert_response = supabase.from_('messages').insert([message_data]).execute()

                    if insert_response.data:
                        st.success("Message sent successfully!")
                        # Optionally navigate to messaging tab or show a link
                    else:
                        st.error(f"Error sending message: {insert_response.error.message}")
                except Exception as e:
                    st.error(f"Error sending message: {str(e)}")
            else:
                st.error("Please enter a message.")
