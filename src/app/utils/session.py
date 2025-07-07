import streamlit as st

def initialize_session_state():
    """Initialize all session state variables"""
    if "uploaded_file" not in st.session_state:
        st.session_state.uploaded_file = None
    
    if "raw_data" not in st.session_state:
        st.session_state.raw_data = None
    
    if "invoice_df" not in st.session_state:
        st.session_state.invoice_df = None

    if "cooc_matrix_df" not in st.session_state:
        st.session_state.cooc_matrix_df = None

    if "analysis_complete" not in st.session_state:
        st.session_state.analysis_complete = False
    
    if "customer_data_valid" not in st.session_state:
        st.session_state.customer_data_valid = False
    
    if "customer_count" not in st.session_state:
        st.session_state.customer_count = 0

    if "customer_analysis_results" not in st.session_state:
        st.session_state.customer_analysis_results = None

def reset_analysis_state():
    """Reset analysis-related session state"""
    st.session_state.invoice_df = None
    st.session_state.cooc_matrix_df = None
    st.session_state.analysis_complete = False
    st.session_state.customer_data_valid = False
    st.session_state.customer_count = 0
    st.session_state.raw_data = None
    st.session_state.customer_analysis_results = None

def check_data_uploaded():
    """Check if all required data is available"""
    return (st.session_state.invoice_df is not None and 
            st.session_state.cooc_matrix_df is not None and 
            st.session_state.analysis_complete)

def validate_customer_data():
    """Validate customer data and update session state"""
    if not st.session_state.raw_data is None:
        # Check if customer_phone column exists and has sufficient data
        if "customer_phone" in st.session_state.raw_data.columns:
            non_null_customers = st.session_state.raw_data["customer_phone"].dropna()
            customer_count = len(non_null_customers)
            
            st.session_state.customer_count = customer_count
            st.session_state.customer_data_valid = customer_count >= 50
            
            return st.session_state.customer_data_valid
        else:
            st.session_state.customer_count = 0
            st.session_state.customer_data_valid = False
            return False
    else:
        st.session_state.customer_count = 0
        st.session_state.customer_data_valid = False
        return False

def check_customer_data_validity():
    """Check customer data validity from session state"""
    return st.session_state.customer_data_valid