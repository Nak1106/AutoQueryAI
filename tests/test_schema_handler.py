import pandas as pd
from core.schema_handler import preview_schema, generate_profile

def test_preview_schema():
    schema = {
        'columns': [
            {'name': 'a', 'dtype': 'int64', 'nulls': 0, 'unique': 2},
            {'name': 'b', 'dtype': 'object', 'nulls': 1, 'unique': 2}
        ],
        'num_rows': 3,
        'num_columns': 2
    }
    preview = preview_schema(schema)
    assert "Columns (2):" in preview
    assert "a (int64)" in preview
    assert "Rows: 3" in preview

def test_generate_profile():
    df = pd.DataFrame({"a": [1, 2, 3], "b": ["x", None, "z"]})
    profile = generate_profile(df)
    assert 'head' in profile
    assert 'describe' in profile
    assert 'nulls' in profile
    assert profile['nulls']['b'] == 1
