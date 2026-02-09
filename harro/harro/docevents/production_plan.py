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
    getdate,
    flt
)
import json
from collections import defaultdict
from erpnext.manufacturing.doctype.bom.bom import get_children as get_bom_children
from erpnext.manufacturing.doctype.production_plan.production_plan import ProductionPlan
from erpnext.manufacturing.report.bom_stock_report.bom_stock_report import get_bom_stock
from erpnext.manufacturing.doctype.production_plan.production_plan import (
    get_warehouse_list, 
    get_materials_from_other_locations,
    get_material_request_items,
    get_raw_materials_of_sub_assembly_items,
    get_bin_details,
    get_uom_conversion_factor,
    get_subitems,
    get_exploded_items
)
from frappe import _

class CustomProductionPlan(ProductionPlan):
    def validate(self):
        remove_row_from_mr_items(self)
        compare_and_update_schedule_dates(self)

        sub_contracting_row = []
        for row in self.sub_assembly_items:
            if row.type_of_manufacturing == "Subcontract" and not row.supplier:
                sub_contracting_row.append(row.idx)
        if sub_contracting_row:
            message = ''
            for row in sub_contracting_row:
                message += f"Mandatory fields required in table <b>Sub Assembly Items Row {row}.</b><br><ul><li>Supplier</li></ul><hr>"
        
            frappe.throw(_(message), title=_("Missing Fields"))
        super().validate()

    def set_sub_assembly_items_based_on_level(self, row, bom_data, manufacturing_type=None):
        "Modify bom_data, set additional details."
        is_group_warehouse = frappe.db.get_value("Warehouse", self.sub_assembly_warehouse, "is_group")
        

        for data in bom_data:
            data.qty = data.stock_qty
            data.production_plan_item = row.name
            data.schedule_date = row.planned_start_date
            manufacturing_type = frappe.db.get_value("Item", data.production_item, "custom_manufacturing_type")
            data.type_of_manufacturing = manufacturing_type or (
                "Subcontract" if data.is_sub_contracted_item else "In House"
            )
            data.custom_item_group = frappe.db.get_value("Item", data.production_item, "item_group")

            if not is_group_warehouse:
                data.fg_warehouse = self.sub_assembly_warehouse
                    
    @frappe.whitelist()
    def make_material_request(self):
        """Create Material Requests grouped by Sales Order, Material Request Type, Customer and Structure Class"""
        material_request_list = []
        material_request_map = {}

        for item in self.mr_items:
            item_doc = frappe.get_cached_doc("Item", item.item_code)

            material_request_type = item.material_request_type or item_doc.default_material_request_type
            item_group = item_doc.item_group or ""  # NEW FIELD

            # Updated key: SO : MR Type : Customer : Structure Class
            key = "{}:{}:{}:{}".format(
                item.sales_order,
                material_request_type,
                item_doc.customer or "",
                item_group
            )

            schedule_date = item.schedule_date or add_days(nowdate(), cint(item_doc.lead_time_days))

            if key not in material_request_map:
                material_request_map[key] = frappe.new_doc("Material Request")
                material_request = material_request_map[key]
                material_request.update(
                    {
                        "transaction_date": nowdate(),
                        "status": "Draft",
                        "company": self.company,
                        "material_request_type": material_request_type,
                        "customer": item_doc.customer or "",
                        "item_group": item_group,  # Optional: store in MR if needed
                    }
                )

                # add custom_ba_number from production plan to material request
                if hasattr(self, 'custom_ba_number') and self.custom_ba_number:
                    material_request.custom_ba_number = self.custom_ba_number

                material_request_list.append(material_request)
            else:
                material_request = material_request_map[key]

            material_request.append(
                "items",
                {
                    "item_code": item.item_code,
                    "from_warehouse": item.from_warehouse if material_request_type == "Material Transfer" else None,
                    "qty": item.quantity,
                    "schedule_date": schedule_date,
                    "warehouse": item.warehouse,
                    "sales_order": item.sales_order,
                    "production_plan": self.name,
                    "material_request_plan_item": item.name,
                    "project": frappe.db.get_value("Sales Order", item.sales_order, "project")
                        if item.sales_order else self.custom_ba_number,
                    "item_group": item_group,
                },
            )

        for material_request in material_request_list:
            material_request.flags.ignore_permissions = 1
            material_request.run_method("set_missing_values")
            material_request.save()
            if self.get("submit_material_request"):
                material_request.submit()

        frappe.flags.mute_messages = False

        if material_request_list:
            material_request_list = [get_link_to_form("Material Request", m.name) for m in material_request_list]
            msgprint(_("{0} created").format(comma_and(material_request_list)))
        else:
            msgprint(_("No material request created"))


    def create_work_order(self, item):
        from erpnext.manufacturing.doctype.work_order.work_order import OverProductionError

        if flt(item.get("qty")) <= 0:
            return
        
        wo = frappe.new_doc("Work Order")
        wo.update(item)
        wo.planned_start_date = item.get("planned_start_date") or item.get("schedule_date")

        # added custom_ba_number from production plan to work order
        if hasattr(self, 'custom_ba_number') and self.custom_ba_number:
            wo.project = self.custom_ba_number

        if item.get("warehouse"):
            wo.fg_warehouse = item.get("warehouse")

        wo.set_work_order_operations()
        wo.set_required_items()

        try:
            wo.flags.ignore_mandatory = True
            wo.flags.ignore_validate = True
            wo.insert()
            return wo.name
        except OverProductionError:
            pass


    def make_subcontracted_purchase_order(self, subcontracted_po, purchase_orders):
        if not subcontracted_po:
            return
        
        for supplier, po_list in subcontracted_po.items():
            po = frappe.new_doc("Purchase Order")
            po.company = self.company
            po.supplier = supplier
            po.schedule_date = getdate(po_list[0].schedule_date) if po_list[0].schedule_date else nowdate()
            po.is_subcontracted = 1

            # add custom_ba_number from production plan to purchase order
            if hasattr(self, 'custom_ba_number') and self.custom_ba_number:
                po.project = self.custom_ba_number

            for row in po_list:
                po_data = {
					"fg_item": row.production_item,
					"warehouse": row.fg_warehouse,
					"production_plan_sub_assembly_item": row.name,
					"bom": row.bom_no,
					"production_plan": self.name,
					"fg_item_qty": row.qty,
				}

                for field in [
					"schedule_date",
					"qty",
					"description",
					"production_plan_item",
				]:
                    po_data[field] = row.get(field)

                po.append("items", po_data)

            po.set_service_items_for_finished_goods()
            po.set_missing_values()
            po.flags.ignore_mandatory = True
            po.flags.ignore_validate = True
            po.insert()
            purchase_orders.append(po.name)




