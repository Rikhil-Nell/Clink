import streamlit as st
import pandas as pd
from src.app.utils.session import check_data_uploaded, check_customer_data_validity
from src.summarization.customer_kpi_summarization import run_customer_summarization
from src.summarization.order_kpi_summarization import run_order_summarization

def render_kpi_analysis_page():
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
        return

    st.header("📊 KPI Analysis Dashboard")

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
        st.subheader("📈 Customer-Level KPI Dashboard")

        if st.session_state.customer_analysis_results is not None:
            with st.spinner("🔍 Generating customer insights..."):
                customer_kpi_results = run_customer_summarization(st.session_state.customer_analysis_results)
                st.session_state.customer_analysis_summary = customer_kpi_results
            # --- Top-level metrics ---
            segments = customer_kpi_results["customer_segments"]
            financial = customer_kpi_results["financial_summary"]
            additional = customer_kpi_results["additional_insights"]

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("👥 Total Customers", f"{segments['total_customers']:,}")
            with col2:
                st.metric("💰 Total Revenue", f"₹{financial['total_revenue']:,.0f}")
            with col3:
                st.metric("🛒 Avg Order Value", f"₹{financial['overall_aov']:,.0f}")
            with col4:
                st.metric("💳 Avg CLV", f"₹{financial['overall_avg_clv']:,.0f}")

            st.markdown("---")

            # --- Customer Segments ---
            st.subheader("🧑‍🤝‍🧑 Customer Segments")
            seg1, seg2, seg3 = st.columns(3)
            with seg1:
                st.metric("🆕 New Customers", f"{segments['new_customers']['count']:,}")
                st.write(f"Avg First Order: ₹{segments['new_customers']['avg_first_order_value']:,.0f}")
                st.write(f"Percentage: {segments['new_customers']['percentage']}%")
            with seg2:
                st.metric("🔥 Active Customers", f"{segments['active_customers']['count']:,}")
                st.write(f"Avg CLV: ₹{segments['active_customers']['avg_clv']:,.0f}")
                st.write(f"Avg Orders: {segments['active_customers']['avg_orders']:.2f}")
                st.write(f"Percentage: {segments['active_customers']['percentage']}%")
            with seg3:
                st.metric("💤 Dormant Customers", f"{segments['dormant_customers']['count']:,}")
                st.write(f"Avg CLV Before Dormancy: ₹{segments['dormant_customers']['avg_clv_before_dormancy']:,.0f}")
                st.write(f"Percentage: {segments['dormant_customers']['percentage']}%")

            st.markdown("---")

            # --- Coupon Strategy Insights ---
            st.subheader("🎟️ Coupon Strategy Insights")
            coupon = customer_kpi_results["coupon_strategy_insights"]
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown("**Stamp Card**")
                st.write(f"Target Customers: {coupon['stamp_card']['target_customer_count']}")
                st.write(coupon['stamp_card']['suggestion'])
            with col2:
                st.markdown("**Miss You Offer**")
                st.write(f"Target Customers: {coupon['miss_you']['target_customer_count']}")
                st.write(f"Avg Spend (Dormant): ₹{coupon['miss_you']['avg_spend_of_dormant_customers']:,.0f}")
                st.write(coupon['miss_you']['suggestion'])
            with col3:
                st.markdown("**Joining Bonus**")
                st.write(f"Target Customers: {coupon['joining_bonus']['target_customer_count']}")
                st.write(f"Avg First Order: ₹{coupon['joining_bonus']['avg_first_order_value']:,.0f}")
                st.write(coupon['joining_bonus']['suggestion'])

            st.markdown("---")

            # --- Additional Insights ---
            st.subheader("🔎 Additional Insights")
            high_value = additional["high_value_customers"]
            freq = additional["order_frequency_insights"]
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("💎 High-Value Customers", f"{high_value['count']:,}")
                st.write(f"Threshold: ₹{high_value['threshold']:,.0f}")
                st.write(f"Avg CLV: ₹{high_value['avg_clv']:,.0f}")
            with col2:
                st.metric("🔁 Repeat Customers", f"{freq['repeat_customers']:,}")
                st.write(f"Single Order: {freq['single_order_customers']:,}")
            with col3:
                st.metric("🏆 High-Frequency Customers", f"{freq['high_frequency_customers']:,}")


    # ==========================
    # ORDER-LEVEL ANALYSIS
    # ==========================
    elif selected_analysis == "Order-Level Analysis":
        st.subheader("📈 Order-Level KPI Dashboard")

        with st.spinner("🔍 Generating order insights..."):
            order_kpi_results = run_order_summarization(
                invoice_df=st.session_state.invoice_df,
                cooc_matrix=st.session_state.cooc_matrix_df
            )
            st.session_state.order_analysis_summary = order_kpi_results
        st.subheader("🎯 Key Performance Indicators")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric(
                "📊 Total Orders",
                f"{order_kpi_results['invoice_analysis']['total_orders']:,}",
                help="Total number of orders processed"
            )
        with col2:
            st.metric(
                "💰 Total Revenue",
                f"₹{order_kpi_results['invoice_analysis']['total_revenue']:,}",
                help="Total revenue generated"
            )
        with col3:
            st.metric(
                "🛒 Average Order Value",
                f"₹{order_kpi_results['invoice_analysis']['average_order_value']:,}",
                help="Average value per order"
            )
        with col4:
            st.metric(
                "📦 Items per Order",
                f"{order_kpi_results['invoice_analysis']['average_items_per_order']:.1f}",
                help="Average number of items per order"
            )

        st.markdown("---")

        tab1, tab2, tab3 = st.tabs(["📊 Order Analytics", "🔗 Product Insights", "💡 Business Recommendations"])

        with tab1:
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("📈 Order Value Distribution")
                order_dist = order_kpi_results['invoice_analysis']['order_value_distribution']
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
                hv_orders = order_kpi_results['invoice_analysis']['high_value_orders']
                st.metric("High-Value Orders", f"{hv_orders['count']:,}")
                st.metric("Percentage", f"{hv_orders['percentage']:.1f}%")
                st.metric("Threshold", f"₹{hv_orders['threshold']:,.0f}")

            st.markdown("---")
            st.subheader("🛒 Basket Size Analysis")
            col1, col2, col3, col4 = st.columns(4)
            basket_analysis = order_kpi_results['invoice_analysis']['basket_size_analysis']
            with col1:
                st.metric("Avg Unique Items", f"{basket_analysis['avg_unique_items']:.1f}")
            with col2:
                st.metric("Min Items", basket_analysis['min_items'])
            with col3:
                st.metric("Max Items", basket_analysis['max_items'])
            with col4:
                st.metric("Most Common Size", basket_analysis['most_common_basket_size'])

            st.markdown("---")
            temporal = order_kpi_results['invoice_analysis']['temporal_patterns']
            if temporal:
                st.subheader("🕐 Temporal Patterns")
                if 'day_of_week_distribution' in temporal and temporal['day_of_week_distribution']:
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write("**📅 Day of Week Distribution:**")
                        day_dist = temporal['day_of_week_distribution']
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
                if 'hour_analysis' in temporal and temporal['hour_analysis']:
                    st.markdown("---")
                    hour_analysis = temporal['hour_analysis']
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write("**🕐 Hourly Distribution (Top 10):**")
                        hourly_dist = hour_analysis.get('hourly_distribution', {})
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
            strongest_pairs = order_kpi_results['cooccurrence_analysis']['strongest_cooccurrences']
            if strongest_pairs:
                for i, pair in enumerate(strongest_pairs[:10], 1):
                    with st.expander(f"#{i} {pair['item_1']} + {pair['item_2']}", expanded=i <= 3):
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.write(f"**Items:** {pair['item_1']} & {pair['item_2']}")
                        with col2:
                            st.metric("Co-purchases", pair['count'])
            else:
                st.info("No significant product pairings found in the data.")

        with tab3:
            st.subheader("💡 AI-Powered Business Recommendations")
            if 'business_insights' in order_kpi_results:
                insights = order_kpi_results['business_insights']
                if insights['bundle_opportunities']:
                    st.write("### 🎁 Bundle Opportunities")
                    for bundle in insights['bundle_opportunities']:
                        st.success(f"**Bundle:** {' + '.join(bundle['bundle_items'])}")
                        st.write(f"📊 {bundle['statistical_strength']}")
                        st.write(f"💡 {bundle['recommendation']}")
                        st.write("---")
                if insights['cross_sell_recommendations']:
                    st.write("### 🎯 Cross-Sell Opportunities")
                    for rec in insights['cross_sell_recommendations'][:5]:
                        st.info(f"When customer orders **{rec['trigger_item']}**, suggest **{rec['suggest_item']}**")
                        st.write(f"📈 {rec['frequency']} | Strategy: {rec['strategy']}")
                        st.write("---")
                if insights['inventory_insights']:
                    st.write("### 📦 Inventory Insights")
                    for insight in insights['inventory_insights']:
                        st.warning(f"**{insight['insight_type'].replace('_', ' ').title()}**")
                        st.write(f"📋 {insight['description']}")
                        st.write(f"🎯 Action: {insight['action']}")
                        st.write("---")