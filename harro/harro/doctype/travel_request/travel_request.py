# Copyright (c) 2025, Fosserp and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class TravelRequest(Document):
    def validate(self):
        self.send_feedback_link()
    
    def on_update_after_submit(self):
        self.send_feedback_link()
    
    def on_update(self):
        self.send_feedback_link()

    def send_feedback_link(self):
        if self.is_new():
            return
        if frappe.db.exists("Travel Arrangement - Feedback", {"travel_request" : self.name}):
            return
        old_doc = self.get_doc_before_save()

        if (
            old_doc
            and old_doc.workflow_state != self.workflow_state
            and self.workflow_state == "Trip Completed"
        ):
            frappe.enqueue(
                method="harro.harro.doctype.travel_request.travel_request.send_form_in_email",
                queue="default",
                enqueue_after_commit=True,
                docname=self.name
            )


def send_form_in_email(docname):
    doc = frappe.get_doc("Travel Request", docname)

    
    feedback_doc = frappe.get_doc({
        "doctype": "Travel Arrangement - Feedback",
        "travel_request": doc.name,
    })
    feedback_doc.flags.ignore_mandatory = True
    feedback_doc.insert(ignore_permissions=True)

    user_id = frappe.db.get_value(
        "Employee",
        doc.employee,
        "user_id"
    )

    if not user_id:
        return

    frappe.share.add_docshare(
        "Travel Arrangement - Feedback",
        feedback_doc.name,
        user_id,
        read=1,
        write=1,
        flags={"ignore_share_permission": True}
    )

    feedback_link = frappe.utils.get_url(
        f"/app/travel-arrangement---feedback/{feedback_doc.name}"
    )

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
