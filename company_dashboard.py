if user.role == "Executive":
    st.title("Company-Wide Dashboard")
    total_revenue = data_handler.get_total_revenue_all_properties()
    avg_occ = data_handler.get_average_occupancy_all_properties()
    st.metric("Total Revenue", f"${total_revenue:,.2f}")
    st.metric("Avg Occupancy", f"{avg_occ:.1f}%")