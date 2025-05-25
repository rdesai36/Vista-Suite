import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

from data_handler import hotel_data
from utils import format_currency, create_download_button

def show_revenue(start_date, end_date):
    """Display revenue analysis page"""
    st.header("Revenue Analysis")
    st.subheader(f"Period: {start_date.strftime('%b %d, %Y')} to {end_date.strftime('%b %d, %Y')}")
    
    # Load data
    revenue_data = pd.DataFrame(hotel_data.get_revenue_data(start_date, end_date))

    # Standardized empty state handling
    if revenue_data is None or (hasattr(revenue_data, 'empty') and revenue_data.empty):
        st.warning("No revenue data available for the selected period.")
        st.info("Once your property is connected to HotelKey, revenue metrics and trends will appear here.")
        return
    
    # Calculate key revenue metrics (if data is available)
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
    
    # Display KPI metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="Total Revenue",
            value=format_currency(total_revenue)
        )
    
    with col2:
        if total_revenue > 0:
            st.metric(
                label="Room Revenue",
                value=format_currency(room_revenue),
                delta=f"{(room_revenue/total_revenue*100):.1f}% of total" if total_revenue > 0 else None
            )
        else:
            st.metric(label="Room Revenue", value="No data")
    
    with col3:
        if total_revenue > 0:
            st.metric(
                label="F&B Revenue",
                value=format_currency(fb_revenue),
                delta=f"{(fb_revenue/total_revenue*100):.1f}% of total" if total_revenue > 0 else None
            )
        else:
            st.metric(label="F&B Revenue", value="No data")
    
    # Revenue breakdown in more detail
    st.subheader("Revenue Breakdown")
    
    if total_revenue > 0:
        # Create a pie chart of revenue sources
        rev_sources = pd.DataFrame({
            'Source': ['Room Revenue', 'F&B Revenue', 'Other Revenue'],
            'Amount': [room_revenue, fb_revenue, other_revenue]
        })
        
        fig = px.pie(
            rev_sources, 
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
    else:
        st.info("No revenue data available for breakdown visualization.")
    
    # Revenue trends over time
    st.subheader("Revenue Trends")
    
    if not revenue_data.empty and 'date' in revenue_data.columns and 'total_revenue' in revenue_data.columns:
        # Create time series chart
        fig = px.line(
            revenue_data,
            x="date",
            y="total_revenue",
            title="Daily Total Revenue",
            labels={"total_revenue": "Revenue ($)", "date": "Date"}
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Stacked area chart showing revenue composition over time
        if ('room_revenue' in revenue_data.columns and 'f&b_revenue' in revenue_data.columns and 
            'other_revenue' in revenue_data.columns):
            
            fig = px.area(
                revenue_data,
                x="date",
                y=["room_revenue", "f&b_revenue", "other_revenue"],
                title="Daily Revenue Composition",
                labels={
                    "value": "Revenue ($)", 
                    "date": "Date", 
                    "variable": "Revenue Type"
                }
            )
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Insufficient data for revenue trend visualization.")
    
    # RevPAR and ADR Analysis section
    st.subheader("RevPAR & ADR Analysis")
    
    # Get occupancy data to calculate RevPAR and ADR
    occupancy_data = hotel_data.get_occupancy_data(start_date, end_date)
    
    if not revenue_data.empty and not occupancy_data.empty:
        try:
            # Merge data sets if needed
            combined_data = pd.merge(
                revenue_data, 
                occupancy_data, 
                on='date', 
                how='inner'
            )
            
            if ('room_revenue' in combined_data.columns and 'rooms_occupied' in combined_data.columns and 
                'total_rooms' in combined_data.columns):
                
                # Calculate ADR (Average Daily Rate) and RevPAR (Revenue Per Available Room)
                combined_data['adr'] = combined_data['room_revenue'] / combined_data['rooms_occupied']
                combined_data['revpar'] = combined_data['room_revenue'] / combined_data['total_rooms']
                
                # Create a subplot with ADR and RevPAR
                fig = go.Figure()
                
                fig.add_trace(
                    go.Scatter(
                        x=combined_data['date'],
                        y=combined_data['adr'],
                        name="ADR",
                        line=dict(color='#1E88E5', width=2)
                    )
                )
                
                fig.add_trace(
                    go.Scatter(
                        x=combined_data['date'],
                        y=combined_data['revpar'],
                        name="RevPAR",
                        line=dict(color='#4CAF50', width=2)
                    )
                )
                
                fig.update_layout(
                    title="ADR and RevPAR Trends",
                    xaxis_title="Date",
                    yaxis_title="Amount ($)",
                    height=400
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Insufficient data for ADR and RevPAR calculations.")
        except Exception as e:
            st.error(f"Error calculating RevPAR and ADR: {str(e)}")
    else:
        st.info("Insufficient data for RevPAR and ADR analysis.")
    
    # Detailed revenue data table
    st.subheader("Detailed Revenue Data")
    
    if not revenue_data.empty:
        st.dataframe(revenue_data, hide_index=True)
        
        # Download option
        create_download_button(revenue_data, "revenue_data.csv", "Download Revenue Data")
    else:
        st.info("No revenue data available for display.")
    
    # Revenue insights section
    st.subheader("Revenue Insights")
    
    insights_container = st.container()
    
    with insights_container:
        st.write("Based on the revenue data, here are some insights:")
        
        if total_revenue > 0:
            # Generate insights based on actual data
            # Revenue mix
            room_rev_pct = room_revenue / total_revenue * 100 if total_revenue > 0 else 0
            fb_rev_pct = fb_revenue / total_revenue * 100 if total_revenue > 0 else 0
            
            if room_rev_pct > 80:
                st.write("- Room revenue dominates the revenue mix. Consider strategies to increase ancillary revenue streams.")
            elif fb_rev_pct > 40:
                st.write("- F&B revenue is a significant contributor to total revenue. This is a strength to build upon.")
            
            # Revenue trends
            if len(revenue_data) > 1 and 'date' in revenue_data.columns and 'total_revenue' in revenue_data.columns:
                # Check if there's a trend by comparing first and last week
                dates = sorted(revenue_data['date'].unique())
                if len(dates) > 10:
                    first_week = revenue_data[revenue_data['date'].isin(dates[:7])]['total_revenue'].mean()
                    last_week = revenue_data[revenue_data['date'].isin(dates[-7:])]['total_revenue'].mean()
                    
                    pct_change = (last_week - first_week) / first_week * 100 if first_week > 0 else 0
                    
                    if pct_change > 10:
                        st.write(f"- Revenue has an increasing trend ({pct_change:.1f}% increase) when comparing the first and last week of the period.")
                    elif pct_change < -10:
                        st.write(f"- Revenue has a decreasing trend ({abs(pct_change):.1f}% decrease) when comparing the first and last week of the period.")
        else:
            st.write("- No revenue data is available to generate insights.")
