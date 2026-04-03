# Copyright (c) 2026, Fosserp and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import cint, flt, getdate
from typing import Dict, List, Optional, Tuple


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
    return (
        frappe.has_permission("Travel Planning", "read") or
        frappe.has_permission("Travel Request", "read")
    )

def validate_filters(filters: Dict) -> Dict:

    cleaned_filters = {}
    
    # Date validation
    if filters.get('from_date') and filters.get('to_date'):
        if getdate(filters['from_date']) > getdate(filters['to_date']):
            frappe.throw(_("From Date cannot be greater than To Date"))
    
    # Copy only non-empty filters
    for key, value in filters.items():
        if value is not None and value != "":
            cleaned_filters[key] = value
    
    return cleaned_filters

def get_columns() -> List[Dict]:

    return [
        {"label": _("Travel Request ID"), "fieldname": "travel_request", "fieldtype": "Link", "options": "Travel Request", "width": 180},
        {"label": _("Travel Plan ID"), "fieldname": "name", "fieldtype": "Link", "options": "Travel Planning", "width": 140},
        {"label": _("Employee ID"), "fieldname": "employee", "fieldtype": "Link", "options": "Employee", "width": 160},
        {"label": _("Employee Name"), "fieldname": "employee_name", "fieldtype": "Data", "width": 160},
        {"label": _("Work Code"), "fieldname": "custom_work_code", "fieldtype": "Data", "width": 120},
        {"label": _("Customer"), "fieldname": "custom_customer", "fieldtype": "Link", "options": "Customer", "width": 150},
        {"label": _("Department"), "fieldname": "custom_department", "fieldtype": "Link", "options": "Department", "width": 150},
        {"label": _("Purpose of Travel"), "fieldname": "purpose_of_travel", "fieldtype": "Link", "options": "Purpose of Travel", "width": 180},
        {"label": _("Travel Type"), "fieldname": "travel_type", "fieldtype": "Data", "width": 120},
        {"label": _("Request Date"), "fieldname": "custom_request_date", "fieldtype": "Date", "width": 120},
        {"label": _("Booked By"), "fieldname": "custom_booked_by", "fieldtype": "Link", "options": "Employee", "width": 150},

        {"label": _("Travel From"), "fieldname": "travel_from", "fieldtype": "Data", "width": 150},
        {"label": _("Travel To"), "fieldname": "travel_to", "fieldtype": "Data", "width": 150},
        {"label": _("Onward Travel Date"), "fieldname": "onward_date", "fieldtype": "Date", "width": 130},
        {"label": _("Return Travel Date"), "fieldname": "return_date", "fieldtype": "Date", "width": 130},
        {"label": _("Extra Baggage"), "fieldname": "extra_baggage", "fieldtype": "Data", "width": 120},
        {"label": _("Baggage Cost"), "fieldname": "baggage_cost", "fieldtype": "Currency", "width": 120},
        {"label": _("Seat Charges"), "fieldname": "seat_charges", "fieldtype": "Currency", "width": 120},
        
        # Status Flags
        {"label": _("Is Claimable"), "fieldname": "is_claimable", "fieldtype": "Check", "width": 100},
        {"label": _("Not Claimable"), "fieldname": "not_claimable", "fieldtype": "Check", "width": 120},
        
        # Flight Details
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

        # Hotel Details
        {"label": _("Stay Required"), "fieldname": "lodging_required", "fieldtype": "Check", "width": 120},
        {"label": _("Hotel Name"), "fieldname": "hotel_name", "fieldtype": "Data", "width": 180},
        {"label": _("Hotel Cost per Day"), "fieldname": "custom_hotel_cost_per_day", "fieldtype": "Currency", "width": 140},
        {"label": _("Total Hotel Charge"), "fieldname": "custom_total_hotel_charge", "fieldtype": "Currency", "width": 140},
        {"label": _("Check-in Date"), "fieldname": "check_in_date", "fieldtype": "Date", "width": 120},
        {"label": _("Check-out Date"), "fieldname": "check_out_date", "fieldtype": "Date", "width": 120},
        {"label": _("Room Nights"), "fieldname": "room_night", "fieldtype": "Int", "width": 110},
        {"label": _("Hotel Booking Status"), "fieldname": "custom_hotel_booking_status", "fieldtype": "Data", "width": 140},
        {"label": _("Hotel Cancellation Charges"), "fieldname": "custom_hotel_cancellation_charges", "fieldtype": "Currency", "width": 170},
        {"label": _("Hotel Refund Amount"), "fieldname": "custom_hotel_refund_amount", "fieldtype": "Currency", "width": 150},

        # Taxi Details
        {"label": _("Taxi Required"), "fieldname": "taxi_required", "fieldtype": "Check", "width": 110},
        {"label": _("Taxi Cost"), "fieldname": "taxi_cost", "fieldtype": "Currency", "width": 120},

    ]

