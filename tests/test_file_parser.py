import pytest
import pandas as pd
from core.file_parser import parse_file, get_schema_from_df

def test_csv_parsing(tmp_path):
    csv_path = tmp_path / "test.csv"
    csv_path.write_text("a,b\n1,2\n3,4")
    df, schema = parse_file(str(csv_path))
    assert isinstance(df, pd.DataFrame)
    assert schema['num_columns'] == 2
    assert schema['num_rows'] == 2
    assert schema['columns'][0]['name'] == 'a'

def test_schema_from_df():
    df = pd.DataFrame({"x": [1, 2, None], "y": ["a", "b", "c"]})
    schema = get_schema_from_df(df)
    assert schema['num_columns'] == 2
    assert schema['columns'][0]['nulls'] == 1
