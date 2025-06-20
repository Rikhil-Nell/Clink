import streamlit as st
import asyncio
from main import Agent, chat_agent, standard_coupon_agent, creative_coupon_agent, Deps, message_history
from pathlib import Path
import time

# Set up the Streamlit app
st.set_page_config(
    page_title="Clink - Restaurant KPI Analyzer",
    page_icon="🍽️",
    layout="wide"
)

st.title("🍽️ Clink - Restaurant KPI Analysis & Coupon Generator")
st.markdown("*Data-driven coupon strategies for Indian restaurants*")

# Sidebar for quick actions and info
with st.sidebar:
    st.header("📊 Quick Actions")

    if st.button("🔍 Explore KPI Structure", use_container_width=True):
        st.session_state.auto_query = "Show me the complete KPI folder structure"
        st.session_state.selected_agent = "chat"

    if st.button("📈 Customer Analysis", use_container_width=True):
        st.session_state.auto_query = "List all files in customer_analysis and give me a brief overview"
        st.session_state.selected_agent = "chat"

    if st.button("🛒 Order Analysis", use_container_width=True):
        st.session_state.auto_query = "List all files in order_analysis and show key insights"
        st.session_state.selected_agent = "chat"

    if st.button("🍕 Product Analysis", use_container_width=True):
        st.session_state.auto_query = "Show me product_analysis structure and recent performance data"
        st.session_state.selected_agent = "chat"
        
    if st.button("📚 Generate Standard Coupon", use_container_width=True):
        st.session_state.auto_query = "Generate standard coupons to increase footfall"
        st.session_state.selected_agent = "standard"

    if st.button("🎲 Generate Creative Coupon", use_container_width=True):
        st.session_state.auto_query = "Generate creative coupon strategies for footfall increase"
        st.session_state.selected_agent = "creative"

    st.divider()

    st.header("💡 Sample Queries")
    st.markdown("""
    **Quick starts:**
    - "Generate coupons for weekend footfall"
    - "Analyze customer retention patterns"
    - "What are our peak and off-peak hours?"
    - "Show me top performing products"
    - "Create loyalty program recommendations"
    """)

    st.divider()

    st.header("⚙️ System Info")
    kpi_path = Path("./results")
    if kpi_path.exists():
        csv_files = list(kpi_path.rglob("*.csv"))
        st.success(f"✅ {len(csv_files)} KPI files detected")
    else:
        st.error("❌ KPI folder not found")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "auto_query" not in st.session_state:
    st.session_state.auto_query = None

if "selected_agent" not in st.session_state:
    st.session_state.selected_agent = "chat"

# Welcome message
if not st.session_state.messages:
    welcome_msg = {
        "role": "assistant",
        "content": "👋 **Welcome to Clink!** I'm here to help you analyze your restaurant data and generate effective coupon strategies. Use the sidebar buttons to get started or ask me directly about your KPIs!",
        "agent_type": "chat"
    }
    st.session_state.messages.append(welcome_msg)

def format_coupon_content(content, section_title=""):
    """Clean and format coupon content for better display"""
    if not content:
        return ""
    
    # Remove extra whitespace and clean up formatting
    content = content.strip()
    
    # Split into lines and clean each line
    lines = content.split('\n')
    cleaned_lines = []
    
    for line in lines:
        line = line.strip()
        if line:
            # Remove multiple asterisks and clean up markdown
            line = line.replace('**Why:**', '\n**Why:**')
            line = line.replace('**Cost Impact:**', '\n**Cost Impact:**')
            cleaned_lines.append(line)
    
    return '\n'.join(cleaned_lines)

def display_coupon_response(response_data):
    """Display coupon response in a structured format"""
    
    # Joining Bonus Coupon
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
    
    # Stamp Card Coupon
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
    
    # Miss You Coupon
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
    
    # Combined Analysis
    if response_data.combined_cost_analysis:
        st.markdown("### 💰 Combined Cost Analysis")
        with st.expander("View Combined Analysis", expanded=True):
            st.write(response_data.combined_cost_analysis)

def display_creative_coupon_response(response_data):
    """Display creative coupon response in a structured format"""
    
    st.markdown("### 🎟️ Creative Coupon Recommendations")
    if response_data.coupons:
        st.markdown(response_data.coupons)
    
    if response_data.reasoning:
        st.markdown("### 🧠 Strategic Reasoning")
        with st.expander("View Strategic Reasoning", expanded=True):
            st.write(response_data.reasoning)
    
    if response_data.cost:
        st.markdown("### 💰 Cost & Impact Analysis")
        with st.expander("View Cost Analysis", expanded=False):
            st.write(response_data.cost)
    
    if response_data.conversation:
        st.markdown("### 💬 Additional Insights")
        st.write(response_data.conversation)

