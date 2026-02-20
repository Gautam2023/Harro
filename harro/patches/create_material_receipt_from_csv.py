import frappe
import csv
import os
from frappe.utils import get_datetime, getdate, flt, today
from datetime import datetime


def execute():
    """
    Create Material Receipt type Stock Entry documents from CSV file
    Supports both local file path and Frappe file path (/files/update 10.30.csv)
    """
    # Try Frappe file path first (production)
    frappe_file_path = "/files/update 10.30.csv"
    local_file_path = "/Users/viralkansodiya/frappe-bench/update 10.30.csv"
    
    csv_file_path = None
    
    # Check if it's a Frappe file path
    if frappe_file_path.startswith("/files/"):
        # Get the site path
        site_path = frappe.get_site_path()
        # Remove /files/ prefix and construct full path
        file_name = frappe_file_path.replace("/files/", "")
        csv_file_path = os.path.join(site_path, "public", "files", file_name)
        
        # If file doesn't exist, try local path
        if not os.path.exists(csv_file_path):
            csv_file_path = local_file_path
    else:
        csv_file_path = local_file_path
    
    if not os.path.exists(csv_file_path):
        frappe.log_error(f"CSV file not found. Tried: {csv_file_path}", "Material Receipt CSV Import")
        frappe.throw(f"CSV file not found at: {csv_file_path}")
        return
    
    # Read CSV file
    csv_data = read_csv_file(csv_file_path)
    
    if not csv_data:
        frappe.log_error("No data found in CSV file", "Material Receipt CSV Import")
        return
    
    # Create a single Stock Entry with all items from CSV
    try:
        stock_entry = create_stock_entry(csv_data)
        frappe.db.commit()
        frappe.msgprint(
            f"Created Stock Entry {stock_entry.name} with {len(stock_entry.items)} items",
            title="Import Status"
        )
    except Exception as e:
        error_message = str(e)
        # Log the full error in the error log's message field, not title
        frappe.log_error(
            message=error_message,
            title="Material Receipt CSV Import Error"
        )
        frappe.db.rollback()
        frappe.throw(f"Error creating Stock Entry. Check Error Log for details.")


def read_csv_file(file_path):
    """Read CSV file and return data rows"""
    data = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        # Read all lines
        lines = f.readlines()
        
        if len(lines) < 3:
            frappe.log_error("CSV file has insufficient rows", "Material Receipt CSV Import")
            return []
        
        # Row 3 (index 2) contains the field names mapping
        # Parse it to get the field names
        field_names_line = lines[2].strip()
        field_names = [field.strip() for field in field_names_line.split(',')]
        
        # Read data starting from row 8 (index 7) onwards
        for idx in range(7, len(lines)):
            line = lines[idx].strip()
            
            # Skip empty lines
            if not line:
                continue
            
            # Skip separator rows
            if '------' in line:
                continue
            
            # Parse CSV line
            reader = csv.reader([line])
            row_values = next(reader)
            
            # Create dict mapping field names to values
            row_dict = {}
            for i, field_name in enumerate(field_names):
                if i < len(row_values):
                    row_dict[field_name] = row_values[i].strip()
                else:
                    row_dict[field_name] = ''
            
            # Skip rows without invoice_no
            if not row_dict.get('invoice_no') or row_dict.get('invoice_no') == '':
                continue
            
            data.append(row_dict)
    
    return data


