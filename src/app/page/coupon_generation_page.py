import streamlit as st
import json
from datetime import datetime
from typing import Tuple, Any, Dict, Union
from src.agents.factory import create_agent, Agent
from src.agents.schemas import OrderStandardCouponResponse, CustomerStandardCouponResponse
from src.app.utils.session import check_data_uploaded, reset_coupon_state
from pydantic_ai.messages import ModelMessage, ModelRequest, ModelResponse, UserPromptPart, TextPart

def initialize_agents() -> Tuple[Agent, Agent, Agent, Agent, Agent, Agent]:
    order_analysis_agent = create_agent(agent_type="analysis_summary", category="order")
    customer_analysis_agent = create_agent(agent_type="analysis_summary", category="customer")
    order_coupon_agent = create_agent(agent_type="standard_coupon", category="order")
    customer_coupon_agent = create_agent(agent_type="standard_coupon", category="customer")
    chat_agent = create_agent(agent_type="chat", category="chat")
    research_agent = create_agent(agent_type="research", category="research")
    return order_analysis_agent, customer_analysis_agent, order_coupon_agent, customer_coupon_agent, chat_agent, research_agent

def get_kpi_summaries() -> Tuple[Dict, Dict]:
    order_kpi_summary = st.session_state.get("order_analysis_summary")
    customer_kpi_summary = st.session_state.get("customer_analysis_summary")
    return order_kpi_summary, customer_kpi_summary

def memory_entry(header: str, content: Any) -> str:
    """Create a formatted memory entry with header and content."""
    return f"--- {header} ---\n{str(content)}"

def build_chat_memory() -> list[ModelMessage]:
    """Build comprehensive chat memory from all available context."""
    messages: list[ModelMessage] = []
    
    # Add KPI summaries to memory
    order_kpi_summary = st.session_state.get("order_analysis_summary")
    customer_kpi_summary = st.session_state.get("customer_analysis_summary")
    
    if order_kpi_summary:
        messages.append(ModelRequest(parts=[UserPromptPart(
            content=memory_entry("Order KPI Summary", str(order_kpi_summary))
        )]))
    
    if customer_kpi_summary:
        messages.append(ModelRequest(parts=[UserPromptPart(
            content=memory_entry("Customer KPI Summary", str(customer_kpi_summary))
        )]))
    
    # Add research response to memory
    research_response = st.session_state.get("research")
    if research_response:
        messages.append(ModelResponse(parts=[TextPart(
            content=memory_entry("Research Agent Response", str(research_response))
        )]))
    
    # Add analysis responses to memory
    order_analysis_response = st.session_state.get("order_analysis_response")
    customer_analysis_response = st.session_state.get("customer_analysis_response")
    
    if order_analysis_response:
        messages.append(ModelResponse(parts=[TextPart(
            content=memory_entry("Order Analysis Agent Response", str(order_analysis_response))
        )]))
    
    if customer_analysis_response:
        messages.append(ModelResponse(parts=[TextPart(
            content=memory_entry("Customer Analysis Agent Response", str(customer_analysis_response))
        )]))
    
    # Add coupon responses to memory
    coupon_responses = st.session_state.get("coupon_responses", [])
    for label, coupon_data in coupon_responses:
        messages.append(ModelResponse(parts=[TextPart(
            content=memory_entry(f"{label} Coupon Agent Response", str(coupon_data))
        )]))
    
    # Add chat history from stored messages (this preserves the conversation flow)
    chat_messages = st.session_state.get("chat_agent_messages", [])
    messages.extend(chat_messages)
    
    return messages

def format_coupon_content(content: str, section_title: str = "") -> str:
    """Format coupon content with proper line breaks and styling."""
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

