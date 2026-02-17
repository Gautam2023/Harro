// Copyright (c) 2026, Fosserp and contributors
// For license information, please see license.txt

frappe.query_reports["Import Receipt"] = {
	"filters": [
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
			label: __("Warehouse"),
			fieldtype: "Link",
			options: "Warehouse",
			get_query: function() {
				return {
					filters: {
						company: frappe.query_report.get_filter_value("company")
					}
				};
			},
		},
		{
			fieldname: "show_outward",
			label: __("Show Outward Goods (Removals)"),
			fieldtype: "Check",
			default: 0,
		},
	],
	"onload": function(report) {
		// Add print format button
		report.page.add_inner_button(__("Print Format"), function() {
			frappe.call({
				method: "harro.harro.report.import_receipt.import_receipt.get_print_format_html",
				args: {
					filters: report.get_filter_values()
				},
				callback: function(r) {
					if (r.message) {
						// Use Blob URL to avoid document.write() deprecation
						// Ensure UTF-8 encoding for proper currency symbol display
						var htmlContent = r.message;
						// Add charset if not present at the beginning
						if (!htmlContent.includes('<meta charset') && !htmlContent.includes('charset=')) {
							htmlContent = '<meta charset="UTF-8">\n' + htmlContent;
						}
						var blob = new Blob([htmlContent], { type: 'text/html;charset=utf-8' });
						var url = URL.createObjectURL(blob);
						var print_window = window.open(url, '_blank');
						
						if (print_window) {
							print_window.onload = function() {
								setTimeout(function() {
									print_window.print();
									// Clean up the blob URL after printing
									setTimeout(function() {
										URL.revokeObjectURL(url);
									}, 1000);
								}, 250);
							};
							// Fallback if onload doesn't fire
							setTimeout(function() {
								if (print_window.document.readyState === 'complete') {
									print_window.print();
									URL.revokeObjectURL(url);
								}
							}, 500);
						}
					}
				}
			});
		});
	}
};