def compare_and_update_schedule_dates(doc):
    if not doc.posting_date:
        return

    posting_date = getdate(doc.posting_date)
    item_map = {}
    for row in doc.sub_assembly_items:
        if row.parent_item_code and item_map.get(row.parent_item_code):
            if getdate(row.schedule_date) == getdate(posting_date):
                row.schedule_date = item_map.get(row.parent_item_code).get("schedule_date")
        if not item_map.get(row.production_item):
            item_map[row.production_item] = { "item_list" : [], "name" : row.name, "schedule_date" : row.schedule_date }

def get_bom_tree(bom_no):
    from erpnext.manufacturing.doctype.bom.bom import get_children
    children = get_children(parent=bom_no)
    
    result = {
     "items": children,     # Direct children
     "child_boms": {}       # Recursive sub-BOMs
    }
    
    for row in children:
        # row["value"] contains the child BOM ID (e.g., BOM-ITEM-001)
        if row.get("expandable") == 1:
            child_bom = row.get("value")
            if child_bom:
                result["child_boms"][child_bom] = get_bom_tree(child_bom)
    
    return result

def flatten_bom_items(bom_tree):
    items = []
    for row in bom_tree.get("items", []):
        if row.get("item_code"):
            items.append(row["item_code"])
    for child_bom, child_tree in bom_tree.get("child_boms", {}).items():
        items.extend(flatten_bom_items(child_tree))
    return items


