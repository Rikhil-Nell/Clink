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
analysis_model: OpenAIModel = OpenAIModel(model_name=MODEL_NAME_ANALYSIS, provider=OpenAIProvider(openai_client=openai_client))

MODEL_NAME_COUPON: OpenAIModelName = "gpt-4.1"
coupon_model: OpenAIModel = OpenAIModel(model_name=MODEL_NAME_COUPON, provider=OpenAIProvider(openai_client=openai_client))

# --- MCP Servers ---
run_python_server = MCPServerSSE(url="http://localhost:3001/sse")

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

# --- Prompt Definitions ---
with open("prompts/analysis_prompt.txt", "r", encoding="utf-8") as f:
    analysis_prompt = f.read()

with open("prompts/standard_coupon.txt", "r", encoding="utf-8") as f:
    standard_coupon_prompt = f.read()

# --- Agents ---

analysis_agent = Agent(
    model=analysis_model,
    model_settings=model_settings,
    system_prompt=analysis_prompt,
    mcp_servers=[run_python_server],
    instrument=True
)

standard_coupon_agent = Agent[StandardResponse](
    model=coupon_model,
    model_settings=model_settings,
    output_type=StandardResponse,
    system_prompt=standard_coupon_prompt,
    instrument=True
)

message_history: list[ModelMessage] = []

@standard_coupon_agent.instructions
def add_analysis():
    with open("order_kpis_summary.json", "r") as file:
        analysis_json = file.read()
        return f"Analysis from analysis agent: \n {analysis_json}"

async def main():
    global message_history

    print("Welcome to the Coupon Strategy Assistant! (type 'exit' to quit)\n")

    while True:
        try:
            user_prompt = input("You: ").strip()
            if not user_prompt:
                continue
            if user_prompt.lower() in ['quit', 'exit', 'bye']:
                print("Goodbye!")
                break

            results = await standard_coupon_agent.run(user_prompt=user_prompt, message_history=message_history)
            message_history = results.all_messages()

            print(
                f"\nCombo Offer: {results.output.combo_offer}\n"
                f"Reasoning: {results.output.combo_offer_reasoning}\n"
                f"Cost Analysis: {results.output.combo_offer_cost_analysis}\n\n"
                f"Threshold Offer: {results.output.threshold_offer}\n"
                f"Reasoning: {results.output.threshold_offer_reasoning}\n"
                f"Cost Analysis: {results.output.threshold_offer_cost_analysis}\n\n"
                f"Happy Hours Offer: {results.output.happy_hours_offer}\n"
                f"Reasoning: {results.output.happy_hours_offer_reasoning}\n"
                f"Cost Analysis: {results.output.happy_hours_offer_cost_analysis}\n\n"
                f"Combined Cost Analysis: {results.output.combined_cost_analysis}\n"
            )
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}\n")
            continue

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())