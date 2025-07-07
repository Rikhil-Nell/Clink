from typing import Type, Union
from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
import logfire

# Local Imports
from config import settings, openai_provider, default_model_settings
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
    category: str
) -> Union[Agent, Agent[BaseModel]]:
    """
    Factory function to create an agent based on category and type.
    
    Args:
        agent_type: 'analysis_summary', 'standard_coupon', or 'creative_coupon'.
        category: 'order', 'customer', or 'product'.
        
    Returns:
        A configured pydantic_ai Agent instance.
    """
    system_prompt = get_prompt(agent_type=agent_type, category=category)
    
    if agent_type == "analysis_summary":
        model = OpenAIModel(
            model_name=settings.analysis_model_name, 
            provider=openai_provider
        )
        return Agent[AnalysisSummaryResponse](
            model=model,
            model_settings=default_model_settings,
            system_prompt=system_prompt,
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
            system_prompt=system_prompt,
            output_type=output_schema,
            instrument=True
        )
        
    elif agent_type == "creative_coupon":
        # Creative agent is unique and doesn't depend on category
        model = OpenAIModel(
            model_name=settings.coupon_model_name, 
            provider=openai_provider
        )
        # Assuming a generic prompt for creative coupons
        creative_prompt = get_prompt('generic', 'creative_coupon')
        return Agent[CreativeCouponResponse](
            model=model,
            model_settings=default_model_settings,
            system_prompt=creative_prompt,
            output_type=CreativeCouponResponse,
            instrument=True
        )
        
    else:
        raise ValueError(f"Unknown agent type: {agent_type}")