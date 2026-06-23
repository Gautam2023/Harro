import frappe
import csv
import io
import os
from datetime import datetime

def _parse_icici_date(date_str):
    """
    Parse ICICI date formats into YYYY-MM-DD string.
    Handles:
        01/03/26 11:54   -> 2026-03-01
        01/03/2026       -> 2026-03-01
        01/03/26         -> 2026-03-01
    """

    date_str = str(date_str).strip()
    
    # strip time component if present
    if " " in date_str:
        date_str = date_str.split(" ")[0]

    for fmt in ("%d/%m/%Y", "%d/%m/%y"):
        try:
            return datetime.strptime(date_str, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue

    frappe.throw(f"Unrecognised date format in bank statement: '{date_str}'")



def _read_file_content(file_url):
    """
    Return raw text content of a Frappe-managed file.
    Handles both public (/files/...) and private (/private/files/...) paths.
    """
    if file_url.startswith("/private"):
        abs_path = frappe.get_site_path() + file_url
    else:
        abs_path = frappe.get_site_path("public") + file_url
 
    if not os.path.exists(abs_path):
        frappe.throw(
            f"Attached file not found on disk: {abs_path}. "
            "Please re-attach the file and try again."
        )
 
    with open(abs_path, "r", encoding="utf-8-sig", errors="replace") as f:
        return f.read() 
    


@frappe.whitelist()
def process_icici_bank_statement(file_url, bank_account, currency, docname):
    """
    Input CSV structure (ICICI format)
    ------------------------------------
    Rows 0-N   : metadata block (Statement of Account, Account No,
                 Customer Name, Currency, Opening/Closing Balance,
                 From/To Date, Debit/Credit counts, etc.)
    Row N+1    : column header row — detected by presence of "Transaction Date"
    Row N+2+   : one transaction per row
 
    Header columns used:
        Transaction Date        -> Date (converted to YYYY-MM-DD)
        Transaction Description -> Description
        Transaction Amount      -> Deposit (if C) or Withdrawal (if D)
        Debit / Credit          -> D = Withdrawal, C = Deposit
        Reference No.           -> Reference Number
 
    Output CSV columns (ERPNext Bank Statement Import format)
    ----------------------------------------------------------
        Date, Deposit, Withdrawal, Description,
        Reference Number, Bank Account, Currency
 
    Bank Account and Currency are taken from the form fields, not the file.
    """

    # 1. Read the raw file                                                
    try:
        raw_content = _read_file_content(file_url)
    except frappe.exceptions.ValidationError:
        raise
    except Exception as e:
        return {"status": "error", "error": str(e)}
 
    try:
        all_rows = list(csv.reader(io.StringIO(raw_content)))
    except Exception as e:
        return {"status": "error", "error": f"Failed to parse CSV: {e}"}
 

    # 2. Locate the transaction header row                                
    header_row_index = None
    for i, row in enumerate(all_rows):
        if any("Transaction Date" in cell.strip() for cell in row):
            header_row_index = i
            break
 
    if header_row_index is None:
        return {
            "status": "error",
            "error": (
                "Could not find the transaction header row "
                "(expected a row containing 'Transaction Date'). "
                "Please make sure you are uploading a valid ICICI CSV statement."
            ),
        }
 
 
    # 3. Map column names to indices                                      
    header = [c.strip() for c in all_rows[header_row_index]]
 
    def col_index(name):
        try:
            return header.index(name)
        except ValueError:
            frappe.throw(
                f"Expected column '{name}' not found in the bank statement. "
                f"Columns found: {header}"
            )
 
    idx_date   = col_index("Transaction Date")
    idx_desc   = col_index("Transaction Description")
    idx_amount = col_index("Transaction Amount")
    idx_dc     = col_index("Debit / Credit")
    idx_ref    = col_index("Reference No.")
    max_idx    = max(idx_date, idx_desc, idx_amount, idx_dc, idx_ref)
 

    # 4. Convert each transaction row                                     
    output_rows = []
    skipped = 0
 
    for raw_row in all_rows[header_row_index + 1:]:
        # Skip blank rows
        if not any(cell.strip() for cell in raw_row):
            continue
 
        # Skip rows that don't have enough columns
        if len(raw_row) <= max_idx:
            skipped += 1
            continue
 
        try:
            txn_date    = _parse_icici_date(raw_row[idx_date])
            description = raw_row[idx_desc].strip()
            amount_str  = raw_row[idx_amount].strip().replace(",", "")
            amount      = float(amount_str) if amount_str else 0.0
            dc_flag     = raw_row[idx_dc].strip().upper()  # "D" or "C"
            reference   = raw_row[idx_ref].strip()
        except Exception as parse_err:
            frappe.log_error(
                f"Skipped malformed row in ICICI statement conversion "
                f"(doc: {docname}): {raw_row} — {parse_err}",
                "ICICI Bank Statement - Row Skip",
            )
            skipped += 1
            continue
 
        deposit    = amount if dc_flag == "C" else 0.0
        withdrawal = amount if dc_flag == "D" else 0.0
 
        output_rows.append(
            [txn_date, deposit, withdrawal, description, reference, bank_account, currency]
        )
 
    if not output_rows:
        return {
            "status": "error",
            "error": (
                f"No valid transaction rows found after the header "
                f"(skipped {skipped} malformed rows). "
                "Please verify the file is a valid ICICI bank statement."
            ),
        }
 

    # 5. Write the converted CSV                                          
    output_buffer = io.StringIO()
    writer = csv.writer(output_buffer)
    writer.writerow(
        ["Date", "Deposit", "Withdrawal", "Description",
         "Reference Number", "Bank Account", "Currency"]
    )
    writer.writerows(output_rows)
    csv_content = output_buffer.getvalue()
 
   
    # 6. Save as a Frappe File and attach to import_file                  
    safe_name      = docname.replace(" ", "_").replace(":", "").replace("/", "")
    output_filename = f"{safe_name}_converted.csv"
 
    try:
        file_doc = frappe.get_doc({
            "doctype": "File",
            "file_name": output_filename,
            "attached_to_doctype": "Bank Statement Import",
            "attached_to_name": docname,
            "attached_to_field": "import_file",
            "content": csv_content.encode("utf-8"),
            "is_private": 1,
        })
        file_doc.insert(ignore_permissions=True)
    except Exception as e:
        return {"status": "error", "error": f"Failed to save converted file: {e}"}
 
    try:
        frappe.db.set_value(
            "Bank Statement Import", docname, "import_file", file_doc.file_url
        )
        frappe.db.commit()
    except Exception as e:
        return {
            "status": "error",
            "error": f"File saved ({file_doc.file_url}) but could not link to import_file: {e}",
        }
 
    return {
        "status": "success",
        "rows": len(output_rows),
        "skipped": skipped,
        "file_url": file_doc.file_url,
    }
 