@frappe.whitelist()
def get_items_for_material_requests(doc, warehouses=None, get_parent_warehouse_data=None):
    if isinstance(doc, str):
        doc = frappe._dict(json.loads(doc))

    if warehouses:
        warehouses = list(set(get_warehouse_list(warehouses)))

        if (
            doc.get("for_warehouse")
            and not get_parent_warehouse_data
            and doc.get("for_warehouse") in warehouses
        ):
            warehouses.remove(doc.get("for_warehouse"))

    doc["mr_items"] = []

    po_items = doc.get("po_items") if doc.get("po_items") else doc.get("items")

    if doc.get("sub_assembly_items"):
        for sa_row in doc.sub_assembly_items:
            sa_row = frappe._dict(sa_row)
            if sa_row.type_of_manufacturing == "Material Request":
                po_items.append(
                    frappe._dict(
                        {
                            "item_code": sa_row.production_item,
                            "required_qty": sa_row.qty,
                            "include_exploded_items": 0,
                        }
                    )
                )

    # Check for empty table or empty rows
    if not po_items or not [row.get("item_code") for row in po_items if row.get("item_code")]:
        frappe.throw(
            _("Items to Manufacture are required to pull the Raw Materials associated with it."),
            title=_("Items Required"),
        )

    company = doc.get("company")
    ignore_existing_ordered_qty = doc.get("ignore_existing_ordered_qty")
    include_safety_stock = doc.get("include_safety_stock")

    so_item_details = frappe._dict()
    existing_sub_assembly_items = set()

    sub_assembly_items = defaultdict(int)
    if doc.get("skip_available_sub_assembly_item") and doc.get("sub_assembly_items"):
        for d in doc.get("sub_assembly_items"):
            sub_assembly_items[(d.get("production_item"), d.get("bom_no"))] += d.get("qty")

    for data in po_items:
        if not data.get("include_exploded_items") and doc.get("sub_assembly_items"):
            data["include_exploded_items"] = 1

        planned_qty = data.get("required_qty") or data.get("planned_qty")
        ignore_existing_ordered_qty = data.get("ignore_existing_ordered_qty") or ignore_existing_ordered_qty
        warehouse = doc.get("for_warehouse")

        item_details = {}
        if data.get("bom") or data.get("bom_no"):
            if data.get("required_qty"):
                bom_no = data.get("bom")
                include_non_stock_items = 1
                include_subcontracted_items = 1 if data.get("include_exploded_items") else 0
            else:
                bom_no = data.get("bom_no")
                include_subcontracted_items = doc.get("include_subcontracted_items")
                include_non_stock_items = doc.get("include_non_stock_items")

            if not planned_qty:
                frappe.throw(_("For row {0}: Enter Planned Qty").format(data.get("idx")))

            if bom_no:
                if data.get("include_exploded_items") and doc.get("skip_available_sub_assembly_item"):
                    item_details = {}
                    if doc.get("sub_assembly_items"):
                        item_details = get_raw_materials_of_sub_assembly_items(
                            existing_sub_assembly_items,
                            item_details,
                            company,
                            bom_no,
                            include_non_stock_items,
                            sub_assembly_items,
                            planned_qty=planned_qty,
                        )

                elif data.get("include_exploded_items") and include_subcontracted_items:
                    # fetch exploded items from BOM
                    item_details = get_exploded_items(
                        item_details,
                        company,
                        bom_no,
                        include_non_stock_items,
                        planned_qty=planned_qty,
                        doc=doc,
                    )
                else:
                    item_details = get_subitems(
                        doc,
                        data,
                        item_details,
                        bom_no,
                        company,
                        include_non_stock_items,
                        include_subcontracted_items,
                        1,
                        planned_qty=planned_qty,
                    )
        elif data.get("item_code"):
            item_master = frappe.get_doc("Item", data["item_code"]).as_dict()
            purchase_uom = item_master.purchase_uom or item_master.stock_uom
            conversion_factor = (
                get_uom_conversion_factor(item_master.name, purchase_uom) if item_master.purchase_uom else 1.0
            )

            item_details[item_master.name] = frappe._dict(
                {
                    "item_name": item_master.item_name,
                    "default_bom": doc.bom,
                    "purchase_uom": purchase_uom,
                    "default_warehouse": item_master.default_warehouse,
                    "min_order_qty": item_master.min_order_qty,
                    "default_material_request_type": item_master.default_material_request_type,
                    "qty": planned_qty or 1,
                    "is_sub_contracted": item_master.is_subcontracted_item,
                    "item_code": item_master.name,
                    "description": item_master.description,
                    "stock_uom": item_master.stock_uom,
                    "conversion_factor": conversion_factor,
                    "safety_stock": item_master.safety_stock,
                }
            )

        sales_order = data.get("sales_order")

        for item_code, details in item_details.items():
            so_item_details.setdefault(sales_order, frappe._dict())
            if item_code in so_item_details.get(sales_order, {}):
                so_item_details[sales_order][item_code]["qty"] = so_item_details[sales_order][item_code].get(
                    "qty", 0
                ) + flt(details.qty)
            else:
                so_item_details[sales_order][item_code] = details

    mr_items = []
    consumed_qty = defaultdict(float)

    for sales_order in so_item_details:
        item_dict = so_item_details[sales_order]
        for details in item_dict.values():
            bin_dict = get_bin_details(details, doc.company, warehouse)
            bin_dict = bin_dict[0] if bin_dict else {}

            if details.qty > 0:
                items = get_material_request_items(
                    doc,
                    details,
                    sales_order,
                    company,
                    ignore_existing_ordered_qty,
                    include_safety_stock,
                    warehouse,
                    bin_dict,
                    consumed_qty
                )
                if items:
                    mr_items.append(items)

    if (not ignore_existing_ordered_qty or get_parent_warehouse_data) and warehouses:
        new_mr_items = []
        for item in mr_items:
            get_materials_from_other_locations(item, warehouses, new_mr_items, company)

        mr_items = new_mr_items
    if mr_items:
        mr_items = update_schedule_date_as_per_tree(doc, mr_items)
    if not mr_items:
        to_enable = frappe.bold(_("Ignore Existing Projected Quantity"))
        warehouse = frappe.bold(doc.get("for_warehouse"))
        message = (
            _(
                "As there are sufficient raw materials, Material Request is not required for Warehouse {0}."
            ).format(warehouse)
            + "<br><br>"
        )
        message += _("If you still want to proceed, please enable {0}.").format(to_enable)

        frappe.msgprint(message, title=_("Note"))

    return mr_items


