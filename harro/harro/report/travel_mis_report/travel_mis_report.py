# Copyright (c) 2026, Fosserp and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import cint, flt, getdate
from typing import Dict, List, Optional, Tuple

# Maximum rows returned to prevent timeout on large datasets
MAX_ROWS = 10000

# Allowlist of valid filter keys to prevent injection of unexpected keys
VALID_FILTER_KEYS = {
    'from_date', 'to_date', 'travel_request', 'travel_plan',
    'employee', 'employee_name', 'travel_type', 'employment_type',
    'flight_booking_status', 'hotel_booking_status',
}


def execute(filters: Optional[Dict] = None) -> Tuple[List[Dict], List[Dict]]:
    if not filters:
        filters = {}

    filters = validate_filters(filters)

    if not has_permission():
        frappe.throw(_("Not permitted to view Travel Planning Report"))

    columns = get_columns()
    data = get_data(filters)
    data = format_data(data)

    return columns, data


def has_permission() -> bool:
    """
    Require read access on both Travel Planning and Travel Request
    for tighter security. Adjust to 'or' if either alone should suffice.
    """
    return (
        frappe.has_permission("Travel Planning", "read") and
        frappe.has_permission("Travel Request", "read")
    )


def validate_filters(filters: Dict) -> Dict:
    """
    Validate date range logic and strip unknown / empty filter keys.
    """
    cleaned_filters = {}

    if filters.get('from_date') and filters.get('to_date'):
        if getdate(filters['from_date']) > getdate(filters['to_date']):
            frappe.throw(_("From Date cannot be greater than To Date"))

    for key, value in filters.items():
        if key not in VALID_FILTER_KEYS:
            # Silently ignore unexpected keys rather than propagating them
            continue
        if value is not None and value != "":
            cleaned_filters[key] = value

    return cleaned_filters


