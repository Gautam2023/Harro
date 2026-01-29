# Copyright (c) 2025, Fosserp and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc


class TravelPlanning(Document):
    def validate(self):
        self.send_feedback_link()

    def send_feedback_link(self):
        if self.is_new():
            return

        old_doc = self.get_doc_before_save()

        if (
            old_doc
            and old_doc.workflow_state != self.workflow_state
            and self.workflow_state == "Paid"
        ):
            frappe.enqueue(
                method="harro.harro.doctype.travel_planning.travel_planning.send_form_in_email",
                queue="default",
                enqueue_after_commit=True,
                docname=self.name
            )


def send_form_in_email(docname):
    doc = frappe.get_doc("Travel Planning", docname)

    for row in doc.travel_itinerary:
        # 1️⃣ Create Feedback Doc
        feedback_doc = frappe.get_doc({
            "doctype": "Travel Arrangement - Feedback",
            "travel_request": row.travel_request,
        })
        feedback_doc.flags.ignore_mandatory = True
        feedback_doc.insert(ignore_permissions=True)

        # 2️⃣ Get employee email
        user_id = frappe.db.get_value(
            "Employee",
            feedback_doc.employee_id,
            "user_id"
        )

        if not user_id:
            continue

        # 3️⃣ Share document
        frappe.share.add_docshare(
            "Travel Arrangement - Feedback",
            feedback_doc.name,
            user_id,
            read=1,
            write=1,
            flags={"ignore_share_permission": True}
        )

        # 4️⃣ Generate link
        feedback_link = frappe.utils.get_url(
            f"/app/travel-arrangement-feedback/{feedback_doc.name}"
        )

        # 5️⃣ Send email
        frappe.sendmail(
            recipients=[user_id],
            subject="We Value Your Feedback – Travel Arrangement",
            message=f"""
                Hi {feedback_doc.employee_name},<br><br>

                We hope you are doing well 😊<br><br>

                Please take a moment to share your feedback regarding your recent travel arrangement.<br><br>

                <a href="{feedback_link}">
                    👉 Click here to submit feedback
                </a><br><br>

                Thank you for your time.<br><br>

                Warm regards,<br>
                <b>HR Team</b>
            """,
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