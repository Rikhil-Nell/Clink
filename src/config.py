from dataclasses import dataclass
from typing import Dict, Any
from pathlib import Path

@dataclass
class AnalysisConfig:
    """Configuration class for KPI analysis parameters"""
    min_pair_support: int = 5
    min_item_support: int = 20
    top_n_items: int = 30
    high_value_percentile: float = 0.8
    peak_hours_threshold: float = 0.1
    
    # File paths
    base_results_dir: Path = Path("src/results")
    order_results_dir: Path = Path("src/results/order_analysis")
    customer_results_dir: Path = Path("src/results/customer_analysis")
    product_results_dir: Path = Path("src/results/product_analysis")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary"""
        return {
            "min_pair_support": self.min_pair_support,
            "min_item_support": self.min_item_support,
            "top_n_items": self.top_n_items,
            "high_value_percentile": self.high_value_percentile,
            "peak_hours_threshold": self.peak_hours_threshold
        }