def get_columns() -> List[Dict]:
    return [
        {"label": _("Travel Request ID"), "fieldname": "travel_request", "fieldtype": "Link", "options": "Travel Request", "width": 180},
        {"label": _("Travel Plan ID"), "fieldname": "name", "fieldtype": "Link", "options": "Travel Planning", "width": 140},
        {"label": _("Employee"), "fieldname": "custom_employee", "fieldtype": "Link", "options": "Employee", "width": 140},
        {"label": _("Employee ID"), "fieldname": "employee", "fieldtype": "Data", "width": 160},
        {"label": _("Employee Name"), "fieldname": "employee_name", "fieldtype": "Data", "width": 160},
        {"label": _("Employment Type"), "fieldname": "employment_type", "fieldtype": "Link", "options": "Employment Type", "width": 160},
        {"label": _("Work Code"), "fieldname": "custom_work_code", "fieldtype": "Data", "width": 120},
        {"label": _("Customer"), "fieldname": "custom_customer", "fieldtype": "Link", "options": "Customer", "width": 150},
        {"label": _("Department"), "fieldname": "custom_department", "fieldtype": "Link", "options": "Department", "width": 150},
        {"label": _("Purpose of Travel"), "fieldname": "purpose_of_travel", "fieldtype": "Link", "options": "Purpose of Travel", "width": 180},
        {"label": _("Travel Type"), "fieldname": "travel_type", "fieldtype": "Data", "width": 120},
        {"label": _("Request Date"), "fieldname": "custom_request_date", "fieldtype": "Date", "width": 120},

        {"label": _("Travel From"), "fieldname": "travel_from", "fieldtype": "Data", "width": 150},
        {"label": _("Travel To"), "fieldname": "travel_to", "fieldtype": "Data", "width": 150},
        {"label": _("Flight Booking Vendor"), "fieldname": "custom_flight_booking_vendor", "fieldtype": "Link", "options": "Supplier", "width": 140},
        {"label": _("Flight Booked By"), "fieldname": "custom_booked_by", "fieldtype": "Link", "options": "Employee", "width": 150},
        {"label": _("Onward Travel Date"), "fieldname": "onward_date", "fieldtype": "Date", "width": 130},
        {"label": _("Return Travel Date"), "fieldname": "return_date", "fieldtype": "Date", "width": 130},
        {"label": _("Extra Baggage"), "fieldname": "extra_baggage", "fieldtype": "Data", "width": 120},
        {"label": _("Baggage Cost"), "fieldname": "baggage_cost", "fieldtype": "Currency", "width": 120},
        {"label": _("Seat Charges"), "fieldname": "seat_charges", "fieldtype": "Currency", "width": 120},
        {"label": _("Is Claimable"), "fieldname": "is_claimable", "fieldtype": "Check", "width": 100},
        {"label": _("Not Claimable"), "fieldname": "not_claimable", "fieldtype": "Check", "width": 120},
        {"label": _("Onward Flight Cost"), "fieldname": "onward_flight_cost", "fieldtype": "Currency", "width": 140},
        {"label": _("Return Flight Cost"), "fieldname": "return_flight_cost", "fieldtype": "Currency", "width": 140},
        {"label": _("Onward Flight (Invoice)"), "fieldname": "custom_onward_flight_cost_as_per_invoice", "fieldtype": "Currency", "width": 150},
        {"label": _("Return Flight (Invoice)"), "fieldname": "custom_return_flight_cost_as_per_invoice", "fieldtype": "Currency", "width": 150},
        {"label": _("Total Flight Cost (Invoice)"), "fieldname": "custom_total_flight_cost_as_per_invoice", "fieldtype": "Currency", "width": 150},
        {"label": _("Flight Booking Status"), "fieldname": "flight_booking_status", "fieldtype": "Data", "width": 150},
        {"label": _("Flight Cancellation Reason"), "fieldname": "custom_reason_for_cancellation", "fieldtype": "Small Text", "width": 200},
        {"label": _("Flight Cancellation Charges"), "fieldname": "custom_flight_cancellation_charges", "fieldtype": "Currency", "width": 170},
        {"label": _("Flight Refund Amount"), "fieldname": "custom_flight_refund_amount", "fieldtype": "Currency", "width": 150},
        {"label": _("Flight Reschedule Reason"), "fieldname": "custom_reason_for_rescheduling", "fieldtype": "Small Text", "width": 200},
        {"label": _("Flight Reschedule Charges"), "fieldname": "custom_flight_reschedule_charges", "fieldtype": "Currency", "width": 170},
        {"label": _("Total Flight Incurred Cost"), "fieldname": "total_flight_incurred_cost", "fieldtype": "Currency", "width": 180},

        {"label": _("Hotel Booked By"), "fieldname": "custom_hotel_booked_by", "fieldtype": "Link", "options": "Employee", "width": 150},
        {"label": _("Stay Required"), "fieldname": "lodging_required", "fieldtype": "Check", "width": 120},
        {"label": _("Hotel Name"), "fieldname": "hotel_name", "fieldtype": "Data", "width": 180},
        {"label": _("Hotel Cost per Day"), "fieldname": "custom_hotel_cost_per_day", "fieldtype": "Currency", "width": 140},
        {"label": _("Total Hotel Charge"), "fieldname": "custom_total_hotel_charge", "fieldtype": "Currency", "width": 140},
        {"label": _("Total Hotel Charge as per Invoice"), "fieldname": "custom_total_hotel_charge_as_per_invoice", "fieldtype": "Currency", "width": 180},
        {"label": _("Check-in Date"), "fieldname": "check_in_date", "fieldtype": "Date", "width": 120},
        {"label": _("Check-out Date"), "fieldname": "check_out_date", "fieldtype": "Date", "width": 120},
        {"label": _("Room Nights"), "fieldname": "room_night", "fieldtype": "Int", "width": 110},
        {"label": _("Hotel Booking Status"), "fieldname": "custom_hotel_booking_status", "fieldtype": "Data", "width": 140},
        {"label": _("Hotel Cancellation Charges"), "fieldname": "custom_hotel_cancellation_charges", "fieldtype": "Currency", "width": 170},
        {"label": _("Hotel Refund Amount"), "fieldname": "custom_hotel_refund_amount", "fieldtype": "Currency", "width": 150},
        {"label": _("Hotel Reschedule Charges"), "fieldname": "custom_hotel_reschedule_charges", "fieldtype": "Currency", "width": 150},
        {"label": _("Total Hotel Incurred Cost"), "fieldname": "total_hotel_incurred_cost", "fieldtype": "Currency", "width": 180},

        {"label": _("Total Expenditure"), "fieldname": "total_expenditure", "fieldtype": "Currency", "width": 180},
        # {"label": _("Claimable Amount (Plan)"), "fieldname": "claimable_amount", "fieldtype": "Currency", "width": 170},
        # {"label": _("Unclaimable Amount (Plan)"), "fieldname": "tp_unclaimed_amount", "fieldtype": "Currency", "width": 180},
        # {"label": _("Total Amount (Expense)"), "fieldname": "total_amount", "fieldtype": "Currency", "width": 170},
        # {"label": _("Paid Amount"), "fieldname": "paid_amount", "fieldtype": "Currency", "width": 130},
        # {"label": _("Outstanding Amount"), "fieldname": "outstanding_amount", "fieldtype": "Currency", "width": 150},
        # {"label": _("Claimed Amount"), "fieldname": "claimed_amount", "fieldtype": "Currency", "width": 140},
        # {"label": _("Unclaimed Amount (Expense)"), "fieldname": "ed_unclaimed_amount", "fieldtype": "Currency", "width": 180},

        {"label": _("Taxi Required"), "fieldname": "taxi_required", "fieldtype": "Check", "width": 110},
        {"label": _("Taxi Cost"), "fieldname": "taxi_cost", "fieldtype": "Currency", "width": 120},
    ]


