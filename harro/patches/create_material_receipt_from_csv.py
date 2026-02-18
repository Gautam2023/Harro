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
    
    # Group rows by invoice_no to create one Stock Entry per invoice
    grouped_data = group_by_invoice(csv_data)
    
    created_count = 0
    error_count = 0
    
    for invoice_no, items in grouped_data.items():
        try:
            create_stock_entry(invoice_no, items)
            created_count += 1
            frappe.db.commit()
        except Exception as e:
            error_count += 1
            frappe.log_error(
                f"Error creating Stock Entry for invoice {invoice_no}: {str(e)}",
                "Material Receipt CSV Import"
            )
            frappe.db.rollback()
    
    frappe.msgprint(
        f"Stock Entries created: {created_count}, Errors: {error_count}",
        title="Import Status"
    )


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


def group_by_invoice(csv_data):
    """Group CSV rows by invoice_no"""
    grouped = {}
    
    for row in csv_data:
        invoice_no = row.get('invoice_no', '').strip()
        
        if not invoice_no:
            continue
        
        if invoice_no not in grouped:
            grouped[invoice_no] = []
        
        grouped[invoice_no].append(row)
    
    return grouped


def create_stock_entry(invoice_no, items):
    """Create a Material Receipt Stock Entry for given invoice"""
    
    if not items:
        return
    
    # Get first item to extract common fields
    first_item = items[0]
    
    # Extract common fields from first item
    supplier_invoice_no = first_item.get('invoice_no', '').strip()
    supplier_invoice_date = parse_date(first_item.get('custom_supplier_invoice_date', ''))
    bill_of_entry = first_item.get('bill_of_entry', '').strip()
    boe_date = parse_date(first_item.get('custom_boe_date', ''))
    vender_name = first_item.get('custom_vender_name', '').strip()
    target_warehouse = first_item.get('t_warehouse', '').strip()
    
    if not target_warehouse:
        frappe.throw(f"Target warehouse is required for invoice {invoice_no}")
    
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
    
    # Add items
    for item_row in items:
        item_code = item_row.get('item_code', '').strip()
        qty = flt(item_row.get('qty', 0))
        
        if not item_code or qty <= 0:
            continue
        
        # Check if item exists
        if not frappe.db.exists("Item", item_code):
            frappe.log_error(
                f"Item {item_code} does not exist for invoice {invoice_no}",
                "Material Receipt CSV Import"
            )
            continue
        
        # Create item row
        item_dict = {
            "item_code": item_code,
            "t_warehouse": target_warehouse,
            "qty": qty,
            "uom": item_row.get('uom', '').strip() or frappe.db.get_value("Item", item_code, "stock_uom"),
            "stock_uom": frappe.db.get_value("Item", item_code, "stock_uom"),
            "conversion_factor": flt(item_row.get('conversion_factor', 1)) or 1.0,
            "transfer_qty": flt(item_row.get('transfer_qty', qty)) or qty,
        }
        
        # Add optional fields
        if item_row.get('batch_no', '').strip():
            item_dict["batch_no"] = item_row.get('batch_no', '').strip()
        
        if item_row.get('serial_no', '').strip():
            item_dict["serial_no"] = item_row.get('serial_no', '').strip()
        
        if item_row.get('cost_center', '').strip():
            item_dict["cost_center"] = item_row.get('cost_center', '').strip()
        
        if item_row.get('expense_account', '').strip():
            item_dict["expense_account"] = item_row.get('expense_account', '').strip()
        
        if item_row.get('basic_rate', '').strip():
            item_dict["basic_rate"] = flt(item_row.get('basic_rate', 0))
        
        if item_row.get('description', '').strip():
            item_dict["description"] = item_row.get('description', '').strip()
        
        if item_row.get('item_name', '').strip():
            item_dict["item_name"] = item_row.get('item_name', '').strip()
        
        # Add rack/bin location if provided
        if item_row.get('to_rack', '').strip():
            item_dict["to_rack"] = item_row.get('to_rack', '').strip()
        
        if item_row.get('to_bin_location', '').strip():
            item_dict["to_bin_location"] = item_row.get('to_bin_location', '').strip()
        
        stock_entry.append("items", item_dict)
    
    if not stock_entry.items:
        frappe.throw(f"No valid items found for invoice {invoice_no}")
    
    # Set missing values
    stock_entry.set_missing_values()
    
    # Save Stock Entry
    stock_entry.insert(ignore_permissions=True)
    
    frappe.msgprint(f"Created Stock Entry {stock_entry.name} for invoice {invoice_no}")
    
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
