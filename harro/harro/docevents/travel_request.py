import frappe
from frappe.utils import get_link_to_form

WORKFLOW_TO_TRIP_STATUS = {
    "Trip Cancelled": "Cancelled",
    "Trip Rescheduled": "Rescheduled",
}


def on_update(doc, method=None):
    """
    Single entry point: ALWAYS sync everything from Travel Request → Travel Planning
    """

    sync_travel_planning_from_travel_request(doc)

    trip_status = WORKFLOW_TO_TRIP_STATUS.get(doc.workflow_state)

    if not trip_status:
        return

    for row in doc.itinerary:
        if row.custom_flight_booking_status != trip_status:
            frappe.db.set_value(
                "Travel Itinerary",
                row.name,
                {
                    "custom_flight_booking_status": trip_status,
                    "custom_hotel_booking_status": trip_status,
                },
                update_modified=False
            )

    frappe.db.commit()


def sync_travel_planning_from_travel_request(doc, method=None):

    # Get all linked Travel Planning docs
    tp_parents = frappe.get_all(
        "Travel Planning Employee Details",
        filters={"travel_request": doc.name},
        pluck="parent"
    )

    tp_parents = list(set(tp_parents))

    if not tp_parents:
        return

    linked_tp_names = []

    tr_map = {row.name: row for row in doc.itinerary}

    for tp_name in tp_parents:

        tp = frappe.get_doc("Travel Planning", tp_name)
        updated = False

        for row in tp.travel_itinerary:

            if row.travel_request != doc.name:
                continue

            tr_row = tr_map.get(row.travel_request_itinerary)

            if not tr_row:
                continue

            # -----------------------------
            # ALWAYS SYNC FIELD BY FIELD
            # -----------------------------

            if row.custom_taxi_required != tr_row.custom_taxi_required:
                row.custom_taxi_required = tr_row.custom_taxi_required
                updated = True

            if row.custom_reason_for_cancellation != tr_row.custom_reason_for_cancellation:
                row.custom_reason_for_cancellation = tr_row.custom_reason_for_cancellation
                updated = True

            if row.custom_reason_for_rescheduling != tr_row.custom_reason_for_rescheduling:
                row.custom_reason_for_rescheduling = tr_row.custom_reason_for_rescheduling
                updated = True

            if row.custom_revised_travel_date != tr_row.custom_revised_travel_date:
                row.custom_revised_travel_date = tr_row.custom_revised_travel_date
                updated = True

            if row.custom_revised_return_date != tr_row.custom_revised_return_date:
                row.custom_revised_return_date = tr_row.custom_revised_return_date
                updated = True

            if row.custom_flight_booking_status != tr_row.custom_flight_booking_status:
                row.custom_flight_booking_status = tr_row.custom_flight_booking_status
                updated = True

            if row.custom_hotel_booking_status != tr_row.custom_hotel_booking_status:
                row.custom_hotel_booking_status = tr_row.custom_hotel_booking_status
                updated = True

            if row.custom_status != tr_row.custom_status:
                row.custom_status = tr_row.custom_status
                updated = True

        if updated:
            tp.flags.ignore_permissions = True
            tp.save()
            linked_tp_names.append(tp.name)

    # -----------------------------
    # OPTIONAL EMAIL NOTIFICATION
    # -----------------------------
    if linked_tp_names:

        travel_manager_users = frappe.get_all(
            "Has Role",
            filters={"role": "Travel Desk Manager"},
            pluck="parent"
        )

        recipient_emails = []

        for user in travel_manager_users:
            email = frappe.get_value("User", user, "email")
            if email:
                recipient_emails.append(email)

        if recipient_emails:

            travel_request_link = get_link_to_form("Travel Request", doc.name)
            tp_links = [
                get_link_to_form("Travel Planning", tp)
                for tp in linked_tp_names
            ]

            tp_links_html = ", ".join(tp_links)

            html_message = f"""
            <p>Hello Travel Manager,</p>

            <p>Travel Request has been updated:</p>
            <p><b>Travel Request:</b> {travel_request_link}</p>

            <p><b>Linked Travel Planning(s):</b> {tp_links_html}</p>

            <p>Regards,<br>HR Team</p>
            """

            # frappe.sendmail(
            #     recipients=recipient_emails,
            #     subject=f"Travel Request {doc.name} Updated",
            #     message=html_message
            # )