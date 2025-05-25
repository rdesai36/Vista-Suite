import streamlit as st
from supabase_client import get_supabase_client
from datetime import datetime

def show_logs(current_user):
    supabase = get_supabase_client()
    st.title("Logbook")

    # --- Log Posting Form ---
    st.subheader("New Log Entry")
    if 'log_title' not in st.session_state:
        st.session_state['log_title'] = ''
    if 'log_message' not in st.session_state:
        st.session_state['log_message'] = ''
    log_title = st.text_input("Title", key="log_title")
    log_message = st.text_area("Message", key="log_message")
    if st.button("Post Log", key="post_log_btn"):
        if not log_title.strip() or not log_message.strip():
            st.warning("Title and message are required.")
        else:
            try:
                import uuid
                supabase.from_('logs').insert({
                    "id": str(uuid.uuid4()),
                    "title": log_title.strip(),
                    "message": log_message.strip(),
                    "user_id": current_user["id"],
                    "author_id": current_user["id"],
                    "type": "General",
                    "user_name": current_user.get("name", st.session_state.get('email', 'Unknown')),
                    "created_at": datetime.now().isoformat(),
                    "read_by": [current_user["id"]]
                }).execute()
                st.success("Log posted!")
                st.session_state['log_title'] = ''
                st.session_state['log_message'] = ''
                st.rerun()
            except Exception as e:
                st.error(f"Error posting log: {str(e)}")
    st.markdown("---")
    st.subheader("Log Entries")
    
    # --- Fetch all profiles for read-by display ---
    try:
        profiles_response = supabase.from_('profiles').select('id, first_name, last_name, name').execute()
        all_profiles = profiles_response.data if profiles_response and profiles_response.data else []
        profile_map = {}
        for p in all_profiles:
            uid = p['id']
            first = p.get('first_name', '') or ''
            last = p.get('last_name', '') or ''
            name = p.get('name', '') or ''
            if first and last:
                display = f"{first} {last[0]}."
            elif name:
                display = name
            elif first:
                display = first
            else:
                display = uid[:8]  # fallback to short id
            profile_map[uid] = display.strip()
    except Exception as e:
        profile_map = {}

    # --- Fetch Logs (filter/search optional) ---
    filter_text = st.text_input("Search (by title/message/user)", value="", key="log_filter")
    logs = []  
    try:
        logs_response = supabase.from_('logs').select('*').order('created_at', desc=True).execute()
        logs = logs_response.data if logs_response and logs_response.data else []
        if filter_text:
            filter_lower = filter_text.lower()
            logs = [
                log for log in logs
                if filter_lower in (log.get('title', '').lower() + log.get('message', '').lower() + log.get('user_name', '').lower())
            ]
    except Exception as e:
        st.error(f"Error fetching logs: {str(e)}")

    user_id = current_user["id"]

    # --- Display Logs ---
    if logs:
        for log in logs:
            import json
            read_by = log.get("read_by") or []
            if isinstance(read_by, str):
                try:
                    read_by = json.loads(read_by)
                except Exception:
                    read_by = []
            is_unread = user_id not in read_by
            # Format user display name
            author_id = log.get('user_id')
            author_name = profile_map.get(author_id, '')
            if author_name and ' ' in author_name:
                first, rest = author_name.split(' ', 1)
                last_initial = rest[0] if rest else ''
                display_name = f"{first} {last_initial}."
            else:
                display_name = author_name or author_id[:8]
            # Format date/time
            import dateutil.parser
            dt_raw = log.get('created_at', '')
            try:
                dt = dateutil.parser.parse(dt_raw)
                dt_str = dt.strftime('%I:%M %p').lstrip('0') + f" on {dt.strftime('%m/%d/%Y')}"
            except Exception:
                dt_str = dt_raw
            meta = f"{display_name} at {dt_str}"
            # Layer title and meta info over the expander using custom HTML label
            # Use Markdown for the expander label, no HTML or unsafe_allow_html
            expander_label = f"**__{log.get('title', 'Log Entry')}__**  \n:gray[{meta}]"
            with st.expander(label=expander_label, expanded=False):
                # Mark as read if not already
                if user_id not in read_by:
                    try:
                        new_read_by = read_by + [user_id]
                        supabase.from_('logs').update({"read_by": new_read_by}).eq('id', log["id"]).execute()
                        read_by = new_read_by  # for display
                    except Exception:
                        pass

                st.write(log.get('message', ''))
                st.caption(f"By: {profile_map.get(log.get('user_id'), 'Unknown')}")
                
                # Who has read
                st.markdown("**Who has read this post:**")
                names = []
                for rid in read_by:
                    name = profile_map.get(rid, "Unknown")
                    if rid == user_id:
                        name += " (you)"
                    names.append(name)
                if names:
                    st.write(", ".join(names))
                else:
                    st.write("_No one has read this yet, except you._")

                # Admin/manager delete
                if current_user.get("role", "").lower() in ["manager", "admin"]:
                    if st.button(f"Delete Log {log['id']}", key=f"delete_{log['id']}"):
                        try:
                            supabase.from_('logs').delete().eq('id', log["id"]).execute()
                            st.success("Log deleted. Please refresh.")
                        except Exception as e:
                            st.error(f"Error deleting log: {str(e)}")
    else:
        st.info("No logs found.")
