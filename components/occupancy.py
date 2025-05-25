import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

from data_handler import hotel_data
from utils import format_percentage, create_download_button

def show_occupancy(start_date, end_date):
    """Display occupancy analysis page"""
    st.header("Occupancy Analysis")
    st.subheader(f"Period: {start_date.strftime('%b %d, %Y')} to {end_date.strftime('%b %d, %Y')}")
    
    # Load data
    occupancy_data = pd.DataFrame(hotel_data.get_occupancy_data(start_date, end_date))

    # Standardized empty state handling
    if occupancy_data is None or (hasattr(occupancy_data, 'empty') and occupancy_data.empty):
        st.warning("No occupancy data available for the selected period.")
        st.info("Once your property is connected to HotelKey, occupancy metrics and trends will appear here.")
        return

    # Calculate overall average occupancy for the period
    avg_occupancy = occupancy_data['occupancy_rate'].mean() if 'occupancy_rate' in occupancy_data.columns else 0
    
    # Display KPI metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if 'occupancy_rate' in occupancy_data.columns:
            max_occupancy = occupancy_data['occupancy_rate'].max()
            st.metric(
                label="Average Occupancy Rate",
                value=f"{avg_occupancy:.1f}%"
            )
        else:
            st.metric(label="Average Occupancy Rate", value="No data")
    
    with col2:
        if 'occupancy_rate' in occupancy_data.columns:
            max_occupancy = occupancy_data['occupancy_rate'].max()
            st.metric(
                label="Peak Occupancy Rate",
                value=f"{max_occupancy:.1f}%"
            )
        else:
            st.metric(label="Peak Occupancy Rate", value="No data")
    
    with col3:
        if 'occupancy_rate' in occupancy_data.columns and 'rooms_occupied' in occupancy_data.columns and 'total_rooms' in occupancy_data.columns:
            avg_vacant_rooms = (occupancy_data['total_rooms'] - occupancy_data['rooms_occupied']).mean()
            st.metric(
                label="Avg. Vacant Rooms",
                value=f"{avg_vacant_rooms:.1f}"
            )
        else:
            st.metric(label="Avg. Vacant Rooms", value="No data")
    
    # Visualization options
    st.subheader("Occupancy Visualization")
    
    viz_type = st.radio(
        "Select Visualization",
        ["Occupancy Trend", "Day of Week Analysis", "Room Type Breakdown"],
        horizontal=True
    )
    
    if viz_type == "Occupancy Trend":
        if 'date' in occupancy_data.columns and 'occupancy_rate' in occupancy_data.columns:
            # Create time series chart
            fig = px.line(
                occupancy_data,
                x="date",
                y="occupancy_rate",
                title="Daily Occupancy Rate",
                labels={"occupancy_rate": "Occupancy Rate (%)", "date": "Date"}
            )
            
            # Add a target line at 80% (common hotel target)
            fig.add_hline(
                y=80, 
                line_dash="dash", 
                line_color="green",
                annotation_text="Target (80%)"
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Insufficient data for trend visualization.")
    
    elif viz_type == "Day of Week Analysis":
        if 'date' in occupancy_data.columns and 'occupancy_rate' in occupancy_data.columns:
            # Extract day of week and calculate averages
            try:
                occupancy_data['day_of_week'] = pd.to_datetime(occupancy_data['date']).dt.day_name()
                day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                
                day_avg = occupancy_data.groupby('day_of_week')['occupancy_rate'].mean().reindex(day_order).reset_index()
                
                # Create bar chart
                fig = px.bar(
                    day_avg,
                    x="day_of_week",
                    y="occupancy_rate",
                    title="Average Occupancy by Day of Week",
                    labels={"occupancy_rate": "Avg. Occupancy Rate (%)", "day_of_week": "Day of Week"}
                )
                
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.error(f"Error processing day of week data: {str(e)}")
        else:
            st.info("Insufficient data for day of week analysis.")
    
    elif viz_type == "Room Type Breakdown":
        st.info("Room type breakdown analysis requires additional data that is not available in the current dataset.")
    
    # Detailed data table with filters
    st.subheader("Detailed Occupancy Data")
    
    # Filter controls
    col1, col2 = st.columns(2)
    with col1:
        if 'occupancy_rate' in occupancy_data.columns:
            min_rate = float(occupancy_data['occupancy_rate'].min())
            max_rate = float(occupancy_data['occupancy_rate'].max())
            filter_rate = st.slider(
                "Occupancy Rate Range (%)",
                min_value=min_rate,
                max_value=max_rate,
                value=(min_rate, max_rate)
            )
        else:
            filter_rate = (0, 100)
            st.info("No occupancy rate data available for filtering.")
    
    # Apply filters
    filtered_data = occupancy_data
    if 'occupancy_rate' in occupancy_data.columns:
        filtered_data = filtered_data[(filtered_data['occupancy_rate'] >= filter_rate[0]) & 
                                     (filtered_data['occupancy_rate'] <= filter_rate[1])]
    
    # Display filtered data
    if not filtered_data.empty:
        st.dataframe(filtered_data, hide_index=True)
        
        # Download option
        create_download_button(filtered_data, "occupancy_data.csv", "Download Occupancy Data")
    else:
        st.info("No data matches the selected filters.")
    
    # Display insights and recommendations
    st.subheader("Insights")
    
    insights_container = st.container()
    
    with insights_container:
        st.write("Based on the occupancy data, here are some insights:")
        
        if 'occupancy_rate' in occupancy_data.columns:
            # Generate insights based on actual data
            if avg_occupancy < 60:
                st.write("- The average occupancy rate is below industry benchmarks (typically 60-70%).")
                st.write("- Consider implementing promotional offers to increase bookings during this period.")
            elif avg_occupancy > 80:
                st.write("- The property is performing well with high occupancy rates.")
                st.write("- Consider reviewing pricing strategy to maximize revenue during high-demand periods.")
            
            # Calculate occupancy variance
            occupancy_variance = occupancy_data['occupancy_rate'].std() if len(occupancy_data) > 1 else 0
            if occupancy_variance > 15:
                st.write("- There's significant variance in occupancy rates, indicating potential for better demand management.")
                st.write("- Focus on strategies to fill rooms during lower occupancy days.")
        else:
            st.write("- No occupancy data is available to generate insights.")
