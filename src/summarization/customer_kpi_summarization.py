# kpi_analyzer.py - Standard Python Version (uses requests)
import pandas as pd
import numpy as np
import json
import sys
import requests
from io import StringIO
import asyncio

# --- CONFIGURATION & ASSUMPTIONS ---
# These can be tweaked. They are necessary for calculations not directly available in the data.
CONFIG = {
    "profit_margin": 0.25,  # Assuming a 25% profit margin on orders
    "dormancy_threshold_days": 60,  # Customers who haven't ordered in 60+ days are "dormant"
    "new_customer_threshold_days": 30, # Customers whose first order was within the last 30 days
}

def load_csv_from_url(url):
    """
    Load CSV data from a URL using requests.
    """
    try:
        response = requests.get(url)
        if response.status_code != 200:
            raise Exception(f"HTTP {response.status_code}: {response.reason}")
        csv_text = response.text
        csv_data = StringIO(csv_text)
        df = pd.read_csv(csv_data)
        return df
    except Exception as e:
        raise Exception(f"Failed to fetch or parse CSV from URL: {e}")

def analyze_kpis(csv_url):
    """
    Main function to load, analyze, and summarize customer KPI data from a CSV URL.
    """
    try:
        df = load_csv_from_url(csv_url)
        print(f"Successfully loaded CSV with {len(df)} rows and {len(df.columns)} columns")
        
        # Print column names for debugging
        print("Available columns:", list(df.columns))
        
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)

    # --- 1. Customer Segmentation ---
    total_customers = len(df)
    
    # Identify New Customers
    new_customers_df = df[df['Days_Since_First_Order'] <= CONFIG['new_customer_threshold_days']]
    
    # Identify Dormant Customers (excluding new customers from this category)
    dormant_customers_df = df[
        (df['Days_Since_Last_Order'] > CONFIG['dormancy_threshold_days']) &
        (df['Days_Since_First_Order'] > CONFIG['new_customer_threshold_days'])
    ]
    
    # Identify Active/Retained Customers (not new, not dormant)
    active_customer_mask = ~df.index.isin(new_customers_df.index) & ~df.index.isin(dormant_customers_df.index)
    active_customers_df = df[active_customer_mask]

    customer_segments = {
        "total_customers": total_customers,
        "new_customers": {
            "count": len(new_customers_df),
            "percentage": round(len(new_customers_df) / total_customers * 100, 2),
            "avg_first_order_value": round(new_customers_df['Average_Spend_Per_Order'].mean(), 2) if len(new_customers_df) > 0 else 0
        },
        "active_customers": {
            "count": len(active_customers_df),
            "percentage": round(len(active_customers_df) / total_customers * 100, 2),
            "avg_clv": round(active_customers_df['Total_Spend_By_Customer'].mean(), 2) if len(active_customers_df) > 0 else 0,
            "avg_orders": round(active_customers_df['Total_Orders_Placed'].mean(), 2) if len(active_customers_df) > 0 else 0
        },
        "dormant_customers": {
            "count": len(dormant_customers_df),
            "percentage": round(len(dormant_customers_df) / total_customers * 100, 2),
            "avg_clv_before_dormancy": round(dormant_customers_df['Total_Spend_By_Customer'].mean(), 2) if len(dormant_customers_df) > 0 else 0
        }
    }

    # --- 2. Financial Baselines ---
    total_revenue = df['Total_Spend_By_Customer'].sum()
    total_orders = df['Total_Orders_Placed'].sum()
    
    financial_summary = {
        "total_revenue": int(total_revenue),
        "estimated_total_profit": int(total_revenue * CONFIG['profit_margin']),
        "overall_aov": round(total_revenue / total_orders, 2) if total_orders > 0 else 0,
        "overall_avg_clv": round(df['Total_Spend_By_Customer'].mean(), 2),
    }

    # --- 3. Coupon-Specific Analysis ---

    # Stamp Card Analysis (for active, multi-order customers)
    multi_order_customers = active_customers_df[active_customers_df['Total_Orders_Placed'] > 1]
    
    if len(multi_order_customers) > 0:
        order_freq_stats = multi_order_customers['Total_Orders_Placed'].describe()
        stamp_card_analysis = {
            "target_customer_count": len(multi_order_customers),
            "order_frequency_distribution": {
                "mean": round(order_freq_stats['mean'], 2),
                "std": round(order_freq_stats['std'], 2),
                "min": int(order_freq_stats['min']),
                "25%": round(order_freq_stats['25%'], 2),
                "50%": round(order_freq_stats['50%'], 2),
                "75%": round(order_freq_stats['75%'], 2),
                "max": int(order_freq_stats['max'])
            },
            "suggestion": f"Most active customers place between {int(order_freq_stats['25%'])} and {int(order_freq_stats['75%'])} orders. A 5 or 7 stamp card could be optimal."
        }
    else:
        stamp_card_analysis = {
            "target_customer_count": 0,
            "order_frequency_distribution": {},
            "suggestion": "No multi-order active customers found for stamp card analysis."
        }

    # Miss You Coupon Analysis
    if len(dormant_customers_df) > 0:
        avg_dormant_spend = dormant_customers_df['Average_Spend_Per_Order'].mean()
        recency_stats = df['Days_Since_Last_Order'].describe()
        
        miss_you_analysis = {
            "target_customer_count": len(dormant_customers_df),
            "dormancy_trigger_point_days": CONFIG['dormancy_threshold_days'],
            "avg_spend_of_dormant_customers": round(avg_dormant_spend, 2),
            "last_order_recency_distribution": {
                "mean": round(recency_stats['mean'], 2),
                "std": round(recency_stats['std'], 2),
                "min": int(recency_stats['min']),
                "25%": round(recency_stats['25%'], 2),
                "50%": round(recency_stats['50%'], 2),
                "75%": round(recency_stats['75%'], 2),
                "max": int(recency_stats['max'])
            },
            "suggestion": f"The average dormant customer used to spend around ${avg_dormant_spend:.2f} per order. A win-back offer should be compelling relative to this amount."
        }
    else:
        miss_you_analysis = {
            "target_customer_count": 0,
            "dormancy_trigger_point_days": CONFIG['dormancy_threshold_days'],
            "avg_spend_of_dormant_customers": 0,
            "last_order_recency_distribution": {},
            "suggestion": "No dormant customers found for miss you coupon analysis."
        }

    # Joining Bonus Analysis
    if len(new_customers_df) > 0:
        avg_first_order = new_customers_df['Average_Spend_Per_Order'].mean()
        joining_bonus_analysis = {
            "target_customer_count": len(new_customers_df),
            "avg_first_order_value": round(avg_first_order, 2),
            "suggestion": f"The average new customer spends ${avg_first_order:.2f} on their first order. A joining bonus should provide value but protect margins on this initial amount."
        }
    else:
        joining_bonus_analysis = {
            "target_customer_count": 0,
            "avg_first_order_value": 0,
            "suggestion": "No new customers found for joining bonus analysis."
        }

    # --- 4. Additional Insights ---
    additional_insights = {
        "high_value_customers": {
            "count": len(df[df['Total_Spend_By_Customer'] > df['Total_Spend_By_Customer'].quantile(0.8)]),
            "threshold": round(df['Total_Spend_By_Customer'].quantile(0.8), 2),
            "avg_clv": round(df[df['Total_Spend_By_Customer'] > df['Total_Spend_By_Customer'].quantile(0.8)]['Total_Spend_By_Customer'].mean(), 2)
        },
        "order_frequency_insights": {
            "single_order_customers": len(df[df['Total_Orders_Placed'] == 1]),
            "repeat_customers": len(df[df['Total_Orders_Placed'] > 1]),
            "high_frequency_customers": len(df[df['Total_Orders_Placed'] >= 5])
        }
    }

    # --- 5. Assemble Final Summary ---
    final_summary = {
        "data_source": csv_url,
        "analysis_timestamp": pd.Timestamp.now().isoformat(),
        "analysis_config": CONFIG,
        "financial_summary": financial_summary,
        "customer_segments": customer_segments,
        "coupon_strategy_insights": {
            "stamp_card": stamp_card_analysis,
            "miss_you": miss_you_analysis,
            "joining_bonus": joining_bonus_analysis,
        },
        "additional_insights": additional_insights
    }

    return json.dumps(final_summary, indent=2)

def main():
    """
    Main function to run the analysis.
    """
    # Default to localhost:8000 with the specified filename
    base_url = "http://localhost:8000"
    filename = "Customer_KPIs_KnownPhonesOnly.csv"
    
    if len(sys.argv) == 2:
        # Allow override of the filename if provided
        filename = sys.argv[1]
    elif len(sys.argv) == 3:
        # Allow override of both base URL and filename
        base_url = sys.argv[1]
        filename = sys.argv[2]
    
    csv_url = f"{base_url}/{filename}"
    print(f"Fetching data from: {csv_url}")
    
    summary_json = analyze_kpis(csv_url)
    print(summary_json)

def run_summarization():
    pass