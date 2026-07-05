import pandas as pd
import json
import os
from typing import Dict, Any

class DataExporter:
    @staticmethod
    def export_csv(df: pd.DataFrame, filepath: str, metadata: Dict[str, Any] = None):
        """Export dataframe to CSV. Standard CSV doesn't embed metadata easily without breaking standard readers, 
        so we'll just export the dataframe."""
        df.to_csv(filepath, index=False)
        
    @staticmethod
    def export_json(df: pd.DataFrame, filepath: str, metadata: Dict[str, Any] = None):
        """Export dataframe to JSON, optionally embedding metadata."""
        export_df = df.copy()
        for col in export_df.columns:
            if pd.api.types.is_datetime64_any_dtype(export_df[col]):
                # Format to ISO format or readable timezone string
                export_df[col] = export_df[col].dt.strftime('%Y-%m-%d %H:%M:%S%z')
        
        records = export_df.to_dict(orient='records')
        
        output = records
        if metadata:
            output = {
                "metadata": metadata,
                "data": records
            }
            
        with open(filepath, "w") as f:
            json.dump(output, f, indent=4)