def get_conditions(filters: Dict) -> Tuple[str, Dict]:
    conditions = []
    values = {}

    # Filter → (SQL condition, value key)
    filter_mappings = {
        'travel_request':       ("tped.travel_request = %(travel_request)s",                    "travel_request"),
        'travel_plan':          ("tp.name = %(travel_plan)s",                                   "travel_plan"),
        'employee':             ("tped.custom_employee = %(employee)s",                         "employee"),
        'employee_name':        ("tped.employee_name LIKE %(employee_name)s",                   "employee_name"),
        'travel_type':          ("tr.travel_type = %(travel_type)s",                            "travel_type"),
        'flight_booking_status':("tri.custom_flight_booking_status = %(flight_booking_status)s","flight_booking_status"),
        'hotel_booking_status': ("tri.custom_hotel_booking_status = %(hotel_booking_status)s",  "hotel_booking_status"),
        'employment_type': ("emp.employment_type = %(employment_type)s", "employment_type"),
    }

    if filters.get('from_date'):
        conditions.append("tped.custom_onward_travel_date >= %(from_date)s")
        values["from_date"] = filters["from_date"]

    if filters.get('to_date'):
        conditions.append("tped.custom_return_travel_date <= %(to_date)s")
        values["to_date"] = filters["to_date"]

    for key, (condition, value_key) in filter_mappings.items():
        if filters.get(key):
            conditions.append(condition)
            values[value_key] = filters[key]

    condition_str = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    return condition_str, values


