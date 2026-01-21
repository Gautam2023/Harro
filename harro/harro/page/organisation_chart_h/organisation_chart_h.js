frappe.pages['organisation-chart-h'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Organisation Chart Harro',
		single_column: true
	});

	$(wrapper).bind("show", () => {
		frappe.require("hierarchy-chart.bundle.js", () => {
			let organizational_chart;
			let method = "harro.harro.page.organisation_chart_h.organizational_chart_h.get_children";

			if (frappe.is_mobile()) {
				organizational_chart = new hrms.HierarchyChartMobile("Employee", wrapper, method);
			} else {
				organizational_chart = new hrms.HierarchyChart("Employee", wrapper, method);
				console.log(organizational_chart);
			}

			frappe.breadcrumbs.add("HR");
			organizational_chart.show();
		});
	});
}