import streamlit as st
from supabase_client import get_supabase_client

supabase = get_supabase_client()

def show_team(current_user):
    """Display the team directory with robust error handling and future extensibility."""
    st.title("Team Directory")
    try:
        # Fetch all user profiles except the current user
        profiles_response = supabase.from_("profiles").select("*").neq("id", current_user.get('id')).execute()
        profiles = profiles_response.data or []
    except Exception as e:
        st.error(f"Error fetching team profiles: {str(e)}")
        return

    # Search/filter controls
    search = st.text_input("Search by name")
    roles = sorted(list({p.get('role', 'Unknown') for p in profiles if p.get('role')}))
    selected_roles = st.multiselect("Filter by role", roles)

    # Filter profiles
    filtered_profiles = profiles
    if search:
        filtered_profiles = [p for p in filtered_profiles if search.lower() in (p.get('name', '') + p.get('first_name', '') + p.get('last_name', '')).lower()]
    if selected_roles:
        filtered_profiles = [p for p in filtered_profiles if p.get('role') in selected_roles]

    if not filtered_profiles:
        st.info("No team members found.")
        return

    # Display team member cards
    cols = st.columns(3)
    for idx, profile in enumerate(filtered_profiles):
        with cols[idx % 3]:
            if profile.get('id') == current_user.get('id') or profile.get('email') == st.session_state.get('email'):
                continue
            full_name = ((profile.get('first_name') or '') + ' ' + (profile.get('last_name') or '')).strip() or profile.get('name', 'Unnamed')
            st.subheader(full_name)
            st.write(f"**Role:** {profile.get('role', 'N/A')}")
            st.write(f"**Email:** {st.session_state.get('email', profile.get('email', 'N/A'))}")
            st.write(f"**Phone:** {profile.get('phone', 'N/A')}")
            # Avatar/profile pic placeholder
            avatar_url = profile.get('avatar_url', '')
            if avatar_url:
                st.image(avatar_url, width=80)
            # Quick actions: Message and View Profile
            if st.button("Message", key=f"msg_{profile.get('id', idx)}"):
                st.session_state['page'] = 'messaging'
                st.session_state['target_user_id'] = profile.get('id')
                st.experimental_rerun()
            if st.button("View Profile", key=f"view_{profile.get('id', idx)}"):
                st.session_state['page'] = 'profile'
                st.session_state['view_user_id'] = profile.get('id')
                st.experimental_rerun()