def display_standard_coupons(response_data: Union[OrderStandardCouponResponse, CustomerStandardCouponResponse], agent_label: str):
    """Display standard coupons based on the agent type."""
    st.markdown(f"## 🎟️ Standard Coupon Strategy ({agent_label})")

    # Define coupon sections based on the actual Pydantic model type
    if isinstance(response_data, CustomerStandardCouponResponse):
        coupon_sections = [
            ("🎁 Joining Bonus Coupon", "joining_bonus_coupon"),
            ("🧾 Stamp Card Coupon", "stamp_card_coupon"),
            ("💌 Miss You Coupon", "miss_you_coupon"),
        ]
    elif isinstance(response_data, OrderStandardCouponResponse):
        coupon_sections = [
            ("🍱 Combo Coupon", "combo_coupon"),
            ("🎯 Threshold Coupon", "threshold_coupon"),
            ("⏰ Happy Hours Coupon", "happy_hours_coupon"),
        ]
    else:
        st.error(f"Unknown response data type: {type(response_data)}")
        return

    # Display each coupon section
    for section_title, attr_prefix in coupon_sections:
        st.markdown(f"### {section_title}")
        
        try:
            coupon_text = getattr(response_data, attr_prefix, "")
            reasoning = getattr(response_data, f"{attr_prefix}_reasoning", "")
            cost_analysis = getattr(response_data, f"{attr_prefix}_cost_analysis", "")
            
            # Display coupon content
            if coupon_text:
                formatted_coupon = format_coupon_content(coupon_text)
                st.info(formatted_coupon)
            else:
                st.warning(f"No {section_title.lower()} content available")
            
            # Display reasoning
            if reasoning:
                st.markdown("**Why:**")
                st.write(reasoning)
            
            # Display cost analysis
            if cost_analysis:
                st.markdown("**Cost Impact:**")
                with st.expander("View Cost Analysis", expanded=False):
                    st.write(cost_analysis)
                    
        except AttributeError as e:
            st.error(f"Error accessing {attr_prefix}: {e}")
            
        st.divider()

    # Combined Analysis (if present)
    try:
        combined_analysis = getattr(response_data, "combined_cost_analysis", "")
        if combined_analysis:
            st.markdown("### 💰 Combined Cost Analysis")
            with st.expander("View Combined Analysis", expanded=True):
                st.write(combined_analysis)
    except AttributeError:
        st.info("No combined cost analysis available")

def format_coupon_for_export(response_data: Union[OrderStandardCouponResponse, CustomerStandardCouponResponse], agent_label: str) -> str:
    """Format coupon data for export."""
    export_text = f"\n{'='*60}\n"
    export_text += f"STANDARD COUPON STRATEGY ({agent_label.upper()})\n"
    export_text += f"{'='*60}\n\n"
    
    # Define coupon sections based on the actual Pydantic model type
    if isinstance(response_data, CustomerStandardCouponResponse):
        coupon_sections = [
            ("🎁 Joining Bonus Coupon", "joining_bonus_coupon"),
            ("🧾 Stamp Card Coupon", "stamp_card_coupon"),
            ("💌 Miss You Coupon", "miss_you_coupon"),
        ]
    elif isinstance(response_data, OrderStandardCouponResponse):
        coupon_sections = [
            ("🍱 Combo Coupon", "combo_coupon"),
            ("🎯 Threshold Coupon", "threshold_coupon"),
            ("⏰ Happy Hours Coupon", "happy_hours_coupon"),
        ]
    else:
        return f"Unknown response data type: {type(response_data)}\n"

    # Format each coupon section
    for section_title, attr_prefix in coupon_sections:
        export_text += f"\n{section_title}\n"
        export_text += f"{'-'*40}\n"
        
        try:
            coupon_text = getattr(response_data, attr_prefix, "")
            reasoning = getattr(response_data, f"{attr_prefix}_reasoning", "")
            cost_analysis = getattr(response_data, f"{attr_prefix}_cost_analysis", "")
            
            if coupon_text:
                export_text += f"COUPON CONTENT:\n{coupon_text}\n\n"
            
            if reasoning:
                export_text += f"REASONING:\n{reasoning}\n\n"
            
            if cost_analysis:
                export_text += f"COST ANALYSIS:\n{cost_analysis}\n\n"
                
        except AttributeError as e:
            export_text += f"Error accessing {attr_prefix}: {e}\n\n"

    # Combined Analysis (if present)
    try:
        combined_analysis = getattr(response_data, "combined_cost_analysis", "")
        if combined_analysis:
            export_text += f"\n{'='*40}\n"
            export_text += f"COMBINED COST ANALYSIS\n"
            export_text += f"{'='*40}\n"
            export_text += f"{combined_analysis}\n"
    except AttributeError:
        pass
    
    return export_text

