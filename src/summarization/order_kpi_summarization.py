from typing import Dict, List, Any

import pandas as pd
from src.config import AnalysisConfig

class OrderAnalysisSummarizer:

    def __init__(self, config: AnalysisConfig):
        self.config = config

    def analyze_order_patterns(self, invoice_df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze order patterns and generate KPIs"""
        total_invoices = len(invoice_df)
        total_revenue = invoice_df['net_invoice_value'].sum()
        total_items_sold = invoice_df['total_quantity'].sum()
       
        # Order value distribution
        order_value_stats = invoice_df['net_invoice_value'].describe()
        high_value_threshold = invoice_df['net_invoice_value'].quantile(self.config.high_value_percentile)
        high_value_orders = len(invoice_df[invoice_df['net_invoice_value'] >= high_value_threshold])
       
        # Basket size analysis
        basket_stats = invoice_df['basket_size'].describe()
       
        # Temporal patterns
        temporal_patterns = self._analyze_temporal_patterns(invoice_df)
       
        return {
            "total_orders": total_invoices,
            "total_revenue": round(total_revenue, 2),
            "total_items_sold": int(total_items_sold),
            "average_order_value": round(total_revenue / total_invoices, 2) if total_invoices > 0 else 0,
            "average_items_per_order": round(total_items_sold / total_invoices, 2) if total_invoices > 0 else 0,
            "order_value_distribution": {
                "mean": round(order_value_stats['mean'], 2),
                "std": round(order_value_stats['std'], 2),
                "min": round(order_value_stats['min'], 2),
                "25%": round(order_value_stats['25%'], 2),
                "50%": round(order_value_stats['50%'], 2),
                "75%": round(order_value_stats['75%'], 2),
                "max": round(order_value_stats['max'], 2)
            },
            "high_value_orders": {
                "count": high_value_orders,
                "percentage": round(high_value_orders / total_invoices * 100, 2),
                "threshold": round(high_value_threshold, 2)
            },
            "basket_size_analysis": {
                "avg_unique_items": round(basket_stats['mean'], 2),
                "min_items": int(basket_stats['min']),
                "max_items": int(basket_stats['max']),
                "most_common_basket_size": int(basket_stats['50%'])
            },
            "temporal_patterns": temporal_patterns
        }
   
    def analyze_cooccurrence_patterns(self, cooc_matrix: pd.DataFrame) -> Dict[str, Any]:
        """Analyze co-occurrence patterns"""
        strongest_pairs = self._extract_strongest_pairs(cooc_matrix)
       
        return {
            "analysis_scope": f"Top {self.config.top_n_items} most popular items",
            "items_in_matrix": len(cooc_matrix.index),
            "strongest_cooccurrences": strongest_pairs,
            "matrix_summary": {
                "total_possible_pairs": len(cooc_matrix.index) * (len(cooc_matrix.index) - 1) // 2,
                "pairs_with_cooccurrence": len(strongest_pairs)
            }
        }
   
    def _analyze_temporal_patterns(self, invoice_df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze temporal patterns in orders"""
        patterns = {}
       
        # Day of week analysis
        if 'order_day' in invoice_df.columns:
            day_distribution = invoice_df['order_day'].value_counts().to_dict()
            peak_days = invoice_df['order_day'].value_counts().head(3).index.tolist()
            patterns.update({
                "day_of_week_distribution": day_distribution,
                "peak_days": peak_days
            })
       
        # Hour analysis
        if 'order_hour' in invoice_df.columns:
            hourly_dist = invoice_df['order_hour'].value_counts().sort_index()
            total_orders = len(invoice_df)
            peak_hours = hourly_dist[
                hourly_dist >= (total_orders * self.config.peak_hours_threshold)
            ].index.tolist()
           
            patterns["hour_analysis"] = {
                "peak_hours": peak_hours,
                "hourly_distribution": hourly_dist.to_dict()
            }
       
        return patterns
   
    def _extract_strongest_pairs(self, matrix: pd.DataFrame) -> List[Dict[str, Any]]:
        """Extract strongest co-occurrence pairs from matrix"""
        pairs = []
        
        # Get the actual item names from the matrix index and columns
        item_names = list(matrix.index)
        
        # Iterate through the matrix using actual item names
        for i in range(len(item_names)):
            for j in range(i + 1, len(item_names)):  # Start from i+1 to avoid duplicates
                item1 = item_names[i]
                item2 = item_names[j]
                
                # Get the co-occurrence count from the matrix
                # Handle both symmetric and asymmetric matrices
                try:
                    count = matrix.loc[item1, item2]
                    if pd.isna(count):
                        count = 0
                except (KeyError, IndexError):
                    try:
                        count = matrix.loc[item2, item1]
                        if pd.isna(count):
                            count = 0
                    except (KeyError, IndexError):
                        count = 0
                
                # Only add pairs with meaningful co-occurrence
                if count > 0:
                    pairs.append({
                        "item_1": item1,
                        "item_2": item2,
                        "count": int(count)
                    })
       
        # Sort by count and return top 15
        return sorted(pairs, key=lambda x: x['count'], reverse=True)[:15]
    
    def generate_business_insights(self, cooc_pairs: List[Dict[str, Any]], 
                                 invoice_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate business insights from co-occurrence patterns and order data"""
        insights = {
            "bundle_opportunities": [],
            "cross_sell_recommendations": [],
            "inventory_insights": []
        }
        
        # Generate bundle opportunities from top co-occurrence pairs
        for pair in cooc_pairs[:5]:  # Top 5 pairs
            insights["bundle_opportunities"].append({
                "bundle_items": [pair['item_1'], pair['item_2']],
                "statistical_strength": f"Co-occurrence: {pair['count']} times",
                "frequency": f"Appears together in {pair['count']} orders",
                "recommendation": "Strong candidate for bundle pricing or combo offers"
            })
        
        # Cross-sell recommendations
        for pair in cooc_pairs[:8]:  # Top 8 for cross-sell
            insights["cross_sell_recommendations"].append({
                "trigger_item": pair['item_1'],
                "suggest_item": pair['item_2'],
                "frequency": f"Bought together {pair['count']} times",
                "strategy": "Suggest as add-on during ordering"
            })
        
        # Inventory insights based on order patterns
        avg_order_value = invoice_analysis.get('average_order_value', 0)
        high_value_threshold = invoice_analysis.get('high_value_orders', {}).get('threshold', 0)
        
        insights["inventory_insights"] = [
            {
                "insight_type": "high_value_correlation",
                "description": f"Orders above ${high_value_threshold:.2f} represent high-value customers",
                "action": "Ensure availability of items that appear in high-value orders"
            },
            {
                "insight_type": "basket_optimization",
                "description": f"Average order value is ${avg_order_value:.2f}",
                "action": "Focus on items that appear in the strongest co-occurrence pairs to drive basket size"
            }
        ]
        
        # Add specific insights for top co-occurring items
        if cooc_pairs:
            top_pair = cooc_pairs[0]
            insights["inventory_insights"].append({
                "insight_type": "top_pair_priority",
                "description": f"'{top_pair['item_1']}' and '{top_pair['item_2']}' are bought together {top_pair['count']} times",
                "action": "Maintain optimal stock levels for both items to avoid losing combo sales"
            })
        
        return insights
    
def run_order_summarization(invoice_df: pd.DataFrame, cooc_matrix: pd.DataFrame):
    config = AnalysisConfig()
    summarizer = OrderAnalysisSummarizer(config=config)

    # Analyze patterns
    invoice_df_summary = summarizer.analyze_order_patterns(invoice_df=invoice_df)
    cooc_matrix_summary = summarizer.analyze_cooccurrence_patterns(cooc_matrix=cooc_matrix)
    
    # Generate business insights
    cooc_pairs = cooc_matrix_summary.get('strongest_cooccurrences', [])
    business_insights = summarizer.generate_business_insights(cooc_pairs, invoice_df_summary)

    summary = {
        "analysis_timestamp": pd.Timestamp.now().isoformat(),
        "analysis_config": summarizer.config.to_dict(),
        "invoice_analysis": invoice_df_summary,
        "cooccurrence_analysis": cooc_matrix_summary,
        "business_insights": business_insights
    }

    import json

    summary_json = json.dumps(summary, indent=2)

    with open("summary_json/order_kpis_summary.json", 'w') as f:
        f.write(summary_json)

    return summary
