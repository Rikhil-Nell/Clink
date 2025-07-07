import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np

from src.analysis.customer_analysis import run_customer_analysis
from src.analysis.order_analysis import run_order_analysis
# from src.analysis.product_analysis import run_analysis

from src.summarization.customer_kpi_summarization import run_customer_summarization
from src.summarization.order_kpi_summarization import run_order_summarization
# from src.summarization.product_kpi_summarization import run_summarization

# Streamlit page setup
st.set_page_config(
    page_title="Clink - Restaurant Analytics",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom styling with built-in Streamlit options
st.markdown("""
    <style>
    .main-header {
        background: linear-gradient(90deg, #ff6b6b, #ffa500);
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        color: white;
        margin-bottom: 2rem;
    }
    .data-overview {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        margin: 1rem 0;
    }
    .overview-metric {
        background: rgba(255, 255, 255, 0.1);
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        border-left: 4px solid #ffffff;
    }
    </style>
""", unsafe_allow_html=True)

# Main title with emoji and styling
st.markdown("""
    <div class="main-header">
        <h1>🍽️ Clink - Data-driven coupon strategies for Indian restaurants</h1>
        <p>Transform your restaurant data into actionable insights</p>
    </div>
""", unsafe_allow_html=True)

# Initialize session state to store data
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

# Initialize session state
initialize_session_state()

# Sidebar navigation with enhanced styling
st.sidebar.markdown("### 🧭 Navigation")
page = st.sidebar.radio(
    "Choose your journey:",
    ["📂 Data Upload", "📈 KPI Analysis", "🎯 Coupon Generation"],
    help="Navigate through different sections of the app"
)

# Function to check if data is uploaded
def check_data_uploaded():
    """Check if all required data is available"""
    return (st.session_state.invoice_df is not None and 
            st.session_state.cooc_matrix_df is not None and 
            st.session_state.analysis_complete)

# Function to validate customer data
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

# Check if customer data is valid (using session state)
def check_customer_data_validity():
    """Check customer data validity from session state"""
    return st.session_state.customer_data_valid

# Function to generate quick data overview
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

# Function to reset analysis state
def reset_analysis_state():
    """Reset analysis-related session state"""
    st.session_state.invoice_df = None
    st.session_state.cooc_matrix_df = None
    st.session_state.analysis_complete = False
    st.session_state.customer_data_valid = False
    st.session_state.customer_count = 0
    st.session_state.raw_data = None
    st.session_state.customer_analysis_results = None

# ==========================
# PAGE 1: DATA UPLOAD + ANALYSIS
# ==========================
if page == "📂 Data Upload":
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

    # File uploader with enhanced styling
    uploaded_file = st.file_uploader(
        "🎯 Choose your data file",
        type=["csv", "xlsx"],
        help="Upload a CSV or Excel file containing your restaurant order data"
    )

    if uploaded_file is not None:
        # Check if this is a new file
        if st.session_state.uploaded_file != uploaded_file:
            # Reset previous analysis state
            reset_analysis_state()
            st.session_state.uploaded_file = uploaded_file
            
            # Load raw data first to validate customer data
            try:
                if uploaded_file.name.endswith('.csv'):
                    st.session_state.raw_data = pd.read_csv(uploaded_file)
                else:
                    st.session_state.raw_data = pd.read_excel(uploaded_file)
                
                # Validate customer data immediately
                validate_customer_data()
                
            except Exception as e:
                st.error(f"❌ Error reading file: {str(e)}")
                reset_analysis_state()
                st.stop()
        
        # Show progress
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Only run analysis if not already complete
        if not st.session_state.analysis_complete:
            status_text.text("🔄 Processing your data...")
            progress_bar.progress(25)
            
            try:
                # Run order analysis
                uploaded_file.seek(0)
                invoice_df, cooc_matrix_df = run_order_analysis(uploaded_file)
                progress_bar.progress(50)
                
                # Store order analysis results
                st.session_state.invoice_df = invoice_df
                st.session_state.cooc_matrix_df = cooc_matrix_df
                
                # Run customer analysis if customer data is valid
                if st.session_state.customer_data_valid:
                    status_text.text("🔄 Processing customer data...")
                    customer_analysis_results = run_customer_analysis(st.session_state.raw_data)
                    st.session_state.customer_analysis_results = customer_analysis_results
                    progress_bar.progress(75)
                
                st.session_state.analysis_complete = True
                progress_bar.progress(100)
                status_text.text("✅ Analysis completed successfully!")
                
                # Success message with enhanced overview
                st.balloons()
                
            except Exception as e:
                st.error(f"❌ Error processing file: {str(e)}")
                reset_analysis_state()
                st.stop()
            
    # Display enhanced overview if data exists
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
            
            # Core Business Metrics
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
            
            # Customer Intelligence Section
            st.subheader("👥 Customer Intelligence")
            
            # Debug information (remove in production)
            with st.expander("🔧 Debug Info", expanded=False):
                st.write(f"Customer data valid: {st.session_state.customer_data_valid}")
                st.write(f"Customer count: {st.session_state.customer_count}")
                st.write(f"Raw data columns: {list(st.session_state.raw_data.columns) if st.session_state.raw_data is not None else 'None'}")
                if st.session_state.raw_data is not None and 'customer_phone' in st.session_state.raw_data.columns:
                    st.write(f"Non-null customer phones: {st.session_state.raw_data['customer_phone'].dropna().shape[0]}")
            
            if overview['customer_insights']['has_customer_data']:
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric(
                        "👥 Unique Customers", 
                        f"{overview['customer_insights']['unique_customers']:,}",
                        help="Total number of unique customers identified"
                    )
                with col2:
                    st.metric(
                        "💳 Avg Customer Value", 
                        f"₹{overview['customer_insights']['avg_spend_per_customer']:,.0f}",
                        help="Average total spending per customer"
                    )
                with col3:
                    orders_per_customer = overview['total_orders'] / overview['customer_insights']['unique_customers']
                    st.metric(
                        "🔄 Orders per Customer", 
                        f"{orders_per_customer:.1f}",
                        help="Average number of orders per customer"
                    )
                
                st.success("✅ **Customer Analysis Available** - Your data has sufficient customer information for detailed segmentation and behavior analysis!")
            else:
                customer_count = overview['customer_insights'].get('customer_count', 0)
                if customer_count > 0:
                    st.warning(f"⚠️ **Limited Customer Data** - Found {customer_count} customer phone entries, but need at least 50 for customer analysis. Order-level analysis will be available.")
                else:
                    st.warning("⚠️ **No Customer Data** - Customer phone numbers are missing. Only order-level analysis will be available.")
            
            # Time Period
            st.subheader("📅 Data Coverage")
            st.info(f"**Date Range:** {overview['date_range']}")
            
            # Quick Action Buttons
            st.markdown("### 🚀 Next Steps")
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("📈 View Detailed Analysis", type="primary", use_container_width=True):
                    # Use query params or session state to switch pages
                    st.session_state.switch_to_analysis = True
                    st.rerun()
            
            with col2:
                if st.button("🎯 Generate Coupons", use_container_width=True):
                    st.session_state.switch_to_coupons = True
                    st.rerun()

        # Detailed Data Preview (Collapsed by default)
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

# Handle page switching from session state
if hasattr(st.session_state, 'switch_to_analysis') and st.session_state.switch_to_analysis:
    st.session_state.switch_to_analysis = False
    page = "📈 KPI Analysis"

if hasattr(st.session_state, 'switch_to_coupons') and st.session_state.switch_to_coupons:
    st.session_state.switch_to_coupons = False
    page = "🎯 Coupon Generation"

# ==========================
# PAGE 2: KPI SUMMARIZATION + RESEARCH
# ==========================
if page == "📈 KPI Analysis":
    if not check_data_uploaded():
        st.markdown("""
        <div style="text-align: center; padding: 3rem; background-color: #778da9; border-radius: 10px; margin: 2rem 0;">
            <h2>🚫 No Data Found</h2>
            <p style="font-size: 1.2rem; color: #666;">Please upload your data first to view KPI analysis.</p>
            <p>👈 Go to the <strong>Data Upload</strong> page to get started!</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("📂 Go to Data Upload", type="primary"):
            # Force page change
            st.rerun()
    else:
        st.header("📈 KPI Analysis Dashboard")
        
        # Show data overview at the top
        overview = generate_data_overview()
        if overview:
            st.markdown("### 📊 Data Summary")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("📊 Total Orders", f"{overview['total_orders']:,}")
            with col2:
                st.metric("💰 Total Revenue", f"₹{overview['total_revenue']:,.0f}")
            with col3:
                st.metric("🛒 Avg Order Value", f"₹{overview['avg_order_value']:,.0f}")
            with col4:
                if overview['customer_insights']['has_customer_data']:
                    st.metric("👥 Unique Customers", f"{overview['customer_insights']['unique_customers']:,}")
                else:
                    st.metric("🛍️ Unique Items", f"{overview['unique_items']:,}")
        
        st.markdown("---")
        
        # Analysis selection
        analysis_options = ["Order-Level Analysis"]
        if check_customer_data_validity():
            analysis_options.append("Customer-Level Analysis")
        
        selected_analysis = st.sidebar.selectbox(
            "Choose the KPI view you want to explore:",
            analysis_options
        )

        # ==========================
        # CUSTOMER-LEVEL ANALYSIS
        # ==========================
        if selected_analysis == "Customer-Level Analysis":
            st.header("📈 Customer-Level KPI Dashboard")
            
            # Use pre-computed customer analysis results
            if st.session_state.customer_analysis_results is not None:
                with st.spinner("🔍 Generating customer insights..."):
                    customer_kpi_results = run_customer_summarization(st.session_state.customer_analysis_results)

                
                st.subheader("🎯 Customer KPIs")
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("👥 Total Customers", f"{customer_kpi_results['total_customers']:,}")
                with col2:
                    st.metric("💳 Avg Spend / Customer", f"₹{customer_kpi_results['avg_spend_per_customer']:,}")
                with col3:
                    st.metric("📅 Avg Days Active", f"{customer_kpi_results['avg_days_active']:.1f}")
                with col4:
                    st.metric("📊 Segments Found", customer_kpi_results['num_segments'])
                
                # Tabs
                tab1, tab2, tab3 = st.tabs(["📊 Customer Summary", "🧬 Segmentation", "💡 Customer Insights"])
                
                with tab1:
                    st.subheader("📝 Customer Summary Table")
                    st.dataframe(customer_kpi_results['customer_summary_df'], use_container_width=True)
                
                with tab2:
                    st.subheader("🧬 Customer Segments Visualization")
                    st.plotly_chart(customer_kpi_results['cluster_plot'], use_container_width=True)
                
                with tab3:
                    st.subheader("💡 Recommendations for Customer Engagement")
                    for insight in customer_kpi_results['recommendations']:
                        st.info(insight)
            else:
                st.error("Customer analysis data not available. Please re-upload your data.")
                st.stop()

        # ==========================
        # ORDER-LEVEL ANALYSIS
        # ==========================
        elif selected_analysis == "Order-Level Analysis":
            st.header("📈 Order-Level KPI Dashboard")
            
            # Run order summarization
            with st.spinner("🔍 Generating order insights..."):
                kpi_results = run_order_summarization(
                    invoice_df=st.session_state.invoice_df, 
                    cooc_matrix=st.session_state.cooc_matrix_df
                )
            
            # Key metrics in a beautiful layout
            st.subheader("🎯 Key Performance Indicators")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "📊 Total Orders", 
                    f"{kpi_results['invoice_analysis']['total_orders']:,}",
                    help="Total number of orders processed"
                )
            
            with col2:
                st.metric(
                    "💰 Total Revenue", 
                    f"₹{kpi_results['invoice_analysis']['total_revenue']:,}",
                    help="Total revenue generated"
                )
            
            with col3:
                st.metric(
                    "🛒 Average Order Value", 
                    f"₹{kpi_results['invoice_analysis']['average_order_value']:,}",
                    help="Average value per order"
                )
            
            with col4:
                st.metric(
                    "📦 Items per Order", 
                    f"{kpi_results['invoice_analysis']['average_items_per_order']:.1f}",
                    help="Average number of items per order"
                )
            
            st.markdown("---")
            
            # Organized sections with tabs
            tab1, tab2, tab3 = st.tabs(["📊 Order Analytics", "🔗 Product Insights", "💡 Business Recommendations"])
            
            with tab1:
                # Order Value Analysis
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("📈 Order Value Distribution")
                    order_dist = kpi_results['invoice_analysis']['order_value_distribution']
                    
                    dist_df = pd.DataFrame([
                        {"Metric": "Average", "Value": f"₹{order_dist['mean']:,.0f}"},
                        {"Metric": "Median", "Value": f"₹{order_dist['50%']:,.0f}"},
                        {"Metric": "25th Percentile", "Value": f"₹{order_dist['25%']:,.0f}"},
                        {"Metric": "75th Percentile", "Value": f"₹{order_dist['75%']:,.0f}"},
                        {"Metric": "Minimum", "Value": f"₹{order_dist['min']:,.0f}"},
                        {"Metric": "Maximum", "Value": f"₹{order_dist['max']:,.0f}"}
                    ])
                    st.dataframe(dist_df, hide_index=True, use_container_width=True)
                
                with col2:
                    st.subheader("🏆 High-Value Orders")
                    hv_orders = kpi_results['invoice_analysis']['high_value_orders']
                    
                    st.metric("High-Value Orders", f"{hv_orders['count']:,}")
                    st.metric("Percentage", f"{hv_orders['percentage']:.1f}%")
                    st.metric("Threshold", f"₹{hv_orders['threshold']:,.0f}")
                
                # Basket Size Analysis
                st.markdown("---")
                st.subheader("🛒 Basket Size Analysis")
                
                col1, col2, col3, col4 = st.columns(4)
                basket_analysis = kpi_results['invoice_analysis']['basket_size_analysis']
                
                with col1:
                    st.metric("Avg Unique Items", f"{basket_analysis['avg_unique_items']:.1f}")
                with col2:
                    st.metric("Min Items", basket_analysis['min_items'])
                with col3:
                    st.metric("Max Items", basket_analysis['max_items'])
                with col4:
                    st.metric("Most Common Size", basket_analysis['most_common_basket_size'])
                
                # Temporal patterns
                st.markdown("---")
                temporal = kpi_results['invoice_analysis']['temporal_patterns']
                
                if temporal:
                    st.subheader("🕐 Temporal Patterns")
                    
                    # Day of week analysis
                    if 'day_of_week_distribution' in temporal and temporal['day_of_week_distribution']:
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write("**📅 Day of Week Distribution:**")
                            day_dist = temporal['day_of_week_distribution']
                            
                            # Create a sorted dataframe for better display
                            day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                            day_data = []
                            for day in day_order:
                                if day in day_dist:
                                    day_data.append({"Day": day, "Orders": day_dist[day]})
                            
                            day_df = pd.DataFrame(day_data)
                            st.dataframe(day_df, hide_index=True, use_container_width=True)
                        
                        with col2:
                            st.write("**🔥 Peak Days:**")
                            if 'peak_days' in temporal and temporal['peak_days']:
                                for i, day in enumerate(temporal['peak_days'], 1):
                                    st.write(f"**#{i}** {day} ({day_dist.get(day, 0):,} orders)")
                            else:
                                st.info("No peak days data available")
                    
                    # Hour analysis
                    if 'hour_analysis' in temporal and temporal['hour_analysis']:
                        st.markdown("---")
                        hour_analysis = temporal['hour_analysis']
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write("**🕐 Hourly Distribution (Top 10):**")
                            hourly_dist = hour_analysis.get('hourly_distribution', {})
                            
                            # Convert to sorted list and take top 10
                            hourly_data = []
                            for hour, count in sorted(hourly_dist.items(), key=lambda x: int(x[0])):
                                hour_12 = int(hour)
                                if hour_12 == 0:
                                    hour_str = "12 AM"
                                elif hour_12 < 12:
                                    hour_str = f"{hour_12} AM"
                                elif hour_12 == 12:
                                    hour_str = "12 PM"
                                else:
                                    hour_str = f"{hour_12 - 12} PM"
                                
                                hourly_data.append({"Hour": hour_str, "Orders": count})
                            
                            # Sort by order count and show top 10
                            hourly_data_sorted = sorted(hourly_data, key=lambda x: x['Orders'], reverse=True)[:10]
                            hourly_df = pd.DataFrame(hourly_data_sorted)
                            st.dataframe(hourly_df, hide_index=True, use_container_width=True)
                        
                        with col2:
                            st.write("**⚡ Peak Hours:**")
                            if 'peak_hours' in hour_analysis and hour_analysis['peak_hours']:
                                for hour in hour_analysis['peak_hours']:
                                    hour_24 = int(hour)
                                    if hour_24 == 0:
                                        hour_str = "12 AM"
                                    elif hour_24 < 12:
                                        hour_str = f"{hour_24} AM"
                                    elif hour_24 == 12:
                                        hour_str = "12 PM"
                                    else:
                                        hour_str = f"{hour_24 - 12} PM"
                                    
                                    order_count = hourly_dist.get(str(hour), 0)
                                    st.write(f"**{hour_str}** ({order_count:,} orders)")
                            else:
                                st.info("No peak hours identified")
                else:
                    st.info("No temporal patterns data available")
            
            with tab2:
                st.subheader("🔥 Top Product Pairings")
                
                strongest_pairs = kpi_results['cooccurrence_analysis']['strongest_cooccurrences']
                
                if strongest_pairs:
                    for i, pair in enumerate(strongest_pairs[:10], 1):
                        with st.expander(f"#{i} {pair['item_1']} + {pair['item_2']}", expanded=i<=3):
                            col1, col2 = st.columns([3, 1])
                            with col1:
                                st.write(f"**Items:** {pair['item_1']} & {pair['item_2']}")
                            with col2:
                                st.metric("Co-purchases", pair['count'])
                else:
                    st.info("No significant product pairings found in the data.")
            
            with tab3:
                st.subheader("💡 AI-Powered Business Recommendations")
                
                if 'business_insights' in kpi_results:
                    insights = kpi_results['business_insights']
                    
                    # Bundle opportunities
                    if insights['bundle_opportunities']:
                        st.write("### 🎁 Bundle Opportunities")
                        for bundle in insights['bundle_opportunities']:
                            st.success(f"**Bundle:** {' + '.join(bundle['bundle_items'])}")
                            st.write(f"📊 {bundle['statistical_strength']}")
                            st.write(f"💡 {bundle['recommendation']}")
                            st.write("---")
                    
                    # Cross-sell recommendations
                    if insights['cross_sell_recommendations']:
                        st.write("### 🎯 Cross-Sell Opportunities")
                        for rec in insights['cross_sell_recommendations'][:5]:
                            st.info(f"When customer orders **{rec['trigger_item']}**, suggest **{rec['suggest_item']}**")
                            st.write(f"📈 {rec['frequency']} | Strategy: {rec['strategy']}")
                            st.write("---")
                    
                    # Inventory insights
                    if insights['inventory_insights']:
                        st.write("### 📦 Inventory Insights")
                        for insight in insights['inventory_insights']:
                            st.warning(f"**{insight['insight_type'].replace('_', ' ').title()}**")
                            st.write(f"📋 {insight['description']}")
                            st.write(f"🎯 Action: {insight['action']}")
                            st.write("---")


# ==========================
# PAGE 3: COUPON GENERATION
# ==========================
elif page == "🎯 Coupon Generation":
    if not check_data_uploaded():
        st.markdown("""
        <div style="text-align: center; padding: 3rem; background-color: #778da9; border-radius: 10px; margin: 2rem 0;">
            <h2>🚫 No Data Found</h2>
            <p style="font-size: 1.2rem; color: #666;">Please upload your data first to generate coupons.</p>
            <p>👈 Go to the <strong>Data Upload</strong> page to get started!</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("📂 Go to Data Upload", type="primary"):
            st.session_state.page = "📂 Data Upload"
            st.rerun()
    else:
        st.header("🎯 Smart Coupon Generation")
        
        # Show data overview
        overview = generate_data_overview()
        if overview:
            st.markdown("### 📊 Available Data for Coupon Strategy")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("📊 Total Orders", f"{overview['total_orders']:,}")
            with col2:
                st.metric("💰 Total Revenue", f"₹{overview['total_revenue']:,.0f}")
            with col3:
                if overview['customer_insights']['has_customer_data']:
                    st.metric("👥 Unique Customers", f"{overview['customer_insights']['unique_customers']:,}")
                else:
                    st.metric("🛍️ Unique Items", f"{overview['unique_items']:,}")
        
        st.markdown("---")
        
        st.markdown("""
        ### 🚀 Coming Soon!
        
        This feature will generate intelligent coupon strategies based on your data analysis:
        
        - **🎁 Bundle Coupons** - Based on co-occurrence patterns
        - **🎯 Targeted Discounts** - For high-value customers
        - **📅 Time-based Offers** - Leveraging temporal patterns
        - **🔄 Cross-sell Promotions** - Drive additional purchases
        
        Stay tuned for this exciting feature!
        """)
        
        # Preview based on available data
        if overview and overview['customer_insights']['has_customer_data']:
            st.success("✅ **Customer-Targeted Coupons Available** - Your data supports personalized customer campaigns!")
            
            # Show coupon strategy preview
            st.markdown("### 🎯 Coupon Strategy Preview")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("""
                **🎁 Bundle Opportunities**
                - Combo deals based on frequently bought together items
                - Dynamic pricing for popular combinations
                - Seasonal bundle promotions
                """)
                
                st.markdown("""
                **👥 Customer Segmentation**
                - VIP customer exclusive offers
                - New customer welcome discounts
                - Win-back campaigns for inactive customers
                """)
            
            with col2:
                st.markdown("""
                **📅 Time-Based Offers**
                - Peak hour promotions
                - Slow day traffic boosters
                - Happy hour specials
                """)
                
                st.markdown("""
                **🔄 Cross-Sell Campaigns**
                - "Complete your meal" suggestions
                - Category-based upselling
                - Loyalty program incentives
                """)
        
        else:
            st.info("💡 **Order-Level Coupons Available** - Bundle and time-based promotions can be created with your current data!")
            
            # Show limited coupon options
            st.markdown("### 🎯 Available Coupon Types")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("""
                **🎁 Product Bundles**
                - Popular item combinations
                - Category-based deals
                - Volume discounts
                """)
            
            with col2:
                st.markdown("""
                **📅 Timing Strategies**
                - Peak vs off-peak pricing
                - Day-of-week promotions
                - Seasonal campaigns
                """)
        
        # Call to action
        st.markdown("---")
        st.info("💡 **Preview:** Use the insights from KPI Analysis to manually create targeted promotions for now!")
        
        if st.button("📈 View Analysis for Coupon Ideas", type="primary"):
            st.session_state.page = "📈 KPI Analysis"
            st.rerun()

# Footer
st.markdown("---")
st.markdown("""
    <div style="text-align: center; color: #666; padding: 1rem;">
        <p>Made with ❤️ for Indian restaurants | Powered by data-driven insights</p>
    </div>
""", unsafe_allow_html=True)