def create_chat_export() -> str:
    """Create a formatted export of all chat messages and agent responses."""
    export_content = f"""
{'='*80}
COUPON GENERATION & STRATEGY EXPORT
{'='*80}
Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Cafe Link: {st.session_state.get('cafe_link', 'Not provided')}

{'='*80}
SUMMARY DATA
{'='*80}

ORDER KPI SUMMARY:
{'-'*40}
{st.session_state.get('order_analysis_summary', 'Not available')}

CUSTOMER KPI SUMMARY:
{'-'*40}
{st.session_state.get('customer_analysis_summary', 'Not available')}

"""

    # Add research results if available
    research_response = st.session_state.get("research")
    if research_response:
        export_content += f"""
{'='*80}
RESEARCH RESULTS
{'='*80}
{research_response}

"""

    # Add analysis responses if available
    order_analysis_response = st.session_state.get("order_analysis_response")
    if order_analysis_response:
        export_content += f"""
{'='*80}
ORDER ANALYSIS RESPONSE
{'='*80}
{order_analysis_response}

"""

    customer_analysis_response = st.session_state.get("customer_analysis_response")
    if customer_analysis_response:
        export_content += f"""
{'='*80}
CUSTOMER ANALYSIS RESPONSE
{'='*80}
{customer_analysis_response}

"""

    # Add coupon strategies
    coupon_responses = st.session_state.get("coupon_responses", [])
    if coupon_responses:
        export_content += f"\n{'='*80}\nCOUPON STRATEGIES\n{'='*80}\n"
        for label, coupon_data in coupon_responses:
            export_content += format_coupon_for_export(coupon_data, label)

    # Add chat conversation
    chat_messages = st.session_state.get("coupon_messages", [])
    if chat_messages:
        export_content += f"\n{'='*80}\nCHAT CONVERSATION\n{'='*80}\n"
        
        for i, message in enumerate(chat_messages):
            if message["role"] == "user":
                export_content += f"\n[USER - {datetime.now().strftime('%H:%M:%S')}]\n"
                export_content += f"{'-'*40}\n"
                export_content += f"{message['content']}\n"
            elif message["role"] == "assistant":
                agent_type = message.get("agent_type", "assistant")
                export_content += f"\n[ASSISTANT - {agent_type.upper()} - {datetime.now().strftime('%H:%M:%S')}]\n"
                export_content += f"{'-'*40}\n"
                
                if agent_type == "chat":
                    export_content += f"{message['content']}\n"
                elif agent_type in ["standard_order", "standard_customer"]:
                    export_content += f"[Coupon strategy displayed in UI - see Coupon Strategies section above]\n"
                elif agent_type == "research":
                    export_content += f"[Research results displayed in UI - see Research Results section above]\n"

    export_content += f"\n{'='*80}\nEND OF EXPORT\n{'='*80}\n"
    
    return export_content

