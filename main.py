from pydantic_ai import Agent
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.models.openai import OpenAIModel, OpenAIModelName, OpenAIModelSettings
from pydantic_ai.messages import ModelMessage
from openai import AsyncOpenAI
from pydantic import BaseModel, Field
import logfire
from tools import *
from settings import Settings
import asyncio

# --- Configuration ---
settings = Settings()
logfire.configure(token=settings.logfire_key)
logfire.instrument_pydantic_ai()

openai_client = AsyncOpenAI(api_key=settings.openai_api_key)
logfire.instrument_openai(openai_client=openai_client)

@dataclass
class Deps:
    kpi_base_folder: str

# Model Settings
model_settings = OpenAIModelSettings(
    temperature=0.1,
    top_p=0.95
)

# Define Models
MODEL_NAME_COUPON: OpenAIModelName = "gpt-4.1"
coupon_model: OpenAIModel = OpenAIModel(model_name=MODEL_NAME_COUPON, provider=OpenAIProvider(openai_client=openai_client))

MODEL_NAME_CHAT: OpenAIModelName = "gpt-4.1-mini"
chat_model: OpenAIModel = OpenAIModel(model_name=MODEL_NAME_CHAT, provider=OpenAIProvider(openai_client=openai_client))


# --- Shared Tools ---
tools = [
    explore_kpi_structure,
    list_kpi_files_by_category,
    load_kpi_file,
    search_kpi_files,
    analyze_time_series_kpi
]


# --- Response Models ---
class StandardResponse(BaseModel):
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

class CreativeResponse(BaseModel):
    coupons: str = Field(description="Best Coupons to bring more footfall to the stores")
    reasoning: str = Field(description="Reasoning behind the suggested coupons")
    cost: str = Field(description="How many orders/sales would increase. How much discount they are going to spend")
    conversation : str = Field(description="Use this field to respond normally if none other fields fit for the answer")


# --- Prompt Definitions ---
with open("prompts/standard_coupon.txt", "r", encoding="utf-8") as f:
    standard_coupon_prompt = f.read()

with open("prompts/creative_coupon.txt", "r", encoding="utf-8") as f:
    creative_coupon_prompt = f.read()

with open("prompts/chat.txt", "r", encoding="utf-8") as f:
    chat_prompt = f.read()


# --- Agents ---
standard_coupon_agent = Agent[Deps, StandardResponse](
    model=coupon_model,
    model_settings=model_settings,
    output_type=StandardResponse,
    system_prompt=standard_coupon_prompt,
    tools=tools,
    deps_type=Deps,
    instrument=True
)

creative_coupon_agent = Agent(
    model=coupon_model,
    model_settings=model_settings,
    system_prompt=creative_coupon_prompt,
    output_type=CreativeResponse,
    tools=tools,
    deps_type=Deps,
    instrument=True
)

chat_agent = Agent(
    model=chat_model,
    model_settings=model_settings,
    system_prompt=chat_prompt,
    intstrument=True
)

message_history: list[ModelMessage] = []

if __name__ == "__main__":

    deps = Deps(kpi_base_folder="./results")  # Set your KPI base folder path
    
    while True:
        user_prompt = input("You: ")
        if user_prompt == "exit":
            break
        
        result = asyncio.run(chat_agent.run(user_prompt=user_prompt, message_history=message_history, deps=deps))
        print("Clink: " + str(result.output))

        message_history = result.all_messages()