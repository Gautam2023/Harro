import frappe
from frappe.core.doctype.version.version import get_diff
from erpnext.stock.report.stock_balance.stock_balance import execute as get_stock_balance
from frappe.utils import today


@frappe.whitelist()
def get_bom_diff(bom1, bom2):
	from frappe.model import table_fields

	if bom1 == bom2:
		frappe.throw(
			_("BOM 1 {0} and BOM 2 {1} should not be same").format(frappe.bold(bom1), frappe.bold(bom2))
		)

	doc1 = frappe.get_doc("BOM", bom1)
	doc2 = frappe.get_doc("BOM", bom2)

	out = get_diff(doc1, doc2)
	out.row_changed = []
	out.added = []
	out.removed = []

	meta = doc1.meta

	identifiers = {
		"operations": "operation",
		"items": "item_code",
		"scrap_items": "item_code",
		"exploded_items": "item_code",
	}

	for df in meta.fields:
		old_value, new_value = doc1.get(df.fieldname), doc2.get(df.fieldname)

		if df.fieldtype in table_fields:
			identifier = identifiers[df.fieldname]
			# make maps
			old_row_by_identifier, new_row_by_identifier = {}, {}
			for d in old_value:
				old_row_by_identifier[d.get(identifier)] = d
			for d in new_value:
				new_row_by_identifier[d.get(identifier)] = d

			# check rows for additions, changes
			for i, d in enumerate(new_value):
				if d.get(identifier) in old_row_by_identifier:
					diff = get_diff(old_row_by_identifier[d.get(identifier)], d, for_child=True)
					if diff and diff.changed:
						out.row_changed.append((df.fieldname, i, d.get(identifier), diff.changed))
				else:
					item_code = d.get("item_code")

					filters = frappe._dict({
						'company': 'Harro Hoefliger Packaging Systems Private Limited',
						'from_date': '2022-01-01',
						'item_code': [item_code],
						'rack': [],
						'to_date': today(),
						'valuation_field_type': 'Currency',
						'warehouse': ['All Warehouses - HH']
					})
					print(item_code)
					stock_balance = get_stock_balance(filters)

					balance = stock_balance[1]
					
					qty_available = sum([
						row.bal_qty for row in balance
					])
					
					d.update({
						"qty_available" : qty_available
					})

					out.added.append([df.fieldname, d.as_dict()])

			# check for deletions
			for d in old_value:
				if d.get(identifier) not in new_row_by_identifier:
					
					item_code = d.get("item_code")

					filters = frappe._dict({
						'company': 'Harro Hoefliger Packaging Systems Private Limited',
						'from_date': '2022-01-01',
						'item_code': [item_code],
						'rack': [],
						'to_date': today(),
						'valuation_field_type': 'Currency',
						'warehouse': ['All Warehouses - HH']
					})

					stock_balance = get_stock_balance(filters)

					qty_available = sum([
						row.bal_qty for row in balance
					])
					
					d.update({
						"qty_available" : qty_available
					})

					out.removed.append([df.fieldname, d.as_dict()])

	return out