import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

from data_handler import hotel_data
from utils import format_currency, format_percentage, create_download_button

def show_reports(start_date, end_date):
    """Display reports and data export functionality"""
    st.header("Hotel Reports")
    st.subheader(f"Period: {start_date.strftime('%b %d, %Y')} to {end_date.strftime('%b %d, %Y')}")
    
    # Load data
    hotel_data.load_data(start_date, end_date)

    if hotel_data is None:
        st.warning("No data available.")
        return
    
    # Sidebar for report type selection
    report_type = st.selectbox(
        "Select Report Type",
        [
            "Daily Occupancy Report",
            "Revenue Summary Report",
            "Booking Source Analysis",
            "Guest Statistics Report",
            "Custom Report Builder"
        ]
    )
    
    # Display selected report
    if report_type == "Daily Occupancy Report":
        show_occupancy_report(start_date, end_date)
    elif report_type == "Revenue Summary Report":
        show_revenue_report(start_date, end_date)
    elif report_type == "Booking Source Analysis":
        show_booking_source_report(start_date, end_date)
    elif report_type == "Guest Statistics Report":
        show_guest_statistics_report(start_date, end_date)
    elif report_type == "Custom Report Builder":
        show_custom_report_builder(start_date, end_date)


def show_occupancy_report(start_date, end_date):
    """Display daily occupancy report"""
    st.subheader("Daily Occupancy Report")
    
    # Get occupancy data
    occupancy_data = hotel_data.get_occupancy_data(start_date, end_date)
    
    if occupancy_data is None:
        st.warning("No occupancy data available for the selected period.")
        return
    
    # Display summary statistics
    if 'occupancy_rate' in occupancy_data.columns:
        avg_occupancy = occupancy_data['occupancy_rate'].mean()
        min_occupancy = occupancy_data['occupancy_rate'].min()
        max_occupancy = occupancy_data['occupancy_rate'].max()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                label="Average Occupancy",
                value=f"{avg_occupancy:.1f}%"
            )
        
        with col2:
            st.metric(
                label="Minimum Occupancy",
                value=f"{min_occupancy:.1f}%"
            )
        
        with col3:
            st.metric(
                label="Maximum Occupancy",
                value=f"{max_occupancy:.1f}%"
            )
    
    # Occupancy trend chart
    st.subheader("Occupancy Trend")
    
    if not occupancy_data.empty and 'date' in occupancy_data.columns and 'occupancy_rate' in occupancy_data.columns:
        fig = px.line(
            occupancy_data,
            x="date",
            y="occupancy_rate",
            title="Daily Occupancy Rate",
            labels={"occupancy_rate": "Occupancy Rate (%)", "date": "Date"}
        )
        
        # Add a reference line at 80% (common hotel target)
        fig.add_hline(
            y=80, 
            line_dash="dash", 
            line_color="green",
            annotation_text="Target (80%)"
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Insufficient data for trend visualization.")
    
    # Data table with daily occupancy
    st.subheader("Daily Occupancy Data")
    
    if not occupancy_data.empty:
        # Display the data table
        st.dataframe(occupancy_data, hide_index=True)
        
        # Add download button
        create_download_button(occupancy_data, "occupancy_report.csv", "Download Occupancy Report")
    else:
        st.info("No occupancy data available.")


def show_revenue_report(start_date, end_date):
    """Display revenue summary report"""
    st.subheader("Revenue Summary Report")
    
    # Get revenue data
    revenue_data = hotel_data.get_revenue_data(start_date, end_date)
    
    if revenue_data.empty:
        st.warning("No revenue data available for the selected period.")
        return
    
    # Calculate summary metrics
    total_revenue = 0
    room_revenue = 0
    fb_revenue = 0
    other_revenue = 0
    
    if 'total_revenue' in revenue_data.columns:
        total_revenue = revenue_data['total_revenue'].sum()
    if 'room_revenue' in revenue_data.columns:
        room_revenue = revenue_data['room_revenue'].sum()
    if 'f&b_revenue' in revenue_data.columns:
        fb_revenue = revenue_data['f&b_revenue'].sum()
    if 'other_revenue' in revenue_data.columns:
        other_revenue = revenue_data['other_revenue'].sum()
    
    # Display summary metrics
    st.subheader("Revenue Summary")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric(
            label="Total Revenue",
            value=format_currency(total_revenue)
        )
        
        st.metric(
            label="Room Revenue",
            value=format_currency(room_revenue),
            delta=f"{(room_revenue/total_revenue*100):.1f}% of total" if total_revenue > 0 else None
        )
    
    with col2:
        st.metric(
            label="F&B Revenue",
            value=format_currency(fb_revenue),
            delta=f"{(fb_revenue/total_revenue*100):.1f}% of total" if total_revenue > 0 else None
        )
        
        st.metric(
            label="Other Revenue",
            value=format_currency(other_revenue),
            delta=f"{(other_revenue/total_revenue*100):.1f}% of total" if total_revenue > 0 else None
        )
    
    # Revenue breakdown pie chart
    if total_revenue > 0:
        # Create pie chart data
        revenue_sources = pd.DataFrame({
            'Source': ['Room Revenue', 'F&B Revenue', 'Other Revenue'],
            'Amount': [room_revenue, fb_revenue, other_revenue]
        })
        
        fig = px.pie(
            revenue_sources, 
            values='Amount', 
            names='Source',
            title="Revenue Distribution",
            color='Source',
            color_discrete_map={
                'Room Revenue': '#1E88E5',  # Blue
                'F&B Revenue': '#4CAF50',   # Green
                'Other Revenue': '#FFC107'  # Yellow
            }
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Daily revenue trend
    if not revenue_data.empty and 'date' in revenue_data.columns and 'total_revenue' in revenue_data.columns:
        fig = px.line(
            revenue_data,
            x="date",
            y="total_revenue",
            title="Daily Total Revenue",
            labels={"total_revenue": "Revenue ($)", "date": "Date"}
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Revenue data table
    st.subheader("Daily Revenue Data")
    
    if not revenue_data.empty:
        # Display the data table
        st.dataframe(revenue_data, hide_index=True)
        
        # Add download button
        create_download_button(revenue_data, "revenue_report.csv", "Download Revenue Report")
    else:
        st.info("No revenue data available.")


def show_booking_source_report(start_date, end_date):
    """Display booking source analysis report"""
    st.subheader("Booking Source Analysis")
    
    # Get booking data
    booking_data = hotel_data.get_booking_data(start_date, end_date)
    
    if booking_data.empty:
        st.warning("No booking data available for the selected period.")
        return
    
    st.info("Booking source analysis requires booking source data that is not currently available.")
    
    # Display empty state for this report
    st.subheader("Sample Report Structure")
    
    st.markdown("""
    This report would typically include:
    
    1. Distribution of bookings by source (OTAs, direct, corporate, travel agents)
    2. Revenue contribution by booking source
    3. Average daily rate (ADR) by booking source
    4. Conversion rates and trends
    5. Commission costs by source
    """)
    
    # Placeholder for booking source data
    st.subheader("Booking Data")
    
    if not booking_data.empty:
        # Display the data table
        st.dataframe(booking_data, hide_index=True)
        
        # Add download button
        create_download_button(booking_data, "booking_report.csv", "Download Booking Data")
    else:
        st.info("No booking data available.")


def show_guest_statistics_report(start_date, end_date):
    """Display guest statistics report"""
    st.subheader("Guest Statistics Report")
    
    # Get guest and booking data
    guest_data = hotel_data.get_guest_data()
    booking_data = hotel_data.get_booking_data(start_date, end_date)
    
    if guest_data.empty or booking_data.empty:
        st.warning("No guest or booking data available for the selected period.")
        return
    
    st.info("Guest statistics analysis requires additional guest data that is not currently available.")
    
    # Display empty state for this report
    st.subheader("Sample Report Structure")
    
    st.markdown("""
    This report would typically include:
    
    1. Guest demographics (age, region, purpose of visit)
    2. New vs returning guest comparison
    3. Average length of stay by guest type
    4. Loyalty program metrics
    5. Guest satisfaction scores
    6. Guest retention rates
    """)
    
    # Placeholder for guest data
    st.subheader("Guest Data Sample")
    
    if not guest_data.empty:
        # Display the data table
        st.dataframe(guest_data, hide_index=True)
        
        # Add download button
        create_download_button(guest_data, "guest_report.csv", "Download Guest Data")
    else:
        st.info("No guest data available.")


def show_custom_report_builder(start_date, end_date):
    """Display custom report builder functionality"""
    st.subheader("Custom Report Builder")
    
    # Load all available data
    hotel_data.load_data(start_date, end_date)
    
    occupancy_data = hotel_data.get_occupancy_data(start_date, end_date)
    revenue_data = hotel_data.get_revenue_data(start_date, end_date)
    booking_data = hotel_data.get_booking_data(start_date, end_date)
    room_data = hotel_data.get_room_status_data()
    
    # Available data sources for report
    st.write("Select data sources to include in your custom report:")
    
    include_occupancy = st.checkbox("Occupancy Data", value=True)
    include_revenue = st.checkbox("Revenue Data", value=True)
    include_bookings = st.checkbox("Booking Data", value=False)
    include_rooms = st.checkbox("Room Data", value=False)
    
    # Chart selection
    st.write("Select charts to include:")
    
    include_occupancy_chart = st.checkbox("Occupancy Trend Chart", value=include_occupancy)
    include_revenue_chart = st.checkbox("Revenue Trend Chart", value=include_revenue)
    include_revenue_pie = st.checkbox("Revenue Distribution Pie Chart", value=include_revenue)
    
    # Generate report button
    if st.button("Generate Custom Report"):
        st.subheader("Custom Report")
        st.write(f"Report Period: {start_date.strftime('%b %d, %Y')} to {end_date.strftime('%b %d, %Y')}")
        
        # Include selected charts
        if include_occupancy_chart and not occupancy_data.empty and 'date' in occupancy_data.columns and 'occupancy_rate' in occupancy_data.columns:
            fig = px.line(
                occupancy_data,
                x="date",
                y="occupancy_rate",
                title="Occupancy Trend",
                labels={"occupancy_rate": "Occupancy Rate (%)", "date": "Date"}
            )
            st.plotly_chart(fig, use_container_width=True)
        
        if include_revenue_chart and not revenue_data.empty and 'date' in revenue_data.columns and 'total_revenue' in revenue_data.columns:
            fig = px.line(
                revenue_data,
                x="date",
                y="total_revenue",
                title="Revenue Trend",
                labels={"total_revenue": "Revenue ($)", "date": "Date"}
            )
            st.plotly_chart(fig, use_container_width=True)
        
        if include_revenue_pie and not revenue_data.empty:
            # Only include if we have the breakdowns
            if all(col in revenue_data.columns for col in ['room_revenue', 'f&b_revenue', 'other_revenue']):
                # Calculate totals
                room_revenue = revenue_data['room_revenue'].sum()
                fb_revenue = revenue_data['f&b_revenue'].sum()
                other_revenue = revenue_data['other_revenue'].sum()
                
                # Create pie chart data
                revenue_sources = pd.DataFrame({
                    'Source': ['Room Revenue', 'F&B Revenue', 'Other Revenue'],
                    'Amount': [room_revenue, fb_revenue, other_revenue]
                })
                
                if revenue_sources['Amount'].sum() > 0:
                    fig = px.pie(
                        revenue_sources, 
                        values='Amount', 
                        names='Source',
                        title="Revenue Distribution",
                        color='Source',
                        color_discrete_map={
                            'Room Revenue': '#1E88E5',  # Blue
                            'F&B Revenue': '#4CAF50',   # Green
                            'Other Revenue': '#FFC107'  # Yellow
                        }
                    )
                    st.plotly_chart(fig, use_container_width=True)
        
        # Include selected data tables
        if include_occupancy and not occupancy_data.empty:
            st.subheader("Occupancy Data")
            st.dataframe(occupancy_data, hide_index=True)
        
        if include_revenue and not revenue_data.empty:
            st.subheader("Revenue Data")
            st.dataframe(revenue_data, hide_index=True)
        
        if include_bookings and not booking_data.empty:
            st.subheader("Booking Data")
            st.dataframe(booking_data, hide_index=True)
        
        if include_rooms and not room_data.empty:
            st.subheader("Room Data")
            st.dataframe(room_data, hide_index=True)
        
        # Create combined dataset for export
        export_datasets = []
        export_names = []
        
        if include_occupancy and not occupancy_data.empty:
            export_datasets.append(occupancy_data)
            export_names.append("occupancy")
        
        if include_revenue and not revenue_data.empty:
            export_datasets.append(revenue_data)
            export_names.append("revenue")
        
        if include_bookings and not booking_data.empty:
            export_datasets.append(booking_data)
            export_names.append("bookings")
        
        if include_rooms and not room_data.empty:
            export_datasets.append(room_data)
            export_names.append("rooms")
        
        if export_datasets:
            export_name = "_".join(export_names)
            create_download_button(
                pd.concat(export_datasets, axis=1) if len(export_datasets) > 1 else export_datasets[0],
                f"custom_report_{export_name}.csv",
                "Download Complete Report Data"
            )
        
        st.success("Custom report generated successfully!")
