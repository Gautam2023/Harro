import frappe
from frappe.utils import flt

def validate(self, method):
    self.planned_manufacturing_hours = round(flt(self.planned_mechanical_assembly) + flt(self.planned_electrical_assembly), 2)

def calculate_project_working_hours(project):
    # Get all submitted job cards for the project
    job_cards = frappe.db.get_all(
        "Job Card",
        filters={"project": project, "docstatus": 1},
        fields=["name", "operation", "total_time_in_mins"]
    )

    # Dictionary to hold operation-wise total minutes
    if not job_cards:
        frappe.db.set_value("Project", project, "actual_mechanical_assembly", 0)
        frappe.db.set_value("Project", project, "actual_electrical_assembly", 0)
        frappe.db.set_value("Project", project, "actual_manufacturing_hours", 0)
        return

    operation_wise_time = {}

    for jc in job_cards:
        operation = jc.operation or "Unknown"
        total_time_in_mins = flt(jc.total_time_in_mins) or 0

        # Sum total time for each operation
        operation_wise_time[operation] = flt(operation_wise_time.get(operation, 0)) + total_time_in_mins
    
    current_actule_manufacturing_hours = frappe.db.get_value("Project", project, "actual_manufacturing_hours") or 0

    if operation_wise_time.get("Mechanical Operation"):
        frappe.db.set_value("Project", project, "actual_mechanical_assembly", round(operation_wise_time.get("Mechanical Operation")/60, 2))

    if operation_wise_time.get("Electrical Operation"):
        frappe.db.set_value("Project", project, "actual_electrical_assembly", round(operation_wise_time.get("Electrical Operation")/60, 2))
    
    actual_mechanical_assembly = flt(operation_wise_time.get("Mechanical Operation")) or 0
    actual_electrical_assembly = flt(operation_wise_time.get("Electrical Operation")) or 0

    current_actule_manufacturing_hours = round(flt(actual_mechanical_assembly) + flt(actual_electrical_assembly) + flt(current_actule_manufacturing_hours), 2)

    frappe.db.set_value("Project", project, "actual_manufacturing_hours", round(current_actule_manufacturing_hours/60, 2))
    


    

import frappe

@frappe.whitelist()
def get_effort_data(project):
    """Return planned and actual hours for all 3 categories."""
    fields = [
        "planned_manufacturing_hours",
        "actual_manufacturing_hours",
        "planned_mechanical_assembly",
        "actual_mechanical_assembly",
        "planned_electrical_assembly",
        "actual_electrical_assembly",
    ]

    data = frappe.db.get_value("Project", project, fields, as_dict=True) or {}

    return {
        "planned_manufacturing_hours": data.get("planned_manufacturing_hours", 0),
        "actual_manufacturing_hours": data.get("actual_manufacturing_hours", 0),
        "planned_mechanical_assembly": data.get("planned_mechanical_assembly", 0),
        "actual_mechanical_assembly": data.get("actual_mechanical_assembly", 0),
        "planned_electrical_assembly": data.get("planned_electrical_assembly", 0),
        "actual_electrical_assembly": data.get("actual_electrical_assembly", 0),
    }



def calculate_timesheet_hours(project):
    timesheet_details = frappe.db.sql(f"""
                                    
                                    Select sum(td.hours) as hours , td.activity_type
                                    From `tabTimesheet` as t
                                    Left Join `tabTimesheet Detail` as td ON td.parent = t.name
                                    Left Join `tabActivity Type` as at ON at.name = td.activity_type
                                    Where t.parent_project = '{project}' and t.docstatus = 1 
                                    Group By td.activity_type

                                        """, as_dict=True)
        
    field_to_update = frappe.db.get_all("Activity Type" , fields = ['name', 'custom_update_to_project_field'], filters={'custom_update_to_project_field' : ["!=", ''], "disabled" : 0})

    field_mapping = {}
    for row in field_to_update:
        field_mapping.update({
            row.name : row.custom_update_to_project_field
        })
    if timesheet_details:
        for row in timesheet_details:
            if field_mapping.get(row.activity_type):
                frappe.db.set_value("Project", project, field_mapping.get(row.activity_type), round(row.hours, 2))
    else:
        for row in field_to_update:
            if field_mapping.get(row.name):
                frappe.db.set_value("Project", project, field_mapping.get(row.name), 0)

@frappe.whitelist()
def get_timesheet_working_hours(name, unproductive):
    doc = frappe.get_doc("Project", name)
    fielddetails = frappe.db.get_all(
                                     "Activity Type", 
                                     fields=["custom_update_to_project_field", "custom_planned_hours_field_name", "name", "parent_activity_type"], 
                                     filters={"custom_unproductive_work" : unproductive, "disabled" : 0}, 
                                     group_by = "parent_activity_type"
                                    )
    dataset = []
    count = 0 
    for row in fielddetails:
        if row.get("custom_update_to_project_field") and row.get("custom_planned_hours_field_name"):
            dataset.append({
                "label": row.get("parent_activity_type"),
                "actual": doc.get(row.get("custom_update_to_project_field")),
                "planned": doc.get(row.get("custom_planned_hours_field_name")),
                "index": count
            })
            count += 1
    return dataset

