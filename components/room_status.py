import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from data_handler import hotel_data

def show_room_status():
    """Display room status visualization and management"""
    st.header("Room Status Management")
    
    # Load data
    if hasattr(hotel_data, 'get_room_status_data'):
        room_data = pd.DataFrame(hotel_data.get_room_status_data())
    else:
        st.error("Room status data function is missing from DataHandler. Please contact support.")
        room_data = pd.DataFrame([])

    # Standardized empty state handling
    if room_data is None or (hasattr(room_data, 'empty') and room_data.empty):
        st.warning("No room status data available for the selected period.")
        st.info("Once your property is connected to HotelKey, room status metrics and trends will appear here.")
        return
    
    # Top summary metrics
    st.subheader("Room Status Summary")
    
    if not room_data.empty:
        # Calculate status counts
        if 'status' in room_data.columns:
            status_counts = room_data['status'].value_counts().to_dict()
            total_rooms = len(room_data)
            
            # Display metrics in columns
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                occupied_count = status_counts.get('Occupied', 0)
                occupied_pct = (occupied_count / total_rooms * 100) if total_rooms > 0 else 0
                st.metric(
                    label="Occupied",
                    value=occupied_count,
                    delta=f"{occupied_pct:.1f}%"
                )
            
            with col2:
                vacant_count = status_counts.get('Vacant', 0)
                vacant_pct = (vacant_count / total_rooms * 100) if total_rooms > 0 else 0
                st.metric(
                    label="Vacant",
                    value=vacant_count,
                    delta=f"{vacant_pct:.1f}%"
                )
            
            with col3:
                dirty_count = status_counts.get('Dirty', 0)
                dirty_pct = (dirty_count / total_rooms * 100) if total_rooms > 0 else 0
                st.metric(
                    label="Dirty",
                    value=dirty_count,
                    delta=f"{dirty_pct:.1f}%"
                )
            
            with col4:
                maintenance_count = status_counts.get('Maintenance', 0) + status_counts.get('Out of Order', 0)
                maintenance_pct = (maintenance_count / total_rooms * 100) if total_rooms > 0 else 0
                st.metric(
                    label="Maintenance/OOO",
                    value=maintenance_count,
                    delta=f"{maintenance_pct:.1f}%"
                )
            
            # Create visualization of room status
            st.subheader("Room Status Visualization")
            
            # Visual representation option
            viz_type = st.radio(
                "Select Visualization",
                ["Status Distribution", "Floor Map", "Room Type Breakdown"],
                horizontal=True
            )
            
            if viz_type == "Status Distribution":
                # Prepare data for pie chart
                status_df = pd.DataFrame({
                    'Status': status_counts.keys(),
                    'Count': status_counts.values()
                })
                
                # Create pie chart
                fig = px.pie(
                    status_df,
                    values='Count',
                    names='Status',
                    title="Room Status Distribution",
                    color='Status',
                    color_discrete_map={
                        'Occupied': '#1E88E5',  # Blue
                        'Vacant': '#4CAF50',    # Green
                        'Dirty': '#FFC107',     # Yellow
                        'Maintenance': '#FF9800', # Orange
                        'Out of Order': '#F44336' # Red
                    }
                )
                st.plotly_chart(fig, use_container_width=True)
            
            elif viz_type == "Floor Map":
                # Create simplified floor map visualization
                if 'room_number' in room_data.columns and 'status' in room_data.columns:
                    try:
                        # Extract floor number from room number (assuming format like 101, 102, 201, 202)
                        room_data['floor'] = room_data['room_number'].astype(str).str[0].astype(int)
                        
                        # Sort by room number
                        room_data = room_data.sort_values('room_number')
                        
                        # Display floor tabs
                        floors = sorted(room_data['floor'].unique())
                        floor_tabs = st.tabs([f"Floor {floor}" for floor in floors])
                        
                        # Create a visualization for each floor
                        for i, floor in enumerate(floors):
                            with floor_tabs[i]:
                                floor_rooms = room_data[room_data['floor'] == floor]
                                
                                # Create grid layout of rooms
                                cols = 5  # number of columns in the grid
                                rows = (len(floor_rooms) + cols - 1) // cols
                                
                                # Create a grid display of rooms
                                for r in range(rows):
                                    row_cols = st.columns(cols)
                                    for c in range(cols):
                                        idx = r * cols + c
                                        if idx < len(floor_rooms):
                                            room = floor_rooms.iloc[idx]
                                            
                                            # Set color based on status
                                            status_colors = {
                                                'Occupied': '#1E88E5',   # Blue
                                                'Vacant': '#4CAF50',     # Green
                                                'Dirty': '#FFC107',      # Yellow
                                                'Maintenance': '#FF9800', # Orange
                                                'Out of Order': '#F44336' # Red
                                            }
                                            
                                            status = room.get('status', 'Unknown')
                                            color = status_colors.get(status, '#9E9E9E')
                                            
                                            # Display room as a colored box with room number
                                            with row_cols[c]:
                                                st.markdown(
                                                    f"""
                                                    <div style="
                                                        background-color: {color};
                                                        color: white;
                                                        border-radius: 5px;
                                                        padding: 10px;
                                                        text-align: center;
                                                        margin: 5px 0;
                                                    ">
                                                        <h3>{room.get('room_number', 'N/A')}</h3>
                                                        <p>{status}</p>
                                                    </div>
                                                    """,
                                                    unsafe_allow_html=True
                                                )
                    except Exception as e:
                        st.error(f"Error creating floor map: {str(e)}")
                        st.info("Floor map visualization requires room numbers in a specific format.")
                else:
                    st.info("Room number data required for floor map visualization.")
            
            elif viz_type == "Room Type Breakdown":
                if 'room_type' in room_data.columns and 'status' in room_data.columns:
                    # Create a grouped bar chart by room type and status
                    room_type_status = pd.crosstab(room_data['room_type'], room_data['status'])
                    
                    # Convert to long format for plotting
                    room_type_status_long = room_type_status.reset_index().melt(
                        id_vars='room_type',
                        var_name='status',
                        value_name='count'
                    )
                    
                    # Create grouped bar chart
                    fig = px.bar(
                        room_type_status_long,
                        x='room_type',
                        y='count',
                        color='status',
                        title="Room Status by Room Type",
                        labels={
                            'room_type': 'Room Type',
                            'count': 'Number of Rooms',
                            'status': 'Status'
                        },
                        color_discrete_map={
                            'Occupied': '#1E88E5',  # Blue
                            'Vacant': '#4CAF50',    # Green
                            'Dirty': '#FFC107',     # Yellow
                            'Maintenance': '#FF9800', # Orange
                            'Out of Order': '#F44336' # Red
                        }
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Room type data required for this visualization.")
        else:
            st.warning("Room status data is not available.")
    else:
        st.warning("No room data available.")
    
    # Detailed room list with filters
    st.subheader("Room List")
    
    if not room_data.empty:
        # Add filters
        col1, col2 = st.columns(2)
        
        with col1:
            if 'status' in room_data.columns:
                status_filter = st.multiselect(
                    "Filter by Status",
                    options=room_data['status'].unique(),
                    default=room_data['status'].unique()
                )
            else:
                status_filter = []
        
        with col2:
            if 'room_type' in room_data.columns:
                type_filter = st.multiselect(
                    "Filter by Room Type",
                    options=room_data['room_type'].unique(),
                    default=room_data['room_type'].unique()
                )
            else:
                type_filter = []
        
        # Apply filters
        filtered_rooms = room_data
        if status_filter and 'status' in room_data.columns:
            filtered_rooms = filtered_rooms[filtered_rooms['status'].isin(status_filter)]
        if type_filter and 'room_type' in room_data.columns:
            filtered_rooms = filtered_rooms[filtered_rooms['room_type'].isin(type_filter)]
        
        # Display filtered room list
        if not filtered_rooms.empty:
            st.dataframe(filtered_rooms, hide_index=True)
            
            # Add change status functionality
            st.subheader("Change Room Status")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                selected_room = st.selectbox(
                    "Select Room",
                    options=filtered_rooms['room_number'] if 'room_number' in filtered_rooms.columns else []
                )
            
            with col2:
                new_status = st.selectbox(
                    "New Status",
                    options=['Vacant', 'Occupied', 'Dirty', 'Maintenance', 'Out of Order']
                )
            
            with col3:
                st.write("Action")
                update_button = st.button("Update Status")
            
            if update_button and selected_room:
                success = db_manager.update_room_status(selected_room_id, selected_status)
                if success:
                    st.success("Room status updated successfully.")
                else:
                    st.error("Failed to update room status.")
        else:
            st.info("Failed to update room status.")
    
    # Housekeeping and maintenance section
    st.subheader("Housekeeping & Maintenance")
    
    tab1, tab2 = st.tabs(["Housekeeping Queue", "Maintenance Requests"])
    
    with tab1:
        st.info("No rooms in housekeeping queue.")
        
        # Add form to request cleaning
        with st.expander("Request Room Cleaning"):
            room_number = st.selectbox(
                "Room Number",
                options=room_data['room_number'] if not room_data.empty and 'room_number' in room_data.columns else []
            )
            priority = st.select_slider(
                "Priority",
                options=["Low", "Medium", "High", "Urgent"]
            )
            notes = st.text_area("Notes", height=100)
            
            if st.button("Submit Cleaning Request"):
                st.success(f"Cleaning request submitted for room {room_number}")
    
    with tab2:
        st.info("No active maintenance requests.")
        
        # Add form to create maintenance request
        with st.expander("Create Maintenance Request"):
            room_number = st.selectbox(
                "Room Number",
                options=room_data['room_number'] if not room_data.empty and 'room_number' in room_data.columns else [],
                key="maintenance_room"
            )
            issue_type = st.selectbox(
                "Issue Type",
                options=["Plumbing", "Electrical", "Furniture", "HVAC", "Other"]
            )
            description = st.text_area("Description", height=100)
            impact = st.radio(
                "Impact on Room",
                options=["Room can still be used", "Room needs to be out of order"]
            )
            
            if st.button("Submit Maintenance Request"):
                st.success(f"Maintenance request submitted for room {room_number}")
