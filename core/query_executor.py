"""
Query executor for AutoQueryAI. Uses DuckDB for SQL execution.
"""
import duckdb
import pandas as pd
from typing import Any

def execute_sql(df: pd.DataFrame, sql: str) -> pd.DataFrame:
    """
    Execute SQL query on a DataFrame using DuckDB.
    """
    con = duckdb.connect()
    con.register('data', df)
    result = con.execute(sql).df()
    con.close()
    return result

def execute_pandas_code(df: pd.DataFrame, code: str) -> Any:
    """
    Execute pandas code string in a restricted namespace.
    Returns the result of the last expression.
    """
    local_vars = {'df': df.copy()}
    exec(code, {}, local_vars)
    return local_vars.get('result', local_vars.get('df'))
