from typing import Union, Optional
from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel

import logfire

# Local Imports
from src.settings import settings, openai_provider, default_model_settings
from src.agents.schemas import (
    AnalysisSummaryResponse,
    OrderStandardCouponResponse,
    CustomerStandardCouponResponse,
    ProductStandardCouponResponse,
    CreativeCouponResponse
)
from src.agents.prompts import get_prompt

logfire.instrument_pydantic_ai()

# Mapping schemas to categories for standard coupons
STANDARD_COUPON_SCHEMAS = {
    "order": OrderStandardCouponResponse,
    "customer": CustomerStandardCouponResponse,
    "product": ProductStandardCouponResponse,
}

def create_agent(
    agent_type: str,
    category: Optional[str] = None
) -> Union[Agent, Agent[BaseModel]]:
    """
    Factory function to create an agent based on category and type.
    
    Args:
        agent_type: 'analysis_summary', 'standard_coupon', 'creative_coupon' or "chat".
        category: 'order', 'customer', or 'product'.
        
    Returns:
        A configured pydantic_ai Agent instance.
    """
    instructions = get_prompt(agent_type=agent_type, category=category)
    
    if agent_type == "analysis_summary":
        model = OpenAIModel(
            model_name=settings.analysis_model_name, 
            provider=openai_provider
        )
        return Agent[AnalysisSummaryResponse](
            model=model,
            model_settings=default_model_settings,
            instructions=instructions,
            output_type=AnalysisSummaryResponse,
            instrument=True
        )
        
    elif agent_type == "standard_coupon":
        output_schema = STANDARD_COUPON_SCHEMAS.get(category)
        if not output_schema:
            raise ValueError(f"No standard coupon schema defined for category: {category}")
            
        model = OpenAIModel(
            model_name=settings.coupon_model_name, 
            provider=openai_provider
        )
        return Agent[output_schema](
            model=model,
            model_settings=default_model_settings,
            instructions=instructions,
            output_type=output_schema,
            instrument=True
        )
        
    elif agent_type == "creative_coupon":
        model = OpenAIModel(
            model_name=settings.coupon_model_name, 
            provider=openai_provider
        )
        creative_prompt = get_prompt('generic', 'creative_coupon')
        return Agent[CreativeCouponResponse](
            model=model,
            model_settings=default_model_settings,
            instructions=creative_prompt,
            output_type=CreativeCouponResponse,
            instrument=True
        )
        
    elif agent_type == "generic":
        model = OpenAIModel(
            model_name=settings.chat_model_name, 
            provider=openai_provider
        )
        chat_prompt = get_prompt('generic', 'chat')
        return Agent(
            model=model,
            model_settings=default_model_settings,
            instructions=chat_prompt,
            instrument=True
        )
    else:
        raise ValueError(f"Unknown agent type: {agent_type}")