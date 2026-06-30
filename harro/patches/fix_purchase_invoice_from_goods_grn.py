import frappe


DECIMAL_COLUMNS = [
	"taxes_and_charges_added",
	"base_taxes_and_charges_deducted",
	"base_write_off_amount",
	"base_total_taxes_and_charges",
	"total_qty",
	"base_total",
	"base_rounded_total",
	"conversion_rate",
	"net_total",
	"base_grand_total",
	"total_advance",
	"rounded_total",
	"total_taxes_and_charges",
	"outstanding_amount",
	"taxes_and_charges_deducted",
	"base_discount_amount",
	"base_paid_amount",
	"base_tax_withholding_net_total",
	"grand_total",
	"additional_discount_percentage",
	"per_received",
	"paid_amount",
	"total_net_weight",
	"rounding_adjustment",
	"base_rounding_adjustment",
	"plc_conversion_rate",
	"discount_amount",
	"base_net_total",
	"itc_integrated_tax",
	"itc_central_tax",
	"write_off_amount",
	"itc_state_tax",
	"itc_cess_amount",
	"total",
	"base_taxes_and_charges_added",
]


def execute():
	if not frappe.db.table_exists("Purchase Invoice"):
		return

	set_clauses = []
	for col in DECIMAL_COLUMNS:
		if frappe.db.has_column("Purchase Invoice", col):
			set_clauses.append(f"`{col}` = CASE WHEN `{col}` = '' OR `{col}` IS NULL THEN 0 ELSE `{col}` END")

	if frappe.db.has_column("Purchase Invoice", "from_goods_grn"):
		set_clauses.append("`from_goods_grn` = CASE WHEN `from_goods_grn` = '' OR `from_goods_grn` IS NULL THEN 0 ELSE `from_goods_grn` END")

	if set_clauses:
		frappe.db.sql(f"UPDATE `tabPurchase Invoice` SET {', '.join(set_clauses)}")
