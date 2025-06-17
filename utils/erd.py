"""
ERD generation utility using ERAlchemy.
"""
from eralchemy import render_er

def generate_erd(db_uri: str, output_path: str):
    """
    Generate ER diagram from a database URI.
    """
    render_er(db_uri, output_path)