def get_data(filters: Dict) -> List[Dict]:
    try:
        condition_str, values = get_conditions(filters)

        data = frappe.db.sql(f"""
            SELECT
                tp.name,
                tped.travel_request,
                tped.custom_employee,
                tped.employee_hh_id AS employee,
                tped.employee_name,
                emp.employment_type,
                tr.custom_work_code,
                tr.custom_customer,
                tr.custom_department,
                tr.purpose_of_travel,
                tr.travel_type,
                tr.custom_request_date,

                -- Flight
                tri.travel_from,
                tri.travel_to,
                tped.custom_flight_booking_vendor,
                tped.custom_booked_by,
                tped.custom_onward_travel_date AS onward_date,
                tped.custom_return_travel_date AS return_date,
                tped.extra_baggage,
                tped.baggage_coast AS baggage_cost,
                tped.custom_seat_charges AS seat_charges,
                tped.custom_is_claimable  AS is_claimable,
                tped.custom_not_claimable AS not_claimable,
                tped.custom_onward_flight_cost AS onward_flight_cost,
                tped.custom_return_flight_cost AS return_flight_cost,
                tped.custom_onward_flight_cost_as_per_invoice,
                tped.custom_return_flight_cost_as_per_invoice,
                tped.custom_total_flight_cost_as_per_invoice,
                tri.custom_flight_booking_status AS flight_booking_status,

                -- FIX: cancellation reason lives on tped, not tri
                tped.custom_reason_for_cancellation,
                tped.custom_flight_cancellation_charges,
                tped.custom_flight_refund_amount,
                tped.custom_reason_for_rescheduling,
                tped.custom_flight_reschedule_charges,
                (
                    IFNULL(tped.custom_total_flight_cost_as_per_invoice, 0)
                    + IFNULL(tped.custom_flight_reschedule_charges, 0)
                    - IFNULL(tped.custom_flight_cancellation_charges, 0)
                ) AS total_flight_incurred_cost,

                -- Hotel
                tped.custom_hotel_booked_by,
                tri.lodging_required,
                tped.custom_hotel_name AS hotel_name,
                tped.custom_hotel_cost_per_day,
                tped.custom_total_hotel_charge,
                tped.custom_total_hotel_charge_as_per_invoice,
                tped.check_in_date,
                tped.check_out_date,
                tped.room_night,
                tri.custom_hotel_booking_status,
                tped.custom_hotel_cancellation_charges,
                tped.custom_hotel_refund_amount,
                tped.custom_hotel_reschedule_charges,
                (
                    IFNULL(tped.custom_total_hotel_charge_as_per_invoice, 0)
                    + IFNULL(tped.custom_hotel_reschedule_charges, 0)
                    - IFNULL(tped.custom_hotel_cancellation_charges, 0)
                ) AS total_hotel_incurred_cost,

                -- Summary
                (
                    (
                        IFNULL(tped.custom_total_flight_cost_as_per_invoice, 0)
                        + IFNULL(tped.custom_flight_reschedule_charges, 0)
                        - IFNULL(tped.custom_flight_cancellation_charges, 0)
                    ) + (
                        IFNULL(tped.custom_total_hotel_charge_as_per_invoice, 0)
                        + IFNULL(tped.custom_hotel_reschedule_charges, 0)
                        - IFNULL(tped.custom_hotel_cancellation_charges, 0)
                    )
                ) AS total_expenditure,

                -- FIX: give tp's unclaimed_amount a unique alias to avoid
                -- collision with ed.unclaimed_amount below
                tp.custom_claimable_expense AS claimable_amount,
                tp.custom_unclaimable_expense AS tp_unclaimed_amount,

                -- Expense Details
                ed.total_amount,
                ed.paid_amount,
                ed.outstanding_amount,
                ed.claimed_amount,
                ed.unclaimed_amount AS ed_unclaimed_amount,

                -- Taxi
                tri.custom_taxi_required AS taxi_required,
                tped.taxi_coast AS taxi_cost

            FROM
                `tabTravel Planning` tp
            LEFT JOIN
                `tabTravel Planning Employee Details`  tped  ON tped.parent = tp.name
            LEFT JOIN
                `tabEmployee` emp   ON emp.name = tped.custom_employee
            LEFT JOIN
                `tabTravel Request` tr    ON tr.name = tped.travel_request
            LEFT JOIN
                `tabTravel Itinerary` tri   ON tri.name = tped.travel_request_itinerary
            LEFT JOIN
                `tabExpense Details` ed    ON ed.parent = tp.name
            {condition_str}
            ORDER BY
                tped.custom_onward_travel_date DESC
            LIMIT {MAX_ROWS}
        """, values, as_dict=True)

        return data

    except Exception as e:
        frappe.log_error(f"Error in Travel Planning Report: {str(e)}", "Report Error")
        frappe.throw(_("An error occurred while fetching report data. Please check the error log."))


def format_data(data: List[Dict]) -> List[Dict]:
    numeric_fields = [
        # Flight
        'onward_flight_cost',
        'return_flight_cost',
        'custom_onward_flight_cost_as_per_invoice',
        'custom_return_flight_cost_as_per_invoice',
        'custom_total_flight_cost_as_per_invoice',      # FIX: was missing
        'custom_flight_cancellation_charges',
        'custom_flight_reschedule_charges',              # FIX: was missing
        'custom_flight_refund_amount',
        'baggage_cost',
        'seat_charges',
        'total_flight_incurred_cost',

        # Hotel
        'custom_hotel_cost_per_day',
        'custom_total_hotel_charge',
        'custom_total_hotel_charge_as_per_invoice',     # FIX: was missing
        'custom_hotel_cancellation_charges',
        'custom_hotel_reschedule_charges',               # FIX: was missing
        'custom_hotel_refund_amount',
        'total_hotel_incurred_cost',                    # FIX: was missing

        # Summary
        'total_expenditure',                            # FIX: was missing
        'claimable_amount',
        'tp_unclaimed_amount',                          # FIX: renamed
        'total_amount',
        'paid_amount',
        'outstanding_amount',
        'claimed_amount',
        'ed_unclaimed_amount',                          # FIX: renamed

        # Taxi
        'taxi_cost',
    ]

    boolean_fields = ['is_claimable', 'not_claimable', 'lodging_required', 'taxi_required']

    date_fields = ['onward_date', 'return_date', 'custom_request_date', 'check_in_date', 'check_out_date']

    for row in data:
        for field in numeric_fields:
            if row.get(field) is not None:
                row[field] = flt(row[field])

        for field in boolean_fields:
            if field in row:
                row[field] = cint(row[field])

        for field in date_fields:
            if row.get(field):
                row[field] = getdate(row[field])

    return data