import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from dotenv import load_dotenv

from models_base import Base  # or wherever your Base is
from models_db import User, OccupancyData, RevenueData, Room, Guest, Booking, Log, MessageThread, Message, LogRead
from datetime import datetime
from supabase_client import get_supabase_client, get_admin_client
import streamlit as st
import pandas as pd
import uuid

class DatabaseManager:
    def __init__(self):
        load_dotenv()

        db_url = os.getenv("DATABASE_URL", "sqlite:///vista.db")
        self.engine = create_engine(db_url, echo=False, connect_args={"check_same_thread": False})
        Base.metadata.create_all(self.engine)
        self.session_factory = sessionmaker(bind=self.engine)
        self.db = scoped_session(self.session_factory)
        self.supabase = get_supabase_client()
    
    def reconnect(self):
        """Refresh the Supabase client connection"""
        self.supabase = get_supabase_client()
    
    def get_session(self):
        """Get the current Supabase client"""
        return self.supabase
    
    # User Management
    def get_all_users(self):
        """Get all users from the profiles table"""
        try:
            response = self.supabase.table('profiles').select('*').execute()
            return response.data
        except Exception as e:
            st.error(f"Error getting users: {str(e)}")
            return []
    
    def get_user_by_id(self, user_id):
        """Get a user by ID"""
        try:
            response = self.supabase.table('profiles').select('*').eq('id', user_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            st.error(f"Error getting user: {str(e)}")
            return None
    
    def update_user_last_active(self, user_id):
        """Update user's last active timestamp"""
        try:
            self.supabase.table('profiles').update({
                'last_active': datetime.utcnow().isoformat()
            }).eq('id', user_id).execute()
            return True
        except Exception as e:
            st.error(f"Error updating user activity: {str(e)}")
            return False
    
    # Log Management
    def get_recent_logs(self, limit=10):
        """Get recent logs with author information"""
        try:
            response = self.supabase.table('logs').select(
                '*,author:profiles(*)'
            ).order('timestamp', desc=True).limit(limit).execute()
            
            return response.data
        except Exception as e:
            st.error(f"Error getting logs: {str(e)}")
            return []
    
    def create_log(self, log_data):
        """Create a new log entry"""
        try:
            # Ensure log_id is unique
            if 'log_id' not in log_data:
                log_data['log_id'] = str(uuid.uuid4())
            
            # Ensure timestamp is in ISO format
            if 'timestamp' not in log_data:
                log_data['timestamp'] = datetime.utcnow().isoformat()
            
            response = self.supabase.table('logs').insert(log_data).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            st.error(f"Error creating log: {str(e)}")
            return None
    
    def mark_log_as_read(self, log_id, user_id):
        """Mark a log as read by a user"""
        try:
            # Check if already read
            check = self.supabase.table('log_reads').select('*').eq('log_id', log_id).eq('user_id', user_id).execute()
            
            if check.data and len(check.data) > 0:
                return True  # Already marked as read
            
            # Mark as read
            response = self.supabase.table('log_reads').insert({
                'log_id': log_id,
                'user_id': user_id,
                'timestamp': datetime.utcnow().isoformat()
            }).execute()
            
            return True if response.data else False
        except Exception as e:
            st.error(f"Error marking log as read: {str(e)}")
            return False
    
    # Message Management
    def get_user_messages(self, user_id):
        """Get all messages where the user is either sender or recipient"""
        try:
            response = self.supabase.table('messages').select(
                '*,sender:profiles!sender_id(*),recipient:profiles!recipient_id(*)'
            ).or_(f'sender_id.eq.{user_id},recipient_id.eq.{user_id}').order('timestamp', desc=True).execute()
            
            return response.data
        except Exception as e:
            st.error(f"Error getting messages: {str(e)}")
            return []
    
    def create_message(self, message_data):
        """Create a new message"""
        try:
            # Ensure message_id is unique
            if 'message_id' not in message_data:
                message_data['message_id'] = str(uuid.uuid4())
            
            # Ensure timestamp is in ISO format
            if 'timestamp' not in message_data:
                message_data['timestamp'] = datetime.utcnow().isoformat()
            
            response = self.supabase.table('messages').insert(message_data).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            st.error(f"Error creating message: {str(e)}")
            return None
    
    def mark_message_as_read(self, message_id):
        """Mark a message as read"""
        try:
            response = self.supabase.table('messages').update({
                'is_read': True
            }).eq('message_id', message_id).execute()
            
            return True if response.data else False
        except Exception as e:
            st.error(f"Error marking message as read: {str(e)}")
            return False
    
    # Message Thread Management
    def get_user_threads(self, user_id):
        """Get all message threads for a user"""
        try:
            # Assuming a 'user_id' column or relationship in message_threads table
            response = self.supabase.table('message_threads').select('*').or_(f'user1_id.eq.{user_id},user2_id.eq.{user_id}').execute()
            return response.data
        except Exception as e:
            st.error(f"Error getting user threads: {str(e)}")
            return []

    # Room Management
    def get_all_rooms(self):
        """Get all rooms"""
        try:
            response = self.supabase.table('rooms').select('*').execute()
            return response.data
        except Exception as e:
            st.error(f"Error getting rooms: {str(e)}")
            return []
    
    def update_room_status(self, room_id, new_status):
        """Update a room's status"""
        try:
            response = self.supabase.table('rooms').update({
                'status': new_status
            }).eq('id', room_id).execute()
            
            return True if response.data else False
        except Exception as e:
            st.error(f"Error updating room status: {str(e)}")
            return False
    
    # Booking Management
    def check_in_booking(self, booking_id):
        """Update booking status to checked-in"""
        try:
            response = self.supabase.table('bookings').update({
                'booking_status': 'Checked-In'
            }).eq('booking_id', booking_id).execute()
            
            if response.data:
                # Also update the room status
                booking = response.data[0]
                if booking and 'room_id' in booking:
                    self.update_room_status(booking['room_id'], 'Occupied')
                return True
            return False
        except Exception as e:
            st.error(f"Error checking in booking: {str(e)}")
            return False
    
    def check_out_booking(self, booking_id):
        """Update booking status to checked-out"""
        try:
            response = self.supabase.table('bookings').update({
                'booking_status': 'Checked-Out'
            }).eq('booking_id', booking_id).execute()
            
            if response.data:
                # Also update the room status
                booking = response.data[0]
                if booking and 'room_id' in booking:
                    self.update_room_status(booking['room_id'], 'Dirty')
                return True
            return False
        except Exception as e:
            st.error(f"Error checking out booking: {str(e)}")
            return False
    
    # Data Retrieval for Analytics
    def get_occupancy_data(self, start_date, end_date):
        """Get occupancy data for a date range"""
        try:
            response = self.supabase.table('occupancy_data').select('*').gte('date', start_date).lte('date', end_date).execute()
            return response.data
        except Exception as e:
            st.error(f"Error getting occupancy data: {str(e)}")
            return []
    
    def get_revenue_data(self, start_date, end_date):
        """Get revenue data for a date range"""
        try:
            response = self.supabase.table('revenue_data').select('*').gte('date', start_date).lte('date', end_date).execute()
            return response.data
        except Exception as e:
            st.error(f"Error getting revenue data: {str(e)}")
            return []
    
    def get_bookings(self, start_date=None, end_date=None):
        """Get bookings, optionally filtered by date range"""
        try:
            query = self.supabase.table('bookings').select('*,guest:profiles(*),room:rooms(*)')
            
            if start_date and end_date:
                query = query.or_(
                    f'check_in_date.gte.{start_date}.and.check_in_date.lte.{end_date},'
                    f'check_out_date.gte.{start_date}.and.check_out_date.lte.{end_date},'
                    f'check_in_date.lte.{start_date}.and.check_out_date.gte.{end_date}'
                )
            
            response = query.execute()
            return response.data
        except Exception as e:
            st.error(f"Error getting bookings: {str(e)}")
            return []

def get_db_manager():
    return db_manager

db_manager = DatabaseManager()