def render_coupon_generation_page():
    """Main function to render the coupon generation page."""
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
    
    st.header("🎯 Coupon Generation & Strategy")
    
    # Initialize agents
    (order_analysis_agent, customer_analysis_agent,
     order_coupon_agent, customer_coupon_agent, chat_agent, research_agent) = initialize_agents()
    
    # Get KPI summaries
    order_kpi_summary, customer_kpi_summary = get_kpi_summaries()

    # Reset coupon state on new data upload
    if st.session_state.get("new_data_uploaded", False):
        reset_coupon_state()

    # Download button - positioned at the top for easy access
    if st.session_state.get("coupon_messages") or st.session_state.get("coupon_responses"):
        export_data = create_chat_export()
        st.download_button(
            label="📥 Download Complete Strategy Report",
            data=export_data,
            file_name=f"coupon_strategy_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain",
            help="Download a complete report including KPIs, research, coupon strategies, and chat conversation"
        )
        st.divider()

    # Coupon generation buttons - 3 column layout
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔍 Run Research Agent"):
            with st.spinner("Running research..."):
                try:
                    cafe_link = st.session_state.get("cafe_link")
                    if cafe_link:
                        research_response = research_agent.run_sync(user_prompt=cafe_link)
                        st.session_state.research = research_response.output
                        
                        # Add to chat messages for display
                        st.session_state.coupon_messages.append({
                            "role": "assistant",
                            "agent_type": "research",
                            "content": research_response.output
                        })
                        st.success("Research completed successfully!")
                    else:
                        st.error("No cafe link found. Please provide a link for research.")
                        
                except Exception as e:
                    st.error(f"Error running research: {e}")
    
    with col2:
        if st.button("Generate Order-Based Standard Coupons"):
            with st.spinner("Generating order-based coupons..."):
                try:
                    # Get research response
                    research_response = st.session_state.get("research")
                    
                    # Run order analysis agent
                    order_analysis_response = order_analysis_agent.run_sync(user_prompt=str(order_kpi_summary))
                    st.session_state.order_analysis_response = order_analysis_response.output
                    
                    # Run order coupon agent with research, analysis, and KPI summary
                    combined_input = f"Research:\n{research_response}\n\nAnalysis:\n{order_analysis_response.output}\n\nKPI Summary:\n{order_kpi_summary}"
                    order_coupon_response = order_coupon_agent.run_sync(user_prompt=combined_input)
                    
                    # Store response
                    st.session_state.coupon_responses.append(("Order", order_coupon_response.output))
                    st.session_state.coupon_messages.append({
                        "role": "assistant",
                        "agent_type": "standard_order",
                        "response_data": order_coupon_response.output
                    })
                    st.success("Order-based coupons generated successfully!")
                    
                except Exception as e:
                    st.error(f"Error generating order coupons: {e}")
    
    with col3:
        if st.button("Generate Customer-Based Standard Coupons"):
            with st.spinner("Generating customer-based coupons..."):
                try:
                    # Get research response
                    research_response = st.session_state.get("research")
                    
                    # Run customer analysis agent
                    customer_analysis_response = customer_analysis_agent.run_sync(user_prompt=str(customer_kpi_summary))
                    st.session_state.customer_analysis_response = customer_analysis_response.output
                    
                    # Run customer coupon agent with research, analysis, and KPI summary
                    combined_input = f"Research:\n{research_response}\n\nAnalysis:\n{customer_analysis_response.output}\n\nKPI Summary:\n{customer_kpi_summary}"
                    customer_coupon_response = customer_coupon_agent.run_sync(user_prompt=combined_input)
                    
                    # Store response
                    st.session_state.coupon_responses.append(("Customer", customer_coupon_response.output))
                    st.session_state.coupon_messages.append({
                        "role": "assistant",
                        "agent_type": "standard_customer",
                        "response_data": customer_coupon_response.output
                    })
                    st.success("Customer-based coupons generated successfully!")
                    
                except Exception as e:
                    st.error(f"Error generating customer coupons: {e}")

    # Chat input for agent
    user_input = st.chat_input("Ask about coupon strategies, targeting, or effectiveness...")
    if user_input:
        with st.spinner("Thinking..."):
            try:
                # Add user message to display immediately
                st.session_state.coupon_messages.append({"role": "user", "content": user_input})
                
                # Build comprehensive memory including KPI, research, analysis, and coupon data
                messages = build_chat_memory()
                
                # Run chat agent with full memory context
                chat_response = chat_agent.run_stream(user_prompt=user_input, message_history=messages)
                
                # Extract all messages from the response (this includes the conversation flow)
                all_messages = chat_response.all_messages()
                
                # Store the new messages in our dedicated chat memory
                # We only want to store the new messages, not rebuild the entire history
                new_messages = all_messages[-2:]  # Last 2 messages (user input + assistant response)
                st.session_state.chat_agent_messages.extend(new_messages)
                
                # Add assistant response to display messages
                st.session_state.coupon_messages.append({
                    "role": "assistant",
                    "agent_type": "chat",
                    "content": chat_response.output
                })
                
            except Exception as e:
                st.error(f"Error in chat response: {e}")
                st.error(f"Error details: {str(e)}")

    # Display all messages (research, coupons and chat)
    for message in st.session_state.coupon_messages:
        if message["role"] == "assistant":
            if message.get("agent_type") == "research":
                with st.chat_message("assistant"):
                    st.markdown("## 🔍 Research Results")
                    st.markdown(message["content"])
            elif message.get("agent_type") == "standard_order":
                with st.chat_message("assistant"):
                    display_standard_coupons(message["response_data"], "Order")
            elif message.get("agent_type") == "standard_customer":
                with st.chat_message("assistant"):
                    display_standard_coupons(message["response_data"], "Customer")
            elif message.get("agent_type") == "chat":
                with st.chat_message("assistant"):
                    st.markdown(message["content"])
        elif message["role"] == "user":
            with st.chat_message("user"):
                st.write(message["content"])
    
    # Debug information (you can remove this in production)
    if st.checkbox("Show Debug Info"):
        st.write("**Order KPI Summary:**", st.session_state.get("order_analysis_summary"))
        st.write("**Customer KPI Summary:**", st.session_state.get("customer_analysis_summary"))
        st.write("**Research Response:**", st.session_state.get("research"))
        st.write("**Order Analysis Response:**", st.session_state.get("order_analysis_response"))
        st.write("**Customer Analysis Response:**", st.session_state.get("customer_analysis_response"))
        st.write("**Coupon Responses:**", st.session_state.get("coupon_responses"))
        st.write("**Chat Agent Messages Count:**", len(st.session_state.get("chat_agent_messages", [])))
        st.write("**Cafe Link:**", st.session_state.get("cafe_link"))
        
        # Show actual memory being passed to chat agent
        if st.button("Show Memory Content"):
            memory = build_chat_memory()
            st.write(f"**Memory Messages Count:** {len(memory)}")
            for i, msg in enumerate(memory):
                st.write(f"**Message {i+1}:** {type(msg).__name__}")
                if hasattr(msg, 'parts') and msg.parts:
                    content = msg.parts[0].content[:200] + "..." if len(msg.parts[0].content) > 200 else msg.parts[0].content
                    st.write(f"Content: {content}")