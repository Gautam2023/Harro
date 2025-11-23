frappe.ui.form.on("Production Plan", {
    refresh:(frm)=>{
        frm.get_docfield("sub_assembly_items").allow_bulk_edit = true
        frm.fields_dict.sub_assembly_items.grid.setup_allow_bulk_edit()
    }
})