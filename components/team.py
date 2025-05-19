import streamlit as st
from supabase_client import get_supabase_client

supabase = get_supabase_client()

def show_team(current_user):
    st.title("Team Directory")

    # Fetch all user profiles from Supabase
    profiles_response = supabase.from_("profiles").select("*").execute()
    profiles = profiles_response.data if profiles_response and profiles_response.data else []

    # Remove current user from the list
    user_id = current_user.get('id')
    profiles = [p for p in profiles if p.get('id') != user_id]

    # Search/filter controls
    search = st.text_input("Search by name")
    roles = list({p.get('role', 'Unknown') for p in profiles if p.get('role')})
    selected_roles = st.multiselect("Filter by role", roles)

    # Filter profiles
    if search:
        profiles = [p for p in profiles if search.lower() in p.get('name', '').lower()]
    if selected_roles:
        profiles = [p for p in profiles if p.get('role') in selected_roles]

    if not profiles:
        st.info("No team members found.")
        return

    # Display team member cards
    cols = st.columns(3)
    for idx, profile in enumerate(profiles):
        with cols[idx % 3]:
            st.subheader(profile.get('name', 'Unnamed'))
            st.write(f"**Role:** {profile.get('role', 'N/A')}")
            st.write(f"**Email:** {profile.get('email', 'N/A')}")
            st.write(f"**Phone:** {profile.get('phone', 'N/A')}")
            # Placeholder for avatar/profile pic if needed

            # Quick actions (messaging, view profile, etc.)
            st.button("Message", key=f"msg_{profile.get('id', idx)}", disabled=True)
            st.button("View Profile", key=f"view_{profile.get('id', idx)}", disabled=True)

