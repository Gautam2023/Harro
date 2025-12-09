frappe.ui.form.on("Request for Quotation", {
    make_supplier_quotation: function (frm) {
        var doc = frm.doc;
        var dialog = new frappe.ui.Dialog({
            title: __("Create Supplier Quotation"),
            fields: [
                {
                    fieldtype: "Link",
                    label: __("Supplier"),
                    fieldname: "supplier",
                    options: "Supplier",
                    reqd: 1,
                    get_query: () => {
                        return {
                            query: "harro.harro.api.get_supplier_list",
                            filters: { name: frm.doc.name }   // ✅ FIXED
                        };
                    },
                },
            ],
            primary_action_label: __("Create"),
            primary_action: (args) => {
                if (!args) return;
                dialog.hide();

                return frappe.call({
                    type: "GET",
                    method: "erpnext.buying.doctype.request_for_quotation.request_for_quotation.make_supplier_quotation_from_rfq",
                    args: {
                        source_name: doc.name,
                        for_supplier: args.supplier,
                    },
                    freeze: true,
                    callback: function (r) {
                        if (!r.exc) {
                            var doc = frappe.model.sync(r.message);
                            frappe.set_route("Form", r.message.doctype, r.message.name);
                        }
                    },
                });
            },
        });

        dialog.show();
    },
});
