import frappe


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_bin_location(doctype, txt, searchfield, start, page_len, filters):
    conditions = "rack_name = %(rack)s"
    params = {"rack": filters.get("rack")}

    # Apply text filter only when 'txt' is not empty
    if txt:
        conditions += " AND name LIKE %(txt)s"
        params["txt"] = f"%{txt}%"

    return frappe.db.sql(f"""
        SELECT name
        FROM `tabBin Location`
        WHERE {conditions}
        LIMIT %(start)s, %(page_len)s
    """, {
        **params,
        "start": start,
        "page_len": page_len
    })
