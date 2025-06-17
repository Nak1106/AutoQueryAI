"""
File parsing and schema detection logic for AutoQueryAI.
Supports CSV, Excel, JSON, and SQL dump files.
"""
import os
import pandas as pd
import duckdb
import json
from typing import Tuple, Dict, Any, Optional

SUPPORTED_EXTENSIONS = ['.csv', '.xlsx', '.xls', '.json', '.sql']

def detect_file_type(file_path: str) -> str:
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()
    if ext in SUPPORTED_EXTENSIONS:
        return ext
    raise ValueError(f"Unsupported file type: {ext}")

def parse_file(file_path: str) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Parse the uploaded file and return a DataFrame and schema info.
    """
    ext = detect_file_type(file_path)
    if ext == '.csv':
        df = pd.read_csv(file_path)
    elif ext in ['.xlsx', '.xls']:
        df = pd.read_excel(file_path)
    elif ext == '.json':
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        df = pd.json_normalize(data)
    elif ext == '.sql':
        # Use DuckDB to load SQL dump
        con = duckdb.connect()
        with open(file_path, 'r', encoding='utf-8') as f:
            sql_script = f.read()
        con.execute(sql_script)
        tables = con.execute("SHOW TABLES").fetchall()
        if not tables:
            raise ValueError("No tables found in SQL dump.")
        table_name = tables[0][0]
        df = con.execute(f"SELECT * FROM {table_name}").df()
    else:
        raise ValueError(f"Unsupported file type: {ext}")
    schema = get_schema_from_df(df)
    return df, schema

def get_schema_from_df(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Generate schema info from a DataFrame.
    """
    schema = {
        'columns': [
            {
                'name': col,
                'dtype': str(df[col].dtype),
                'nulls': int(df[col].isnull().sum()),
                'unique': int(df[col].nunique())
            }
            for col in df.columns
        ],
        'num_rows': len(df),
        'num_columns': len(df.columns)
    }
    return schema
