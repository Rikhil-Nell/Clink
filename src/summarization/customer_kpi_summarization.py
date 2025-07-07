from typing import Dict, Any, List
from dataclasses import dataclass
import pandas as pd
import json
from src.config import AnalysisConfig

@dataclass
class CustomerSegments:
    total_customers: int
    new_customers: Dict[str, Any]
    active_customers: Dict[str, Any]
    dormant_customers: Dict[str, Any]

class CustomerKPIAnalyzer:
    def __init__(self, config: AnalysisConfig):
        self.config = config

    def segment_customers(self, df: pd.DataFrame) -> CustomerSegments:
        total_customers = len(df)

        new_customers_df = df[df['Days_Since_First_Order'] <= 30]
        dormant_customers_df = df[
            (df['Days_Since_Last_Order'] > 60) &
            (df['Days_Since_First_Order'] > 30)
        ]
        active_mask = ~df.index.isin(new_customers_df.index) & ~df.index.isin(dormant_customers_df.index)
        active_customers_df = df[active_mask]

        return CustomerSegments(
            total_customers=total_customers,
            new_customers={
                "count": len(new_customers_df),
                "percentage": round(len(new_customers_df) / total_customers * 100, 2) if total_customers else 0,
                "avg_first_order_value": float(round(new_customers_df['Average_Spend_Per_Order'].mean(), 2)) if len(new_customers_df) > 0 else 0
            },
            active_customers={
                "count": len(active_customers_df),
                "percentage": round(len(active_customers_df) / total_customers * 100, 2) if total_customers else 0,
                "avg_clv": float(round(active_customers_df['Total_Spend_By_Customer'].mean(), 2)) if len(active_customers_df) > 0 else 0,
                "avg_orders": float(round(active_customers_df['Total_Orders_Placed'].mean(), 2)) if len(active_customers_df) > 0 else 0
            },
            dormant_customers={
                "count": len(dormant_customers_df),
                "percentage": round(len(dormant_customers_df) / total_customers * 100, 2) if total_customers else 0,
                "avg_clv_before_dormancy": float(round(dormant_customers_df['Total_Spend_By_Customer'].mean(), 2)) if len(dormant_customers_df) > 0 else 0
            }
        )

    def analyze_financials(self, df: pd.DataFrame) -> Dict[str, Any]:
        total_revenue = df['Total_Spend_By_Customer'].sum()
        total_orders = df['Total_Orders_Placed'].sum()
        return {
            "total_revenue": float(round(total_revenue, 2)),
            "estimated_total_profit": float(round(total_revenue * 0.25, 2)),
            "overall_aov": float(round(total_revenue / total_orders, 2)) if total_orders > 0 else 0,
            "overall_avg_clv": float(round(df['Total_Spend_By_Customer'].mean(), 2))
        }

    def coupon_insights(self, segments: CustomerSegments, df: pd.DataFrame) -> Dict[str, Any]:
        active_multi_order = df[
            (df['Total_Orders_Placed'] > 1) &
            ~df.index.isin(df[df['Days_Since_First_Order'] <= 30].index) &
            ~df.index.isin(df[(df['Days_Since_Last_Order'] > 60) & (df['Days_Since_First_Order'] > 30)].index)
        ]
        dormant_df = df[(df['Days_Since_Last_Order'] > 60) & (df['Days_Since_First_Order'] > 30)]
        new_df = df[df['Days_Since_First_Order'] <= 30]

        # Stamp card suggestion
        if len(active_multi_order) > 0:
            stats = active_multi_order['Total_Orders_Placed'].describe()
            stamp_card = {
                "target_customer_count": len(active_multi_order),
                "order_frequency_distribution": {k: round(v, 2) for k, v in stats.items()},
                "suggestion": f"Most active customers place between {int(stats['25%'])} and {int(stats['75%'])} orders. Recommend 5 or 7 stamp card."
            }
        else:
            stamp_card = {
                "target_customer_count": 0,
                "order_frequency_distribution": {},
                "suggestion": "No multi-order active customers found."
            }

        # Miss you
        if len(dormant_df) > 0:
            recency_stats = df['Days_Since_Last_Order'].describe()
            miss_you = {
                "target_customer_count": len(dormant_df),
                "avg_spend_of_dormant_customers": float(round(dormant_df['Average_Spend_Per_Order'].mean(), 2)),
                "last_order_recency_distribution": {k: round(v, 2) for k, v in recency_stats.items()},
                "suggestion": "A win-back offer should be compelling relative to these averages."
            }
        else:
            miss_you = {
                "target_customer_count": 0,
                "avg_spend_of_dormant_customers": 0,
                "last_order_recency_distribution": {},
                "suggestion": "No dormant customers found."
            }

        # Joining bonus
        if len(new_df) > 0:
            joining = {
                "target_customer_count": len(new_df),
                "avg_first_order_value": float(round(new_df['Average_Spend_Per_Order'].mean(), 2)),
                "suggestion": "Offer joining bonuses cautiously to protect margins."
            }
        else:
            joining = {
                "target_customer_count": 0,
                "avg_first_order_value": 0,
                "suggestion": "No new customers found."
            }

        return {
            "stamp_card": stamp_card,
            "miss_you": miss_you,
            "joining_bonus": joining
        }

    def additional_insights(self, df: pd.DataFrame) -> Dict[str, Any]:
        top20_threshold = df['Total_Spend_By_Customer'].quantile(0.8)
        return {
            "high_value_customers": {
                "count": len(df[df['Total_Spend_By_Customer'] > top20_threshold]),
                "threshold": float(round(top20_threshold, 2)),
                "avg_clv": float(round(df[df['Total_Spend_By_Customer'] > top20_threshold]['Total_Spend_By_Customer'].mean(), 2))
            },
            "order_frequency_insights": {
                "single_order_customers": len(df[df['Total_Orders_Placed'] == 1]),
                "repeat_customers": len(df[df['Total_Orders_Placed'] > 1]),
                "high_frequency_customers": len(df[df['Total_Orders_Placed'] >= 5])
            }
        }

def run_customer_summarization(customer_df: pd.DataFrame):
    config = AnalysisConfig()
    analyzer = CustomerKPIAnalyzer(config=config)

    segments = analyzer.segment_customers(customer_df)
    financials = analyzer.analyze_financials(customer_df)
    coupons = analyzer.coupon_insights(segments, customer_df)
    additional = analyzer.additional_insights(customer_df)

    summary = {
        "analysis_timestamp": pd.Timestamp.now().isoformat(),
        "analysis_config": config.to_dict(),
        "customer_segments": segments.__dict__,
        "financial_summary": financials,
        "coupon_strategy_insights": coupons,
        "additional_insights": additional
    }

    summary_json = json.dumps(summary, indent=2)

    # Save for human review
    with open("summary_json/customer_kpis_summary.json", "w") as f:
        f.write(summary_json)

    return summary
