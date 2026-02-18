frappe.ui.form.on("Delivery Note", {
	refresh: function(frm) {
		// Add button to generate export report for submitted Delivery Notes
		if (frm.doc.docstatus === 1 && !frm.doc.is_return) {
			frm.add_custom_button(__("Export Report"), function() {
				frappe.call({
					method: "harro.harro.report.import_receipt.import_receipt.get_export_report_from_delivery_note",
					args: {
						delivery_note: frm.doc.name
					},
					callback: function(r) {
						if (r.message) {
							// Use Blob URL to avoid document.write() deprecation
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
					},
					error: function(r) {
						frappe.msgprint({
							title: __("Error"),
							message: __("Failed to generate export report. Please try again."),
							indicator: "red"
						});
					}
				});
			}, __("Reports"));
		}
	}
});
