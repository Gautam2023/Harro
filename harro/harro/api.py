import frappe

@frappe.whitelist()
def get_supplier_list(doctype, txt, searchfield, start, page_len, filters):
    filters = frappe._dict(filters)
    rfq_doc = frappe.get_doc("Request for Quotation", filters.get("name"))

    sq_supplier_list = frappe.db.sql(f"""
                                     Select sq.supplier
                                     From `tabSupplier Quotation` as sq
                                     Left Join `tabSupplier Quotation Item` as sqi ON sqi.parent = sq.name
                                     Where sq.docstatus < 2 and sqi.request_for_quotation = '{rfq_doc.name}'
                                """, as_dict=1)
    
    sq_supplier = [
        row.supplier for row in sq_supplier_list
    ]
    
    rfq_supplier_list = [
        row.supplier for row in rfq_doc.suppliers
    ]

    final_supplier_list = tuple([(s,) for s in rfq_supplier_list if s not in sq_supplier])

    return final_supplier_list



@frappe.whitelist()
def get_open_tasks_for_user():
    user = frappe.session.user

    # find task assigned to currently logged in user
    todos = frappe.db.get_all(
        "ToDo",
        filters = {
            "reference_type": "Task",
            "allocated_to": user,
            "status": "Open"
        },
        pluck = "reference_name"
    )

    if not todos:
        return {
            "value": 0,
            "fieldtype": "Int"
        }
    
    # count only valid tasks that are not completed/cancelled/template
    count = frappe.db.count(
        "Task",
        filters={
            "name": ["in",todos],
            "status": ["not in", ["Completed","Cancelled","Template"]]
        }
    )

    return {
        "value": count,
        "fieldtype": "Int"
    }