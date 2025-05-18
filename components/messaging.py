import streamlit as st
import pandas as pd
from datetime import datetime
import uuid # Import uuid for generating thread/message IDs
from styles import format_timestamp, render_role_badge
from supabase_client import get_supabase_client # Import the function to get Supabase client


def show_messaging(current_user=None):
    """Display messaging system with threads"""
    if not current_user:
        st.warning("Please log in to access messages.")
        return

    # Get Supabase client
    supabase = get_supabase_client()
    
    st.title("Messages")

    # Create tabs for Inbox and New Message
    tab1, tab2 = st.tabs(["Inbox", "New Message"])

    with tab1:
        show_inbox(current_user, supabase)

    with tab2:
        create_new_thread(current_user, supabase)


def show_inbox(current_user, supabase):
    """Show threads the user is participating in"""
    # Get threads for current user from Supabase
    try:
        response = supabase.from_('thread_participants').select('thread_id, threads(id, title, last_message_time)').eq('user_id', current_user.user_id).execute()
        threads_data = response.data
        threads = [p['threads'] for p in threads_data if p['threads']] # Extract thread data
    except Exception as e:
        st.error(f"Error fetching threads: {str(e)}")
        threads = []

    if not threads:
        st.info("You don't have any message threads yet.")
        return

    # Create sidebar to select thread
    if "active_thread_id" not in st.session_state:
        st.session_state.active_thread_id = None

    col1, col2 = st.columns([1, 3])

    with col1:
        st.subheader("Conversations")
        for thread in threads:
            # Get participants for display
            try:
                participants_response = supabase.from_('thread_participants').select('user_id, profiles(id, name)').eq('thread_id', thread['id']).execute()
                participants_data = participants_response.data
                participant_users = [p['profiles'] for p in participants_data if p['profiles'] and p['profiles']['id'] != current_user.user_id]
            except Exception as e:
                st.error(f"Error fetching participants for thread {thread['id']}: {str(e)}")
                participant_users = []

            # Create thread title for display
            thread_title = thread.get('title') if thread.get('title') else "Conversation"
            if participant_users:
                participant_names = ", ".join([u['name'] for u in participant_users])
                thread_title = f"{thread_title} with {participant_names}"

            # Display last message time
            last_message_time = format_timestamp(datetime.fromisoformat(thread['last_message_time']), "%b %d %I:%M %p") if thread.get('last_message_time') else "No messages yet"

            # Show button for thread with conditional styling
            is_active = st.session_state.active_thread_id == thread['id']
            button_type = "primary" if is_active else "secondary"

            if st.button(
                f"{thread_title}\n{last_message_time}",
                key=f"thread_{thread['id']}",
                use_container_width=True,
                type=button_type
            ):
                st.session_state.active_thread_id = thread['id']
                # Mark thread as read (update read_until timestamp for this user in thread_participants)
                try:
                    supabase.from_('thread_participants').update({'read_until': datetime.now().isoformat()}).eq('thread_id', thread['id']).eq('user_id', current_user.user_id).execute()
                except Exception as e:
                    st.error(f"Error marking thread as read: {str(e)}")
                st.rerun()

    with col2:
        if st.session_state.active_thread_id:
            show_thread_messages(st.session_state.active_thread_id, current_user, supabase)
        else:
            st.info("Select a conversation to view messages.")


