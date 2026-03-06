# Copyright (c) 2025, Fosserp and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc


class TravelPlanning(Document):
    def on_update(self):
        self.send_ticket_booked_emails()

    def send_ticket_booked_emails(self):
        if self.is_new():
            return
        
        old_doc = self.get_doc_before_save()

        if (
            old_doc
            and old_doc.workflow_state != self.workflow_state
            and self.workflow_state == "Ticket Booked"
        ):
            frappe.enqueue(
                method="harro.harro.doctype.travel_planning.travel_planning.send_attachment_emails",
                queue="default",
                enqueue_after_commit=True,
                docname=self.name
            )

def send_attachment_emails(docname):
    doc = frappe.get_doc("Travel Planning", docname)

    attachment_fields = [
        "custom_evisa",
        "custom_travel_insurance",
        "custom_flight_bill",
        "custom_taxi_bill"
    ]

    for row in doc.travel_itinerary:
        if not row.custom_contact_email:
            continue

        attachments = [
            {"file_url": row.get(field)}
            for field in attachment_fields  
            if row.get(field)
        ]
        if not attachments:
            continue

        frappe.sendmail(
            recipients=[row.custom_contact_email],
            subject="Ticket Booked – Travel Documents",
            message=f"""
                Hello {row.employee_name},<br><br>

                Your ticket has been booked and the following travel documents are attached.<br><br>

                <b>Travel Planning:</b> {doc.name}<br>
                <b>Employee:</b> {row.employee_name}<br><br>

                Regards,<br>
                <b>Travel Team</b>
            """,
            attachments=attachments,
            reference_doctype=doc.doctype,
            reference_name=doc.name
        )


@frappe.whitelist()
def create_purchase_invoice(source_name, target_doc=None):
	doclist = get_mapped_doc(
		"Travel Planning",
		source_name,
		{
			"Travel Planning": {
				"doctype": "Purchase Invoice", 
				"field_map" : {
					"name" : "travel_planning"
				}
			},
		},
		target_doc,
	)

	return doclist

@frappe.whitelist()
def get_travel_dates(travel_request):
    items = frappe.get_all(
        "Travel Itinerary",
        filters={"parent": travel_request},
        fields=["custom_onward_travel_date","custom_return_travel_date"],
        limit=1
    )

    if not items:
        return {}
    
    return items[0]

@frappe.whitelist()
def create_travel_checklist(source_name):
    tp = frappe.get_doc("Travel Planning", source_name)

    created = []
    skipped = []

    for row in tp.travel_itinerary:
        if not row.travel_request:
            continue

        # Check if Travel Checklist exists
        tc_name = frappe.db.get_value(
            "Travel Checklist",
            {"custom_travel_request": row.travel_request},
            "name"
        )

        if tc_name:
            # Generate link to existing Travel Checklist
            skipped.append(f'<a href="/app/travel-checklist/{tc_name}" target="_blank">{row.travel_request}</a>')
            continue

        # Create new Travel Checklist
        tc = frappe.new_doc("Travel Checklist")
        tc.custom_travel_request = row.travel_request
        tc.travel_type = tp.travel_type
        tc.travell_to = row.travel_to
        tc.visit_no = 0
        tc.insert(ignore_permissions=True)

        # Add link for newly created checklist
        created.append(f'<a href="/app/travel-checklist/{tc.name}" target="_blank">{row.travel_request}</a>')

    # Build message with links
    message = ""
    if created:
        message += f"Created Travel Checklist for: {', '.join(created)}<br>"
    if skipped:
        message += f"⚠ Already exists for: {', '.join(skipped)}"

    return message

