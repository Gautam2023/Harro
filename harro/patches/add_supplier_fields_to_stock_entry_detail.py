import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
    """Create supplier/bill fields on Stock Entry Detail and migrate existing data."""
    fields = {
        "Stock Entry Detail": [
            {
                "fieldname": "supplier_invoice_no",
                "label": "Supplier Invoice No",
                "fieldtype": "Data",
                "insert_after": "invoice_no",
            },
            {
                "fieldname": "supplier_invoice_date",
                "label": "Supplier Invoice Date",
                "fieldtype": "Date",
                "insert_after": "custom_supplier_invoice_date",
            },
            {
                "fieldname": "bill_of_entry_date",
                "label": "Bill of Entry Date",
                "fieldtype": "Date",
                "insert_after": "custom_boe_date",
            },
            {
                "fieldname": "supplier",
                "label": "Supplier",
                "fieldtype": "Link",
                "options": "Supplier",
                "insert_after": "vender_name",
            },
        ]
    }

    create_custom_fields(fields)

    # Ensure the doctype is reloaded so new fields are available
    try:
        frappe.reload_doc("stock", "doctype", "stock_entry_detail")
    except Exception:
        # If reload fails for any reason, still attempt data migration using direct SQL
        pass

    # Migrate values:
    # invoice_no -> supplier_invoice_no
    frappe.db.sql(
        """
        UPDATE `tabStock Entry Detail`
        SET supplier_invoice_no = invoice_no
        WHERE (supplier_invoice_no IS NULL OR supplier_invoice_no = '')
          AND invoice_no IS NOT NULL AND invoice_no != ''
        """
    )

    # custom_supplier_invoice_date -> supplier_invoice_date (if source field exists)
    if "custom_supplier_invoice_date" in frappe.db.get_table_columns("Stock Entry Detail"):
        frappe.db.sql(
            """
            UPDATE `tabStock Entry Detail`
            SET supplier_invoice_date = custom_supplier_invoice_date
            WHERE (supplier_invoice_date IS NULL)
              AND custom_supplier_invoice_date IS NOT NULL
            """
        )

    # custom_boe_date -> bill_of_entry_date (if source field exists)
    if "custom_boe_date" in frappe.db.get_table_columns("Stock Entry Detail"):
        frappe.db.sql(
            """
            UPDATE `tabStock Entry Detail`
            SET bill_of_entry_date = custom_boe_date
            WHERE (bill_of_entry_date IS NULL)
              AND custom_boe_date IS NOT NULL
            """
        )

    # vender_name -> supplier
    if "vender_name" in frappe.db.get_table_columns("Stock Entry Detail"):
        frappe.db.sql(
            """
            UPDATE `tabStock Entry Detail`
            SET supplier = vender_name
            WHERE (supplier IS NULL OR supplier = '')
              AND vender_name IS NOT NULL AND vender_name != ''
            """
        )

