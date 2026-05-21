import frappe
from frappe.utils import get_link_to_form, now
from frappe.utils import getdate

WORKFLOW_TO_TRIP_STATUS = {
    "Trip Cancelled": "Cancelled",
    "Trip Rescheduled": "Rescheduled",
}

def on_update(doc, method=None):
    trip_status = WORKFLOW_TO_TRIP_STATUS.get(doc.workflow_state)

    if trip_status:
        tr_updated = False
        for row in doc.itinerary:
            if row.custom_flight_booking_status != trip_status:
                row.custom_flight_booking_status = trip_status
                row.custom_hotel_booking_status = trip_status
                tr_updated = True

        if tr_updated:
            doc.flags.ignore_permissions = True
            doc.save()

    tr_map = {row.name: row for row in doc.itinerary}

    tp_parents = frappe.get_all(
        "Travel Planning Employee Details",
        filters={"travel_request": doc.name},
        pluck="parent"
    )

    tp_parents = list(set(tp_parents))  

    linked_tp_names = []

    for tp_name in tp_parents:
        tp = frappe.get_doc("Travel Planning", tp_name)
        updated = False

        for row in tp.travel_itinerary:
            if row.travel_request != doc.name:
                continue

            # Get corresponding Travel Request itinerary row
            tr_row = tr_map.get(row.travel_request_itinerary)

            # Sync Taxi Required
            if tr_row and row.custom_taxi_required != tr_row.custom_taxi_required:
                row.custom_taxi_required = tr_row.custom_taxi_required
                updated = True

            # Sync reason for cancellation
            if tr_row and row.custom_reason_for_cancellation != tr_row.custom_reason_for_cancellation:
                row.custom_reason_for_cancellation = tr_row.custom_reason_for_cancellation
                updated = True

            # Sync reason for rescheduling
            if tr_row and row.custom_reason_for_rescheduling != tr_row.custom_reason_for_rescheduling:
                row.custom_reason_for_rescheduling = tr_row.custom_reason_for_rescheduling
                updated = True

            # Sync Workflow Status
            if trip_status:
                if row.custom_flight_booking_status != trip_status:
                    row.custom_flight_booking_status = trip_status
                    row.custom_hotel_booking_status = trip_status
                    updated = True

        if updated:
            tp.flags.ignore_permissions = True
            tp.save()
            linked_tp_names.append(tp.name)

    if trip_status and linked_tp_names:
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
            tp_links = [get_link_to_form("Travel Planning", tp) for tp in linked_tp_names]
            tp_links_html = ", ".join(tp_links)

            html_message = f"""
            <p>Hello Travel Manager,</p>

            <p>The following Travel Request has been <strong>{trip_status}</strong>:</p>
            <p>Travel Request: {travel_request_link}</p>

            <p>Linked Travel Planning(s): {tp_links_html}</p>

            <p>Regards,<br>HR Team</p>
            """

            # frappe.sendmail(
            #     recipients=recipient_emails,
            #     subject=f"Travel Request {doc.name} {trip_status}",
            #     message=html_message,
            #     delayed=False
            # )


def sync_travel_planning_from_travel_request(doc, method=None):

    travel_planning = frappe.db.get_value(
        "Travel Planning Employee Details",
        {"travel_request": doc.name},
        "parent"
    )

    if not travel_planning:
        return

    tp_doc = frappe.get_doc("Travel Planning", travel_planning)

    added = False

    for tr_row in doc.itinerary:

        if not tr_row.name:
            continue

        tp_rows = frappe.get_all(
            "Travel Planning Employee Details",
            filters={
                "travel_request": doc.name,
                "travel_request_itinerary": tr_row.name
            },
            fields=["name"]
        )

        update_values = {
            "custom_flight_booking_status": tr_row.custom_flight_booking_status,
            "custom_hotel_booking_status": tr_row.custom_hotel_booking_status,
            "custom_status": tr_row.custom_status
        }
        if tp_rows:
            for tp in tp_rows:
                frappe.db.set_value(
                    "Travel Planning Employee Details",
                    tp.name,
                    update_values,
                    update_modified=False
                )
        else:
            tp_doc.append("travel_itinerary", {
                "travel_request": doc.name,
                "travel_request_itinerary": tr_row.name,
                "employee_name": doc.employee_name,
                "custom_contact_email": doc.prefered_email,
                "employee_hh_id": doc.custom_hh__employee_id,
                "travel_from": tr_row.travel_from,
                "travel_to": tr_row.travel_to,
                "mode_of_travel": tr_row.mode_of_travel,
                "extra_baggage": tr_row.custom_extra_baggage,
                "lodging_required": tr_row.lodging_required,
                "check_in_date": tr_row.check_in_date,
                "check_out_date": tr_row.check_out_date,
                "room_night": tr_row.room_night,
                "custom_taxi_required": tr_row.custom_taxi_required,
                **update_values
            })
            added = True

    if added:
        tp_doc.flags.ignore_validate = True
        tp_doc.flags.ignore_mandatory = True
        tp_doc.flags.ignore_links = True
        tp_doc.flags.ignore_permissions = True

        tp_doc.save(ignore_permissions=True, ignore_version=True)
