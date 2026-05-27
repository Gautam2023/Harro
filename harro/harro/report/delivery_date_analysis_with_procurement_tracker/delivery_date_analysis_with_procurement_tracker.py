# Copyright (c) 2026, Fosserp and contributors
# For license information, please see license.txt

import frappe
from erpnext.buying.report.procurement_tracker.procurement_tracker import execute as procurement_tracker_execute


def execute(filters=None):
    # Call standard report — get all columns and data
    columns, data = procurement_tracker_execute(filters)
    
    # Find index of actual_delivery_date column
    actual_delivery_index = None
    for i, col in enumerate(columns):
        if col.get("fieldname") == "actual_delivery_date":
            actual_delivery_index = i
            break
    
    # Define the Delay column
    delay_column = {
        "label": "Delay (Days)",
        "fieldname": "delay",
        "fieldtype": "Data",
        "width": 120
    }
    
    # Insert Delay column after actual_delivery_date
    if actual_delivery_index is not None:
        columns.insert(actual_delivery_index + 1, delay_column)
    else:
        columns.append(delay_column)
    
    # Calculate delay for each row and apply color
    for row in data:
        expected = row.get("expected_delivery_date")
        actual = row.get("actual_delivery_date")
        
        if expected and actual:
            diff = (actual - expected).days
            
            if diff > 0:
                # Late — Red
                row["delay"] = f'<span style="color: red; font-weight: bold;">+{diff}</span>'
            elif diff < 0:
                # Early — Green
                row["delay"] = f'<span style="color: green; font-weight: bold;">{diff}</span>'
            else:
                # On time — Green
                row["delay"] = f'<span style="color: green; font-weight: bold;">0</span>'
        else:
            row["delay"] = ""
    
    return columns, data