def display_messages():
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if message["role"] == "assistant":
                agent_type = message.get("agent_type", "chat")
                
                if agent_type == "standard" and hasattr(message.get("response_data"), 'joining_bonus_coupon'):
                    st.markdown("## 🎟️ Standard Coupon Strategy")
                    display_coupon_response(message["response_data"])
                    
                    # Download button
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
                    
                elif agent_type == "creative" and hasattr(message.get("response_data"), 'coupons'):
                    st.markdown("## 🎲 Creative Coupon Strategy")
                    display_creative_coupon_response(message["response_data"])
                    
                    # Download button
                    full_content = f"""
# Creative Coupon Strategy

## 🎟️ Coupon Recommendations
{message["response_data"].coupons}

## 🧠 Strategic Reasoning
{message["response_data"].reasoning}

## 💰 Cost & Impact Analysis
{message["response_data"].cost}

## 💬 Additional Insights
{message["response_data"].conversation}
"""
                    st.download_button(
                        label="📥 Download Strategy",
                        data=full_content,
                        file_name=f"creative_coupon_strategy_{int(time.time())}.txt",
                        mime="text/plain"
                    )
                else:
                    # Regular chat response
                    st.markdown(message["content"])
            else:
                st.write(message["content"])

async def get_bot_response(user_input: str):
    global message_history

    try:
        with st.spinner("🤖 Clink is analyzing your data..."):
            
            active_agent: Agent
            if st.session_state.selected_agent == "standard":
                active_agent = standard_coupon_agent
            elif st.session_state.selected_agent == "creative":
                active_agent = creative_coupon_agent
            else:
                active_agent = chat_agent

            response = await active_agent.run(
                user_prompt=user_input,
                message_history=message_history,
                deps=Deps(kpi_base_folder="./results")
            )

            message_history = response.all_messages()
            
            return response, st.session_state.selected_agent

    except Exception as e:
        error_response = type('ErrorResponse', (), {})()
        error_response.output = f"❌ **Error:** {str(e)}\n\nPlease try again or check your data."
        return error_response, "error"

# Main chat interface
col1, col2 = st.columns([3, 1])

with col1:
    display_messages()

with col2:
    if st.session_state.messages:
        st.markdown("### 📊 Chat Stats")
        user_msgs = [m for m in st.session_state.messages if m["role"] == "user"]
        st.metric("Queries Made", len(user_msgs))
        
        # Show agent usage
        agent_counts = {}
        for msg in st.session_state.messages:
            if msg["role"] == "assistant":
                agent_type = msg.get("agent_type", "chat")
                agent_counts[agent_type] = agent_counts.get(agent_type, 0) + 1
        
        if agent_counts:
            st.markdown("### 🤖 Agent Usage")
            for agent, count in agent_counts.items():
                st.metric(f"{agent.title()} Agent", count)

# Handle auto-query from sidebar
if st.session_state.auto_query:
    user_input = st.session_state.auto_query
    st.session_state.auto_query = None

    st.session_state.messages.append({"role": "user", "content": user_input})
    
    response, agent_type = asyncio.run(get_bot_response(user_input))
    
    if agent_type == "standard":
        st.session_state.messages.append({
            "role": "assistant", 
            "content": "Standard coupon strategy generated successfully!",
            "response_data": response.output,
            "agent_type": "standard"
        })
    elif agent_type == "creative":
        st.session_state.messages.append({
            "role": "assistant", 
            "content": "Creative coupon strategy generated successfully!",
            "response_data": response.output,
            "agent_type": "creative"
        })
    else:
        st.session_state.messages.append({
            "role": "assistant", 
            "content": response.output if hasattr(response, 'output') else str(response),
            "agent_type": "chat"
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
    
    if agent_type == "error":
        st.session_state.messages.append({
            "role": "assistant", 
            "content": response.output,
            "agent_type": "chat"
        })
    else:
        st.session_state.messages.append({
            "role": "assistant", 
            "content": response.output if hasattr(response, 'output') else str(response),
            "agent_type": "chat"
        })
    
    with st.chat_message("assistant"):
        st.markdown(response.output if hasattr(response, 'output') else str(response))