def show_thread_messages(thread_id, current_user, supabase):
    """Show messages in a thread"""
    # Get thread details
    try:
        thread_response = supabase.from_('threads').select('*').eq('id', thread_id).execute()
        thread = thread_response.data[0] if thread_response.data else None
    except Exception as e:
        st.error(f"Error fetching thread {thread_id}: {str(e)}")
        thread = None

    if not thread:
        st.error("Thread not found.")
        return

    # Show thread title
    st.subheader(thread.get('title') or "Conversation")

    # Get all participants in the thread
    try:
        participants_response = supabase.from_('thread_participants').select('user_id, profiles(id, name, avatar, role)').eq('thread_id', thread_id).execute()
        participants_data = participants_response.data
        participant_users = {p['profiles']['id']: p['profiles'] for p in participants_data if p['profiles']}
    except Exception as e:
        st.error(f"Error fetching participants for thread {thread_id}: {str(e)}")
        participant_users = {}

    # Get messages in thread
    try:
        messages_response = supabase.from_('messages').select('*').eq('thread_id', thread_id).order('timestamp', asc=True).execute()
        messages = messages_response.data
    except Exception as e:
        st.error(f"Error fetching messages for thread {thread_id}: {str(e)}")
        messages = []

    # Message container with fixed height and scrolling
    message_container = st.container(height=400) # Added height for scrolling
    with message_container:
        for message in messages:
            # Get sender
            sender = participant_users.get(message.get('sender_id'))
            sender_name = sender.get('name', 'Unknown') if sender else 'Unknown'
            sender_avatar = sender.get('avatar') if sender else None
            is_self = sender.get('id') == current_user.user_id if sender else False

            # Create message layout
            cols = st.columns([1, 6])

            with cols[0]:
                if sender_avatar:
                    st.image(sender_avatar, width=50)
                else:
                    st.markdown("👤")

            with cols[1]:
                # Message header with sender name and timestamp
                timestamp_str = message.get('timestamp')
                formatted_time = format_timestamp(datetime.fromisoformat(timestamp_str), '%I:%M %p') if timestamp_str else 'Unknown Time'
                st.markdown(f"**{sender_name}** - {formatted_time}")

                # Message content
                message_style = "message-sent" if is_self else "message-received"
                st.markdown(f"""
                <div class=\"{message_style}\">
                    {message.get('content', 'No Content')}
                </div>
                """, unsafe_allow_html=True)

            st.markdown("---")

    # Input for new message
    with st.form(key=f"thread_reply_{thread_id}", clear_on_submit=True):
        new_message = st.text_area("Reply", key=f"new_message_{thread_id}")
        submit = st.form_submit_button("Send")

        if submit and new_message.strip():
            # Add message to thread using Supabase
            try:
                message_data = {
                    'thread_id': thread_id,
                    'sender_id': current_user.user_id,
                    'content': new_message,
                    'timestamp': datetime.now().isoformat()
                }
                insert_response = supabase.from_('messages').insert([message_data]).execute()
                if insert_response.data:
                    # Update last_message_time in the thread
                    supabase.from_('threads').update({'last_message_time': datetime.now().isoformat()}).eq('id', thread_id).execute()
                    st.rerun()
                else:
                    st.error(f"Error sending message: {insert_response.error}")
            except Exception as e:
                st.error(f"Error sending message: {str(e)}")


def create_new_thread(current_user, supabase):
    """Create a new message thread"""
    st.subheader("Start New Conversation")

    # Get all users from Supabase
    try:
        users_response = supabase.from_('profiles').select('id, name, role').execute()
        all_users = users_response.data
    except Exception as e:
        st.error(f"Error fetching users: {str(e)}")
        all_users = []

    # Filter out current user
    other_users = [u for u in all_users if u['id'] != current_user.user_id]

    if not other_users:
        st.warning("No other users found to start a conversation with.")
        return

    # Create form for new thread
    with st.form(key="new_thread_form", clear_on_submit=True):
        # Thread title (optional)
        thread_title = st.text_input("Subject (optional)")

        # Select participants
        options = [(u['id'], f"{u['name']} ({u['role']})") for u in other_users]
        selected_ids = []

        if options:
            st.write("Select participants:")
            for user_id, user_label in options:
                if st.checkbox(user_label, key=f"user_{user_id}"):
                    selected_ids.append(user_id)

        # Message content
        message_content = st.text_area("Message")

        # Submit button
        submit = st.form_submit_button("Send")

        if submit:
            if not selected_ids:
                st.error("Please select at least one participant.")
                return

            if not message_content.strip():
                st.error("Please enter a message.")
                return

            # Create new thread in Supabase
            try:
                new_thread_id = str(uuid.uuid4())
                thread_data = {
                    'id': new_thread_id,
                    'title': thread_title if thread_title else None,
                    'created_at': datetime.now().isoformat(),
                    'last_message_time': datetime.now().isoformat() # Set initial last message time
                }
                thread_insert_response = supabase.from_('threads').insert([thread_data]).execute()

                if thread_insert_response.data:
                    # Add current user as participant
                    participant_data = {'thread_id': new_thread_id, 'user_id': current_user.user_id, 'joined_at': datetime.now().isoformat(), 'read_until': datetime.now().isoformat()}
                    supabase.from_('thread_participants').insert([participant_data]).execute()

                    # Add selected users as participants
                    for user_id in selected_ids:
                        participant_data = {'thread_id': new_thread_id, 'user_id': user_id, 'joined_at': datetime.now().isoformat(), 'read_until': datetime.now().isoformat()}
                        supabase.from_('thread_participants').insert([participant_data]).execute()

                    # Add initial message
                    message_data = {
                        'thread_id': new_thread_id,
                        'sender_id': current_user.user_id,
                        'content': message_content,
                        'timestamp': datetime.now().isoformat()
                    }
                    supabase.from_('messages').insert([message_data]).execute()

                    st.success("Message sent!")

                    # Set active thread to the new thread
                    st.session_state.active_thread_id = new_thread_id

                    # Switch to inbox tab
                    st.session_state.active_tab = "Inbox" # Assuming a session state variable for active tab
                    st.rerun()
                else:
                    st.error(f"Error creating thread: {thread_insert_response.error}")
            except Exception as e:
                st.error(f"Error creating thread: {str(e)}")