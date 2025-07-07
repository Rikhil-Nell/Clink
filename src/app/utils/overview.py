import pandas as pd
import streamlit as st
from .session import check_data_uploaded

def generate_data_overview():
    """Generate data overview using session state data"""
    if not check_data_uploaded():
        return None
    
    df = st.session_state.invoice_df
    cooc_df = st.session_state.cooc_matrix_df
    
    # Basic metrics
    total_orders = len(df)
    total_revenue = df['net_invoice_value'].sum()
    avg_order_value = df['net_invoice_value'].mean()
    unique_items = len(cooc_df)
    
    # Date range
    if 'date' in df.columns:
        try:
            df['date'] = pd.to_datetime(df['date'])
            date_range = f"{df['date'].min().strftime('%Y-%m-%d')} to {df['date'].max().strftime('%Y-%m-%d')}"
        except:
            date_range = "Date parsing error"
    else:
        date_range = "No date column found"
    
    # Customer insights using session state
    customer_insights = {}
    if st.session_state.customer_data_valid:
        # Use the invoice_df which should have customer data if it was valid
        if 'customer_phone' in df.columns:
            unique_customers = df['customer_phone'].nunique()
            avg_spend_per_customer = df.groupby('customer_phone')['net_invoice_value'].sum().mean()
            customer_insights = {
                'unique_customers': unique_customers,
                'avg_spend_per_customer': avg_spend_per_customer,
                'has_customer_data': True
            }
        else:
            customer_insights = {
                'has_customer_data': False,
                'customer_count': st.session_state.customer_count
            }
    else:
        customer_insights = {
            'has_customer_data': False,
            'customer_count': st.session_state.customer_count
        }
    
    return {
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'avg_order_value': avg_order_value,
        'unique_items': unique_items,
        'date_range': date_range,
        'customer_insights': customer_insights
    }