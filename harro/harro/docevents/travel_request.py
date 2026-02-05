import frappe

WORKFLOW_TO_TRIP_STATUS = {
    "Trip Cancelled": "Cancelled",
    "Trip Rescheduled": "Rescheduled",
}

def on_update(doc, method=None):
    trip_status = WORKFLOW_TO_TRIP_STATUS.get(doc.workflow_state)
    if not trip_status:
        return

    travel_plannings = frappe.get_all(
        "Travel Planning",
        fields=["name"]
    )

    for tp_row in travel_plannings:
        tp = frappe.get_doc("Travel Planning", tp_row.name)
        updated = False

        for row in tp.travel_itinerary:
            if row.travel_request == doc.name:
                if row.custom_flight_booking_status != trip_status:
                    row.custom_flight_booking_status = trip_status
                    row.custom_hotel_booking_status = trip_status
                    updated = True

        if updated:
            tp.flags.ignore_permissions = True
            tp.save()
