// Copyright (c) 2026, Fosserp and contributors
// For license information, please see license.txt
frappe.query_reports["Stock Ledger With Rack and Bin location"] = {
	filters: [
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company"),
			reqd: 1,
		},
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: frappe.datetime.add_months(frappe.datetime.get_today(), -1),
			reqd: 1,
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			default: frappe.datetime.get_today(),
			reqd: 1,
		},
		{
			fieldname: "warehouse",
			label: __("Warehouses"),
			fieldtype: "MultiSelectList",
			options: "Warehouse",
			get_data: function (txt) {
				const company = frappe.query_report.get_filter_value("company");

				return frappe.db.get_link_options("Warehouse", txt, {
					company: company,
				});
			},
		},
		{
			fieldname: "item_code",
			label: __("Items"),
			fieldtype: "MultiSelectList",
			options: "Item",
			get_data: async function (txt) {
				let { message: data } = await frappe.call({
					method: "erpnext.controllers.queries.item_query",
					args: {
						doctype: "Item",
						txt: txt,
						searchfield: "name",
						start: 0,
						page_len: 10,
						filters: {},
						as_dict: 1,
					},
				});
				data = data.map(({ name, ...rest }) => {
					return {
						value: name,
						description: Object.values(rest),
					};
				});

				return data || [];
			},
		},
		{
			fieldname: "item_group",
			label: __("Item Group"),
			fieldtype: "Link",
			options: "Item Group",
		},
		{
			fieldname: "batch_no",
			label: __("Batch No"),
			fieldtype: "Link",
			options: "Batch",
			on_change() {
				const batch_no = frappe.query_report.get_filter_value("batch_no");
				if (batch_no) {
					frappe.query_report.set_filter_value("segregate_serial_batch_bundle", 1);
				} else {
					frappe.query_report.set_filter_value("segregate_serial_batch_bundle", 0);
				}
			},
		},
		{
			fieldname: "brand",
			label: __("Brand"),
			fieldtype: "Link",
			options: "Brand",
		},
		{
			fieldname: "voucher_no",
			label: __("Voucher #"),
			fieldtype: "Data",
		},
		{
			fieldname: "project",
			label: __("Project"),
			fieldtype: "Link",
			options: "Project",
		},
		{
			fieldname: "include_uom",
			label: __("Include UOM"),
			fieldtype: "Link",
			options: "UOM",
		},
		{
			fieldname: "valuation_field_type",
			label: __("Valuation Field Type"),
			fieldtype: "Select",
			width: "80",
			options: "Currency\nFloat",
			default: "Currency",
		},
		{
			fieldname: "segregate_serial_batch_bundle",
			label: __("Segregate Serial / Batch Bundle"),
			fieldtype: "Check",
			default: 1,
		},
	],
	formatter: function (value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		if (column.fieldname == "out_qty" && data && data.out_qty < 0) {
			value = "<span style='color:red'>" + value + "</span>";
		} else if (column.fieldname == "in_qty" && data && data.in_qty > 0) {
			value = "<span style='color:green'>" + value + "</span>";
		}

		return value;
	},

	onload: function (report) {
		report.page.add_inner_button(__("View Stock Balance"), function () {
			var filters = report.get_values();
			frappe.set_route("query-report", "Stock Balance", filters);
		});
	},
};

function add_inventory_dimensions (report_name, index) {
	let filters = frappe.query_reports[report_name].filters;

	frappe.call({
		method: "erpnext.stock.doctype.inventory_dimension.inventory_dimension.get_inventory_dimensions",
		callback: function (r) {
			if (r.message && r.message.length) {
				r.message.forEach((dimension) => {
					let existing_filter = filters.filter((el) => el.fieldname === dimension["fieldname"]);

					if (!existing_filter.length) {
						filters.splice(index, 0, {
							fieldname: dimension["fieldname"],
							label: __(dimension["doctype"]),
							fieldtype: "MultiSelectList",
							depends_on:
								report_name === "Stock Balance"
									? "eval:doc.show_dimension_wise_stock === 1"
									: "",
							get_data: function (txt) {
								return frappe.db.get_link_options(dimension["doctype"], txt);
							},
						});
					} else {
						existing_filter[0]["fieldtype"] = "MultiSelectList";
						existing_filter[0]["get_data"] = function (txt) {
							return frappe.db.get_link_options(dimension["doctype"], txt);
						};
					}
				});
			}
		},
	});
}

add_inventory_dimensions("Stock Ledger With Rack and Bin location", 10);