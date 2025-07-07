import streamlit as st

def apply_custom_styles():
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