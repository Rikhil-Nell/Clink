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
                    st.markdown(cost_analysis)
                    
        except AttributeError as e:
            st.error(f"Error accessing {attr_prefix}: {e}")
            
        st.divider()

    # Combined Analysis (if present)
    try:
        combined_analysis = getattr(response_data, "combined_cost_analysis", "")
        if combined_analysis:
            st.markdown("### 💰 Combined Cost Analysis")
            with st.expander("View Combined Analysis", expanded=True):
                st.markdown(combined_analysis)
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

def format_json_for_markdown(data):
    """Format JSON data as a properly indented code block."""
    if data is None:
        return "```json\n\"Not available\"\n```"
    
    if isinstance(data, str):
        try:
            # Try to parse if it's a JSON string
            data = json.loads(data)
        except:
            # If it's not valid JSON, wrap it as a string
            return f"```json\n{json.dumps(data, indent=2)}\n```"
    
    # Format with proper indentation
    formatted_json = json.dumps(data, indent=2, ensure_ascii=False)
    return f"```json\n{formatted_json}\n```"

def create_chat_export() -> str:
    """Create a formatted markdown export of all chat messages and agent responses."""
    export_content = f"""# 🎯 Coupon Generation & Strategy Report

**Generated on:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Cafe Link:** {st.session_state.get('cafe_link', 'Not provided')}

---

## 📊 Summary Data

### Order KPI Summary
{format_json_for_markdown(st.session_state.get('order_analysis_summary', 'Not available'))}

### Customer KPI Summary
{format_json_for_markdown(st.session_state.get('customer_analysis_summary', 'Not available'))}

---
"""

    # Add research results if available
    research_response = st.session_state.get("research")
    if research_response:
        export_content += f"""## 🔍 Research Results

{research_response}

---
"""

    # Add analysis responses if available
    order_analysis_response = st.session_state.get("order_analysis_response")
    if order_analysis_response:
        export_content += f"""## 📈 Order Analysis Response

{order_analysis_response.summary}\n
{order_analysis_response.recommendations}

---
"""

    customer_analysis_response = st.session_state.get("customer_analysis_response")
    if customer_analysis_response:
        export_content += f"""## 👥 Customer Analysis Response

{customer_analysis_response.summary}\n
{customer_analysis_response.recommendations}

---
"""

    # Add coupon strategies
    coupon_responses = st.session_state.get("coupon_responses", [])
    if coupon_responses:
        export_content += f"""## 🎟️ Coupon Strategies

"""
        for label, coupon_data in coupon_responses:
            export_content += format_coupon_for_export_markdown(coupon_data, label)

    # Add chat conversation
    chat_messages = st.session_state.get("coupon_messages", [])
    if chat_messages:
        export_content += f"""## 💬 Chat Conversation

"""
        
        for i, message in enumerate(chat_messages):
            timestamp = datetime.now().strftime('%H:%M:%S')
            
            if message["role"] == "user":
                export_content += f"""### 👤 User - {timestamp}

{message['content']}

"""
            elif message["role"] == "assistant":
                agent_type = message.get("agent_type", "assistant")
                
                if agent_type == "chat":
                    export_content += f"""### 🤖 Assistant (Chat) - {timestamp}

{message['content']}

"""
                elif agent_type == "research":
                    export_content += f"""### 🔍 Assistant (Research) - {timestamp}

*Research results displayed above in the Research Results section*

"""
                elif agent_type in ["standard_order", "standard_customer"]:
                    export_content += f"""### 🎟️ Assistant ({agent_type.replace('standard_', '').title()} Coupons) - {timestamp}

*Coupon strategy displayed above in the Coupon Strategies section*

"""

    export_content += f"""---

## 📋 Export Information

- **Export Format:** Markdown
- **Total Chat Messages:** {len(chat_messages)}
- **Total Coupon Strategies:** {len(coupon_responses)}
- **Research Included:** {'Yes' if research_response else 'No'}
- **Analysis Included:** {'Yes' if order_analysis_response or customer_analysis_response else 'No'}

---

*End of Report*
"""
    
    return export_content

