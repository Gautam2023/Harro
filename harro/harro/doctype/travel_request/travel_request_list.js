frappe.listview_settings["Travel Request"] = {
	onload: function (listview) {
        const method = "harro.harro.docevents.travel_planning.create_travel_plan"
		listview.page.add_action_item(__("Travel Plan"), function () {
			listview.call_for_selected_items(method);
		});
	},
};
