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
        "custom_taxi_bill",
        "custom_return_flight_ticket"
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

        frappe.sendmail(
            recipients=[doc.custom_requestor_contact_email],
            subject=f"Ticket has been booked for {row.employee_name} against Travel Request {row.travel_request}",
            message=f"""
                Hello {frappe.db.get_value('Employee', doc.travel_requestor, 'employee_name')},<br><br>
                
                This is to inform you that the ticket has been issued for {row.employee_name} against the travel request {row.travel_request},
                and the travel documents are attached for your reference.<br><br>

                <b>Travel Planning:</b> {doc.name}<br>
                <b>Employee:</b> {row.employee_name}<br><br>

                Regards,<br>
                <b>Travel Team</b>
            """,
            attachments=attachments,      
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


@frappe.whitelist()
def get_flight_purchase_invoice_defaults(employee_row, travel_doc):
    import json

    if isinstance(employee_row, str):
        employee_row = json.loads(employee_row)

    row = frappe._dict(employee_row)

    ba_number = frappe.get_value("Travel Planning", travel_doc, "ba_number")

    mandatory_fields = {
        "Vendor Name": row.get("custom_flight_booking_vendor"),
        "Bill No": row.get("custom_flight_invoice_id"),
        "BA Number": ba_number,
        "Service Type": row.get("custom_service_type"),
        "Total Amount": row.get("custom_total_flight_cost_as_per_invoice")
    }

    missing_fields = [field for field, value in mandatory_fields.items() if not value]

    if missing_fields:
        frappe.throw(f"Mandatory field(s) missing: {', '.join(missing_fields)}")

    doc = frappe.get_doc({
        "doctype": "Purchase Invoice",
        "supplier": row.custom_flight_booking_vendor,
        "travel_planning": travel_doc,
        "bill_no": row.custom_flight_invoice_id,
        "project": ba_number
    })

    doc.append("items", {
        "item_code": row.custom_service_type,
        "qty": 1,
        "rate": row.custom_total_flight_cost_as_per_invoice
    })

    doc.flags.ignore_permissions = True
    doc.flags.ignore_mandatory = True

    doc.insert()

    attachments = [
        row.get("custom_onward_flight_invoice_attachment"),
        row.get("custom_return_flight_invoice_attachment")
    ]

    for file_url in attachments:
        if file_url:
            frappe.get_doc({
                "doctype": "File",
                "file_url": file_url,
                "attached_to_doctype": "Purchase Invoice",
                "attached_to_name": doc.name
            }).insert(ignore_permissions=True)

    return doc.name


@frappe.whitelist()
def custom_flight_email_sent(expense_detail_row, travel_planning):
    row = frappe.parse_json(expense_detail_row)

    child = frappe.get_doc("Travel Planning Employee Details", row.get("name"))

    if child.custom_flight_email_sent:
        frappe.throw("Email already sent for this row.")

    accounts_managers = frappe.get_all(
        "Has Role",
        filters={"role": "Accounts Manager"},
        pluck="parent"
    )

    recipients = frappe.get_all(
        "User",
        filters={
            "name": ["in", accounts_managers],
            "enabled": 1
        },
        pluck="email"
    )

    if not recipients:
        frappe.throw("No active Accounts Manager found")

    subject = "Action Required: Supplier Invoice Details Updated – Please Create Purchase Invoice"
    doc_link = frappe.utils.get_url_to_form("Travel Planning", travel_planning)

    message = f"""
    <p>Dear Accounts Manager,</p>

    <p>
    The flight invoice details have been updated against the travel request 
    (<b>{child.travel_request}</b>). Kindly review and proceed with the creation 
    of the Purchase Invoice and payment processing.
    </p>

    <p>
    <a href="{doc_link}">Open Travel Planning</a>
    </p>

    <p>
    Regards,<br>
    Travel Manager
    </p>
    """

    frappe.sendmail(
        recipients=recipients,
        subject=subject,
        message=message
    )

    child.db_set("custom_flight_email_sent", 1)

    return "Email sent successfully"


@frappe.whitelist()
def get_hotel_purchase_invoice_defaults(employee_row, travel_doc):
    import json

    if isinstance(employee_row, str):
        employee_row = json.loads(employee_row)

    row = frappe._dict(employee_row)

    ba_number = frappe.get_value("Travel Planning", travel_doc, "ba_number")

    mandatory_fields = {
        "Vendor Name": row.get("custom_hotel_booking_vendor_name"),
        "Bill No": row.get("custom_hotel_invoice_id"),
        "BA Number": ba_number,
		"Service Type": row.get("custom_service_category"),
		"Total Amount": row.get("custom_total_hotel_charge")
    }

    missing_fields = [field for field, value in mandatory_fields.items() if not value]

    if missing_fields:
        frappe.throw(f"Mandatory field(s) missing: {', '.join(missing_fields)}")

    doc = frappe.get_doc({
        "doctype": "Purchase Invoice",
        "supplier": row.custom_hotel_booking_vendor_name,
        "travel_planning": travel_doc,
        "bill_no": row.custom_hotel_invoice_id,
        "project": ba_number,
		"custom_supplier_invoice": row.custom_taxi_bill
    })

    doc.append(
        "items",
        {
            "item_code": row.custom_service_category,
            "qty": 1,
            "rate": row.custom_total_hotel_charge
        }
    )

    doc.flags.ignore_permissions = True
    doc.flags.ignore_mandatory = True

    doc.insert()

    return doc.name


@frappe.whitelist()
def custom_send_email_hotel(expense_detail_row, travel_planning):
    row = frappe.parse_json(expense_detail_row)

    child = frappe.get_doc("Travel Planning Employee Details", row.get("name"))

    if child.custom_hotel_email_sent:
        frappe.throw("Email already sent for this row.")

    accounts_managers = frappe.get_all(
        "Has Role",
        filters={"role": "Accounts Manager"},
        pluck="parent"
    )

    recipients = frappe.get_all(
        "User",
        filters={
            "name": ["in", accounts_managers],
            "enabled": 1
        },
        pluck="email"
    )

    if not recipients:
        frappe.throw("No active Accounts Manager found")

    subject = "Action Required: Supplier Invoice Details Updated – Please Create Purchase Invoice"
    doc_link = frappe.utils.get_url_to_form("Travel Planning", travel_planning)

    message = f"""
    <p>Dear Accounts Manager,</p>

    <p>
    The Hotel invoice details have been updated against the travel request 
    (<b>{child.travel_request}</b>). Kindly review and proceed with the creation 
    of the Purchase Invoice and payment processing.
    </p>

    <p>
    <a href="{doc_link}">Open Travel Planning</a>
    </p>

    <p>
    Regards,<br>
    Travel Manager
    </p>
    """

    frappe.sendmail(
        recipients=recipients,
        subject=subject,
        message=message
    )

    child.db_set("custom_hotel_email_sent", 1)

    return "Email sent successfully"

@frappe.whitelist()
def get_taxi_purchase_invoice_defaults(employee_row, travel_doc):
    import json

    if isinstance(employee_row, str):
        employee_row = json.loads(employee_row)

    row = frappe._dict(employee_row)

    ba_number = frappe.get_value("Travel Planning", travel_doc, "ba_number")

    mandatory_fields = {
        "Vendor Name": row.get("custom_taxi_vendor"),
        "Bill No": row.get("custom_taxi_invoice_id"),
        "BA Number": ba_number,
		"Service Type": row.get("custom_taxi_type"),
		"Total Amount": row.get("taxi_coast")
    }

    missing_fields = [field for field, value in mandatory_fields.items() if not value]

    if missing_fields:
        frappe.throw(f"Mandatory field(s) missing: {', '.join(missing_fields)}")

    doc = frappe.get_doc({
        "doctype": "Purchase Invoice",
        "supplier": row.custom_taxi_vendor,
        "travel_planning": travel_doc,
        "bill_no": row.custom_taxi_invoice_id,
        "project": ba_number,
		"custom_supplier_invoice": row.custom_taxi_invoice_attachment
    })

    doc.append(
        "items",
        {
            "item_code": row.custom_service_item,
            "qty": 1,
            "rate": row.taxi_coast
        }
    )

    doc.flags.ignore_permissions = True
    doc.flags.ignore_mandatory = True

    doc.insert()

    return doc.name


@frappe.whitelist()
def custom_send_email(expense_detail_row, travel_planning):
    row = frappe.parse_json(expense_detail_row)

    child = frappe.get_doc("Travel Planning Employee Details", row.get("name"))

    if child.custom_email_sent:
        frappe.throw("Email already sent for this row.")

    accounts_managers = frappe.get_all(
        "Has Role",
        filters={"role": "Accounts Manager"},
        pluck="parent"
    )

    recipients = frappe.get_all(
        "User",
        filters={
            "name": ["in", accounts_managers],
            "enabled": 1
        },
        pluck="email"
    )

    if not recipients:
        frappe.throw("No active Accounts Manager found")

    subject = "Action Required: Supplier Invoice Details Updated – Please Create Purchase Invoice"
    doc_link = frappe.utils.get_url_to_form("Travel Planning", travel_planning)

    message = f"""
    <p>Dear Accounts Manager,</p>

    <p>
    The taxi invoice details have been updated against the travel request 
    (<b>{child.travel_request}</b>). Kindly review and proceed with the creation of the Purchase Invoice and payment processing.
    </p>

    <p>
    <a href="{doc_link}">Open Travel Planning</a>
    </p>

    <p>
    Regards,<br>
    Travel Manager
    </p>
    """

    frappe.sendmail(
        recipients=recipients,
        subject=subject,
        message=message
    )

    child.db_set("custom_email_sent", 1)

    return "Email sent successfully"

