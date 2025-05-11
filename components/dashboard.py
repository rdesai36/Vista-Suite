import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

from data_handler import hotel_data
from utils import format_currency, format_percentage, display_metric_card

def show_dashboard(start_date, end_date):
    """Main dashboard page showing overview of key metrics"""
    st.header("Hotel Performance Dashboard")
    st.subheader(f"Overview: {start_date.strftime('%b %d, %Y')} to {end_date.strftime('%b %d, %Y')}")
    
    # Load data for the selected date range
    data_loaded = hotel_data.load_data(start_date, end_date)
    
    if not data_loaded:
        st.error("Failed to load hotel data. Please check your data source connection.")
        return
    
    # Get KPI summary for selected period
    kpi_data = hotel_data.get_kpi_summary(start_date, end_date)
    
    # Get the same data for previous period (for comparison)
    period_length = (end_date - start_date).days
    prev_end_date = start_date - timedelta(days=1)
    prev_start_date = prev_end_date - timedelta(days=period_length)
    prev_kpi_data = hotel_data.get_kpi_summary(prev_start_date, prev_end_date)
    
    # Display KPI metrics in cards (4 columns)
    st.subheader("Key Performance Indicators")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if kpi_data["occupancy_rate"] is not None:
            st.metric(
                label="Occupancy Rate",
                value=format_percentage(kpi_data["occupancy_rate"]),
                delta=f"{kpi_data['occupancy_rate'] - prev_kpi_data['occupancy_rate']:.1f}%" 
                    if prev_kpi_data["occupancy_rate"] is not None else None
            )
        else:
            st.metric(label="Occupancy Rate", value="No data")

    with col2:
        if kpi_data["adr"] is not None:
            st.metric(
                label="ADR (Average Daily Rate)",
                value=format_currency(kpi_data["adr"]),
                delta=f"{kpi_data['adr'] - prev_kpi_data['adr']:.2f}" 
                    if prev_kpi_data["adr"] is not None else None
            )
        else:
            st.metric(label="ADR (Average Daily Rate)", value="No data")

    with col3:
        if kpi_data["revpar"] is not None:
            st.metric(
                label="RevPAR",
                value=format_currency(kpi_data["revpar"]),
                delta=f"{kpi_data['revpar'] - prev_kpi_data['revpar']:.2f}" 
                    if prev_kpi_data["revpar"] is not None else None
            )
        else:
            st.metric(label="RevPAR", value="No data")

    with col4:
        if kpi_data["total_revenue"] is not None:
            st.metric(
                label="Total Revenue",
                value=format_currency(kpi_data["total_revenue"]),
                delta=f"{kpi_data['total_revenue'] - prev_kpi_data['total_revenue']:.2f}" 
                    if prev_kpi_data["total_revenue"] is not None else None
            )
        else:
            st.metric(label="Total Revenue", value="No data")
    
    # Second row of metrics
    col1, col2 = st.columns(2)
    
    with col1:
        if kpi_data["bookings"] is not None:
            st.metric(
                label="Total Bookings",
                value=kpi_data["bookings"],
                delta=kpi_data["bookings"] - prev_kpi_data["bookings"] 
                    if prev_kpi_data["bookings"] is not None else None
            )
        else:
            st.metric(label="Total Bookings", value="No data")

    with col2:
        if kpi_data["avg_length_of_stay"] is not None:
            st.metric(
                label="Avg. Length of Stay (Days)",
                value=f"{kpi_data['avg_length_of_stay']:.1f}",
                delta=f"{kpi_data['avg_length_of_stay'] - prev_kpi_data['avg_length_of_stay']:.1f}" 
                    if prev_kpi_data["avg_length_of_stay"] is not None else None
            )
        else:
            st.metric(label="Avg. Length of Stay (Days)", value="No data")
    
    # Charts section
    st.subheader("Performance Trends")
    
    # Get data for charts
    occupancy_data = hotel_data.get_occupancy_data(start_date, end_date)
    revenue_data = hotel_data.get_revenue_data(start_date, end_date)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Occupancy Rate Trend")
        if not occupancy_data.empty:
            fig = px.line(
                occupancy_data,
                x="date",
                y="occupancy_rate",
                title="Daily Occupancy Rate (%)",
                labels={"occupancy_rate": "Occupancy Rate (%)", "date": "Date"}
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No occupancy data available for the selected date range.")
    
    with col2:
        st.subheader("Revenue Breakdown")
        if not revenue_data.empty:
            # Create revenue breakdown chart
            fig = px.bar(
                revenue_data, 
                x="date", 
                y=["room_revenue", "f&b_revenue", "other_revenue"],
                title="Daily Revenue Breakdown",
                labels={
                    "value": "Revenue ($)", 
                    "date": "Date", 
                    "variable": "Revenue Type"
                }
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No revenue data available for the selected date range.")
    
    # Front office quick overview - today's check-ins and check-outs
    st.subheader("Today's Front Office Activity")
    
    checkins, checkouts = hotel_data.get_checkin_checkout_today()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader(f"Check-ins Today: {len(checkins)}")
        if not checkins.empty:
            st.dataframe(checkins, hide_index=True)
        else:
            st.info("No check-ins scheduled for today.")
    
    with col2:
        st.subheader(f"Check-outs Today: {len(checkouts)}")
        if not checkouts.empty:
            st.dataframe(checkouts, hide_index=True)
        else:
            st.info("No check-outs scheduled for today.")
    
    # Room status summary
    st.subheader("Room Status Summary")
    
    room_data = hotel_data.get_room_status_data()
    
    if not room_data.empty:
        # Count rooms by status
        room_status_counts = room_data['status'].value_counts().reset_index()
        room_status_counts.columns = ['Status', 'Count']
        
        # Create room status pie chart
        fig = px.pie(
            room_status_counts, 
            values='Count', 
            names='Status',
            title="Room Status Distribution",
            color='Status',
            color_discrete_map={
                'Occupied': '#1E88E5',  # Blue
                'Vacant': '#4CAF50',    # Green
                'Maintenance': '#FFC107', # Yellow
                'Out of Order': '#F44336', # Red
                'Dirty': '#9E9E9E'      # Grey
            }
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No room status data available.")