def format_coupon_for_export_markdown(response_data, agent_label: str) -> str:
    """Format coupon data for markdown export."""
    from src.agents.schemas import OrderStandardCouponResponse, CustomerStandardCouponResponse
    
    export_text = f"""### 🎟️ {agent_label} Coupon Strategy

"""
    
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
        return f"**Error:** Unknown response data type: {type(response_data)}\n\n"

    # Format each coupon section
    for section_title, attr_prefix in coupon_sections:
        export_text += f"""#### {section_title}

"""
        
        try:
            coupon_text = getattr(response_data, attr_prefix, "")
            reasoning = getattr(response_data, f"{attr_prefix}_reasoning", "")
            cost_analysis = getattr(response_data, f"{attr_prefix}_cost_analysis", "")
            
            if coupon_text:
                export_text += f"""**Coupon Content:**
> {coupon_text.replace(chr(10), chr(10) + '> ')}

"""
            
            if reasoning:
                export_text += f"""**Reasoning:**
{reasoning}

"""
            
            if cost_analysis:
                export_text += f"""**Cost Analysis:**
<details>
<summary>View Cost Analysis</summary>

{cost_analysis}

</details>

"""
                
        except AttributeError as e:
            export_text += f"**Error accessing {attr_prefix}:** {e}\n\n"

    # Combined Analysis (if present)
    try:
        combined_analysis = getattr(response_data, "combined_cost_analysis", "")
        if combined_analysis:
            export_text += f"""#### 💰 Combined Cost Analysis

<details>
<summary>View Combined Analysis</summary>

{combined_analysis}

</details>

"""
    except AttributeError:
        pass
    
    export_text += "---\n\n"
    return export_text

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

    # SIDEBAR CONTROLS
    with st.sidebar:
        st.header("🎯 Control Panel")
        
        # Initial Setup Section
        st.subheader("⚙️ Initial Setup")
        
        # Research Agent
        if st.button("🔍 Run Research Agent", use_container_width=True):
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
                        st.success("Research completed!")
                        st.rerun()
                    else:
                        st.error("No cafe link found. Please provide a link for research.")
                        
                except Exception as e:
                    st.error(f"Error running research: {e}")
        
        # Analysis Agents
        if st.button("📊 Run Analysis Agents", use_container_width=True):
            with st.spinner("Running analysis for both order and customer data..."):
                try:
                    # Run order analysis agent
                    order_analysis_response = order_analysis_agent.run_sync(user_prompt=str(order_kpi_summary))
                    st.session_state.order_analysis_response = order_analysis_response.output
                    
                    # Run customer analysis agent
                    customer_analysis_response = customer_analysis_agent.run_sync(user_prompt=str(customer_kpi_summary))
                    st.session_state.customer_analysis_response = customer_analysis_response.output
                    
                    st.success("Analysis completed for both order and customer data!")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Error running analysis: {e}")
        
        st.divider()
        
        # Coupon Generation Section
        st.subheader("🎟️ Coupon Generation")
        
        if st.button("Generate Order-Based Coupons", use_container_width=True):
            with st.spinner("Generating order-based coupons..."):
                try:
                    # Get stored responses
                    research_response = st.session_state.get("research", "")
                    order_analysis_response = st.session_state.get("order_analysis_response", "")
                    
                    # Run order coupon agent with stored research and analysis
                    combined_input = f"Research:\n{research_response}\n\nAnalysis:\n{order_analysis_response}\n\nKPI Summary:\n{order_kpi_summary}"
                    order_coupon_response = order_coupon_agent.run_sync(user_prompt=combined_input)
                    
                    # Store response
                    st.session_state.coupon_responses.append(("Order", order_coupon_response.output))
                    st.session_state.coupon_messages.append({
                        "role": "assistant",
                        "agent_type": "standard_order",
                        "response_data": order_coupon_response.output
                    })
                    st.success("Order coupons generated!")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Error generating order coupons: {e}")
        
        if st.button("Generate Customer-Based Coupons", use_container_width=True):
            with st.spinner("Generating customer-based coupons..."):
                try:
                    # Get stored responses
                    research_response = st.session_state.get("research", "")
                    customer_analysis_response = st.session_state.get("customer_analysis_response", "")
                    
                    # Run customer coupon agent with stored research and analysis
                    combined_input = f"Research:\n{research_response}\n\nAnalysis:\n{customer_analysis_response}\n\nKPI Summary:\n{customer_kpi_summary}"
                    customer_coupon_response = customer_coupon_agent.run_sync(user_prompt=combined_input)
                    
                    # Store response
                    st.session_state.coupon_responses.append(("Customer", customer_coupon_response.output))
                    st.session_state.coupon_messages.append({
                        "role": "assistant",
                        "agent_type": "standard_customer",
                        "response_data": customer_coupon_response.output
                    })
                    st.success("Customer coupons generated!")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Error generating customer coupons: {e}")
        
        st.divider()
        
        # Export Section
        st.subheader("📥 Export")
        if st.session_state.get("coupon_messages") or st.session_state.get("coupon_responses"):
            export_data = create_chat_export()
            st.download_button(
                label="📥 Download Strategy Report",
                data=export_data,
                file_name=f"coupon_strategy_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                mime="text/plain",
                help="Download complete report with KPIs, research, strategies, and chat",
                use_container_width=True
            )
        else:
            st.info("💡 Generate some content first to enable download")
        
        st.divider()
        
        # Debug Section
        st.subheader("🔧 Debug")
        if st.button("Show Debug Info", use_container_width=True):
            st.session_state.show_debug = not st.session_state.get("show_debug", False)

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
                chat_response = chat_agent.run_sync(user_prompt=user_input, message_history=messages)
                
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