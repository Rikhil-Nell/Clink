import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np

from src.analysis.customer_analysis import run_analysis
from src.analysis.order_analysis import run_analysis
from src.analysis.product_analysis import run_analysis

from src.summarization.customer_kpi_summarization import run_summarization
from src.summarization.order_kpis_summarization import run_summarization
from src.summarization.product_kpi_summarization import run_summarization

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
    </style>
""", unsafe_allow_html=True)

# Main title with emoji and styling
st.markdown("""
    <div class="main-header">
        <h1>🍽️ Clink - Data-driven coupon strategies for Indian restaurants</h1>
        <p>Transform your restaurant data into actionable insights</p>
    </div>
""", unsafe_allow_html=True)

# Sidebar navigation with enhanced styling
st.sidebar.markdown("### 🧭 Navigation")
page = st.sidebar.radio(
    "Choose your journey:",
    ["📂 Data Upload", "📈 KPI Analysis", "🎯 Coupon Generation"],
    help="Navigate through different sections of the app"
)

# Initialize session state to store data
if "uploaded_file" not in st.session_state:
    st.session_state.uploaded_file = None

if "invoice_df" not in st.session_state:
    st.session_state.invoice_df = None

if "cooc_matrix_df" not in st.session_state:
    st.session_state.cooc_matrix_df = None

if "analysis_complete" not in st.session_state:
    st.session_state.analysis_complete = False

# Function to check if data is uploaded
def check_data_uploaded():
    return (st.session_state.invoice_df is not None and 
            st.session_state.cooc_matrix_df is not None and 
            st.session_state.analysis_complete)

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
        st.session_state.uploaded_file = uploaded_file
        
        # Show progress
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        status_text.text("🔄 Processing your data...")
        progress_bar.progress(25)
        
        try:
            # Run your analysis function directly on the uploaded file-like object
            invoice_df, cooc_matrix_df = run_analysis(uploaded_file)
            progress_bar.progress(75)
            
            # Store in session state
            st.session_state.invoice_df = invoice_df
            st.session_state.cooc_matrix_df = cooc_matrix_df
            st.session_state.analysis_complete = True
            
            progress_bar.progress(100)
            status_text.text("✅ Analysis completed successfully!")
            
            # Success message with metrics
            st.balloons()
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("📊 Total Orders", len(invoice_df))
            with col2:
                st.metric("🛍️ Unique Items", len(cooc_matrix_df))
            with col3:
                st.metric("💰 Revenue", f"₹{invoice_df['net_invoice_value'].sum():,.0f}")
            
        except Exception as e:
            st.error(f"❌ Error processing file: {str(e)}")
            st.session_state.analysis_complete = False

    # Display results if they exist in session
    if check_data_uploaded():
        st.markdown("---")
        
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


# ==========================
# PAGE 2: KPI SUMMARIZATION + RESEARCH
# ==========================
elif page == "📈 KPI Analysis":
    if not check_data_uploaded():
        st.markdown("""
        <div style="text-align: center; padding: 3rem; background-color: #778da9; border-radius: 10px; margin: 2rem 0;">
            <h2>🚫 No Data Found</h2>
            <p style="font-size: 1.2rem; color: #666;">Please upload your data first to view KPI analysis.</p>
            <p>👈 Go to the <strong>Data Upload</strong> page to get started!</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("📂 Go to Data Upload", type="primary"):
            st.session_state.page = "📂 Data Upload"
            st.rerun()
    else:
        st.header("📈 KPI Analysis Dashboard")
        
        # Run KPI analysis
        with st.spinner("🔍 Analyzing your data..."):
            kpi_results = run_summarization(
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
        
        st.markdown("""
        ### 🚀 Coming Soon!
        
        This feature will generate intelligent coupon strategies based on your data analysis:
        
        - **🎁 Bundle Coupons** - Based on co-occurrence patterns
        - **🎯 Targeted Discounts** - For high-value customers
        - **📅 Time-based Offers** - Leveraging temporal patterns
        - **🔄 Cross-sell Promotions** - Drive additional purchases
        
        Stay tuned for this exciting feature!
        """)
        
        # Placeholder for future coupon generation
        st.info("💡 **Preview:** Use the insights from KPI Analysis to manually create targeted promotions for now!")

# Footer
st.markdown("---")
st.markdown("""
    <div style="text-align: center; color: #666; padding: 1rem;">
        <p>Made with ❤️ for Indian restaurants | Powered by data-driven insights</p>
    </div>
""", unsafe_allow_html=True)