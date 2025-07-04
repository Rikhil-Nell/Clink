import streamlit as st
import asyncio
from main import Agent, chat_agent, standard_coupon_agent, message_history
from pathlib import Path
import time

# Set up the Streamlit app
st.set_page_config(
    page_title="Clink",
    page_icon="🍽️",
    layout="wide"
)

st.title("🍽️ Clink - *Data-driven coupon strategies for Indian restaurants*")

# Sidebar navigation
page = st.sidebar.radio("Navigate", ["Coupon Settings", "Chatbot"])

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "coupon_settings" not in st.session_state:
    st.session_state.coupon_settings = {}

if "auto_query" not in st.session_state:
    st.session_state.auto_query = None

if "selected_agent" not in st.session_state:
    st.session_state.selected_agent = "chat"

# Coupon Settings Form
if page == "Coupon Settings":
    st.header("📝 Configure Your Coupon Strategy Preferences")

    # --- Profitability and customer definitions ---
    st.markdown("#### 📊 Business Baselines")
    profit_margin = st.number_input(
        "What is your average profit margin on orders? (as a decimal, e.g., 0.25 for 25%)",
        min_value=0.0, max_value=1.0, step=0.01, value=0.25
    )
    dormancy_threshold_days = st.number_input(
        "After how many days without ordering do you consider a customer 'dormant'?",
        min_value=1, step=1, value=60
    )
    new_customer_threshold_days = st.number_input(
        "For how many days after their first order is someone a 'new customer'?",
        min_value=1, step=1, value=30
    )

    st.divider()

    # --- Discount limits ---
    st.markdown("#### 💸 Discount Preferences")
    max_discount = st.text_input(
        "What is the **maximum discount** (₹ or %) you're comfortable giving per order?"
    )
    overall_discount_pct = st.number_input(
        "What is your **overall target discount percentage** on all orders?",
        min_value=0.0, max_value=100.0, step=0.5
    )
    incentive_type = st.radio(
        "Do you prefer **threshold incentives** (e.g., 'Spend ₹250, save ₹2') or **tiered incentives** (e.g., 'Spend ₹300, save ₹10')?",
        ["Threshold (Spend ₹250, save ₹2)", "Tiered (Spend ₹300, save ₹10)"]
    )

    st.divider()

    # --- Exclusions ---
    st.markdown("#### 🚫 Exclusions and Restrictions")
    exclusions_daypart = st.text_input(
        "Are there specific **items or times** where discounting is off-limits? (e.g., alcohol, Fridays after 7 pm)"
    )
    exclusions_categories = st.text_input(
        "Are there any **menu categories excluded from discounting**? (e.g., alcohol, limited-supply dishes)"
    )

    # --- Save button ---
    if st.button("💾 Save Settings"):
        st.session_state.coupon_settings = {
            "profit_margin": profit_margin,
            "dormancy_threshold_days": dormancy_threshold_days,
            "new_customer_threshold_days": new_customer_threshold_days,
            "max_discount": max_discount,
            "overall_discount_pct": overall_discount_pct,
            "incentive_type": incentive_type,
            "exclusions_daypart": exclusions_daypart,
            "exclusions_categories": exclusions_categories
        }
        st.success("✅ Settings saved! You can now switch to the Chatbot.")
    st.stop()


# Sidebar quick actions inside chatbot
with st.sidebar:
    if st.button("🍕 Product Analysis", use_container_width=True):
        st.session_state.auto_query = "Show me product_analysis structure and recent performance data"
        st.session_state.selected_agent = "chat"
        
    if st.button("📚 Generate Standard Coupon", use_container_width=True):
        st.session_state.auto_query = "Generate standard coupons to increase footfall"
        st.session_state.selected_agent = "standard"

# Welcome message
if not st.session_state.messages:
    welcome_msg = {
        "role": "assistant",
        "content": "👋 **Welcome to Clink!** I'm here to help you analyze your restaurant data and generate effective coupon strategies. Use the sidebar buttons to get started or ask me directly about your KPIs!",
        "agent_type": "chat"
    }
    st.session_state.messages.append(welcome_msg)

# ========== UTILITIES FOR DISPLAY ==========
def format_coupon_content(content, section_title=""):
    if not content:
        return ""
    content = content.strip()
    lines = content.split('\n')
    cleaned_lines = []
    for line in lines:
        line = line.strip()
        if line:
            line = line.replace('**Why:**', '\n**Why:**')
            line = line.replace('**Cost Impact:**', '\n**Cost Impact:**')
            cleaned_lines.append(line)
    return '\n'.join(cleaned_lines)

