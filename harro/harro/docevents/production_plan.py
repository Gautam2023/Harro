# Copyright (c) 2017, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt




import frappe
from frappe import _, msgprint
from frappe.utils import (
    add_days,
    cint,
    comma_and,
    get_link_to_form,
    nowdate,
    getdate
)
from erpnext.manufacturing.doctype.production_plan.production_plan import ProductionPlan
from erpnext.manufacturing.report.bom_stock_report.bom_stock_report import get_bom_stock

class CustomProductionPlan(ProductionPlan):
    @frappe.whitelist()
    def make_material_request(self):
        """Create Material Requests grouped by Sales Order and Material Request Type"""
        material_request_list = []
        material_request_map = {}

        date_map = {}

        for row in self.sub_assembly_items:
            filters = {
                "bom" : row.bom_no,
                "warehouse" : "All Warehouses - HH",
                "show_exploded_view" :  1,
                "qty_to_produce" : 1
            }

            report_data =  get_bom_stock(filters=filters)

            report_items = [ row[0] for row in report_data ]

            for item in report_items:
                if not date_map.get(item):
                    date_map[item] = row.schedule_date
                else:
                    if getdate(date_map.get(item)) > getdate(row.schedule_date):
                        date_map[item] = row.schedule_date

        for item in self.mr_items:
            item_doc = frappe.get_cached_doc("Item", item.item_code)

            material_request_type = item.material_request_type or item_doc.default_material_request_type

            # key for Sales Order:Material Request Type:Customer
            key = "{}:{}:{}".format(item.sales_order, material_request_type, item_doc.customer or "")
            schedule_date = item.schedule_date or add_days(nowdate(), cint(item_doc.lead_time_days))

            if key not in material_request_map:
                # make a new MR for the combination
                material_request_map[key] = frappe.new_doc("Material Request")
                material_request = material_request_map[key]
                material_request.update(
                    {
                        "transaction_date": nowdate(),
                        "status": "Draft",
                        "company": self.company,
                        "material_request_type": material_request_type,
                        "customer": item_doc.customer or "",
                    }
                )
                material_request_list.append(material_request)
            else:
                material_request = material_request_map[key]

            # add item
            material_request.append(
                "items",
                {
                    "item_code": item.item_code,
                    "from_warehouse": item.from_warehouse
                    if material_request_type == "Material Transfer"
                    else None,
                    "qty": item.quantity,
                    "schedule_date": date_map.get(item.item_code),
                    "warehouse": item.warehouse,
                    "sales_order": item.sales_order,
                    "production_plan": self.name,
                    "material_request_plan_item": item.name,
                    "project": frappe.db.get_value("Sales Order", item.sales_order, "project")
                    if item.sales_order
                    else None
                },
            )

        for material_request in material_request_list:
            # submit
            material_request.flags.ignore_permissions = 1
            material_request.run_method("set_missing_values")

            material_request.save()
            if self.get("submit_material_request"):
                material_request.submit()

        frappe.flags.mute_messages = False

        if material_request_list:
            material_request_list = [
                get_link_to_form("Material Request", m.name) for m in material_request_list
            ]
            msgprint(_("{0} created").format(comma_and(material_request_list)))
        else:
            msgprint(_("No material request created"))