def get_conditions(filters: Dict) -> Tuple[str, Dict]:

    conditions = []
    values = {}
    
    # Define filter mappings
    filter_mappings = {
        'ba_number': ("tp.ba_number = %(ba_number)s", "ba_number"),
        'travel_request': ("tped.travel_request = %(travel_request)s", "travel_request"),
        'travel_plan': ("tp.name = %(travel_plan)s", "travel_plan"),
        'employee': ("tped.employee_hh_id = %(employee)s", "employee"),
        'employee_name': ("tped.employee_name = %(employee_name)s", "employee_name"),
        'travel_type': ("tr.travel_type = %(travel_type)s", "travel_type"),
        'flight_booking_status': ("tri.custom_flight_booking_status = %(flight_booking_status)s", "flight_booking_status"),
        'hotel_booking_status': ("tri.custom_hotel_booking_status = %(hotel_booking_status)s", "hotel_booking_status"),
    }
    
    # Add date range conditions
    if filters.get('from_date'):
        conditions.append("tped.custom_onward_travel_date >= %(from_date)s")
        values["from_date"] = filters["from_date"]
    
    if filters.get('to_date'):
        conditions.append("tped.custom_return_travel_date <= %(to_date)s")
        values["to_date"] = filters["to_date"]
    
    # Add other filter conditions
    for key, (condition, value_key) in filter_mappings.items():
        if filters.get(key):
            conditions.append(condition)
            values[value_key] = filters[key]
    
    # Build condition string
    condition_str = " AND ".join(conditions)
    if condition_str:
        condition_str = "WHERE " + condition_str
    
    return condition_str, values

def get_data(filters: Dict) -> List[Dict]:

    try:
        # Get conditions
        condition_str, values = get_conditions(filters)
        
        # Execute query with proper error handling
        data = frappe.db.sql(f"""
            SELECT
                tp.name,
                tp.ba_number,
                tped.travel_request,
                tped.employee_hh_id AS employee,
                tr.custom_work_code,
                tr.custom_customer,
                tr.custom_department,
                tr.purpose_of_travel,
                tr.travel_type,
                tr.custom_request_date,
                tped.custom_booked_by,
                tri.travel_from,
                tri.travel_to,
                tped.employee_name,
                tped.custom_is_claimable AS is_claimable,
                tped.custom_not_claimable AS not_claimable,
                tped.custom_onward_travel_date AS onward_date,
                tped.custom_return_travel_date AS return_date,
                tped.custom_onward_flight_cost AS onward_flight_cost,
                tped.custom_return_flight_cost AS return_flight_cost,
                tped.custom_seat_charges AS seat_charges,
                tped.hotel_coast,
                tped.taxi_coast AS taxi_cost,
                tped.custom_onward_flight_cost_as_per_invoice,
                tped.custom_return_flight_cost_as_per_invoice,
                tped.custom_total_flight_cost_as_per_invoice,
                tri.custom_reason_for_cancellation,
                tped.custom_reason_for_rescheduling,
                tped.custom_flight_reschedule_charges,
                tped.custom_flight_cancellation_charges,
                tped.custom_flight_refund_amount,
                tped.extra_baggage,
                tped.custom_hotel_cost_per_day,
                tped.custom_total_hotel_charge,
                tped.custom_hotel_cancellation_charges,
                tped.custom_hotel_refund_amount,
                tp.custom_claimable_expense AS claimable_amount,
                tp.custom_unclaimable_expense AS unclaimed_amount,
                ed.total_amount,
                ed.paid_amount,
                ed.outstanding_amount,
                ed.claimed_amount,
                ed.unclaimed_amount,
                tri.custom_flight_booking_status AS flight_booking_status,
                tri.lodging_required,
                tri.custom_hotel_booking_status,
                tri.custom_taxi_required AS taxi_required,
                tped.baggage_coast AS baggage_cost,
                tped.check_in_date,
                tped.check_out_date,
                tped.room_night,
                tped.custom_hotel_name AS hotel_name
            FROM 
                `tabTravel Planning` tp
            LEFT JOIN 
                `tabTravel Planning Employee Details` tped 
                ON tp.name = tped.parent
            LEFT JOIN 
                `tabExpense Details` ed 
                ON ed.parent = tp.name
            LEFT JOIN 
                `tabTravel Request` tr 
                ON tr.name = tped.travel_request
            LEFT JOIN 
                `tabTravel Itinerary` tri 
                ON tri.name = tped.travel_request_itinerary
            {condition_str}
            ORDER BY 
                tp.creation DESC
        """, values, as_dict=True)
        
        return data
        
    except Exception as e:
        frappe.log_error(f"Error in Travel Planning Report: {str(e)}", "Report Error")
        frappe.throw(_("An error occurred while fetching report data. Please check the error log."))

def format_data(data: List[Dict]) -> List[Dict]:

    for row in data:
        # Ensure numeric fields are properly typed
        numeric_fields = [
            'onward_flight_cost', 'return_flight_cost', 'custom_onward_flight_cost_as_per_invoice',
            'custom_return_flight_cost_as_per_invoice', 'custom_flight_cancellation_charges',
            'custom_flight_refund_amount', 'baggage_cost', 'seat_charges', 'custom_hotel_cost_per_day',
            'custom_total_hotel_charge', 'custom_hotel_cancellation_charges', 'custom_hotel_refund_amount',
            'taxi_cost', 'total_amount', 'paid_amount', 'outstanding_amount', 'claimable_amount',
            'unclaimed_amount'
        ]
        
        for field in numeric_fields:
            if field in row and row[field] is not None:
                row[field] = flt(row[field])
        
        # Ensure boolean fields are properly typed
        boolean_fields = ['is_claimable', 'not_claimable', 'lodging_required', 'taxi_required']
        for field in boolean_fields:
            if field in row:
                row[field] = cint(row[field])
        
        # Format dates if needed
        date_fields = ['onward_date', 'return_date', 'custom_request_date']
        for field in date_fields:
            if field in row and row[field]:
                row[field] = getdate(row[field])
    
    return data
