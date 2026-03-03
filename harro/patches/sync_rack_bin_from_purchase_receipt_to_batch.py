"""
Patch: Sync rack and bin_location from Purchase Receipt Item to Batch.

When Purchase Receipt items have rack and bin_location set, update the
corresponding Batch records with those values. This ensures Batch always
reflects the storage location from the Purchase Receipt.
"""

import frappe


def execute():
	# Check if Batch has rack and bin_location fields (custom fields from harro)
	batch_meta = frappe.get_meta("Batch")
	if not batch_meta.has_field("rack") or not batch_meta.has_field("bin_location"):
		return

	# Get all Purchase Receipt Items with rack or bin_location (from submitted PRs)
	pr_items = frappe.db.sql(
		"""
		SELECT pri.name, pri.parent, pri.rack, pri.bin_location
		FROM `tabPurchase Receipt Item` pri
		INNER JOIN `tabPurchase Receipt` pr ON pr.name = pri.parent
		WHERE pr.docstatus = 1
		  AND (pri.rack IS NOT NULL AND pri.rack != ''
		       OR pri.bin_location IS NOT NULL AND pri.bin_location != '')
		""",
		as_dict=True,
	)

	if not pr_items:
		return

	updated_batches = set()

	for item in pr_items:
		update_data = {}
		if item.get("rack"):
			update_data["rack"] = item.rack
		if item.get("bin_location"):
			update_data["bin_location"] = item.bin_location

		if not update_data:
			continue

		# Find batches linked via Serial and Batch Bundle
		batches = frappe.db.sql(
			"""
			SELECT DISTINCT sbe.batch_no
			FROM `tabSerial and Batch Entry` sbe
			INNER JOIN `tabSerial and Batch Bundle` sbb
				ON sbb.name = sbe.parent
			WHERE sbb.voucher_type = 'Purchase Receipt'
			  AND sbb.voucher_no = %(pr_name)s
			  AND sbb.voucher_detail_no = %(item_name)s
			  AND sbb.docstatus = 1
			  AND sbe.batch_no IS NOT NULL
			""",
			{"pr_name": item.parent, "item_name": item.name},
			as_dict=True,
		)

		for row in batches:
			if row.batch_no and row.batch_no not in updated_batches:
				frappe.db.set_value(
					"Batch",
					row.batch_no,
					update_data,
					update_modified=True,
				)
				updated_batches.add(row.batch_no)

	frappe.db.commit()
