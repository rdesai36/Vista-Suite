import streamlit as st
from supabase_client import get_supabase_client
from datetime import datetime

def show_logs(current_user):
    supabase = get_supabase_client()
    st.title("Front Desk Logbook")

    # --- Fetch all profiles for read-by display ---
    try:
        profiles_response = supabase.from_('profiles').select('id, first_name, last_name').execute()
        all_profiles = profiles_response.data if profiles_response and profiles_response.data else []
        profile_map = {p['id']: f"{p.get('first_name','')} {p.get('last_name','')[0]}.".strip() for p in all_profiles}
    except Exception as e:
        profile_map = {}

    # --- Fetch Logs (filter/search optional) ---
    filter_text = st.text_input("Filter logs (by title/message/user)", value="", key="log_filter")
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
            read_by = log.get("read_by") or []
            is_unread = user_id not in read_by
            expander_header = (
                f"{'🟢' if is_unread else '⚪'} "
                f"{log.get('title', 'Log Entry')} - {log.get('created_at', '')[:19].replace('T', ' ')}"
            )
            with st.expander(expander_header):
                # Mark as read if not already
                if user_id not in read_by:
                    try:
                        new_read_by = read_by + [user_id]
                        supabase.from_('logs').update({"read_by": new_read_by}).eq('id', log["id"]).execute()
                        read_by = new_read_by  # for display
                    except Exception:
                        pass

                st.write(log.get('message', ''))
                st.caption(f"By: {log.get('user_name', 'Unknown')}")
                
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
                    st.write("_No one has read this yet._")

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

    # --- Add New Log ---
    st.markdown("---")
    st.subheader("Add New Log Entry")
    with st.form("add_log_form"):
        title = st.text_input("Title", max_chars=50)
        message = st.text_area("Message", max_chars=2000)
        submitted = st.form_submit_button("Submit Log")
        if submitted:
            log_data = {
                "title": title,
                "message": message,
                "user_id": user_id,
                "user_name": current_user.get("first_name", "") + " " + current_user.get("last_name", ""),
                "created_at": datetime.now().isoformat(),
                "read_by": [user_id],  # Mark creator as read
            }
            try:
                insert_res = supabase.from_('logs').insert(log_data).execute()
                if insert_res.data:
                    st.success("Log entry added!")
                    st.experimental_rerun()
                else:
                    st.error("Failed to add log.")
            except Exception as e:
                st.error(f"Error adding log: {str(e)}")