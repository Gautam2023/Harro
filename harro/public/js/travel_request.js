frappe.ui.form.on("Travel Itinerary", {
    check_in_date: function (frm, cdt, cdn) {
        console.log("hello Hello jell")
        calculate_nights(cdt, cdn);
    },

    check_out_date: function (frm, cdt, cdn) {
        calculate_nights(cdt, cdn);
    }
});

function calculate_nights(cdt, cdn) {
    let row = locals[cdt][cdn];

    if (row.check_in_date && row.check_out_date) {
        let check_in_date = frappe.datetime.str_to_obj(row.check_in_date);
        let check_out_date = frappe.datetime.str_to_obj(row.check_out_date);

        let diff = frappe.datetime.get_diff(check_out_date, check_in_date);

        // Number of nights (checkout - checkin)
        room_night = diff > 0 ? diff : 0;
        console.log(room_night)
        frappe.model.set_value(cdt, cdn, "room_night", room_night)

        refresh_field("travel_itinerary");
    }
}