def display_coupon_response(response_data):
    st.markdown("### 🎁 Joining Bonus Coupon")
    coupon_text = format_coupon_content(response_data.joining_bonus_coupon)
    if coupon_text:
        st.info(coupon_text)
    if response_data.joining_bonus_coupon_reasoning:
        st.markdown("**Why:**")
        st.write(response_data.joining_bonus_coupon_reasoning)
    if response_data.joining_bonus_coupon_cost_analysis:
        st.markdown("**Cost Impact:**")
        with st.expander("View Cost Analysis", expanded=False):
            st.write(response_data.joining_bonus_coupon_cost_analysis)
    st.divider()

    st.markdown("### 🧾 Stamp Card Coupon")
    coupon_text = format_coupon_content(response_data.stamp_card_coupon)
    if coupon_text:
        st.info(coupon_text)
    if response_data.stamp_card_coupon_reasoning:
        st.markdown("**Why:**")
        st.write(response_data.stamp_card_coupon_reasoning)
    if response_data.stamp_card_coupon_cost_analysis:
        st.markdown("**Cost Impact:**")
        with st.expander("View Cost Analysis", expanded=False):
            st.write(response_data.stamp_card_coupon_cost_analysis)
    st.divider()

    st.markdown("### 💌 Miss You Coupon")
    coupon_text = format_coupon_content(response_data.miss_you_coupon)
    if coupon_text:
        st.info(coupon_text)
    if response_data.miss_you_coupon_reasoning:
        st.markdown("**Why:**")
        st.write(response_data.miss_you_coupon_reasoning)
    if response_data.miss_you_coupon_cost_analysis:
        st.markdown("**Cost Impact:**")
        with st.expander("View Cost Analysis", expanded=False):
            st.write(response_data.miss_you_coupon_cost_analysis)
    st.divider()

    if response_data.combined_cost_analysis:
        st.markdown("### 💰 Combined Cost Analysis")
        with st.expander("View Combined Analysis", expanded=True):
            st.write(response_data.combined_cost_analysis)

def display_messages():
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if message["role"] == "assistant":
                agent_type = message.get("agent_type", "chat")
                if agent_type == "standard" and hasattr(message.get("response_data"), 'joining_bonus_coupon'):
                    st.markdown("## 🎟️ Standard Coupon Strategy")
                    display_coupon_response(message["response_data"])
                    full_content = f"""
# Standard Coupon Strategy

## 🎁 Joining Bonus Coupon
{message["response_data"].joining_bonus_coupon}

Why: {message["response_data"].joining_bonus_coupon_reasoning}

Cost Impact: {message["response_data"].joining_bonus_coupon_cost_analysis}

## 🧾 Stamp Card Coupon
{message["response_data"].stamp_card_coupon}

Why: {message["response_data"].stamp_card_coupon_reasoning}

Cost Impact: {message["response_data"].stamp_card_coupon_cost_analysis}

## 💌 Miss You Coupon
{message["response_data"].miss_you_coupon}

Why: {message["response_data"].miss_you_coupon_reasoning}

Cost Impact: {message["response_data"].miss_you_coupon_cost_analysis}

## 💰 Combined Cost Analysis
{message["response_data"].combined_cost_analysis}
"""
                    st.download_button(
                        label="📥 Download Strategy",
                        data=full_content,
                        file_name=f"standard_coupon_strategy_{int(time.time())}.txt",
                        mime="text/plain"
                    )
                else:
                    st.markdown(message["content"])
            else:
                st.write(message["content"])

# ========== BACKEND LOGIC ==========
async def get_bot_response(user_input: str):
    global message_history
    try:
        with st.spinner("🤖 Clink is analyzing your data..."):
            active_agent: Agent
            if st.session_state.selected_agent == "standard":
                active_agent = standard_coupon_agent
            else:
                active_agent = chat_agent

            response = await active_agent.run(
                user_prompt=user_input,
                message_history=message_history
            )
            message_history = response.all_messages()
            return response, st.session_state.selected_agent
    except Exception as e:
        error_response = type('ErrorResponse', (), {})()
        error_response.output = f"❌ **Error:** {str(e)}\n\nPlease try again or check your data."
        return error_response, "error"

# ========== MAIN CHAT INTERFACE ==========
col1, col2 = st.columns([3, 1])

with col1:
    display_messages()

# Handle auto-query
if st.session_state.auto_query:
    user_input = st.session_state.auto_query
    st.session_state.auto_query = None
    st.session_state.messages.append({"role": "user", "content": user_input})
    response, agent_type = asyncio.run(get_bot_response(user_input))
    st.session_state.messages.append({
        "role": "assistant", 
        "content": "Standard coupon strategy generated successfully!",
        "response_data": response.output,
        "agent_type": "standard"
    })
    st.rerun()

# Handle direct user input
user_input = st.chat_input("Ask Clink about your restaurant data...")
if user_input:
    st.session_state.selected_agent = "chat"
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)
    response, agent_type = asyncio.run(get_bot_response(user_input))
    st.session_state.messages.append({
        "role": "assistant", 
        "content": response.output if hasattr(response, 'output') else str(response),
        "agent_type": "chat"
    })
    with st.chat_message("assistant"):
        st.markdown(response.output if hasattr(response, 'output') else str(response))
