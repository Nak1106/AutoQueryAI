"""
AutoJoin: Suggests join keys and queries for multi-table data (BONUS).
"""
def suggest_joins(tables):
    # tables: dict of {table_name: [columns]}
    joins = []
    table_names = list(tables.keys())
    for i, t1 in enumerate(table_names):
        for t2 in table_names[i+1:]:
            common = set(tables[t1]) & set(tables[t2])
            if common:
                joins.append({
                    'tables': (t1, t2),
                    'columns': list(common)
                })
    return joins
