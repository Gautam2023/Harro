# Stop Timer Functionality — Task, Job Card & Timesheet

## Overview

Timers are automatically stopped in two scenarios:

| Scenario | Trigger | Cron Schedule |
|---|---|---|
| **Cut-off time exceeded** | Timer running longer than configured max hours | Every 5 minutes |
| **Shift end** | Employee's shift has ended | Every 15 minutes |

Both scenarios apply to **Task** and **Job Card**. Timesheet is updated as a side-effect of stopping the Task timer (not triggered independently).

---

## 1. Stop Timer on Cut-off Time Exceeded

### 1.1 Job Card — `stop_timer_for_jobcard_every_two_hours`

**File:** `harro/harro/api.py`  
**Cron:** `*/5 * * * *`

**Flow:**

```
Fetch ALL Job Cards
  └─ For each Job Card:
       └─ Find active time log (from_time set, to_time empty)
            └─ If none → skip
       └─ Calculate hours elapsed since from_time
       └─ Read permissable_hours from Projects Settings → job_card_cut_of_time
       └─ If elapsed >= permissable_hours:
            1. Delete corrupt time log rows (from_time=null AND to_time=null)
            2. Append row to custom_unproductive_work_timelogs  [update_unproductive_log]
            3. Call make_time_log → CustomJobCard.add_time_log
                 └─ Sets to_time on all open time log rows
                 └─ Saves Job Card (status → On Hold)
                 └─ Fallback: if save fails, directly SQL-updates to_time + sets status
            4. Send email notification to employee
```

**Config:**  
`Projects Settings.job_card_cut_of_time` — cut-off in hours (e.g. `0.1` = 6 minutes)

---

### 1.2 Task — `update_task_timer`

**File:** `harro/harro/docevents/task.py`  
**Cron:** `*/5 * * * *` (same scheduler as Job Card)

**Flow:**

```
Fetch all Tasks with working_status = 'Work In Progress'
Read permissable_hours from Projects Settings → task_cut_of_time
  └─ For each Task:
       └─ Find active unproductive_work_timelogs row (from_time set, to_time empty)
            └─ If none → skip
       └─ Calculate hours elapsed since from_time
       └─ If elapsed >= permissable_hours:
            1. Call update_stop_task_log
                 └─ Sets to_time on last unproductive_work_timelogs row
                 └─ Saves Task (working_status → On Hold)
                 └─ Updates Timesheet (find open Timesheet for employee+project)
                      └─ If existing time log for task → update to_time
                      └─ Else → append new time log row
                      └─ If no Timesheet found → create new Timesheet + insert
            2. Send email notification to employee
            3. frappe.db.commit()
```

**Config:**  
`Projects Settings.task_cut_of_time` — cut-off in hours

---

## 2. Stop Timer on Shift End

### 2.1 Job Card — `update_the_job_card_timer_based_on_shift_end`

**File:** `harro/harro/api.py`  
**Cron:** `*/15 * * * *`

**Flow:**

```
Fetch all Employees with default_shift set
  └─ For each Employee:
       └─ Get shift end_time from Shift Type
       └─ Calculate diff = shift_end_time - now  (in minutes)
       └─ If diff NOT in range [-15, 0] → skip
            (i.e. only process within 15 min AFTER shift has ended)
       └─ SQL query: find Job Cards where
            - status = 'Work In Progress'
            - time log has this employee, to_time is NULL
            - time log was created before shift end
       └─ For each matching Job Card:
            1. Append to custom_unproductive_work_timelogs  [update_unproductive_log_employee_wise]
            2. Call make_time_log (complete_time=now, status=On Hold)
                 └─ CustomJobCard.add_time_log → sets to_time, saves
            3. Send email notification to employee
```

**Why -15 to 0 window:**  
Cron fires every 15 minutes. If shift ends at minute 3 between two fires, the next fire is at minute 15 (diff = -12). Window must be ≥ -15 to guarantee the job card is caught within one cron cycle.

---

### 2.2 Task — `update_the_task_timer_based_on_shift_end`

**File:** `harro/harro/api.py`  
**Cron:** `*/15 * * * *`

**Flow:**

```
Fetch all Employees with default_shift set
  └─ For each Employee:
       └─ Get shift end_time from Shift Type
       └─ Calculate diff = shift_end_time - now  (in minutes)
       └─ If diff NOT in range [-15, 0] → skip
       └─ SQL query: find Tasks where
            - working_status = 'Work In Progress'
            - assigned to this employee
            - Timesheet Detail (td) has to_time NULL and was created before shift end
       └─ For each matching Task:
            1. Call update_stop_task_log (to_time=now)
                 └─ Stops unproductive_work_timelogs row
                 └─ Updates / creates Timesheet entry
                 └─ Sets Task working_status → On Hold
            2. Send email notification to employee
```

---

## 3. Core Helper Functions