def create_stock_entry(csv_data):
    """Create a single Material Receipt Stock Entry with all items from CSV"""
    
    if not csv_data:
        frappe.throw("No data provided to create Stock Entry")
    
    # Get common fields from first row
    first_row = csv_data[0]
    supplier_invoice_no = first_row.get('invoice_no', '').strip()
    supplier_invoice_date = parse_date(first_row.get('custom_supplier_invoice_date', ''))
    bill_of_entry = first_row.get('bill_of_entry', '').strip()
    boe_date = parse_date(first_row.get('custom_boe_date', ''))
    vender_name = first_row.get('custom_vender_name', '').strip()
    
    # Get target warehouse from first row (assuming all rows have same warehouse)
    target_warehouse = first_row.get('t_warehouse', '').strip()
    
    if not target_warehouse:
        frappe.throw("Target warehouse is required")
    
    # Get company from warehouse
    company = frappe.db.get_value("Warehouse", target_warehouse, "company")
    if not company:
        frappe.throw(f"Company not found for warehouse {target_warehouse}")
    
    # Create Stock Entry
    stock_entry = frappe.new_doc("Stock Entry")
    stock_entry.stock_entry_type = "Material Receipt"
    stock_entry.purpose = "Material Receipt"
    stock_entry.company = company
    stock_entry.supplier_invoice_no = supplier_invoice_no
    stock_entry.custom_supplier_invoice_date = supplier_invoice_date
    stock_entry.bill_of_entry = bill_of_entry
    stock_entry.custom_boe_date = boe_date
    stock_entry.custom_vender_name = vender_name
    
    # Set posting date from invoice date or today
    if supplier_invoice_date:
        stock_entry.posting_date = supplier_invoice_date
    else:
        stock_entry.posting_date = today()
    
    
    # Add all items from CSV rows
    valid_items_count = 0
    missing_items = []
    
    for idx, row in enumerate(csv_data, start=1):
        item_code = row.get('item_code', '').strip()
        qty = flt(row.get('qty', 0))
        
        # Skip rows without valid item code or quantity
        if not item_code or qty <= 0:
            continue
        
        # Check if item exists
        if not frappe.db.exists("Item", item_code):
            missing_items.append(f"Row {idx}: {item_code}")
            continue
        
        # Get item details
        item_stock_uom = frappe.db.get_value("Item", item_code, "stock_uom")
        
        # Use warehouse from row if different, otherwise use first row's warehouse
        row_warehouse = row.get('t_warehouse', '').strip() or target_warehouse
        
        # Create item row
        item_dict = {
            "item_code": item_code,
            "t_warehouse": row_warehouse,
            "qty": qty,
            "uom": row.get('uom', '').strip() or item_stock_uom,
            "stock_uom": item_stock_uom,
            "conversion_factor": flt(row.get('conversion_factor', 1)) or 1.0,
            "transfer_qty": flt(row.get('transfer_qty', qty)) or qty,
        }
        
        # Add optional fields
        if row.get('batch_no', '').strip():
            item_dict["batch_no"] = row.get('batch_no', '').strip()
        
        if row.get('serial_no', '').strip():
            item_dict["serial_no"] = row.get('serial_no', '').strip()
        
        if row.get('cost_center', '').strip():
            item_dict["cost_center"] = row.get('cost_center', '').strip()
        
        if row.get('expense_account', '').strip():
            item_dict["expense_account"] = row.get('expense_account', '').strip()
        
        if row.get('basic_rate', '').strip():
            item_dict["basic_rate"] = flt(row.get('basic_rate', 0))
        
        if row.get('description', '').strip():
            item_dict["description"] = row.get('description', '').strip()
        
        if row.get('item_name', '').strip():
            item_dict["item_name"] = row.get('item_name', '').strip()
        
        
        stock_entry.append("items", item_dict)
        valid_items_count += 1
    
    if missing_items:
        # Log missing items but don't fail the entire import
        frappe.log_error(
            message=f"The following items were not found and were skipped: {', '.join(missing_items[:50])}" +
                   (f" and {len(missing_items)-50} more" if len(missing_items) > 50 else ""),
            title="Missing Items During Import"
        )
    
    if not stock_entry.items:
        frappe.throw("No valid items found in CSV data")
    
    # Set missing values
    stock_entry.set_missing_values()
    
    # Save Stock Entry
    stock_entry.insert(ignore_permissions=True)
    
    return stock_entry


def parse_date(date_str):
    """Parse date string in various formats"""
    if not date_str or not date_str.strip():
        return None
    
    date_str = date_str.strip()
    
    # Try different date formats
    date_formats = [
        '%d/%m/%y',      # 09/02/24
        '%d-%m-%y',      # 09-02-24
        '%d/%m/%Y',      # 09/02/2024
        '%d-%m-%Y',      # 09-02-2024
        '%Y-%m-%d',      # 2024-02-09
    ]
    
    for fmt in date_formats:
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    
    # If all formats fail, log error and return None
    frappe.log_error(f"Could not parse date: {date_str}", "Material Receipt CSV Import")
    return None