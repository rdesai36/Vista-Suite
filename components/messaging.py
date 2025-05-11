import streamlit as st
import pandas as pd
from datetime import datetime
from models import UserProfile
from styles import format_timestamp, render_role_badge
from database import get_db_manager

def show_messaging(current_user=None):
    """Display messaging system with threads"""
    if not current_user:
        st.warning("Please log in to access messages.")
        return
    
    # Get database manager
    db_manager = get_db_manager()
    
    st.title("Messages")
    
    # Create tabs for Inbox and New Message
    tab1, tab2 = st.tabs(["Inbox", "New Message"])
    
    with tab1:
        show_inbox(current_user, db_manager)
    
    with tab2:
        create_new_thread(current_user, db_manager)

def show_inbox(current_user, db_manager):
    """Show threads the user is participating in"""
    # Get threads for current user
    threads = db_manager.get_user_threads(current_user.user_id)
    
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
            participants = db_manager.get_thread_participants(thread.id)
            participant_users = []
            for p in participants:
                user = db_manager.get_user_by_id(p.user_id) if hasattr(p, 'user_id') else None
                if user and user.id != current_user.id:
                    participant_users.append(user)
            
            # Create thread title for display
            thread_title = thread.title if thread.title else "Conversation"
            if participant_users:
                participant_names = ", ".join([u.name for u in participant_users])
                thread_title = f"{thread_title} with {participant_names}"
            
            # Display last message time
            last_message_time = format_timestamp(thread.last_message_time, "%b %d %I:%M %p")
            
            # Show button for thread with conditional styling
            is_active = st.session_state.active_thread_id == thread.id
            button_type = "primary" if is_active else "secondary"
            
            if st.button(
                f"{thread_title}\n{last_message_time}", 
                key=f"thread_{thread.id}",
                use_container_width=True,
                type=button_type
            ):
                st.session_state.active_thread_id = thread.id
                # Mark thread as read
                db_manager.mark_thread_as_read(thread.id, current_user.user_id)
                st.rerun()
    
    with col2:
        if st.session_state.active_thread_id:
            show_thread_messages(st.session_state.active_thread_id, current_user, db_manager)
        else:
            st.info("Select a conversation to view messages.")

def show_thread_messages(thread_id, current_user, db_manager):
    """Show messages in a thread"""
    thread = db_manager.get_thread_by_id(thread_id)
    if not thread:
        threads = db_manager.get_user_threads(current_user.user_id)
        if threads:
            thread = threads[0]
        else:
            st.error("Thread not found.")
            return
    
    # Show thread title
    st.subheader(thread.title or "Conversation")
    
    # Get all participants in the thread
    participants = db_manager.get_thread_participants(thread.id)
    participant_users = {}
    for p in participants:
        user = db_manager.get_user_by_id(p.user_id) if hasattr(p, 'user_id') else None
        if user:
            participant_users[user.id] = user
    
    # Get messages in thread
    messages = db_manager.get_thread_messages(thread.id)
    
    # Message container with fixed height and scrolling
    message_container = st.container()
    with message_container:
        for message in messages:
            # Get sender
            sender = participant_users.get(message.sender_id)
            sender_name = sender.name if sender else "Unknown"
            sender_avatar = sender.avatar if sender else None
            is_self = sender.id == current_user.id if sender else False
            
            # Create message layout
            cols = st.columns([1, 6])
            
            with cols[0]:
                if sender_avatar:
                    st.image(sender_avatar, width=50)
                else:
                    st.markdown("👤")
            
            with cols[1]:
                # Message header with sender name and timestamp
                st.markdown(f"**{sender_name}** - {format_timestamp(message.timestamp, '%I:%M %p')}")
                
                # Message content
                message_style = "message-sent" if is_self else "message-received"
                st.markdown(f"""
                <div class="{message_style}">
                    {message.content}
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("---")
    
    # Input for new message
    with st.form(key=f"thread_reply_{thread.id}", clear_on_submit=True):
        new_message = st.text_area("Reply", key=f"new_message_{thread.id}")
        submit = st.form_submit_button("Send")
        
        if submit and new_message.strip():
            # Add message to thread
            db_manager.create_message_in_thread(thread.id, current_user.id, new_message)
            st.rerun()

def create_new_thread(current_user, db_manager):
    """Create a new message thread"""
    st.subheader("Start New Conversation")
    
    # Get all users
    all_users = db_manager.get_all_users()
    
    # Filter out current user
    other_users = [u for u in all_users if u.id != current_user.id]
    
    if not other_users:
        st.warning("No other users found to start a conversation with.")
        return
    
    # Create form for new thread
    with st.form(key="new_thread_form", clear_on_submit=True):
        # Thread title (optional)
        thread_title = st.text_input("Subject (optional)")
        
        # Select participants
        options = [(u.id, f"{u.name} ({u.role})") for u in other_users]
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
            
            # Create new thread
            new_thread = db_manager.create_thread(thread_title)
            
            # Add current user as participant
            db_manager.add_participant_to_thread(new_thread.id, current_user.id)
            
            # Add selected users as participants
            for user_id in selected_ids:
                db_manager.add_participant_to_thread(new_thread.id, user_id)
            
            # Add initial message
            db_manager.create_message_in_thread(new_thread.id, current_user.id, message_content)
            
            st.success("Message sent!")
            
            # Set active thread to the new thread
            st.session_state.active_thread_id = new_thread.id
            
            # Switch to inbox tab
            st.session_state.active_tab = "Inbox"
            st.rerun()