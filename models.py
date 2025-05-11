import pandas as pd
from datetime import datetime, timedelta
import json
import os
import uuid
import streamlit as st
from database import db_manager

class UserProfile:
    """User profile model"""
    
    def __init__(self, user_id, name, role, email=None, phone=None, bio=None, avatar=None, last_active=None):
        self.user_id = user_id
        self.name = name
        self.role = role
        self.email = email
        self.phone = phone
        self.bio = bio or ""
        self.avatar = avatar or f"https://ui-avatars.com/api/?name={name.replace(' ', '+')}&background=random"
        self.last_active = last_active or datetime.now()
    
    def to_dict(self):
        """Convert user profile to dictionary"""
        return {
            "user_id": self.user_id,
            "name": self.name,
            "role": self.role,
            "email": self.email,
            "phone": self.phone,
            "bio": self.bio,
            "avatar": self.avatar,
            "last_active": self.last_active.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create user profile from dictionary"""
        user = cls(
            user_id=data["user_id"],
            name=data["name"],
            role=data["role"],
            email=data.get("email"),
            phone=data.get("phone"),
            bio=data.get("bio", ""),
            avatar=data.get("avatar")
        )
        
        # Convert ISO string to datetime
        if "last_active" in data:
            try:
                user.last_active = datetime.fromisoformat(data["last_active"])
            except (ValueError, TypeError):
                user.last_active = datetime.now()
        
        return user
    
    @classmethod
    def from_db(cls, db_user):
        """Create user profile from database model"""
        if not db_user:
            return None
        
        return cls(
            user_id=db_user.user_id,
            name=db_user.name,
            role=db_user.role,
            email=db_user.email,
            phone=db_user.phone,
            bio=db_user.bio,
            avatar=db_user.avatar,
            last_active=db_user.last_active
        )


class LogEntry:
    """Log entry model for shift logs, notes, etc."""
    
    def __init__(self, log_id, title, message, author_id, author_name, author_role, timestamp=None, read_by=None):
        self.log_id = log_id
        self.title = title
        self.message = message
        self.author_id = author_id
        self.author_name = author_name
        self.author_role = author_role
        self.timestamp = timestamp or datetime.now()
        self.read_by = read_by or []
    
    def to_dict(self):
        """Convert log entry to dictionary"""
        return {
            "log_id": self.log_id,
            "title": self.title,
            "message": self.message,
            "author_id": self.author_id,
            "author_name": self.author_name,
            "author_role": self.author_role,
            "timestamp": self.timestamp.isoformat(),
            "read_by": self.read_by
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create log entry from dictionary"""
        log = cls(
            log_id=data["log_id"],
            title=data["title"],
            message=data["message"],
            author_id=data["author_id"],
            author_name=data["author_name"],
            author_role=data["author_role"],
            read_by=data.get("read_by", [])
        )
        
        # Convert ISO string to datetime
        if "timestamp" in data:
            try:
                log.timestamp = datetime.fromisoformat(data["timestamp"])
            except (ValueError, TypeError):
                log.timestamp = datetime.now()
        
        return log
    
    @classmethod
    def from_db(cls, db_log, read_by=None):
        """Create log entry from database model"""
        if not db_log:
            return None
        
        # Get author info
        author_name = db_log.author.name if db_log.author else "Unknown"
        author_role = db_log.author.role if db_log.author else "Unknown"
        
        return cls(
            log_id=db_log.log_id,
            title=db_log.title,
            message=db_log.message,
            author_id=db_log.author.user_id if db_log.author else "unknown",
            author_name=author_name,
            author_role=author_role,
            timestamp=db_log.timestamp,
            read_by=read_by or []
        )


class Message:
    """Direct message model"""
    
    def __init__(self, message_id, sender_id, recipient_id, content, timestamp=None, is_read=False):
        self.message_id = message_id
        self.sender_id = sender_id
        self.recipient_id = recipient_id
        self.content = content
        self.timestamp = timestamp or datetime.now()
        self.is_read = is_read
    
    def to_dict(self):
        """Convert message to dictionary"""
        return {
            "message_id": self.message_id,
            "sender_id": self.sender_id,
            "recipient_id": self.recipient_id,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "is_read": self.is_read
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create message from dictionary"""
        message = cls(
            message_id=data["message_id"],
            sender_id=data["sender_id"],
            recipient_id=data["recipient_id"],
            content=data["content"],
            is_read=data.get("is_read", False)
        )
        
        # Convert ISO string to datetime
        if "timestamp" in data:
            try:
                message.timestamp = datetime.fromisoformat(data["timestamp"])
            except (ValueError, TypeError):
                message.timestamp = datetime.now()
        
        return message
    
    @classmethod
    def from_db(cls, db_message):
        """Create message from database model"""
        if not db_message:
            return None
        
        return cls(
            message_id=db_message.message_id,
            sender_id=db_message.sender.user_id if db_message.sender else "unknown",
            recipient_id=db_message.recipient.user_id if db_message.recipient else "unknown",
            content=db_message.content,
            timestamp=db_message.timestamp,
            is_read=db_message.is_read
        )


class DataManager:
    """Manager for handling user profiles, logs, and messages"""
    
    def __init__(self):
        """Initialize using database manager"""
        # The database manager is initialized in database.py
        pass
    
    def get_user(self, user_id):
        """Get user by ID"""
        db_user = db_manager.get_user_by_id(user_id)
        return UserProfile.from_db(db_user)
    
    def update_user(self, user):
        """Update user profile"""
        # Update the user in the database
        updated_user = db_manager.update_user(
            user.user_id,
            name=user.name,
            role=user.role,
            email=user.email,
            phone=user.phone,
            bio=user.bio,
            avatar=user.avatar,
            last_active=user.last_active
        )
        
        return updated_user is not None
    
    def add_user(self, user):
        """Add new user"""
        # Not implemented - users are created in the database
        pass
    
    def get_users_by_role(self, role=None):
        """Get users filtered by role"""
        if role:
            db_users = db_manager.get_users_by_role(role)
        else:
            db_users = db_manager.get_all_users()
        
        return [UserProfile.from_db(user) for user in db_users]
    
    @property
    def users(self):
        """Get all users"""
        db_users = db_manager.get_all_users()
        return [UserProfile.from_db(user) for user in db_users]
    
    def get_recent_logs(self, limit=10):
        """Get recent logs"""
        db_logs = db_manager.get_recent_logs(limit)
        
        logs = []
        for db_log in db_logs:
            # Get users who have read this log
            read_by = []
            for log_read in db_log.read_by:
                if log_read.user_id:
                    # Import User model directly
                    from database import User
                    user = db_manager.db.query(User).get(log_read.user_id)
                    if user:
                        read_by.append(user.user_id)
            
            log = LogEntry.from_db(db_log, read_by)
            logs.append(log)
        
        return logs
    
    def add_log(self, log):
        """Add new log entry"""
        # Convert author_id from user_id to database ID
        db_user = db_manager.get_user_by_id(log.author_id)
        
        # Create log in database
        db_manager.create_log({
            "log_id": log.log_id,
            "title": log.title,
            "message": log.message,
            "author_id": db_user.id if db_user else None,
            "timestamp": log.timestamp
        })
    
    def mark_log_as_read(self, log_id, user_id):
        """Mark log as read by user"""
        return db_manager.mark_log_as_read(log_id, user_id)
    
    def get_messages(self, user_id):
        """Get messages for a user"""
        db_user = db_manager.get_user_by_id(user_id)
        if not db_user:
            return []
        
        db_messages = db_manager.get_user_messages(user_id)
        return [Message.from_db(msg) for msg in db_messages]
    
    def send_message(self, sender_id, recipient_id, content):
        """Send a new message"""
        # Get database user IDs
        db_sender = db_manager.get_user_by_id(sender_id)
        db_recipient = db_manager.get_user_by_id(recipient_id)
        
        if not db_sender or not db_recipient:
            return None
        
        # Create message in database
        message_data = {
            "message_id": f"msg_{uuid.uuid4().hex[:8]}",
            "sender_id": db_sender.id,
            "recipient_id": db_recipient.id,
            "content": content,
            "is_read": False
        }
        
        db_message = db_manager.create_message(message_data)
        
        # Return message object
        return Message.from_db(db_message)
    
    def mark_message_as_read(self, message_id):
        """Mark message as read"""
        return db_manager.mark_message_as_read(message_id)
    
    @property
    def logs(self):
        """Get all logs (used for compatibility)"""
        db_logs = db_manager.get_recent_logs(100)  # Get a large number
        
        logs = []
        for db_log in db_logs:
            # Get users who have read this log
            read_by = []
            for log_read in db_log.read_by:
                if log_read.user_id:
                    # Import User model directly
                    from database import User
                    user = db_manager.db.query(User).get(log_read.user_id)
                    if user:
                        read_by.append(user.user_id)
            
            log = LogEntry.from_db(db_log, read_by)
            logs.append(log)
        
        return logs
    
    @property
    def messages(self):
        """Get all messages (used for compatibility)"""
        # This is inefficient but used for backward compatibility
        all_messages = []
        for user in self.users:
            all_messages.extend(self.get_messages(user.user_id))
        return all_messages

# Create a singleton instance
data_manager = DataManager()