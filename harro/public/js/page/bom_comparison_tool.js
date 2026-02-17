frappe.provide("harro");
frappe.provide("erpnext");

frappe.pages["bom-comparison-tool"].on_page_load = function (wrapper) {
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: __("BOM Comparison Tool"),
        single_column: true,
    });

    new erpnext.BOMComparisonTool(page);
};

erpnext.BOMComparisonTool = class BOMComparisonTool {
    constructor(page) {
        this.page = page;
        this.selected_items = [];
        frappe.route_options = null;

        this.make_form();
        this.add_header_buttons();
    }

    make_form() {
        this.form = new frappe.ui.FieldGroup({
            fields: [
                {
                    label: __("BOM 1"),
                    fieldname: "name1",
                    fieldtype: "Link",
                    options: "BOM",
                    change: () => this.fetch_and_render(),
                    get_query: () => ({
                        filters: {
                            name: ["not in", [this.form.get_value("name2") || ""]],
                        },
                    }),
                },
                { fieldtype: "Column Break" },
                {
                    label: __("BOM 2"),
                    fieldname: "name2",
                    fieldtype: "Link",
                    options: "BOM",
                    change: () => this.fetch_and_render(),
                    get_query: () => ({
                        filters: {
                            name: ["not in", [this.form.get_value("name1") || ""]],
                        },
                    }),
                },
                { fieldtype: "Section Break" },
                { fieldtype: "HTML", fieldname: "preview" },
            ],
            body: this.page.body,
        });

        this.form.make();
    }

    add_header_buttons() {
        this.page.add_inner_button(__('Create Work Order'), () => {
            if (!this.selected_items.length) {
                frappe.msgprint(__("Please select sub-assembly items."));
                return;
            }

            frappe.call({
                method: "harro.harro.docevents.bom_comparison_tool.create_work_orders",
                args: { items: this.selected_items },
                freeze: true,
                freeze_message: __("Preparing Work Order..."),
                callback: (r) => {
                    if (r.message) {
                        frappe.model.sync(r.message);

                        frappe.set_route("Form", "Work Order", r.message.name);
                    } else {
                        frappe.msgprint(__("Work Order could not be prepared"));
                    }
                }
            });
        }).addClass('btn-primary');


        this.page.add_inner_button(__('Create Material Request'), () => {
            if (!this.selected_items.length) {
                frappe.msgprint(__("Please select items."));
                return;
            }

            frappe.call({
                method: "harro.harro.docevents.bom_comparison_tool.create_material_request",
                args: { items: this.selected_items },
                freeze: true,
                freeze_message: __("Preparing Material Request..."),
                callback: (r) => {
                    if (r.message) {
                        // Sync unsaved doc to client model
                        let doc = frappe.model.sync(r.message)[0];

                        // Redirect to form (unsaved)
                        frappe.set_route("Form", doc.doctype, doc.name);
                    } else {
                        frappe.msgprint(__("Material Request could not be created"));
                    }
                }
            });
        }).addClass('btn-primary');

    }

    fetch_and_render() {
        let { name1, name2 } = this.form.get_values();

        if (!(name1 && name2)) {
            this.form.get_field("preview").html("");
            return;
        }

        this.form.get_field("preview").html(
            `<div class="text-muted margin-top">${__("Fetching...")}</div>`
        );

        frappe.call(
            "erpnext.manufacturing.doctype.bom.bom.get_bom_diff",
            { bom1: name1, bom2: name2 }
        ).then(r => {
            let diff = r.message;
            frappe.model.with_doctype("BOM", () => {
                this.render("BOM", name1, name2, diff);
            });
        });
    }

    render(doctype, name1, name2, diff) {
        let me = this;
        this.selected_items = [];

        let value_changes_html = this.get_values_changed_html(
            doctype,
            name1,
            diff.changed
        );

        let added_html = this.get_added_removed_html(
            __("Rows Added in {0}"),
            group_items(diff.added, r => r[0])
        );

        let removed_html = this.get_added_removed_html(
            __("Rows Removed in {0}"),
            group_items(diff.removed, r => r[0])
        );

        let html = `
            ${value_changes_html}
            ${added_html}
            ${removed_html}
        `;

        this.form.get_field("preview").html(html);

        $(document).off("change", ".select-item").on("change", ".select-item", function (e) {
            e.stopPropagation();
            let item_code = $(this).data("item-code");
            let table = $(this).closest("table");

            if (this.checked) {
                if (!me.selected_items.includes(item_code)) {
                    me.selected_items.push(item_code);
                }
            } else {
                me.selected_items = me.selected_items.filter(i => i !== item_code);
                table.find(".select-all").prop("checked", false);
            }

            let all_checked =
                table.find(".select-item").length ===
                table.find(".select-item:checked").length;

            table.find(".select-all").prop("checked", all_checked);
        });

        $(document).off("change", ".select-all").on("change", ".select-all", function (e) {
            e.stopPropagation();
            let checked = this.checked;
            let table = $(this).closest("table");

            table.find(".select-item").each(function () {
                $(this).prop("checked", checked).trigger("change");
            });
        });
    }

    get_values_changed_html(doctype, name1, changed) {
        let rows = this.get_changed_values(doctype, changed)
            .map(([fieldname, v1, v2]) => `
                <tr>
                    <td>${frappe.meta.get_label(doctype, fieldname)}</td>
                    <td>${v1}</td>
                    <td>${v2}</td>
                </tr>
            `).join("");

        return `
            <h4 class="margin-top">${__("Values Changed")}</h4>
            <table class="table table-bordered">
                <tr>
                    <th>${__("Field")}</th>
                    <th>${name1}</th>
                    <th>${__("BOM 2")}</th>
                </tr>
                ${rows}
            </table>
        `;
    }

    get_added_removed_html(title, grouped_items) {
        return Object.keys(grouped_items).map(fieldname => {
            let rows = grouped_items[fieldname];
            let df = frappe.meta.get_docfield("BOM", fieldname);
            let fields = frappe.meta
                .get_docfields(df.options)
                .filter(df => df.in_list_view);

            let html_rows = rows.map(([, doc]) => {
                let checkbox = `<td>
                    <input type="checkbox" class="select-item"
                    data-item-code="${doc.item_code || doc.name}">
                </td>`;

                let cells = checkbox + fields
                    .map(f => `<td>${doc[f.fieldname] || ""}</td>`)
                    .join("");

                return `<tr>${cells}</tr>`;
            }).join("");

            let header =
                `<th><input type="checkbox" class="select-all"></th>` +
                fields.map(f => `<th>${f.label}</th>`).join("");

            return `
                <h4 class="margin-top">${$.format(title, [df.label])}</h4>
                <table class="table table-bordered">
                    <tr>${header}</tr>
                    ${html_rows}
                </table>
            `;
        }).join("");
    }

    get_changed_values(doctype, changed) {
        return changed.filter(([fieldname, v1, v2]) => {
            v1 = v1 || "";
            v2 = v2 || "";
            if (v1 === v2) return false;

            let df = frappe.meta.get_docfield(doctype, fieldname);
            return df && !df.hidden;
        });
    }
};

function group_items(array, fn) {
    return array.reduce((acc, item) => {
        let key = fn(item);
        (acc[key] = acc[key] || []).push(item);
        return acc;
    }, {});
}
