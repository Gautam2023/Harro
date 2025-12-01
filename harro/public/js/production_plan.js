frappe.ui.form.on("Production Plan", {
    refresh:(frm)=>{
        override_setup_download(frm);
        frm.get_docfield("sub_assembly_items").allow_bulk_edit = true
        frm.fields_dict.sub_assembly_items.grid.setup_allow_bulk_edit()
    }
})

function override_setup_download(frm) {
    let grid = frm.fields_dict.sub_assembly_items.grid;

    // override the method
    grid.setup_download = function () {
        let title = this.df.label || frappe.model.unscrub(this.df.fieldname);

        $(this.wrapper)
            .find(".grid-download")
            .removeClass("hidden")
            .off("click")                          // FIX added
            .on("click", () => {

                // ---- your corrected download code here ----

                var data = [];
                var docfields = [];

                data.push([__("Bulk Edit {0}", [title])]);
                data.push([]);
                data.push([]);
                data.push([]);
                data.push([__("The CSV format is case sensitive")]);
                data.push([__("Do not edit headers which are preset in the template")]);
                data.push(["------"]);

                $.each(frappe.get_meta(this.df.options).fields, (i, df) => {
                    if (frappe.model.is_value_type(df.fieldtype)) {
                        data[1].push(df.label);
                        data[2].push(df.fieldname);

                        let description = (df.description || "") + " ";
                        if (df.fieldtype === "Date") {
                            description += frappe.boot.sysdefaults.date_format;
                        }

                        data[3].push(description);
                        docfields.push(df);
                    }
                });

                $.each(frm.doc[this.df.fieldname] || [], (i, d) => {
                    var row = [];
                    $.each(data[2], (i, fieldname) => {
                        var value = d[fieldname];

                        if (docfields[i].fieldtype === "Date" && value) {
                            value = frappe.datetime.str_to_user(value);
                        }
                        row.push(value || "");
                    });
                    data.push(row);
                });

                frappe.tools.downloadify(data, null, title);
                return false;
            });
    };
}