@frappe.whitelist() 
def get_activity(unproductive=0):
    fielddetails = frappe.db.get_all(
                                     "Activity Type", 
                                     fields=["custom_update_to_project_field", "custom_planned_hours_field_name", "name", "parent_activity_type"], 
                                     filters={"custom_unproductive_work" : unproductive, "disabled" : 0}, 
                                     group_by = "parent_activity_type"
                                    )
    
    activity_list = []
    for row in fielddetails:
        if row.get("custom_update_to_project_field") and row.get("custom_planned_hours_field_name"):
            activity_list.append(row.get("parent_activity_type"))
        
    return activity_list


## custom function for employee chart
# @frappe.whitelist()
# def get_project_hierarchy(project):
#     project_employees = frappe.get_all(
#         "Project User",   
#         filters={"parent": project},
#         pluck="custom_employee"
#     )

#     if not project_employees:
#         return []
#     employees = frappe.get_all(
#         "Employee",
#         filters={
#             "name": ["in", project_employees],
#             "status": "Active"
#         },
#         fields=[
#             "name as id",
#             "employee_name as name",
#             "reports_to",
#             "designation as title",
#             "image",
#             "lft",
#             "rgt"
#         ],
#         order_by="employee_name"
#     )

#     for emp in employees:
#         emp.connections = sum(
#             1 for e in employees if e.get("reports_to") == emp.id
#         )
#         emp.expandable = bool(emp.connections)
#     frappe.log_error(message=frappe.as_json(employees), title="employees")
#     return employees



@frappe.whitelist()
def get_project_hierarchy(project, parent=None):
    """
    Get employee hierarchy for a project
    - If parent is None: returns root nodes (employees without a manager in the project)
    - If parent is provided: returns direct reports of that parent
    """
    project_employees = frappe.get_all(
        "Project User",   
        filters={"parent": project},
        pluck="custom_employee"
    )

    if not project_employees:
        return []
    
    # Build filters based on parent parameter
    filters = {
        "name": ["in", project_employees],
        "status": "Active"
    }
    
    if parent:
        # Get direct reports of this parent
        filters["reports_to"] = parent
    else:
        # Get root nodes: employees with no reports_to OR reports_to not in project
        filters["reports_to"] = ["is", "set"]
    
    employees = frappe.get_all(
        "Employee",
        filters=filters,
        fields=[
            "name as id",
            "employee_name as name",
            "reports_to",
            "designation as title",
            "image"
        ],
        order_by="employee_name"
    )
    
    # For root nodes, we need to filter out those whose manager is also in the project
    if not parent:
        root_employees = []
        for emp in employees:
            if not emp.reports_to or emp.reports_to not in project_employees:
                root_employees.append(emp)
        employees = root_employees
    
    # Get count of direct reports for each employee
    for emp in employees:
        # Count how many employees report to this person within the project
        direct_reports = frappe.get_all(
            "Employee",
            filters={
                "reports_to": emp.id,
                "name": ["in", project_employees],
                "status": "Active"
            },
            count=True
        )
        emp.connections = direct_reports
        emp.expandable = direct_reports > 0
    
    frappe.log_error(message=frappe.as_json(employees), title=f"Project hierarchy for {project}")
    return employees

@frappe.whitelist()
def get_all_project_nodes(project):
    """
    Get all nodes in the project hierarchy for Expand All functionality
    Returns a list of [parent, [children]] pairs
    """
    project_employees = frappe.get_all(
        "Project User",   
        filters={"parent": project},
        pluck="custom_employee"
    )

    if not project_employees:
        return []
    
    # Get all active employees in the project
    all_employees = frappe.get_all(
        "Employee",
        filters={
            "name": ["in", project_employees],
            "status": "Active"
        },
        fields=[
            "name as id",
            "employee_name as name",
            "reports_to",
            "designation as title",
            "image"
        ]
    )
    
    # Build a mapping of manager -> direct reports
    manager_map = {}
    for emp in all_employees:
        if emp.reports_to:
            manager_map.setdefault(emp.reports_to, []).append(emp)
    
    # Create result in the format expected by the frontend
    result = []
    for emp in all_employees:
        if emp.id in manager_map:  # This employee has direct reports
            children = manager_map[emp.id]
            
            # Format parent
            parent_data = {
                "id": emp.id,
                "name": emp.name,
                "title": emp.title,
                "image": emp.image,
                "connections": len(children),
                "expandable": True
            }
            
            # Format children
            children_data = []
            for child in children:
                child_data = {
                    "id": child.id,
                    "name": child.name,
                    "title": child.title,
                    "image": child.image,
                    "connections": len(manager_map.get(child.id, [])),
                    "expandable": child.id in manager_map
                }
                children_data.append(child_data)
            
            result.append([parent_data, children_data])
    
    return result