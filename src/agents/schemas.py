from pydantic import BaseModel, Field

class AnalysisSummaryResponse(BaseModel):
    """Generic response for any analysis summary."""
    summary: str = Field(description="A concise, data-driven summary of the key findings from the analysis.")
    recommendations: list[str] = Field(description="A list of actionable recommendations based on the summary.")

class OrderStandardCouponResponse(BaseModel):
    # Combo coupon
    combo_coupon: str = Field(description="Best Combo coupon strategy to increase basket size.")
    combo_coupon_reasoning: str = Field(description="Why this combo coupon makes sense based on order patterns.")
    combo_coupon_cost_analysis: str = Field(description="Financial projection for the combo coupon.")

    # Threshold coupon
    threshold_coupon: str = Field(description="Best Threshold coupon to increase average order value.")
    threshold_coupon_reasoning: str = Field(description="Why this threshold works based on bill value distribution.")
    threshold_coupon_cost_analysis: str = Field(description="Financial projection for the threshold coupon.")

    # Happy Hours coupon
    happy_hours_coupon: str = Field(description="Best Happy Hours coupon to boost low traffic periods.")
    happy_hours_coupon_reasoning: str = Field(description="Why this timing-based coupon is optimal.")
    happy_hours_coupon_cost_analysis: str = Field(description="Financial projection for the happy hours coupon.")
    
    # Combined analysis
    combined_cost_analysis: str = Field(description="Overall financial impact and risk factors for all coupons combined.")

class CustomerStandardCouponResponse(BaseModel):
    # Joining Bonus Coupon
    joining_bonus_coupon: str = Field(description="Best Joining Bonus Coupon for new customers.")
    joining_bonus_coupon_reasoning: str = Field(description="Reasoning for the joining bonus coupon.")
    joining_bonus_coupon_cost_analysis: str = Field(description="Cost analysis for the joining bonus.")

    # Stamp Card Coupon
    stamp_card_coupon: str = Field(description="Best Stamp Card Coupon to encourage repeat visits.")
    stamp_card_coupon_reasoning: str = Field(description="Reasoning for the stamp card coupon.")
    stamp_card_coupon_cost_analysis: str = Field(description="Cost analysis for the stamp card.")

    # Miss You Coupon
    miss_you_coupon: str = Field(description="Best Miss You Coupon to win back lapsed customers.")
    miss_you_coupon_reasoning: str = Field(description="Reasoning for the miss you coupon.")
    miss_you_coupon_cost_analysis: str = Field(description="Cost analysis for the miss you coupon.")

    # Combined Cost Analysis
    combined_cost_analysis: str = Field(description="Overall financial impact of all customer-focused coupons.")

class ProductStandardCouponResponse(BaseModel):
    """Define response fields for product-related standard coupons."""
    # Example:
    slow_moving_item_coupon: str = Field(description="coupon to boost sales of slow-moving items.")
    slow_moving_item_reasoning: str = Field(description="Reasoning based on sales data.")


class CreativeCouponResponse(BaseModel):
    """A flexible schema for unique, creative coupon ideas."""
    coupons: str = Field(description="Creative coupon ideas to generate excitement and footfall.")
    reasoning: str = Field(description="The strategic reasoning behind these creative ideas.")
    cost_impact: str = Field(description="Estimated impact on sales, revenue, and discount spending.")
    conversation: str = Field(description="Use this field for a conversational response if other fields don't fit.")