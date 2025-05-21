import streamlit as st
from datetime import datetime
import uuid
from styles import format_timestamp
from supabase_client import get_supabase_client

def show_messaging(current_user=None):
    if not current_user:
        st.warning("Please log in to access messages.")
        return

    if "active_thread_id" not in st.session_state:
        st.session_state.active_thread_id = None

    supabase = get_supabase_client()
    st.title("Messages")
    tab1, tab2 = st.tabs(["Inbox", "New Message"])

    with tab1:
        show_inbox(current_user, supabase)
    with tab2:
        create_new_thread(current_user, supabase)

def show_inbox(current_user, supabase):
    """Show threads the user participates in"""
    try:
        # Get all threads for the user
        threads_resp = supabase.from_('thread_participants').select('thread_id').eq('user_id', current_user['id']).execute()
        thread_ids = [tp['thread_id'] for tp in threads_resp.data] if threads_resp.data else []

        # Get thread details
        threads = []
        for tid in thread_ids:
            thread_resp = supabase.from_('threads').select('id, title, last_message_time').eq('id', tid).single().execute()
            thread = thread_resp.data if hasattr(thread_resp, 'data') else None
            if not thread:
                continue

            # Get participants (excluding self)
            participants_resp = supabase.from_('thread_participants').select('user_id, profiles(name)').eq('thread_id', tid).neq('user_id', current_user['id']).execute()
            participants = participants_resp.data if hasattr(participants_resp, 'data') else []
            names = ', '.join([p['profiles']['name'] for p in participants if p.get('profiles')]) or 'Unknown'

            # Get last message
            msg_resp = supabase.from_('messages').select('content, created_at').eq('thread_id', tid).order('created_at', desc=True).limit(1).execute()
            last_msg = msg_resp.data[0] if msg_resp.data else None
            last_message = last_msg['content'] if last_msg else ''
            last_message_time = last_msg['created_at'] if last_msg else thread.get('last_message_time')

            threads.append({
                'thread_id': tid,
                'display_names': names,
                'last_message': last_message,
                'last_message_time': last_message_time,
            })
    except Exception as e:
        st.error(f"Error fetching threads: {str(e)}")
        threads = []

    if not threads:
        st.info("You don't have any conversations yet.")
        return

    if "active_thread_id" not in st.session_state:
        st.session_state.active_thread_id = None

    col1, col2 = st.columns([1, 3])
    with col1:
        st.subheader("Conversations")
        for thread in threads:
            display_name = thread.get('display_names', 'Unknown')
            last_msg = (thread.get('last_message', '')[:30] + '...') if thread.get('last_message') else 'No messages'
            last_time = format_timestamp(datetime.fromisoformat(thread['last_message_time']), "%b %d %I:%M %p") if thread.get('last_message_time') else ''
            is_active = st.session_state.active_thread_id == thread['thread_id']
            button_type = "primary" if is_active else "secondary"
            if st.button(
                f"{display_name}\n{last_msg} • {last_time}",
                key=f"thread_{thread['thread_id']}",
                use_container_width=True,
                type=button_type
            ):
                st.session_state.active_thread_id = thread['thread_id']
                st.rerun()
    with col2:
        if st.session_state.active_thread_id:
            show_conversation(st.session_state.active_thread_id, current_user, supabase)
        else:
            if threads:
                st.session_state.active_thread_id = threads[0]['thread_id']
                st.rerun()
            else:
                st.info("Select a conversation to view messages.")

