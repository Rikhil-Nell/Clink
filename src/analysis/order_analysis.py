import pandas as pd
from itertools import combinations
from collections import Counter
from pathlib import Path

from src.config import AnalysisConfig
from src.utils.data_loader import DataLoader


class OrderAnalyzer:
    """Analyzes order-level KPIs and patterns"""
   
    def __init__(self, config: AnalysisConfig):
        self.config = config
   
    def compute_invoice_aggregation(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Aggregates invoice-level metrics.
        Returns invoice-level dataframe.
        """
        # Calculate basket size (unique items per invoice)
        basket_sizes = df.groupby('invoice_no')['item_name'].nunique().rename('basket_size')
       
        # Aggregate
        invoice_kpis = (
            df.groupby('invoice_no').agg(
                order_date=('date', 'min'),
                total_quantity=('item_quantity', 'sum'),
                total_discount=('discount', 'sum'),
                total_waived_off=('waived_off', 'sum'),
                net_invoice_value=('net_sales', 'sum')
            )
        )
       
        # Merge basket sizes
        invoice_kpis = invoice_kpis.join(basket_sizes)
       
        # Additional time features
        invoice_kpis['order_day'] = invoice_kpis['order_date'].dt.day_name()
        invoice_kpis['order_hour'] = invoice_kpis['order_date'].dt.hour
       
        invoice_kpis = invoice_kpis.reset_index()
        return invoice_kpis
   
    def compute_cooccurrence_matrix(self, df: pd.DataFrame, top_n: int = 30) -> pd.DataFrame:
        """
        Builds item co-occurrence matrix, filtered to top N most frequent items.
        Returns the symmetric matrix dataframe.
        """
        # Group items by invoice
        invoice_items = df.groupby('invoice_no')['item_name'].apply(list).reset_index()
       
        # Build pair counts
        pair_counter = Counter()
        for items in invoice_items['item_name']:
            unique_items = list(set(items))
            if len(unique_items) > 1:
                pairs = combinations(sorted(unique_items), 2)
                pair_counter.update(pairs)
       
        co_occurrence_df = pd.DataFrame(pair_counter.items(), columns=['item_pair', 'count'])
        co_occurrence_df[['item_1', 'item_2']] = pd.DataFrame(co_occurrence_df['item_pair'].tolist(), index=co_occurrence_df.index)
        co_occurrence_df.drop(columns='item_pair', inplace=True)
       
        # Build symmetric matrix
        matrix_df = pd.pivot_table(
            co_occurrence_df,
            values='count',
            index='item_1',
            columns='item_2',
            fill_value=0
        )
        full_matrix = matrix_df + matrix_df.T.fillna(0)
       
        # Limit to top-N items
        top_items = df['item_name'].value_counts().head(top_n).index
        filtered_matrix = full_matrix.loc[top_items, top_items]
       
        return filtered_matrix


def run_order_analysis(df: pd.DataFrame):
    """
    Main orchestrator function for Streamlit compatibility.
    - Loads data from file path or file-like object (csv/xlsx).
    - Cleans data.
    - Returns (invoice_kpis_df, cooccurrence_matrix_df).
    """
   
    # Preprocess data
    df = DataLoader.preprocess_raw_data(df)
   
    # Create analyzer
    config = AnalysisConfig()
    analyzer = OrderAnalyzer(config)
   
    # Compute outputs
    invoice_df = analyzer.compute_invoice_aggregation(df)
    cooc_matrix_df = analyzer.compute_cooccurrence_matrix(df)
   
    # Create output directories if they don't exist
    script_dir = Path(__file__).parent
    results_dir = script_dir.parent / "results" / "order_analysis"  # Fixed typo
    results_dir.mkdir(parents=True, exist_ok=True)
    
    # Save outputs with correct paths
    invoice_df.to_csv(results_dir / "Invoice_Aggregation.csv", index=False)
    cooc_matrix_df.to_csv(results_dir / "Product_Co_occurrence_Top30.csv")  # Match your directory structure

    return invoice_df, cooc_matrix_df


if __name__ == "__main__":
    # Get the script directory and construct proper paths
    script_dir = Path(__file__).parent
    data_file = script_dir.parent / "test data" / "Year Order Item Data.csv"  # Fixed path
    
    # Check if file exists
    if not data_file.exists():
        print(f"Error: Data file not found at {data_file}")
        print("Please check the file path and ensure the data file exists.")
    else:
        try:
            # Pass the file path directly instead of opening in text mode
            invoice_df, cooc_matrix_df = run_order_analysis(str(data_file))
            print("Analysis completed successfully!")
            print(f"Invoice aggregation shape: {invoice_df.shape}")
            print(f"Co-occurrence matrix shape: {cooc_matrix_df.shape}")
        except Exception as e:
            print(f"Error running analysis: {e}")
            import traceback
            traceback.print_exc()