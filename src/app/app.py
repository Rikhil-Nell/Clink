import streamlit as st
import pandas as pd

# 1. Import custom modules
from src.app.utils.styling import apply_custom_styles
from src.app.utils.session import initialize_session_state
from src.app.page.data_upload_page import render_data_upload_page
from src.app.page.kpi_analysis_page import render_kpi_analysis_page
from src.app.page.coupon_generation_page import render_coupon_generation_page

def main():    # 2. Streamlit page config and styling
    st.set_page_config(
        page_title="Clink - Restaurant Analytics",
        page_icon="🍽️",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    apply_custom_styles()

    # 3. Session state initialization and validation
    initialize_session_state()

    # 4. Navigation
    st.sidebar.markdown("### 🧭 Navigation")
    page = st.sidebar.radio(
        "Choose your journey:",
        ["📂 Data Upload", "📈 KPI Analysis", "🎯 Coupon Generation"],
        help="Navigate through different sections of the app"
    )

    # 5. Page Routing
    if page == "📂 Data Upload":
        # Handles file upload, validation, and overview display
        render_data_upload_page()

    elif page == "📈 KPI Analysis":
        # Handles KPI summarization and visualization
        render_kpi_analysis_page()

    elif page == "🎯 Coupon Generation":
        # Handles coupon strategy preview (future: agentic logic)
        render_coupon_generation_page()

    # 6. Footer (optional, can be moved to a utils/footer.py if desired)
    # st.markdown("---")
    # st.markdown("""
    #     <div style="text-align: center; color: #666; padding: 1rem;">
    #         <p>Made with ❤️ for Indian restaurants | Powered by data-driven insights</p>
    #     </div>
    # """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()