def show_conversation(thread_id, current_user, supabase):
    """Show messages in a thread"""
    try:
        # Get participants
        participants_resp = supabase.from_('thread_participants').select('user_id, profiles(name, avatar_url)').eq('thread_id', thread_id).execute()
        participants = participants_resp.data if hasattr(participants_resp, 'data') else []
        participant_users = {p['user_id']: p['profiles'] for p in participants if p.get('profiles')}

        # Get messages
        messages_resp = supabase.from_('messages').select('*').eq('thread_id', thread_id).order('created_at', asc=True).execute()
        messages = messages_resp.data if hasattr(messages_resp, 'data') else []

        # Header
        other_participants = [u for uid, u in participant_users.items() if uid != current_user['id']]
        names = ', '.join([u.get('name', 'Unknown') for u in other_participants]) or 'Unknown'
        st.subheader(f"Conversation with {names}")

        message_container = st.container(height=400)
        with message_container:
            for msg in messages:
                sender = participant_users.get(msg['sender_id'])
                sender_name = sender.get('name', 'Unknown') if sender else 'Unknown'
                sender_avatar = sender.get('avatar_url') if sender else None
                is_self = msg['sender_id'] == current_user['id']
                cols = st.columns([1, 6])
                with cols[0]:
                    if sender_avatar:
                        st.image(sender_avatar, width=40)
                    else:
                        st.markdown("👤")
                with cols[1]:
                    formatted_time = format_timestamp(datetime.fromisoformat(msg['created_at']), '%I:%M %p') if msg.get('created_at') else 'Unknown Time'
                    st.markdown(f"**{sender_name}** - {formatted_time}")
                    message_style = "message-sent" if is_self else "message-received"
                    st.markdown(f"""
                    <div class="{message_style}">
                        {msg.get('content', 'No Content')}
                    </div>
                    """, unsafe_allow_html=True)
                st.markdown("---")

        # Message input
        with st.form(key=f"thread_reply_{thread_id}", clear_on_submit=True):
            new_message = st.text_area("Reply", key=f"new_message_{thread_id}")
            submit = st.form_submit_button("Send")
            if submit and new_message.strip():
                try:
                    message_data = {
                        'thread_id': thread_id,
                        'sender_id': current_user['id'],
                        'content': new_message,
                        'created_at': datetime.now().isoformat()
                    }
                    insert_response = supabase.from_('messages').insert([message_data]).execute()
                    if insert_response.data:
                        supabase.from_('threads').update({'last_message_time': datetime.now().isoformat()}).eq('id', thread_id).execute()
                        st.rerun()
                    else:
                        st.error(f"Error sending message: {getattr(insert_response, 'error', 'Unknown error')}")
                except Exception as e:
                    st.error(f"Error sending message: {str(e)}")
    except Exception as e:
        st.error(f"Error loading conversation: {str(e)}")

def create_new_thread(current_user, supabase):
    """Create a new thread and send the first message"""
    st.subheader("Start New Conversation")
    try:
        users_resp = supabase.from_('profiles').select('id, name').neq('id', current_user['id']).execute()
        users = users_resp.data if hasattr(users_resp, 'data') else []
    except Exception as e:
        st.error(f"Error fetching users: {str(e)}")
        users = []
    if not users:
        st.warning("No other users found to message.")
        return

    with st.form(key="new_thread_form", clear_on_submit=True):
        thread_title = st.text_input("Subject (optional)")
        options = [(u['id'], u['name']) for u in users]
        selected_ids = []
        st.write("Select participants:")
        for user_id, user_name in options:
            if st.checkbox(user_name, key=f"user_{user_id}"):
                selected_ids.append(user_id)
        message_content = st.text_area("Message")
        submitted = st.form_submit_button("Send Message")
        if submitted:
            if not selected_ids or not message_content.strip():
                st.error("Please select at least one recipient and enter a message.")
                return
            try:
                new_thread_id = str(uuid.uuid4())
                thread_data = {
                    'id': new_thread_id,
                    'title': thread_title if thread_title else None,
                    'created_at': datetime.now().isoformat(),
                    'last_message_time': datetime.now().isoformat()
                }
                thread_resp = supabase.from_('threads').insert([thread_data]).execute()
                if thread_resp.data:
                    # Add participants
                    participant_data = [{
                        'thread_id': new_thread_id,
                        'user_id': uid,
                        'joined_at': datetime.now().isoformat(),
                        'read_until': datetime.now().isoformat()
                    } for uid in selected_ids + [current_user['id']]]
                    supabase.from_('thread_participants').insert(participant_data).execute()
                    # Add initial message
                    message_data = {
                        'thread_id': new_thread_id,
                        'sender_id': current_user['id'],
                        'content': message_content,
                        'created_at': datetime.now().isoformat()
                    }
                    supabase.from_('messages').insert([message_data]).execute()
                    st.success("Message sent!")
                    st.session_state.active_thread_id = new_thread_id
                    st.rerun()
                else:
                    st.error(f"Error creating thread: {getattr(thread_resp, 'error', 'Unknown error')}")
            except Exception as e:
                st.error(f"Error creating thread: {str(e)}")