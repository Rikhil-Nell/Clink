import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np

from src.analysis.order_analysis import run_order_analysis
from src.analysis.customer_analysis import run_customer_analysis

from src.app.utils.session import reset_analysis_state, validate_customer_data, check_data_uploaded
from src.app.utils.overview import generate_data_overview

def handle_file_upload():
    uploaded_file = st.file_uploader(
        "🎯 Choose your data file",
        type=["csv", "xlsx"],
        help="Upload a CSV or Excel file containing your restaurant order data"
    )
    if uploaded_file is not None:
        if st.session_state.uploaded_file != uploaded_file:
            reset_analysis_state()
            st.session_state.uploaded_file = uploaded_file
            try:
                if uploaded_file.name.endswith('.csv'):
                    st.session_state.raw_data = pd.read_csv(uploaded_file)
                else:
                    st.session_state.raw_data = pd.read_excel(uploaded_file)
                validate_customer_data()
            except Exception as e:
                st.error(f"❌ Error reading file: {str(e)}")
                reset_analysis_state()
                st.stop()
        return uploaded_file
    return None

def run_analysis(uploaded_file):
    progress_bar = st.progress(0)
    status_text = st.empty()

    if not st.session_state.analysis_complete:
        status_text.text("🔄 Processing your data...")
        progress_bar.progress(25)
        try:
            # Replace with your actual analysis functions
            uploaded_file.seek(0)
            invoice_df, cooc_matrix_df = run_order_analysis(st.session_state.raw_data)
            progress_bar.progress(50)
            st.session_state.invoice_df = invoice_df
            st.session_state.cooc_matrix_df = cooc_matrix_df
            if st.session_state.customer_data_valid:
                status_text.text("🔄 Processing customer data...")
                customer_analysis_results = run_customer_analysis(st.session_state.raw_data)
                st.session_state.customer_analysis_results = customer_analysis_results
                progress_bar.progress(75)
            st.session_state.analysis_complete = True
            progress_bar.progress(100)
            status_text.text("✅ Analysis completed successfully!")
            st.balloons()
        except Exception as e:
            st.error(f"❌ Error processing file: {str(e)}")
            reset_analysis_state()
            st.stop()

def show_overview():
    if check_data_uploaded():
        overview = generate_data_overview()
        if overview:
            st.markdown("---")
            st.markdown("""
                <div class="data-overview">
                    <h3>📊 Data Overview - Your Restaurant at a Glance</h3>
                    <p>Here's what we discovered in your data:</p>
                </div>
            """, unsafe_allow_html=True)
            st.subheader("💼 Core Business Metrics")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("📊 Total Orders", f"{overview['total_orders']:,}")
            with col2:
                st.metric("💰 Total Revenue", f"₹{overview['total_revenue']:,.0f}")
            with col3:
                st.metric("🛒 Avg Order Value", f"₹{overview['avg_order_value']:,.0f}")
            with col4:
                st.metric("🛍️ Unique Items", f"{overview['unique_items']:,}")
            st.subheader("👥 Customer Intelligence")
            if overview['customer_insights']['has_customer_data']:
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("👥 Unique Customers", f"{overview['customer_insights']['unique_customers']:,}")
                with col2:
                    st.metric("💳 Avg Spend/Customer", f"₹{overview['customer_insights']['avg_spend_per_customer']:,.0f}")
                with col3:
                    orders_per_customer = overview['total_orders'] / overview['customer_insights']['unique_customers']
                    st.metric("🔄 Orders per Customer", f"{orders_per_customer:.1f}", help="Average number of orders per customer")
                st.success("✅ Customer Analysis Available")
            else:
                customer_count = overview['customer_insights'].get('customer_count', 0)
                if customer_count >=50:
                    st.success(f"✅ **Customer Data Requirement - Succeeded**: Found {customer_count} customer phone entries.")
                if 50 > customer_count:
                    st.warning(f"⚠️ **Customer Data Requirement - Failed**: Found {customer_count} customer phone entries, but need at least 50 for customer analysis. Order-level analysis will be unavailable.")
                else:
                    st.warning("⚠️ **No Customer Data** - Customer phone numbers are missing. Only order-level analysis will be available.")

        with st.expander("🔍 Detailed Data Preview", expanded=False):
            # Tabbed interface for better organization
            tab1, tab2, tab3 = st.tabs(["📋 Invoice Summary", "🔗 Co-occurrence Matrix", "📈 Visualization"])
            
            with tab1:
                st.subheader("🧾 Invoice-Level Aggregation Preview")
                st.dataframe(
                    st.session_state.invoice_df.head(10), 
                    use_container_width=True,
                    hide_index=True
                )
                
                if st.button("📥 Download Invoice Data"):
                    csv = st.session_state.invoice_df.to_csv(index=False)
                    st.download_button(
                        label="Download CSV",
                        data=csv,
                        file_name="invoice_aggregation.csv",
                        mime="text/csv"
                    )
            
            with tab2:
                st.subheader("🔗 Top 30 Product Co-Occurrence Matrix")
                st.dataframe(
                    st.session_state.cooc_matrix_df.head(10), 
                    use_container_width=True,
                    hide_index=True
                )
            
            with tab3:
                st.subheader("🔥 Product Co-Occurrence Heatmap")
                
                cooc = st.session_state.cooc_matrix_df.copy()
                mask = np.triu(np.ones_like(cooc, dtype=bool))

                fig, ax = plt.subplots(figsize=(14, 12))
                sns.heatmap(
                    cooc,
                    mask=mask,
                    cmap="rocket_r",
                    linewidths=0.5,
                    linecolor="gray",
                    annot=True,
                    fmt=".0f",
                    annot_kws={"size": 8},
                    cbar_kws={"label": "Co-Occurrence Count"},
                    square=True,
                    ax=ax
                )
                ax.set_title("Top 30 Product Co-Occurrence (Lower Triangle)", fontsize=18, pad=16)
                plt.xticks(rotation=45, ha='right', fontsize=10)
                plt.yticks(rotation=0, fontsize=10)
                plt.tight_layout()
                st.pyplot(fig)

def render_data_upload_page():
    col1, col2 = st.columns([2, 1])
    with col1:
        st.header("📂 Upload Your Order Data")
        st.markdown("""
        ### 🚀 Get Started in 3 Simple Steps:
        1. **📋 Prepare your data** - CSV or Excel file with order details  
        2. **⬆️ Upload** - Click below to select your file  
        3. **⚡ Analyze** - Watch the magic happen!
        ---
        **Expected columns:** `invoice_no`, `item_name`, `date`, `item_quantity`, `item_total`, etc.  
        **For customer analysis:** Include `customer_phone` column with at least 50 entries
        """)
    with col2:
        st.info("💡 **Pro Tip:** \n\nMake sure your data includes order-level information with item details for the best analysis!")
    uploaded_file = handle_file_upload()
    if uploaded_file:
        run_analysis(uploaded_file)
    show_overview()
