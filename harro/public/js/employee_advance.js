frappe.ui.form.on("Employee Advance", {
    custom_onward_travel_date: function (frm) {
        calculate_no_of_days(frm);
    },
    custom_return_travel_date: function (frm) {
        calculate_no_of_days(frm);
    },
});


function calculate_no_of_days(frm) {
    if (frm.doc.custom_onward_travel_date && frm.doc.custom_return_travel_date) {
        let onward_travel_date = frappe.datetime.str_to_obj(frm.doc.custom_onward_travel_date);
        let return_travel_date = frappe.datetime.str_to_obj(frm.doc.custom_return_travel_date);

        let diff = frappe.datetime.get_diff(return_travel_date, onward_travel_date)

        no_of_days = diff > 0 ? diff : 0;
        console.log("No of days", no_of_days);
        frm.set_value("custom_no_of_days", no_of_days)
    }
}