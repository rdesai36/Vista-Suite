import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import calendar
from supabase_client import get_supabase_client
from data_handler import hotel_data

def show_dashboard(start_date, end_date):
    """
    Display the main dashboard page with key hotel metrics, trends, and visualizations.
    Args:
        start_date (datetime): Start of the date range.
        end_date (datetime): End of the date range.
    """
    st.title("Dashboard")
    
    # Get data for the selected date range
    occupancy_data = hotel_data.get_occupancy_data(start_date, end_date)
    revenue_data = hotel_data.get_revenue_data(start_date, end_date)
    
    # Convert to pandas DataFrames for easier manipulation
    df_occupancy = pd.DataFrame(occupancy_data) if occupancy_data else pd.DataFrame()
    df_revenue = pd.DataFrame(revenue_data) if revenue_data else pd.DataFrame()
    
    # Display key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        avg_occupancy = df_occupancy['occupancy_rate'].mean() if not df_occupancy.empty else 0
        st.metric("Average Occupancy", f"{avg_occupancy:.1f}%")
    
    with col2:
        total_revenue = df_revenue['total_revenue'].sum() if not df_revenue.empty else 0
        st.metric("Total Revenue", f"${total_revenue:,.2f}")
    
    with col3:
        avg_daily_rate = df_revenue['average_daily_rate'].mean() if not df_revenue.empty else 0
        st.metric("Average Daily Rate", f"${avg_daily_rate:.2f}")
    
    with col4:
        revpar = df_revenue['revpar'].mean() if not df_revenue.empty else 0
        st.metric("RevPAR", f"${revpar:.2f}")
    
    # Create charts
    st.subheader("Occupancy & Revenue Trends")
    
    # Prepare data for charts
    if not df_occupancy.empty:
        df_occupancy['date'] = pd.to_datetime(df_occupancy['date'])
        df_occupancy = df_occupancy.sort_values('date')
    
    if not df_revenue.empty:
        df_revenue['date'] = pd.to_datetime(df_revenue['date'])
        df_revenue = df_revenue.sort_values('date')
    
    # Create charts
    tab1, tab2 = st.tabs(["Occupancy", "Revenue"])
    
    with tab1:
        if not df_occupancy.empty:
            fig = px.line(df_occupancy, x='date', y='occupancy_rate', 
                          title='Occupancy Rate Over Time',
                          labels={'date': 'Date', 'occupancy_rate': 'Occupancy Rate (%)'},
                          line_shape='linear')
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No occupancy data available for the selected date range.")
            st.info("Once your property is connected to HotelKey, occupancy metrics and trends will appear here.")

    with tab2:
        if not df_revenue.empty:
            fig = px.line(df_revenue, x='date', y=['total_revenue', 'room_revenue', 'f&b_revenue', 'other_revenue'], 
                          title='Revenue Breakdown Over Time',
                          labels={'date': 'Date', 'value': 'Revenue ($)', 'variable': 'Revenue Type'},
                          line_shape='linear')
            fig.update_layout(height=400, legend_title_text='Revenue Type')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No revenue data available for the selected date range.")
            st.info("Once your property is connected to HotelKey, revenue metrics and trends will appear here.")

    # with tab3:
    #     if not df_bookings.empty:
    #         # Extract check-in dates
    #         check_ins = pd.DataFrame(df_bookings)
    #         check_ins['date'] = pd.to_datetime(check_ins['check_in_date'])
    #         check_ins = check_ins.groupby(check_ins['date'].dt.date).size().reset_index(name='count')
    #         check_ins['type'] = 'Check-ins'
            
            # Extract check-out dates
            # check_outs = pd.DataFrame(df_bookings)
            # check_outs['date'] = pd.to_datetime(check_outs['check_out_date'])
            # check_outs = check_outs.groupby(check_outs['date'].dt.date).size().reset_index(name='count')
            # check_outs['type'] = 'Check-outs'
            
            # Combine data
            # booking_activity = pd.concat([check_ins, check_outs])
            
            # Create chart
            # fig = px.bar(booking_activity, x='date', y='count', color='type',
            #              title='Check-ins and Check-outs',
            #              labels={'date': 'Date', 'count': 'Number of Bookings', 'type': 'Activity Type'},
            #              barmode='group')
            # fig.update_layout(height=400)
            # st.plotly_chart(fig, use_container_width=True)
        # else:
        #     st.info("No booking data available for the selected date range.")