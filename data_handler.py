import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sqlalchemy as sa
from models_db import OccupancyData, RevenueData, Room, Guest, Booking
from database import db_manager

class HotelDataHandler:
    """Class for handling hotel data operations"""
    
    def __init__(self):
        """Initialize data storage"""
        # References to cached data
        self.occupancy_data = None
        self.revenue_data = None
        self.booking_data = None
        self.room_data = None
        self.guest_data = None 
    
    def _check_data_loaded(self):
        """Check if data is loaded and show appropriate error if not"""
        if (self.occupancy_data is None or self.revenue_data is None or 
            self.booking_data is None or self.room_data is None or 
            self.guest_data is None):
            return False
        return True
    
    def load_data(self, start_date=None, end_date=None):
        """
        Load data from database.
        """
        try:
            # Make sure we have a clean database session
            if hasattr(db_manager, 'db') and db_manager.db is not None:
                try:
                    # Try to check the connection with a simple query
                    db_manager.db.execute(sa.sql.text("SELECT 1"))
                except Exception as e:
                    # If there's an error, try to rollback and reconnect
                    try:
                        db_manager.db.rollback()
                    except:
                        pass
                    
                    try:
                        db_manager.db.close()
                    except:
                        pass
                    
                    from database import SessionLocal
                    if SessionLocal:
                        db_manager.db = SessionLocal()
            
            # Convert database models to DataFrames
            
            # Get rooms from database
            rooms = db_manager.get_all_rooms()
            if rooms:
                room_data = []
                for room in rooms:
                    room_data.append({
                        'room_id': room.id,
                        'room_number': room.room_number,
                        'room_type': room.room_type,
                        'status': room.status,
                        'last_cleaned': room.last_cleaned,
                        'maintenance_due': room.maintenance_due
                    })
                self.room_data = pd.DataFrame(room_data)
            else:
                self.room_data = pd.DataFrame(columns=['room_id', 'room_number', 'room_type', 'status', 'last_cleaned', 'maintenance_due'])
            
            # Query occupancy data from database
            if start_date and end_date:
                # Convert to datetime if they're date objects
                if isinstance(start_date, datetime.date) and not isinstance(start_date, datetime):
                    start_date = datetime.combine(start_date, datetime.min.time())
                if isinstance(end_date, datetime.date) and not isinstance(end_date, datetime):
                    end_date = datetime.combine(end_date, datetime.min.time())
                
                # Query occupancy data for date range
                occupancy_data = db_manager.db.query(OccupancyData).filter(
                    OccupancyData.date >= start_date,
                    OccupancyData.date <= end_date
                ).all()
                
                if occupancy_data:
                    occ_data = []
                    for occ in occupancy_data:
                        occ_data.append({
                            'date': occ.date,
                            'rooms_occupied': occ.rooms_occupied,
                            'total_rooms': occ.total_rooms,
                            'occupancy_rate': occ.occupancy_rate
                        })
                    self.occupancy_data = pd.DataFrame(occ_data)
                else:
                    self.occupancy_data = pd.DataFrame(columns=['date', 'rooms_occupied', 'total_rooms', 'occupancy_rate'])
                
                # Query revenue data for date range
                revenue_data = db_manager.db.query(RevenueData).filter(
                    RevenueData.date >= start_date,
                    RevenueData.date <= end_date
                ).all()
                
                if revenue_data:
                    rev_data = []
                    for rev in revenue_data:
                        rev_data.append({
                            'date': rev.date,
                            'room_revenue': rev.room_revenue,
                            'f&b_revenue': rev.fb_revenue,
                            'other_revenue': rev.other_revenue,
                            'total_revenue': rev.total_revenue
                        })
                    self.revenue_data = pd.DataFrame(rev_data)
                else:
                    self.revenue_data = pd.DataFrame(columns=['date', 'room_revenue', 'f&b_revenue', 'other_revenue', 'total_revenue'])
                
                # Query bookings for date range
                bookings = db_manager.db.query(Booking).filter(
                    sa.or_(
                        sa.and_(
                            Booking.check_in_date >= start_date,
                            Booking.check_in_date <= end_date
                        ),
                        sa.and_(
                            Booking.check_out_date >= start_date,
                            Booking.check_out_date <= end_date
                        ),
                        sa.and_(
                            Booking.check_in_date <= start_date,
                            Booking.check_out_date >= end_date
                        )
                    )
                ).all()
                
                if bookings:
                    booking_data = []
                    for booking in bookings:
                        guest_name = booking.guest.name if booking.guest else "Unknown"
                        room_type = booking.room.room_type if booking.room else "Unknown"
                        room_number = booking.room.room_number if booking.room else "Unknown"
                        
                        booking_data.append({
                            'booking_id': booking.booking_id,
                            'guest_name': guest_name,
                            'check_in_date': booking.check_in_date,
                            'check_out_date': booking.check_out_date,
                            'room_type': room_type,
                            'room_number': room_number,
                            'booking_status': booking.booking_status,
                            'payment_status': booking.payment_status,
                            'total_amount': booking.total_amount
                        })
                    self.booking_data = pd.DataFrame(booking_data)
                else:
                    self.booking_data = pd.DataFrame(columns=['booking_id', 'guest_name', 'check_in_date', 'check_out_date', 'room_type', 'room_number', 'booking_status', 'payment_status', 'total_amount'])
            else:
                # Initialize empty DataFrames if no date range provided
                self.occupancy_data = pd.DataFrame(columns=['date', 'rooms_occupied', 'total_rooms', 'occupancy_rate'])
                self.revenue_data = pd.DataFrame(columns=['date', 'room_revenue', 'f&b_revenue', 'other_revenue', 'total_revenue'])
                self.booking_data = pd.DataFrame(columns=['booking_id', 'guest_name', 'check_in_date', 'check_out_date', 'room_type', 'room_number', 'booking_status', 'payment_status', 'total_amount'])
            
            # Get all guests
            guests = db_manager.db.query(Guest).all()
            if guests:
                guest_data = []
                for guest in guests:
                    # Check if guest has a current stay
                    current_stay = None
                    current_booking = db_manager.db.query(Booking).filter(
                        Booking.guest_id == guest.id,
                        Booking.check_in_date <= datetime.now(),
                        Booking.check_out_date >= datetime.now(),
                        Booking.booking_status == "Confirmed"
                    ).first()
                    
                    if current_booking:
                        room_number = current_booking.room.room_number if current_booking.room else "Unknown"
                        current_stay = {
                            'room': room_number,
                            'check_in': current_booking.check_in_date,
                            'check_out': current_booking.check_out_date
                        }
                    
                    guest_data.append({
                        'guest_id': guest.guest_id,
                        'guest_name': guest.name,
                        'phone': guest.phone,
                        'email': guest.email,
                        'address': guest.address,
                        'loyalty_level': guest.loyalty_level,
                        'current_stay': current_stay
                    })
                self.guest_data = pd.DataFrame(guest_data)
            else:
                self.guest_data = pd.DataFrame(columns=['guest_id', 'guest_name', 'phone', 'email', 'address', 'loyalty_level', 'current_stay'])
            
            return True
        except Exception as e:
            # In a real application, you'd want to log this error
            print(f"Error loading data: {str(e)}")
            
            # Make sure to rollback any failed transaction
            if hasattr(db_manager, 'db') and db_manager.db is not None:
                try:
                    db_manager.db.rollback()
                except:
                    pass
                
                # Try to reset the session after error
                try:
                    db_manager.reconnect()
                except:
                    pass
            
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
hotel_data = HotelDataHandler()
