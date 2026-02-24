# Copyright (c) 2025, Fosserp and contributors
# For license information, please see license.txt

import re
import frappe
from frappe.model.document import Document
from frappe.utils.password import encrypt, decrypt


class CreditCard(Document):
    def autoname(self):
        if not self.card_number:
            return
        if self.card_number.startswith("gAAAA"):
            number = decrypt(self.card_number)
        else:
            number = re.sub(r"\D", "", self.card_number)
        last4 = number[-4:]
        self.name = f"{last4}"

    def before_save(self):
        if not self.card_number:
            return
        if self.card_number.startswith("gAAAA"):
            return
        if "*" in self.card_number:
            if not self.is_new():
                original = frappe.db.get_value(
                    self.doctype, self.name, "card_number"
                )
                self.card_number = original
            return
        number = re.sub(r"\D", "", self.card_number)
        if not (13 <= len(number) <= 19):
            frappe.throw("Enter a valid credit card number")

        self.card_number = encrypt(number)

    def onload(self):
        if not self.card_number:
            return
        if not self.card_number.startswith("gAAAA"):
            return

        try:
            number = decrypt(self.card_number)
            last4 = number[-4:]
            masked = "*" * (len(number) - 4) + last4
            self.__dict__["card_number"] = masked

        except Exception:
            frappe.log_error(
                title="Credit Card Masking Error",
                message=frappe.get_traceback()
            )
