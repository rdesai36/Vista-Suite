import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

from data_handler import hotel_data

def show_front_office():
    """Display front office management interface"""
    st.header("Front Office Management")
    
    # Load data
    hotel_data.load_data()
    
    # Get today's arrivals and departures
    checkins, checkouts = hotel_data.get_checkin_checkout_today()
    
    # Tabs for different front office functions
    tab1, tab2, tab3, tab4 = st.tabs([
        "Today's Activity", 
        "Guest Search", 
        "Room Availability", 
        "Quick Actions"
    ])
    
    with tab1:
        show_today_activity(checkins, checkouts)
    
    with tab2:
        show_guest_search()
    
    with tab3:
        show_room_availability()
    
    with tab4:
        show_quick_actions()


def show_today_activity(checkins, checkouts):
    """Display today's check-ins and check-outs"""
    st.subheader("Today's Front Desk Activity")
    today = datetime.now().strftime("%A, %B %d, %Y")
    st.write(f"Date: {today}")
    
    # Summary metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(label="Expected Check-ins", value=len(checkins))
    
    with col2:
        st.metric(label="Expected Check-outs", value=len(checkouts))
    
    with col3:
        # This would normally be calculated from actual data
        st.metric(label="Rooms Available Tonight", value="N/A")
    
    # Check-ins section
    st.subheader("Check-ins")
    
    if not checkins.empty:
        # Add status column for demonstration
        if 'status' not in checkins.columns:
            checkins['status'] = "Pending"
        
        # Show check-ins with action buttons
        for i, row in checkins.iterrows():
            with st.expander(f"{row.get('guest_name', 'Guest')} - Room {row.get('room_number', 'N/A')}"):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**Booking ID:** {row.get('booking_id', 'N/A')}")
                    st.write(f"**Room Type:** {row.get('room_type', 'N/A')}")
                    st.write(f"**Nights:** {row.get('nights', 'N/A')}")
                    st.write(f"**Amount:** ${row.get('amount', 0):.2f}")
                
                with col2:
                    st.button("Check In", key=f"checkin_{row.get('booking_id', i)}")
                    st.button("Edit", key=f"edit_checkin_{row.get('booking_id', i)}")
    else:
        st.info("No check-ins scheduled for today.")
    
    # Check-outs section
    st.subheader("Check-outs")
    
    if not checkouts.empty:
        # Add status column for demonstration
        if 'status' not in checkouts.columns:
            checkouts['status'] = "Pending"
        
        # Show check-outs with action buttons
        for i, row in checkouts.iterrows():
            with st.expander(f"{row.get('guest_name', 'Guest')} - Room {row.get('room_number', 'N/A')}"):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**Booking ID:** {row.get('booking_id', 'N/A')}")
                    st.write(f"**Room Type:** {row.get('room_type', 'N/A')}")
                    st.write(f"**Stayed Nights:** {row.get('stayed_nights', 'N/A')}")
                    st.write(f"**Amount Due:** ${row.get('amount', 0):.2f}")
                    st.write(f"**Payment Status:** {row.get('payment_status', 'Not Paid')}")
                
                with col2:
                    st.button("Check Out", key=f"checkout_{row.get('booking_id', i)}")
                    st.button("Process Payment", key=f"payment_{row.get('booking_id', i)}")
    else:
        st.info("No check-outs scheduled for today.")


def show_guest_search():
    """Display guest search functionality"""
    st.subheader("Guest Search")
    
    search_term = st.text_input("Search by Guest Name, Room Number or Booking ID")
    
    if search_term:
        # Search in guest data
        guests = hotel_data.get_guest_data(search_term)
        
        if not guests.empty:
            st.subheader(f"Found {len(guests)} guests")
            
            for i, guest in guests.iterrows():
                with st.expander(f"{guest.get('guest_name', 'Guest')}"):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.write(f"**Guest ID:** {guest.get('guest_id', 'N/A')}")
                        st.write(f"**Phone:** {guest.get('phone', 'N/A')}")
                        st.write(f"**Email:** {guest.get('email', 'N/A')}")
                        st.write(f"**Loyalty Level:** {guest.get('loyalty_level', 'N/A')}")
                        
                        # Show current stay info if available
                        if guest.get('current_stay'):
                            st.write("**Current Stay:**")
                            st.write(f"  - Room: {guest.get('current_stay', {}).get('room', 'N/A')}")
                            st.write(f"  - Check-in: {guest.get('current_stay', {}).get('check_in', 'N/A')}")
                            st.write(f"  - Check-out: {guest.get('current_stay', {}).get('check_out', 'N/A')}")
                    
                    with col2:
                        st.button("View Details", key=f"view_{guest.get('guest_id', i)}")
                        st.button("Edit", key=f"edit_{guest.get('guest_id', i)}")
        else:
            st.info(f"No guests found matching '{search_term}'")
    else:
        st.info("Enter a search term to find guests")


def show_room_availability():
    """Display room availability interface"""
    st.subheader("Room Availability")
    
    # Date selection for availability check
    col1, col2 = st.columns(2)
    with col1:
        check_in_date = st.date_input("Check-in Date", datetime.now().date())
    with col2:
        check_out_date = st.date_input("Check-out Date", datetime.now().date() + timedelta(days=1))
    
    if check_in_date >= check_out_date:
        st.error("Check-out date must be after check-in date")
    else:
        # Get room data
        room_data = hotel_data.get_room_status_data()
        
        # In a real app, this would filter for available rooms between these dates
        if not room_data.empty:
            # Simulate filtering available rooms (in a real app this would check actual availability)
            available_rooms = room_data[room_data['status'] == 'Vacant'] if 'status' in room_data.columns else pd.DataFrame()
            
            st.write(f"Showing available rooms from {check_in_date} to {check_out_date}")
            
            if not available_rooms.empty:
                # Group by room type and count
                if 'room_type' in available_rooms.columns:
                    room_types = available_rooms.groupby('room_type').size().reset_index()
                    room_types.columns = ['Room Type', 'Available Count']
                    
                    # Display available room types
                    st.dataframe(room_types, hide_index=True)
                    
                    # Show detailed room list
                    st.subheader("Available Rooms")
                    st.dataframe(available_rooms, hide_index=True)
                else:
                    st.info("Room type information not available.")
            else:
                st.warning("No rooms available for the selected dates.")
        else:
            st.info("No room data available.")


def show_quick_actions():
    """Display quick actions for front desk staff"""
    st.subheader("Quick Actions")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("Guest Management")
        st.button("New Reservation")
        st.button("Walk-in Check-in")
        st.button("Early Check-in Request")
        st.button("Late Check-out Request")
    
    with col2:
        st.write("Room Management")
        st.button("Room Status Update")
        st.button("Housekeeping Request")
        st.button("Maintenance Request")
        st.button("Room Change Request")
    
    # Daily tasks and notes section
    st.subheader("Front Desk Notes")
    
    notes = st.text_area("Add notes for the team", height=100)
    if st.button("Save Notes"):
        st.success("Notes saved successfully!")
    
    # Display existing notes (in a real app, these would be loaded from a database)
    st.subheader("Shift Notes")
    st.info("No previous notes found.")
