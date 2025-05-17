import pandas as pd
from datetime import datetime, timedelta
from database import db_manager
import streamlit as st

class DataHandler:
    def __init__(self):
        self.occupancy_data = None
        self.revenue_data = None
        self.booking_data = None
        self.room_data = None
        self.guest_data = None
    
    def _check_data_loaded(self):
        """Check if data is loaded"""
        return (self.occupancy_data is not None and 
                self.revenue_data is not None and 
                self.booking_data is not None and 
                self.room_data is not None and 
                self.guest_data is not None)
    
    def load_data(self, start_date=None, end_date=None):
        """
        Load data from Supabase database.
        """
        try:
            # Get rooms from database
            rooms = db_manager.get_all_rooms()
            if rooms:
                self.room_data = pd.DataFrame(rooms)
            else:
                self.room_data = pd.DataFrame(columns=['id', 'room_number', 'room_type', 'status', 'last_cleaned', 'maintenance_due'])
            
            # Query occupancy data from database
            if start_date and end_date:
                # Convert to ISO format strings if they're date objects
                if isinstance(start_date, datetime.date) and not isinstance(start_date, datetime):
                    start_date = datetime.combine(start_date, datetime.min.time()).isoformat()
                if isinstance(end_date, datetime.date) and not isinstance(end_date, datetime):
                    end_date = datetime.combine(end_date, datetime.min.time()).isoformat()
            return False
        except Exception as e:
            print(f"Error loading data: {str(e)}")
            return False
    
    def get_kpi_summary(self, start_date, end_date):
        """Get summary of key performance indicators for the given date range"""
        if not self._check_data_loaded():
            self.load_data(start_date, end_date)
        
        # Calculate KPIs based on loaded data
        kpi_data = {
            "occupancy_rate": None,
            "adr": None,  # Average Daily Rate
            "revpar": None,  # Revenue Per Available Room
            "total_revenue": None,
            "bookings": None,
            "avg_length_of_stay": None
        }
        
        # Calculate occupancy rate if data is available
        if not self.occupancy_data.empty and 'occupancy_rate' in self.occupancy_data.columns:
            kpi_data["occupancy_rate"] = self.occupancy_data['occupancy_rate'].mean()
        
        # Calculate revenue metrics if data is available
        if not self.revenue_data.empty:
            if 'total_revenue' in self.revenue_data.columns:
                kpi_data["total_revenue"] = self.revenue_data['total_revenue'].sum()
            
            # Calculate ADR and RevPAR if we have both occupancy and revenue data
            if (not self.occupancy_data.empty and 'rooms_occupied' in self.occupancy_data.columns
                and 'room_revenue' in self.revenue_data.columns):
                
                total_room_revenue = self.revenue_data['room_revenue'].sum()
                total_rooms_occupied = self.occupancy_data['rooms_occupied'].sum()
                total_available_rooms = self.occupancy_data['total_rooms'].sum()
                
                if total_rooms_occupied > 0:
                    kpi_data["adr"] = total_room_revenue / total_rooms_occupied
                
                if total_available_rooms > 0:
                    kpi_data["revpar"] = total_room_revenue / total_available_rooms
        
        # Calculate booking metrics if data is available
        if not self.booking_data.empty:
            kpi_data["bookings"] = len(self.booking_data)
            
            # Calculate average length of stay
            if 'check_in_date' in self.booking_data.columns and 'check_out_date' in self.booking_data.columns:
                self.booking_data['length_of_stay'] = (self.booking_data['check_out_date'] - self.booking_data['check_in_date']).dt.days
                kpi_data["avg_length_of_stay"] = self.booking_data['length_of_stay'].mean()
        
        return kpi_data
    
    def get_occupancy_data(self, start_date, end_date):
        """Get occupancy data for the given date range"""
        if not self._check_data_loaded():
            self.load_data(start_date, end_date)
        
        return self.occupancy_data
    
    def get_revenue_data(self, start_date, end_date):
        """Get revenue data for the given date range"""
        if not self._check_data_loaded():
            self.load_data(start_date, end_date)
        
        return self.revenue_data
    
    def get_booking_data(self, start_date, end_date):
        """Get booking data for the given date range"""
        if not self._check_data_loaded():
            self.load_data(start_date, end_date)
        
        return self.booking_data
    
    def get_room_status_data(self):
        """Get current room status data"""
        if not self._check_data_loaded():
            self.load_data()
        
        return self.room_data
    
    def get_checkin_checkout_today(self):
        """Get check-ins and check-outs for today"""
        if not self._check_data_loaded():
            self.load_data()
        
        today = datetime.now().date()
        today_start = datetime.combine(today, datetime.min.time())
        today_end = datetime.combine(today, datetime.max.time())
        
        try:
            # Make sure we have a valid database session
            if hasattr(db_manager, 'db') and db_manager.db is not None:
                try:
                    # Test the connection before querying
                    db_manager.db.execute(sa.sql.text("SELECT 1"))
                except Exception:
                    # Reset session if needed
                    db_manager.reconnect()
            
            # Query database for check-ins and check-outs today
            from sqlalchemy.orm import joinedload
            checkin_bookings = db_manager.db.query(Booking).options(
                joinedload(Booking.guest),
                joinedload(Booking.room)
            ).filter(
                Booking.check_in_date >= today_start,
                Booking.check_in_date <= today_end
            ).all()
            
            checkout_bookings = db_manager.db.query(Booking).options(
                joinedload(Booking.guest),
                joinedload(Booking.room)
            ).filter(
                Booking.check_out_date >= today_start,
                Booking.check_out_date <= today_end
            ).all()
            
        except Exception as e:
            print(f"Error getting check-ins/check-outs: {str(e)}")
            # Rollback transaction on error
            if hasattr(db_manager, 'db') and db_manager.db is not None:
                try:
                    db_manager.db.rollback()
                except:
                    pass
            
            # Return empty results on error
            checkin_bookings = []
            checkout_bookings = []
        
        # Convert to DataFrames
        if checkin_bookings:
            checkins_data = []
            for booking in checkin_bookings:
                guest_name = booking.guest.name if booking.guest else "Unknown"
                room_number = booking.room.room_number if booking.room else "Unknown"
                room_type = booking.room.room_type if booking.room else "Unknown"
                nights = (booking.check_out_date - booking.check_in_date).days
                
                checkins_data.append({
                    'booking_id': booking.booking_id,
                    'guest_name': guest_name,
                    'room_number': room_number,
                    'room_type': room_type,
                    'nights': nights,
                    'amount': booking.total_amount
                })
            checkins = pd.DataFrame(checkins_data)
        else:
            checkins = pd.DataFrame(columns=['booking_id', 'guest_name', 'room_number', 'room_type', 'nights', 'amount'])
        
        if checkout_bookings:
            checkouts_data = []
            for booking in checkout_bookings:
                guest_name = booking.guest.name if booking.guest else "Unknown"
                room_number = booking.room.room_number if booking.room else "Unknown"
                room_type = booking.room.room_type if booking.room else "Unknown"
                stayed_nights = (booking.check_out_date - booking.check_in_date).days
                
                checkouts_data.append({
                    'booking_id': booking.booking_id,
                    'guest_name': guest_name,
                    'room_number': room_number,
                    'room_type': room_type,
                    'stayed_nights': stayed_nights,
                    'amount': booking.total_amount,
                    'payment_status': booking.payment_status
                })
            checkouts = pd.DataFrame(checkouts_data)
        else:
            checkouts = pd.DataFrame(columns=['booking_id', 'guest_name', 'room_number', 'room_type', 'stayed_nights', 'amount', 'payment_status'])
        
        return checkins, checkouts
    
    def get_guest_data(self, search_term=None):
        """Get guest data, optionally filtered by search term"""
        try:
            if not self._check_data_loaded():
                success = self.load_data()
                if not success:
                    return pd.DataFrame(columns=['guest_id', 'guest_name', 'phone', 'email', 'address', 'loyalty_level', 'current_stay'])
            
            # If search term provided, filter data
            if search_term and not self.guest_data.empty:
                # Filter by name if column exists
                if 'guest_name' in self.guest_data.columns:
                    return self.guest_data[self.guest_data['guest_name'].str.contains(search_term, case=False, na=False)]
            
            return self.guest_data
        except Exception as e:
            print(f"Error getting guest data: {str(e)}")
            # Return empty dataframe on error
            return pd.DataFrame(columns=['guest_id', 'guest_name', 'phone', 'email', 'address', 'loyalty_level', 'current_stay'])

# Create a singleton instance to be used across the app
hotel_data = DataHandler()