def update_schedule_date_as_per_tree(doc, items):
    item_schedule_date_map = {}
    item_group_map = {}
    for row in doc.sub_assembly_items:
        bom_tree = get_bom_tree(row.get("bom_no"))
        bom_items = set(flatten_bom_items(bom_tree))
        for item in bom_items:
            if item_schedule_date_map.get(item):
                final_date = min(getdate(row.get("schedule_date")), getdate(item_schedule_date_map.get(item)))
                item_schedule_date_map[item] = final_date
            else:
                item_schedule_date_map[item] = row.get("schedule_date")
        if not item_group_map.get(row.get("production_item")):
            item_group_map[row.get("production_item")] = row.get("custom_item_group")
        

    for row in items:
        row.update({"schedule_date" : item_schedule_date_map.get(row.get("item_code"))})
        if item_group_map.get(row.get("item_code")):
            row.update({"commodity_group" : item_group_map.get(row.get("item_code"))})
        else:
            row.update({"commodity_group" : frappe.db.get_value("Item", row.get("item_code"), "item_group")})

    return items

def remove_row_from_mr_items(self):
    if not self.mr_items:
        return
    # Item Groups selected for removal
    item_group_list = [row.commodity_group for row in self.remove_based_item_group]

    filtered_items = []
    for row in self.mr_items:
        item_group = frappe.db.get_value("Item", row.item_code, "item_group")
        if item_group not in item_group_list:
            filtered_items.append(row)

    # Replace original table with filtered table
    self.mr_items = filtered_items    



import json
import frappe
from erpnext.manufacturing.doctype.bom.bom import get_bom_items

@frappe.whitelist()
def remove_items_as_per_bom(doc):
    doc = frappe._dict(json.loads(doc))
    doc = frappe.get_doc(doc)

    skip_items = [
            row.item_code for row in doc.remove_from_sub_and_raw
    ]
    
    qty_map = {}
    for row in doc.sub_assembly_items:
        if row.production_item in skip_items:
            if not qty_map.get(row.production_item):
                qty_map[row.production_item] = row.qty
                qty_map[f"bom-{row.production_item}"] = row.bom_no
            else:
                qty_map[row.production_item] += row.qty
    
    bom_stock_data = []
    for row in skip_items:
        filters = frappe._dict({
            "bom" : qty_map.get(f"bom-{row}"),
            "warehouse" : "Store - HH",
            "show_exploded_view" : 1,
            "qty_to_produce" : qty_map.get(row)
        })
        bom_stock_data += get_bom_stock(filters)
    
    bom_stock_data_map = {}
    for row in bom_stock_data:
        if not bom_stock_data_map.get(row[0]):
            bom_stock_data_map[row[0]] = row[5]
        else:
            bom_stock_data_map[row[0]] += row[5]

    for row in list(doc.mr_items):
        if bom_stock_data_map.get(row.item_code):
            row.quantity = flt(row.quantity) - flt(bom_stock_data_map.get(row.item_code))

        if row.quantity <= 0:
            doc.remove(row)

    get_sub_assembly_items(doc)

    doc.save(ignore_permissions=True)

    return {
        "status": "success"
    }

