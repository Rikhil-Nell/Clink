from pydantic_ai import Agent
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.models.openai import OpenAIModel, OpenAIModelName, OpenAIModelSettings
from pydantic_ai.messages import ModelMessage
from pydantic_ai.mcp import MCPServerSSE
from openai import AsyncOpenAI
from pydantic import BaseModel, Field
import logfire
from settings import Settings

# --- Configuration ---
settings = Settings()
logfire.configure(token=settings.logfire_key)
logfire.instrument_pydantic_ai()

openai_client = AsyncOpenAI(api_key=settings.openai_api_key)
logfire.instrument_openai(openai_client=openai_client)

# Model Settings
model_settings = OpenAIModelSettings(
    temperature=0.1,
    top_p=0.95
)

# Define Models
MODEL_NAME_ANALYSIS: OpenAIModelName = "gpt-4.1"
analysis_summary_model: OpenAIModel = OpenAIModel(model_name=MODEL_NAME_ANALYSIS, provider=OpenAIProvider(openai_client=openai_client))

MODEL_NAME_COUPON: OpenAIModelName = "gpt-4.1"
coupon_model: OpenAIModel = OpenAIModel(model_name=MODEL_NAME_COUPON, provider=OpenAIProvider(openai_client=openai_client))

# --- MCP Servers ---
run_python_server = MCPServerSSE(url="http://localhost:3001/sse")

# --- Response Models ---

class CustomerStandardResponse(BaseModel):

    # joining bonus coupon
    joining_bonus_coupon : str = Field(description="Best Joining Bonus Coupon to bring more footfall to the stores")
    joining_bonus_coupon_reasoning : str = Field(description="Best Joining Bonus Coupon to bring more footfall to the stores")
    joining_bonus_coupon_cost_analysis : str = Field(description="Analyze the cost of the joining bonus coupon, like 'How many orders/sales would increase?','How much discount they are going to spend?'")
    
    # stamp card coupon
    stamp_card_coupon : str = Field(description="Best Stamp Card Coupon to bring more footfall to the stores")
    stamp_card_coupon_reasoning : str = Field(description="Reasoning behind the suggested stamp card coupon")
    stamp_card_coupon_cost_analysis : str = Field(description="Analyze the cost of the stamp card coupon, like 'How many orders/sales would increase?','How much discount they are going to spend?'")

    # miss you coupon
    miss_you_coupon : str = Field(description="Best Miss You Coupon to bring more footfall to the stores")
    miss_you_coupon_reasoning : str = Field(description="Reasoning behind the suggested miss you coupon")
    miss_you_coupon_cost_analysis : str = Field(description="Analyze the cost of the miss you coupon, like 'How many orders/sales would increase?','How much discount they are going to spend?'")

    # combined cost analysis
    combined_cost_analysis : str = Field(description="Analyze the cost of all the coupons, like 'How many orders/sales would increase?','How much discount they are going to spend?'")


class ProductStandardResponse(BaseModel):
    pass


class StandardResponse(BaseModel):
    # Combo Offer
    combo_offer: str = Field(description="Best Combo Offer strategy to increase basket size by combining popular items.")
    combo_offer_reasoning: str = Field(description="Why this combo offer makes sense based on order patterns.")
    combo_offer_cost_analysis: str = Field(description="Financial projection: redemption, uplift, break-even for the combo offer.")

    # Threshold Offer
    threshold_offer: str = Field(description="Best Threshold Offer strategy to increase average order value.")
    threshold_offer_reasoning: str = Field(description="Why this threshold offer works based on bill value distribution.")
    threshold_offer_cost_analysis: str = Field(description="Financial projection: redemption, uplift, break-even for the threshold offer.")

    # Happy Hours Offer
    happy_hours_offer: str = Field(description="Best Happy Hours or Slow Day offer to boost low traffic periods.")
    happy_hours_offer_reasoning: str = Field(description="Why this timing-based offer is optimal based on order time patterns.")
    happy_hours_offer_cost_analysis: str = Field(description="Financial projection: redemption, uplift, break-even for the happy hours offer.")

    # Combined analysis
    combined_cost_analysis: str = Field(description="Overall impact: total expected uplift, ROI timeline, risk factors for all offers combined.")

class CreativeResponse(BaseModel):

    coupons: str = Field(description="Best Coupons to bring more footfall to the stores")
    reasoning: str = Field(description="Reasoning behind the suggested coupons")
    cost: str = Field(description="How many orders/sales would increase. How much discount they are going to spend")
    conversation : str = Field(description="Use this field to respond normally if none other fields fit for the answer")


# --- Prompt Definitions ---
with open("src/prompts/analysis summary prompts/order_analysis_summary_prompt.txt", "r", encoding="utf-8") as f:
    order_analysis_summary_prompt = f.read()

with open("src/prompts/standard coupon prompts/order_standard_coupon.txt", "r", encoding="utf-8") as f:
    order_standard_coupon_prompt = f.read()

# --- Agents ---

order_analysis_summary_agent = Agent(
    model=analysis_summary_model,
    model_settings=model_settings,
    system_prompt=order_analysis_summary_prompt,
    mcp_servers=[run_python_server],
    instrument=True
)

order_standard_coupon_agent = Agent[StandardResponse](
    model=coupon_model,
    model_settings=model_settings,
    output_type=StandardResponse,
    system_prompt=order_standard_coupon_prompt,
    instrument=True
)

message_history: list[ModelMessage] = []

@order_standard_coupon_agent.instructions
def add_analysis():
    with open("order_kpis_summary.json", "r") as file:
        analysis_json = file.read()
        return f"Generated KPI Analysis: \n {analysis_json}"
