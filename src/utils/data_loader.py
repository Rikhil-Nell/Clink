# data_loader.py
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Union, Tuple, Optional
from io import StringIO
import requests

class DataLoader:
    """Handles loading and preprocessing of order data"""
    
    @staticmethod
    def load_local_file(file_path: Union[str, Path]) -> pd.DataFrame:
        """Load data from local file"""
        file_path = Path(file_path)
        
        if file_path.suffix.lower() == '.xlsx':
            return pd.read_excel(file_path, parse_dates=['date'])
        elif file_path.suffix.lower() == '.csv':
            return pd.read_csv(file_path, parse_dates=['date'])
        else:
            raise ValueError(f"Unsupported file format: {file_path.suffix}")
    
    @staticmethod
    async def load_csv_from_url(url: str) -> pd.DataFrame:
        """Load CSV from HTTP server using pyfetch"""
        response = await requests.get(url)
        if not response.ok:
            raise Exception(f"HTTP {response.status}: {response.status_text}")
        
        csv_text = await response.string()
        csv_data = StringIO(csv_text)
        return pd.read_csv(csv_data)
    
    @staticmethod
    def preprocess_raw_data(df: pd.DataFrame) -> pd.DataFrame:
        """Clean and preprocess raw order data"""
        # Create a copy to avoid modifying original
        df = df.copy()
        
        # Filter unwanted order types
        df = df[df['order_type'] != "Delivery(Parcel)"]
        
        # Define numeric columns
        numeric_cols = [
            'my_amount', 'total_tax', 'discount', 'delivery_charge',
            'container_charge', 'service_charge', 'additional_charge',
            'waived_off', 'round_off', 'total', 'item_price', 
            'item_quantity', 'item_total'
        ]
        
        # Convert to numeric
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Fill nulls in discount columns
        df[['discount', 'waived_off']] = df[['discount', 'waived_off']].fillna(0)
        
        # Drop incomplete rows
        required_cols = ['invoice_no', 'item_name', 'item_quantity', 'item_total']
        df.dropna(subset=required_cols, inplace=True)
        
        # Compute net sales
        df['net_sales'] = df['item_total'] - df[['discount', 'waived_off']].sum(axis=1)
        
        # Add time features
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            df['YearMonth'] = df['date'].dt.to_period('M')
            df['DateOnly'] = df['date'].dt.date
            df['Weekday'] = df['date'].dt.day_name()
            df['Hour'] = df['date'].dt.hour
        
        return df