@frappe.whitelist()
def get_sub_assembly_items(self, manufacturing_type=None):
    "Fetch sub assembly items and optionally combine them."
    self.sub_assembly_items = []
    sub_assembly_items_store = []  # temporary store to process all subassembly items
    bin_details = frappe._dict()

    for row in self.po_items:
        if self.skip_available_sub_assembly_item and not self.sub_assembly_warehouse:
            frappe.throw(_("Row #{0}: Please select the Sub Assembly Warehouse").format(row.idx))

        if not row.item_code:
            frappe.throw(_("Row #{0}: Please select Item Code in Assembly Items").format(row.idx))

        if not row.bom_no:
            frappe.throw(_("Row #{0}: Please select the BOM No in Assembly Items").format(row.idx))

        bom_data = []
        skip_items = {
            row.item_code for row in self.remove_from_sub_and_raw
        }
        get_sub_assembly_items_(
            [item.production_item for item in sub_assembly_items_store],
            bin_details,
            row.bom_no,
            bom_data,
            row.planned_qty,
            self.company,
            warehouse=self.sub_assembly_warehouse,
            skip_available_sub_assembly_item=self.skip_available_sub_assembly_item,
            skip_items = skip_items
        )
        self.set_sub_assembly_items_based_on_level(row, bom_data, manufacturing_type)
        sub_assembly_items_store.extend(bom_data)

    if not sub_assembly_items_store and self.skip_available_sub_assembly_item:
        message = (
            _(
                "As there are sufficient Sub Assembly Items, Work Order is not required for Warehouse {0}."
            ).format(self.sub_assembly_warehouse)
            + "<br><br>"
        )
        message += _(
            "If you still want to proceed, please disable 'Skip Available Sub Assembly Items' checkbox."
        )

        frappe.msgprint(message, title=_("Note"))

    if self.combine_sub_items:
        # Combine subassembly items
        sub_assembly_items_store = self.combine_subassembly_items(sub_assembly_items_store)

    for idx, row in enumerate(sub_assembly_items_store):
        row.idx = idx + 1
        self.append("sub_assembly_items", row)

    self.set_default_supplier_for_subcontracting_order()


def get_sub_assembly_items_(
    sub_assembly_items,
    bin_details,
    bom_no,
    bom_data,
    to_produce_qty,
    company,
    warehouse=None,
    indent=0,
    skip_available_sub_assembly_item=False,
    skip_items=None,   # 👈 NEW
):
    skip_items = skip_items or set()

    data = get_bom_children(parent=bom_no)

    for d in data:

        # 🚫 Skip selected assembly and its whole tree
        if d.item_code in skip_items:
            continue

        if d.expandable:
            parent_item_code = frappe.get_cached_value("BOM", bom_no, "item")
            stock_qty = (d.stock_qty / d.parent_bom_qty) * flt(to_produce_qty)

            if skip_available_sub_assembly_item and d.item_code not in sub_assembly_items:
                bin_details.setdefault(d.item_code, get_bin_details(d, company, for_warehouse=warehouse))

                for _bin_dict in bin_details[d.item_code]:
                    if _bin_dict.projected_qty > 0:
                        if _bin_dict.projected_qty >= stock_qty:
                            _bin_dict.projected_qty -= stock_qty
                            stock_qty = 0
                        else:
                            stock_qty -= _bin_dict.projected_qty
                            sub_assembly_items.append(d.item_code)

            elif warehouse:
                bin_details.setdefault(d.item_code, get_bin_details(d, company, for_warehouse=warehouse))

            if stock_qty > 0:
                bom_data.append(
                    frappe._dict({
                        "actual_qty": bin_details[d.item_code][0].get("actual_qty", 0)
                        if bin_details.get(d.item_code) else 0,
                        "parent_item_code": parent_item_code,
                        "description": d.description,
                        "production_item": d.item_code,
                        "item_name": d.item_name,
                        "stock_uom": d.stock_uom,
                        "uom": d.stock_uom,
                        "bom_no": d.value,
                        "is_sub_contracted_item": d.is_sub_contracted_item,
                        "bom_level": indent,
                        "indent": indent,
                        "stock_qty": stock_qty,
                    })
                )

                # 🔁 Recurse only if not skipped
                if d.value:
                    get_sub_assembly_items_(
                        sub_assembly_items,
                        bin_details,
                        d.value,
                        bom_data,
                        stock_qty,
                        company,
                        warehouse,
                        indent + 1,
                        skip_available_sub_assembly_item,
                        skip_items,   # 👈 PASS DOWN
                    )


