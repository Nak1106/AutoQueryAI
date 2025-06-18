"""
InsightAgent: Runs prebuilt business queries for quick insights (BONUS).
"""
class InsightAgent:
    def __init__(self):
        self.insights = [
            {
                'name': 'Top earning vendors',
                'sql': "SELECT VendorID, SUM(total_amount) as total FROM data GROUP BY VendorID ORDER BY total DESC LIMIT 5;"
            },
            {
                'name': 'Average tip per mile by hour',
                'sql': "SELECT EXTRACT(HOUR FROM tpep_pickup_datetime) as hour, AVG(tip_amount/trip_distance) as avg_tip_per_mile FROM data GROUP BY hour ORDER BY hour;"
            }
        ]

    def get_insights(self):
        return self.insights
