import streamlit as st
from datetime import datetime
import uuid
from styles import format_timestamp
from supabase_client import get_supabase_client

def show_messaging(current_user=None):
    if not current_user:
        st.warning("Please log in to access messages.")
        return

    supabase = get_supabase_client()
    st.title("Messages")

    # Handle direct user-to-user messaging from team directory
    target_user_id = st.session_state.pop('target_user_id', None)
    if target_user_id and target_user_id != current_user['id']:
        # Try to find an existing thread with just these two participants
        try:
            # Find all threads where current_user is a participant
            tp_resp = supabase.from_('thread_participants').select('thread_id').eq('user_id', current_user['id']).execute()
            thread_ids = [tp['thread_id'] for tp in (tp_resp.data or [])]
            found_thread_id = None
            if thread_ids:
                # For each thread, check if target_user is also a participant and there are only two participants
                tp2_resp = supabase.from_('thread_participants').select('thread_id, user_id').in_('thread_id', thread_ids).execute()
                from collections import defaultdict
                thread_part_map = defaultdict(set)
                for tp in (tp2_resp.data or []):
                    thread_part_map[tp['thread_id']].add(tp['user_id'])
                for tid, users in thread_part_map.items():
                    if users == {current_user['id'], target_user_id}:
                        found_thread_id = tid
                        break
            if not found_thread_id:
                # Create a new thread
                thread_title = f"Direct: {current_user.get('first_name') or current_user.get('name', '')} & User"
                thread_resp = supabase.from_('threads').insert({"title": thread_title}).execute()
                new_thread_id = thread_resp.data[0]['id'] if thread_resp and thread_resp.data else None
                if new_thread_id:
                    # Add both participants
                    supabase.from_('thread_participants').insert([
                        {"thread_id": new_thread_id, "user_id": current_user['id']},
                        {"thread_id": new_thread_id, "user_id": target_user_id}
                    ]).execute()
                    found_thread_id = new_thread_id
            if found_thread_id:
                st.session_state['active_thread_id'] = found_thread_id
        except Exception as e:
            st.error(f"Could not start direct message: {str(e)}")

    if "active_thread_id" not in st.session_state:
        st.session_state.active_thread_id = None

    tab1, tab2 = st.tabs(["Inbox", "New Message"])

    with tab1:
        show_inbox(current_user, supabase)
    with tab2:
        create_new_thread(current_user, supabase)

def show_inbox(current_user, supabase):
    """Show all threads the user participates in. Uses normalized schema and robust error handling."""
    try:
        # Fetch thread IDs for current user
        threads_resp = supabase.from_('thread_participants').select('thread_id').eq('user_id', current_user['id']).execute()
        thread_ids = [tp['thread_id'] for tp in (threads_resp.data or [])]
        if not thread_ids:
            st.info("You don't have any conversations yet.")
            return

        # Fetch thread details
        threads_resp = supabase.from_('threads').select('id, title, last_message_time').in_('id', thread_ids).order('last_message_time', desc=True).execute()
        threads_data = threads_resp.data or []

        # Fetch last messages for all threads
        last_msgs = {}
        if threads_data:
            msgs_resp = supabase.from_('messages').select('thread_id, content, created_at').in_('thread_id', [t['id'] for t in threads_data]).order('created_at', desc=True).execute()
            for msg in (msgs_resp.data or []):
                if msg['thread_id'] not in last_msgs:
                    last_msgs[msg['thread_id']] = msg

        # Fetch participants for all threads
        participants_resp = supabase.from_('thread_participants').select('thread_id, user_id, profiles(name)').in_('thread_id', [t['id'] for t in threads_data]).execute()
        participants_by_thread = {}
        for p in (participants_resp.data or []):
            tid = p['thread_id']
            if tid not in participants_by_thread:
                participants_by_thread[tid] = []
            # Exclude current user from display
            if p['user_id'] != current_user['id']:
                participants_by_thread[tid].append(p['profiles']['name'] if p.get('profiles') else 'Unknown')

        # Build thread summaries
        threads = []
        for thread in threads_data:
            tid = thread['id']
            names = ', '.join(participants_by_thread.get(tid, [])) or 'Unknown'
            last_msg = last_msgs.get(tid, {})
            last_message = last_msg.get('content', '')
            last_message_time = last_msg.get('created_at', thread.get('last_message_time'))
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

    # Set default active thread if not set
    if "active_thread_id" not in st.session_state or not st.session_state.active_thread_id:
        st.session_state.active_thread_id = threads[0]['thread_id']

    # Layout: thread list and conversation
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
            st.info("Select a conversation to view messages.")

def show_conversation(thread_id, current_user, supabase):
    """Show messages in a thread. Uses normalized schema and robust error handling."""
    try:
        # Fetch all participants for this thread
        participants_resp = supabase.from_('thread_participants').select('user_id, profiles(name, avatar_url)').eq('thread_id', thread_id).execute()
        participants = participants_resp.data or []
        participant_users = {p['user_id']: p['profiles'] for p in participants if p.get('profiles')}

        # Fetch all messages for this thread
        messages_resp = supabase.from_('messages').select('*').eq('thread_id', thread_id).order('created_at', asc=True).execute()
        messages = messages_resp.data or []

        # Header: show conversation with other participants
        other_participants = [u for uid, u in participant_users.items() if uid != current_user['id']]
        names = ', '.join([u.get('name', 'Unknown') for u in other_participants]) or 'Unknown'
        st.subheader(f"Conversation with {names}")

        # --- Display all messages in the thread ---
        for msg in messages:
            sender = participant_users.get(msg['user_id'], {'name': 'Unknown', 'avatar_url': ''})
            with st.container():
                col1, col2 = st.columns([1, 8])
                with col1:
                    if sender.get('avatar_url'):
                        st.image(sender['avatar_url'], width=40)
                with col2:
                    st.markdown(f"**{sender.get('name', 'Unknown')}**  ")
                    st.markdown(f"{msg['content']}")
                    st.caption(msg['created_at'])

        # --- Send new message ---
        with st.form(key=f"send_message_{thread_id}"):
            new_message = st.text_area("Message", key=f"msg_input_{thread_id}")
            if st.form_submit_button("Send") and new_message.strip():
                try:
                    message_data = {
                        'thread_id': thread_id,
                        'user_id': current_user['id'],
                        'content': new_message.strip(),
                        'created_at': datetime.now().isoformat()
                    }
                    insert_response = supabase.from_('messages').insert([message_data]).execute()
                    if insert_response.data:
                        supabase.from_('threads').update({'last_message_time': datetime.now().isoformat()}).eq('id', thread_id).execute()
                        st.experimental_rerun()
                    else:
                        st.error(f"Error sending message: {getattr(insert_response, 'error', 'Unknown error')}")
                except Exception as e:
                    st.error(f"Error sending message: {str(e)}")

    except Exception as e:
        st.error(f"Error loading conversation: {str(e)}")

def create_new_thread(current_user, supabase):
    """Create a new thread and send the first message. Uses normalized schema and robust error handling."""
    st.subheader("Start New Conversation")
    try:
        users_resp = supabase.from_('profiles').select('id, name').neq('id', current_user['id']).execute()
        users = users_resp.data or []
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
                    # Add participants (including self)
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