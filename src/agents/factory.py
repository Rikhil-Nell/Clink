from typing import Union, Optional
from pydantic import BaseModel
from pydantic_ai import Agent

import logfire

# Local Imports
from src.settings import research_model, chat_model, analysis_model, coupon_model, default_model_settings
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
        agent_type: 'research', 'analysis_summary', 'standard_coupon', 'creative_coupon' or "chat".
        category: 'order', 'customer', or 'product'.
        
    Returns:
        A configured pydantic_ai Agent instance.
    """
    instructions = get_prompt(agent_type=agent_type, category=category)
    
    if agent_type == "analysis_summary":

        return Agent[AnalysisSummaryResponse](
            model=analysis_model,
            model_settings=default_model_settings,
            instructions=instructions,
            output_type=AnalysisSummaryResponse,
            instrument=True
        )
        
    elif agent_type == "standard_coupon":
        output_schema = STANDARD_COUPON_SCHEMAS.get(category)
        if not output_schema:
            raise ValueError(f"No standard coupon schema defined for category: {category}")

        return Agent[output_schema](
            model=coupon_model,
            model_settings=default_model_settings,
            instructions=instructions,
            output_type=output_schema,
            instrument=True
        )
        
    elif agent_type == "creative_coupon":

        return Agent[CreativeCouponResponse](
            model=coupon_model,
            model_settings=default_model_settings,
            instructions=instructions,
            output_type=CreativeCouponResponse,
            instrument=True
        )
        
    elif agent_type == "chat":

        return Agent(
            model=chat_model,
            model_settings=default_model_settings,
            instructions=instructions,
            instrument=True
        )
    
    elif agent_type == "research":

        return Agent(
            model=research_model,
            model_settings=default_model_settings,
            instructions=instructions,
            instrument=True
        ) 
    
    else:
        raise ValueError(f"Unknown agent type: {agent_type}")