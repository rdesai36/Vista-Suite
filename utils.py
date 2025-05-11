import pandas as pd
import numpy as np
import streamlit as st
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go

def format_currency(value):
    """Format a value as currency"""
    return f"${value:,.2f}"

def format_percentage(value):
    """Format a value as percentage"""
    return f"{value:.1f}%"

def calculate_percentage_change(current, previous):
    """Calculate percentage change between two values"""
    if previous == 0:
        return 0
    return ((current - previous) / previous) * 100

def get_change_color(change):
    """Return color based on change value (positive/negative)"""
    if change > 0:
        return "green"
    elif change < 0:
        return "red"
    return "gray"

def display_metric_card(title, value, previous_value=None, format_func=None, prefix="", suffix=""):
    """Display a metric card with title, value, and change indicator"""
    if format_func:
        formatted_value = format_func(value)
    else:
        formatted_value = f"{prefix}{value}{suffix}"
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.metric(
            label=title,
            value=formatted_value,
            delta=calculate_percentage_change(value, previous_value) if previous_value is not None else None
        )

def create_date_ranges():
    """Create common date range options"""
    today = datetime.now().date()
    date_ranges = {
        "Last 7 Days": (today - timedelta(days=7), today),
        "Last 30 Days": (today - timedelta(days=30), today),
        "This Month": (today.replace(day=1), today),
        "Last Month": ((today.replace(day=1) - timedelta(days=1)).replace(day=1), 
                       today.replace(day=1) - timedelta(days=1)),
        "Year to Date": (today.replace(month=1, day=1), today)
    }
    return date_ranges

def export_dataframe(df, filename="report.csv"):
    """Convert dataframe to CSV for download"""
    csv = df.to_csv(index=False)
    return csv

def create_download_button(df, filename="report.csv", button_text="Download Report"):
    """Create a download button for exporting data"""
    csv = export_dataframe(df, filename)
    st.download_button(
        label=button_text,
        data=csv,
        file_name=filename,
        mime="text/csv"
    )
