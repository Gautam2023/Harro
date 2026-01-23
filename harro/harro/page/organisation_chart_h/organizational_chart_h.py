import frappe
from frappe.query_builder.functions import Count

import frappe


@frappe.whitelist()
def get_children(parent=None, company=None, project=None, exclude_node=None):
	if not project:
		return []

	# 1️⃣ Fetch Project Users (ROOT employees)
	project_users = frappe.get_all(
		"Project User",
		fields=["custom_employee"],
		filters={"parent": project}
	)

	project_user_emps = {
		u.custom_employee for u in project_users if u.custom_employee
	}

	# 2️⃣ Fetch tasks for the project
	tasks = frappe.get_all(
		"Task",
		fields=[
			"name",
			"custom_employee__assign_to_employee_ as parent_emp"
		],
		filters={"project": project}
	)

	# 3️⃣ Collect task names & task owners
	task_names = []
	task_owners = set()

	for t in tasks:
		task_names.append(t.name)
		if t.parent_emp:
			task_owners.add(t.parent_emp)

	# 4️⃣ Fetch all task dependencies
	depends_all = []
	if task_names:
		depends_all = frappe.get_all(
			"Task Depends On",
			fields=["parent", "custom_employee"],
			filters={"parent": ["in", task_names]}
		)

	# 5️⃣ Map task → dependent employees
	depends_map = {}
	child_emps = set()

	for d in depends_all:
		if d.custom_employee:
			depends_map.setdefault(d.parent, []).append(d.custom_employee)
			child_emps.add(d.custom_employee)

	# 6️⃣ Build parent → children mapping
	task_parents = {}
	for t in tasks:
		if not t.parent_emp:
			continue

		children = depends_map.get(t.name, [])
		if children:
			task_parents.setdefault(t.parent_emp, set()).update(children)

	# 7️⃣ Collect ALL employees involved
	all_emps = set()
	all_emps.update(project_user_emps)  # ⭐ ROOT from Project User
	all_emps.update(task_owners)        # task owners
	all_emps.update(child_emps)         # dependency children

	if exclude_node:
		all_emps.discard(exclude_node)

	if not all_emps:
		return []

	# 8️⃣ Fetch employee metadata
	emps = frappe.get_all(
		"Employee",
		fields=[
			"name as id",
			"employee_name as name",
			"image",
			"designation as title"
		],
		filters={
			"name": ["in", list(all_emps)],
			"status": "Active"
		}
	)

	emp_dict = {e.id: e for e in emps}

	# 9️⃣ Identify employees assigned as children
	assigned_as_child = set()
	for children in task_parents.values():
		assigned_as_child.update(children)

	# 🔟 Determine nodes to return
	if parent:
		child_ids = task_parents.get(parent, [])
		nodes = [emp_dict[cid] for cid in child_ids if cid in emp_dict]
	else:
		# top-level includes:
		# - project users
		# - task owners not assigned as child
		top_level = set()
		top_level.update(project_user_emps)

		for emp_id in all_emps:
			if emp_id not in assigned_as_child:
				top_level.add(emp_id)

		nodes = [emp_dict[eid] for eid in top_level if eid in emp_dict]

	# 1️⃣1️⃣ Enrich node data
	for node in nodes:
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
