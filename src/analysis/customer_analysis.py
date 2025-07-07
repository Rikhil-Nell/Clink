# src/customer_analysis.py
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

from src.config import AnalysisConfig
from src.utils.data_loader import DataLoader

class CustomerAnalyzer:
    def __init__(self, config: AnalysisConfig):
        self.config = config

    def prepare_customer_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Filters known customers and builds key date fields.
        """
        df_known = df[df['customer_phone'].notnull()].copy()
        df_known = df_known[df_known['order_type'] != "Delivery(Parcel)"].copy()
        df_known['customer_phone'] = df_known['customer_phone'].astype(str)

        df_known['date_only'] = df_known['date'].dt.date
        df_known['date_dt'] = pd.to_datetime(df_known['date_only'])
        return df_known

    def build_customer_kpis(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Constructs customer-level KPIs such as total spend, orders, recency, tenure.
        """
        latest_date = df['date'].max()

        # Deduplicate invoice totals
        invoice_totals = df.groupby(['customer_phone', 'invoice_no'])['total'].first().reset_index()

        # Total Spend
        total_spend = invoice_totals.groupby('customer_phone')['total'].sum().reset_index(name='Total_Spend_By_Customer')

        # Average Spend Per Order
        avg_spend_order = invoice_totals.groupby('customer_phone')['total'].mean().reset_index(name='Average_Spend_Per_Order')

        # Total Orders Placed
        order_count = invoice_totals.groupby('customer_phone')['invoice_no'].nunique().reset_index(name='Total_Orders_Placed')

        # Total Items Ordered
        item_count = df.groupby('customer_phone')['item_quantity'].sum().reset_index(name='Total_Items_Ordered')

        # Average Spend Per Item
        avg_spend_item = total_spend.merge(item_count, on='customer_phone')
        avg_spend_item['Average_Spend_Per_Item'] = avg_spend_item['Total_Spend_By_Customer'] / avg_spend_item['Total_Items_Ordered']
        avg_spend_item = avg_spend_item[['customer_phone', 'Average_Spend_Per_Item']]

        # Recency
        recency = df.groupby('customer_phone')['date'].max().reset_index()
        recency['Days_Since_Last_Order'] = (latest_date - recency['date']).dt.days

        # Tenure
        first_order = df.groupby('customer_phone')['date_dt'].min().reset_index(name='First_Order_Date')
        first_order['Days_Since_First_Order'] = (latest_date - first_order['First_Order_Date']).dt.days

        # Frequent customer name for personalization
        name_map = (
            df.groupby('customer_phone')['customer_name']
            .agg(lambda x: x.mode().iloc[0] if not x.mode().empty else 'Valued Customer')
            .reset_index()
        )

        # Merge all into final KPI master
        kpi_master = (
            total_spend
            .merge(avg_spend_order, on='customer_phone')
            .merge(order_count, on='customer_phone')
            .merge(avg_spend_item, on='customer_phone')
            .merge(item_count, on='customer_phone')
            .merge(recency[['customer_phone', 'Days_Since_Last_Order']], on='customer_phone')
            .merge(first_order[['customer_phone', 'Days_Since_First_Order']], on='customer_phone')
            .merge(name_map, on='customer_phone')
        )

        return kpi_master

    def perform_rfm_clustering(self, kpi_df: pd.DataFrame) -> pd.DataFrame:
        """
        Runs RFM scoring and K-Means clustering.
        """
        rfm = kpi_df[[
            'customer_phone', 'Days_Since_Last_Order',
            'Total_Orders_Placed', 'Total_Spend_By_Customer'
        ]].rename(columns={
            'Days_Since_Last_Order': 'Recency',
            'Total_Orders_Placed': 'Frequency',
            'Total_Spend_By_Customer': 'Monetary'
        })

        # RFM Scores
        rfm['Recency_Score'] = pd.qcut(rfm['Recency'], 5, labels=[5,4,3,2,1], duplicates='drop')
        rfm['Frequency_Score'] = pd.qcut(rfm['Frequency'].rank(method='first'), 5, labels=[1,2,3,4,5], duplicates='drop')
        rfm['Monetary_Score'] = pd.qcut(rfm['Monetary'], 5, labels=[1,2,3,4,5], duplicates='drop')
        rfm['RFM_Total_Score'] = rfm[['Recency_Score', 'Frequency_Score', 'Monetary_Score']].astype(int).sum(axis=1)

        # Log transform
        rfm_log = np.log1p(rfm[['Recency', 'Frequency', 'Monetary']])

        # Scale
        scaler = StandardScaler()
        rfm_scaled = scaler.fit_transform(rfm_log)

        # Optimal K using silhouette could be added here — we fix to 3 for stability
        optimal_k = 3
        kmeans = KMeans(n_clusters=optimal_k, random_state=42, n_init=10)
        rfm['Cluster'] = kmeans.fit_predict(rfm_scaled)

        # Merge cluster back to master
        kpi_df = kpi_df.merge(rfm[['customer_phone', 'Cluster']], on='customer_phone')
        return kpi_df


def run_customer_analysis(df: pd.DataFrame):
    """
    Orchestrator function that takes a CSV or Excel file path or file-like object,
    preprocesses, builds KPIs, runs clustering, saves outputs.
    """

    # Preprocess raw data (external util)
    df = DataLoader.preprocess_raw_data(df)

    # Create analyzer
    config = AnalysisConfig()
    analyzer = CustomerAnalyzer(config)

    # Build customer data
    df_known = analyzer.prepare_customer_data(df)
    customer_kpis = analyzer.build_customer_kpis(df_known)
    customer_kpis = analyzer.perform_rfm_clustering(customer_kpis)

    # Create output directories
    script_dir = Path(__file__).parent
    results_dir = script_dir.parent / "results" / "customer_analysis"
    results_dir.mkdir(parents=True, exist_ok=True)

    # Save output
    customer_kpis.to_csv(results_dir / "Customer_KPIs_KnownPhonesOnly.csv", index=False)

    return customer_kpis


if __name__ == "__main__":
    script_dir = Path(__file__).parent
    data_file = script_dir.parent / "test data" / "Year Order Item Data.csv"

    if not data_file.exists():
        print(f"Data file not found at {data_file}")
    else:
        try:
            customer_summary = run_customer_analysis(str(data_file))
            print("Customer analysis completed successfully!")
            print(f"Output shape: {customer_summary.shape}")
        except Exception as e:
            print(f"Error: {e}")