### `make_time_log(args)` — Job Card

**File:** `harro/harro/docevents/employee_checkin.py`

```
args: { job_card_id, complete_time, status, completed_qty }

  └─ frappe.get_doc("Job Card", job_card_id)
  └─ doc.validate_sequence_id()
  └─ doc.add_time_log(args)  →  CustomJobCard.add_time_log
```

---

### `CustomJobCard.add_time_log(args)` — Job Card Override

**File:** `harro/harro/override/job_card.py`

```
If complete_time provided:
  └─ Loop all time_logs → set to_time on any row where to_time is empty
  └─ If status = On Hold and last_row has valid from/to → set current_time
  └─ doc.save(ignore_mandatory=True, ignore_validate=True)
       - ignore_mandatory: handles job cards missing project or other mandatory fields
       - ignore_validate: skips ERPNext's overlap-employee validation

If start_time provided:
  └─ Append new time log row (start timer)
```

---

### `update_stop_task_log(arg)` — Task

**File:** `harro/harro/docevents/task.py`

```
args: { task, to_time }

  1. Load Task doc
  2. Set to_time on last unproductive_work_timelogs row
  3. doc.save() → Task working_status stays until explicitly set
  4. Find open Timesheet for (employee, project, docstatus=0)
       └─ Found: update existing time_log row for this task
       └─ Not found: create new Timesheet with one time_log row
  5. frappe.db.set_value(Task, working_status, "On Hold")
  6. Return True
```

---

### `update_unproductive_log(args, job_card)` — Job Card

**File:** `harro/harro/docevents/job_card.py`

```
Appends a row to Job Card → custom_unproductive_work_timelogs
  - activity_type, from_time, project, employee (one row per employee in doc.employee)
doc.save(ignore_mandatory=True)
```

---

## 4. Timesheet — How It Gets Updated

Timesheet is **not stopped independently**. It is updated as part of stopping the Task timer via `update_stop_task_log`:

```
Task timer stopped
  └─ update_stop_task_log
       └─ Find Timesheet WHERE employee = X AND parent_project = Y AND docstatus = 0
            └─ Existing Timesheet found:
                 └─ Find time_log row where task = current task
                      └─ If found → update to_time
                      └─ If not found → append new row
                 └─ timesheet_doc.save()
            └─ No Timesheet found:
                 └─ frappe.get_doc("Timesheet", {...}).insert()
                      with time_logs = [{ from_time, to_time, activity_type, employee, project, task }]
```

Timesheet rows are **never deleted or cancelled** by the stop timer logic — only `to_time` is filled in.

---

## 5. Scheduler Configuration

**File:** `harro/hooks.py`

```python
scheduler_events = {
    "cron": {
        "*/15 * * * *": [
            "harro.harro.api.update_the_task_timer_based_on_shift_end",
            "harro.harro.api.update_the_job_card_timer_based_on_shift_end",
        ],
        "*/5 * * * *": [
            "harro.harro.docevents.task.update_task_timer",
            "harro.harro.api.stop_timer_for_jobcard_every_two_hours",
        ],
    },
}
```

---

## 6. Email Notifications

| Event | Subject | Recipient |
|---|---|---|
| Job Card cut-off reached | "Job Card Timer Stopped — Cut-off Limit Reached" | Employee's user_id (email) |
| Job Card shift end | "Job Card Timer Stopped Due to Shift End" | Employee's user_id |
| Task cut-off reached | "Action Required: Please Restart Your Task Timer" | Employee's user_id |
| Task shift end | "Task Timer Stopped Due to Shift End" | Employee's user_id |

All emails include a direct link to the Task / Job Card form.  
Email failures are caught separately and logged — they do not block the timer stop.

---

## 7. Known Edge Cases & Fixes Applied

| Issue | Root Cause | Fix |
|---|---|---|
| Timer not stopping when corrupt time log row exists (from_time=null, to_time=null) | `time_logs[-1]` picked the null row; `time_diff_in_seconds(null)` crashed | Delete null rows via DB before calling `make_time_log`; find active log by iterating instead of using `[-1]` |
| Shift-end timer never triggered | Window was `-5 to 0` min but cron runs every 15 min — shift end falls outside window by next fire | Window changed to `-15 to 0` min |
| Job Card missing `project` caused `MandatoryError` on save | `update_unproductive_log` and `CustomJobCard.add_time_log` called `doc.save()` without flags | Added `ignore_mandatory=True` and `ignore_validate=True` to both |
| ERPNext overlap validation raised `OverlapError` during timer stop | ERPNext's `validate_time_logs` checks employee workstation overlaps on every save | `ignore_validate=True` in `CustomJobCard.add_time_log` skips this |
| Task `update_task_timer` used `unproductive_work_timelogs[-1]` | Last row may not be the active one if earlier rows have null from_time | Iterate to find row where `to_time` is empty and `from_time` is set |
