import frappe
from frappe.query_builder.functions import Count


@frappe.whitelist()
def get_children(parent=None, company=None, project=None, exclude_node=None):
	if not project:
		return []

	# get task for particular project
	tasks = frappe.get_all(
		"Task",
		fields=[
			"name",
			"custom_employee__assign_to_employee_ as parent_emp"
		],
		filters={"project": project}
	)

	if not tasks:
		return []

	# 2. mapping parent_emp → child_emps
	task_parents = {}
	for t in tasks:
		if not t.parent_emp:
			continue

		depends = frappe.get_all(
			"Task Depends On",
			fields=["custom_employee"],
			filters={"parent": t.name}
		)

		children = [d.custom_employee for d in depends if d.custom_employee]

		if children:
			task_parents.setdefault(t.parent_emp, set()).update(children)

	# flatten all employees involved in this project
	all_emps = set(task_parents.keys())
	for children in task_parents.values():
		all_emps.update(children)

		# employee metadata
		emps = frappe.get_all(
			"Employee",
			fields=[
				"employee_name as name",
				"name as id",
				"image",
				"designation as title"
			],
			filters=[["name", "in", list(all_emps)], ["status", "=", "Active"]]
		)

	# convert list to dicty for lookup
	emp_dict = {e.id: e for e in emps}

	# 5. Determine children nodes for UI request
	if parent:
		children_ids = task_parents.get(parent, [])
		nodes = [emp_dict.get(cid) for cid in children_ids if cid in emp_dict]
	else:
		# top level = parents without anyone assigning them
		assigned_as_child = {cid for c in task_parents.values() for cid in c}
		top_level = [pid for pid in task_parents.keys() if pid not in assigned_as_child]
		nodes = [emp_dict.get(pid) for pid in top_level if pid in emp_dict]

	# 6. Enhance output structure
	for node in nodes:
		node.id = node.id
		node.reports_to = parent or ""
		children = task_parents.get(node.id, [])
		node.connections = len(children)
		node.expandable = len(children) > 0
	
	return nodes



def get_connections(employee: str, lft: int, rgt: int) -> int:
	Employee = frappe.qb.DocType("Employee")
	query = (
		frappe.qb.from_(Employee)
		.select(Count(Employee.name))
		.where((Employee.lft > lft) & (Employee.rgt < rgt) & (Employee.status == "Active"))
	).run()

	return query[0][0]
