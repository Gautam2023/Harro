import frappe

def execute():
    update_purchase_receipt_invoice_fields()

def update_purchase_receipt_invoice_fields():
    frappe.db.sql("""
                    UPDATE `tabPurchase Receipt`
                    SET 
                        supplier_invoice_no = custom_supplier_invoice_no,
                        supplier_invoice_date = custom_supplier_invoice_date
                    WHERE 
                        custom_supplier_invoice_no IS NOT NULL
                        OR custom_supplier_invoice_date IS NOT NULL;
                """, as_dict=True)
    frappe.db.commit()
    print("Completed")