import streamlit as st
from supabase_client import get_supabase_client
from datetime import datetime

def show_profile(current_user, view_user_id=None):
    """Display and edit user profiles with robust error handling and normalized fields."""
    supabase = get_supabase_client()
    user_id = view_user_id or current_user["id"]
    user_profile = current_user if not view_user_id or view_user_id == current_user["id"] else None

    # If viewing another user, fetch their profile
    if not user_profile:
        try:
            resp = supabase.from_("profiles").select("*").eq("id", user_id).single().execute()
            user_profile = resp.data if resp and resp.data else None
        except Exception as e:
            st.error(f"User not found: {str(e)}")
            return
        if not user_profile:
            st.error("User not found.")
            return

    # --- Avatar Display ---
    avatar_url = user_profile.get("avatar_url", "")
    col1, col2 = st.columns([1,3])
    with col1:
        if avatar_url:
            st.image(avatar_url, width=150)
        else:
            st.info("No avatar set. (Upload below if this is your profile)")

    # --- Name/Role Display ---
    full_name = ((user_profile.get("first_name") or "") + " " + (user_profile.get("last_name") or "")).strip()
    short_name = (user_profile.get("first_name") or "") + " " + ((user_profile.get("last_name") or "")[:1]).upper() + "."
    st.session_state["sidebar_name"] = short_name.strip() if user_profile.get("first_name") else user_profile.get("name", "")
    with col2:
        st.title(f"{full_name or user_profile.get('name', '')}")
        st.caption(f"Role: {user_profile.get('role', 'N/A')}")

    # --- Profile Info Section ---
    st.markdown("---")
    st.subheader("Contact Info")
    st.write(f"**First Name:** {user_profile.get('first_name', 'N/A')}")
    st.write(f"**Last Name:** {user_profile.get('last_name', 'N/A')}")
    st.write(f"**Email:** {st.session_state.get('email', user_profile.get('email', 'N/A'))}")
    st.write(f"**Phone:** {user_profile.get('phone', 'N/A')}")

    st.markdown("---")
    st.subheader("Account Details")
    st.write(f"**Bio:** {user_profile.get('bio', 'N/A')}")

    # --- Profile Edit Section (Self Only) ---
    if not view_user_id or view_user_id == current_user["id"]:
        st.markdown("---")
        st.subheader("Edit Contact Info")
        with st.form("edit_contact_info_form"):
            new_first = st.text_input("First Name", value=user_profile.get("first_name", ""))
            new_last = st.text_input("Last Name", value=user_profile.get("last_name", ""))
            new_phone = st.text_input("Phone", value=user_profile.get("phone", ""))
            new_bio = st.text_area("Bio", value=user_profile.get("bio", ""))
            if st.form_submit_button("Save Changes"):
                update_fields = {
                    "first_name": new_first,
                    "last_name": new_last,
                    "phone": new_phone,
                    "bio": new_bio
                }
                try:
                    supabase.from_("profiles").update(update_fields).eq("id", user_id).execute()
                    st.success("Profile updated. Refresh to see changes.")
                except Exception as e:
                    st.error(f"Error updating profile: {str(e)}")

        st.markdown("---")
        st.subheader("Update Profile Photo")
        uploaded_file = st.file_uploader("Upload avatar (PNG/JPG, max 2MB)", type=["png", "jpg", "jpeg"])
        if uploaded_file:
            bucket = "avatars"
            file_ext = uploaded_file.name.split('.')[-1]
            file_path = f"{user_id}/avatar.{file_ext}"
            storage = supabase.storage()
            try:
                storage.from_(bucket).remove([file_path])
            except Exception:
                pass
            try:
                upload_res = storage.from_(bucket).upload(file_path, uploaded_file)
                if upload_res:
                    supabase_url = supabase._client_config['url'] if hasattr(supabase, '_client_config') else st.secrets["SUPABASE_URL"]
                    public_url = f"{supabase_url}/storage/v1/object/public/{bucket}/{file_path}"
                    supabase.from_("profiles").update({"avatar_url": public_url}).eq("id", user_id).execute()
                    st.success("Avatar updated!")
            except Exception as e:
                st.error(f"Error uploading avatar: {str(e)}")
            if hasattr(upload_res, "status_code") and upload_res.status_code not in [200, 201]:
                st.error("Failed to upload avatar. Try again or check file size.")
            else:
                supabase_url = supabase._client_config['url'] if hasattr(supabase, '_client_config') else st.secrets["SUPABASE_URL"]
                public_url = f"{supabase_url}/storage/v1/object/public/{bucket}/{file_path}"
                supabase.from_("profiles").update({"avatar_url": public_url}).eq("id", user_id).execute()
                st.success("Avatar updated! Please refresh the page to see it.")

    # --- Extra Info/Legacy Fields ---
    st.markdown("---")
    st.subheader("Legacy/Other Info")
    st.write(f"**Name (legacy):** {user_profile.get('name', '')}")

    # --- Messaging Section ---
    st.markdown("---")
    profile_user = user_profile
    if view_user_id and profile_user:
        st.subheader(f"Send Message to {profile_user.get('first_name', profile_user.get('name', 'Unknown User'))}")
        with st.form("send_direct_message_form"):
            message_content = st.text_area("Message", "", height=100)
            send_submitted = st.form_submit_button("Send Message")
            if send_submitted:
                if message_content:
                    try:
                        message_data = {
                            'sender_id': current_user['id'],
                            'receiver_id': profile_user['id'],
                            'content': message_content,
                            'created_at': datetime.now().isoformat(),
                            'read': False
                        }
                        insert_response = supabase.from_('messages').insert([message_data]).execute()
                        if insert_response.data:
                            st.success("Message sent successfully!")
                        else:
                            st.error(f"Error sending message: {insert_response.error.message}")
                    except Exception as e:
                        st.error(f"Error sending message: {str(e)}")
                else:
                    st.error("Please enter a message.")