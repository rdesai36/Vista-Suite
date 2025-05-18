import pandas as pd
from datetime import datetime, timedelta
from supabase_client import get_supabase_client

class DataHandler:
    """Class to handle data operations for the hotel dashboard"""
    
    def __init__(self):
        """Initialize the data handler"""
        # We'll use Supabase client directly instead of db_manager
        pass
        
    def get_occupancy_data(self, start_date, end_date):
        """Get occupancy data for the given date range"""
        try:
            supabase = get_supabase_client()
            response = supabase.from_('occupancy_data').select('*').gte('date', start_date.isoformat()).lte('date', end_date.isoformat()).execute()
            return response.data
        except Exception as e:
            print(f"Error getting occupancy data: {str(e)}")
            return []
    
    def get_revenue_data(self, start_date, end_date):
        """Get revenue data for the given date range"""
        try:
            supabase = get_supabase_client()
            response = supabase.from_('revenue_data').select('*').gte('date', start_date.isoformat()).lte('date', end_date.isoformat()).execute()
            return response.data
        except Exception as e:
            print(f"Error getting revenue data: {str(e)}")
            return []
    
    def get_bookings(self, start_date=None, end_date=None):
        """Get bookings, optionally filtered by date range"""
        try:
            supabase = get_supabase_client()
            query = supabase.from_('bookings').select('*,guest:profiles(*),room:rooms(*)')
            
            if start_date and end_date:
                query = query.or_(
                    f'check_in_date.gte.{start_date.isoformat()}.and.check_in_date.lte.{end_date.isoformat()},'
                    f'check_out_date.gte.{start_date.isoformat()}.and.check_out_date.lte.{end_date.isoformat()},'
                    f'check_in_date.lte.{start_date.isoformat()}.and.check_out_date.gte.{end_date.isoformat()}'
                )
            
            response = query.execute()
            return response.data
        except Exception as e:
            print(f"Error getting bookings: {str(e)}")
            return []
    
    def get_rooms(self):
        """Get all rooms"""
        try:
            supabase = get_supabase_client()
            response = supabase.from_('rooms').select('*').execute()
            return response.data
        except Exception as e:
            print(f"Error getting rooms: {str(e)}")
            return []
    
    def get_users(self):
        """Get all users"""
        try:
            supabase = get_supabase_client()
            response = supabase.from_('profiles').select('*').execute()
            return response.data
        except Exception as e:
            print(f"Error getting users: {str(e)}")
            return []
    
    def get_user_by_id(self, user_id):
        """Get a user by ID"""
        try:
            supabase = get_supabase_client()
            response = supabase.from_('profiles').select('*').eq('id', user_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error getting user: {str(e)}")
            return None

# Create a singleton instance to be used across the app
hotel_data = DataHandler()