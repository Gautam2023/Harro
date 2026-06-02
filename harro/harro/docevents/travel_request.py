import frappe
from frappe.utils import get_link_to_form

WORKFLOW_TO_TRIP_STATUS = {
    "Trip Cancelled": "Cancelled",
    "Trip Rescheduled": "Rescheduled",
}


def on_update(doc, method=None):

    trip_status = WORKFLOW_TO_TRIP_STATUS.get(doc.workflow_state)

    if trip_status:
        for row in doc.itinerary:
            if row.custom_flight_booking_status != trip_status:  # guard preserved
                # Update in-memory first so sync picks it up
                row.custom_flight_booking_status = trip_status
                row.custom_hotel_booking_status = trip_status
                row.custom_status = trip_status

                # Persist to DB
                frappe.db.set_value(
                    "Travel Itinerary",
                    row.name,
                    {
                        "custom_flight_booking_status": trip_status,
                        "custom_hotel_booking_status": trip_status,
                        "custom_status": trip_status,
                    },
                    update_modified=False
                )

        frappe.db.commit()

    # Sync AFTER in-memory doc is updated
    sync_travel_planning_from_travel_request(doc)


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

    # Build a map of TR itinerary rows: name → row
    tr_map = {row.name: row for row in doc.itinerary}

    for tp_name in tp_parents:

        tp = frappe.get_doc("Travel Planning", tp_name)
        updated = False

        # STEP 1: Build set of TR itinerary names already
        #         present in this Travel Planning doc
        existing_tr_itinerary_names = {
            row.travel_request_itinerary
            for row in tp.travel_itinerary
            if row.travel_request == doc.name
        }

        # STEP 2: Sync existing rows (field-by-field)
        for row in tp.travel_itinerary:

            if row.travel_request != doc.name:
                continue

            tr_row = tr_map.get(row.travel_request_itinerary)

            if not tr_row:
                continue

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

        # STEP 3: Add NEW rows that don't exist in TP yet
        #
        # A row is "new" when:
        #   - It has a saved name (not __islocal)
        #   - Its name is NOT already in existing_tr_itinerary_names
        #   - It belongs to this Travel Request
        for tr_row in doc.itinerary:
            # Skip unsaved/local rows — they have no stable DB name yet
            if getattr(tr_row, "__islocal", False):
                continue

            # Skip rows already synced into this TP
            if tr_row.name in existing_tr_itinerary_names:
                continue

            # Get the employee details from the first existing TP row for this TR
            # so we can carry over employee-level fields
            reference_tp_row = next(
                (r for r in tp.travel_itinerary if r.travel_request == doc.name),
                None
            )

            new_tp_row = tp.append("travel_itinerary", {
                # link back to source
                "travel_request": doc.name,
                "travel_request_itinerary": tr_row.name,

                # employee identity (copied from sibling row or TR doc)
                "custom_employee": (
                    reference_tp_row.custom_employee
                    if reference_tp_row
                    else doc.employee
                ),
                "employee_name": (
                    reference_tp_row.employee_name
                    if reference_tp_row
                    else doc.employee_name
                ),
                "employee_hh_id": (
                    reference_tp_row.employee_hh_id
                    if reference_tp_row
                    else getattr(doc, "custom_hh__employee_id", "")
                ),
                "custom_contact_email": (
                    reference_tp_row.custom_contact_email
                    if reference_tp_row
                    else doc.prefered_email
                ),
                "custom_is_claimable": (
                    reference_tp_row.custom_is_claimable
                    if reference_tp_row
                    else getattr(doc, "custom_is_claimable", 0)
                ),
                "custom_not_claimable": (
                    reference_tp_row.custom_not_claimable
                    if reference_tp_row
                    else getattr(doc, "custom_not_claimable", 0)
                ),

                # itinerary fields from TR row
                "travel_from": tr_row.travel_from,
                "travel_to": tr_row.travel_to,
                "mode_of_travel": tr_row.mode_of_travel,
                "lodging_required": tr_row.lodging_required,
                "room_night": tr_row.room_night,
                "extra_baggage": tr_row.custom_extra_baggage,

                # --- status / booking fields ---
                "custom_status": tr_row.custom_status or "Active",
                "custom_flight_booking_status": tr_row.custom_flight_booking_status,
                "custom_hotel_booking_status": tr_row.custom_hotel_booking_status,
                "custom_taxi_required": tr_row.custom_taxi_required,
                "custom_reason_for_cancellation": tr_row.custom_reason_for_cancellation,
                "custom_reason_for_rescheduling": tr_row.custom_reason_for_rescheduling,
                "custom_revised_travel_date": tr_row.custom_revised_travel_date,
                "custom_revised_return_date": tr_row.custom_revised_return_date,
            })

            updated = True

        if updated:
            tp.flags.ignore_permissions = True
            tp.save()
            linked_tp_names.append(tp.name)

    # OPTIONAL EMAIL NOTIFICATION
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