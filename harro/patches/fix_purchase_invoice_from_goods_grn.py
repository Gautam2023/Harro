import frappe


def execute():
	if frappe.db.has_column("Purchase Invoice", "from_goods_grn"):
		frappe.db.sql(
			"UPDATE `tabPurchase Invoice` SET `from_goods_grn` = 0 WHERE `from_goods_grn` = '' OR `from_goods_grn` IS NULL"
		)
