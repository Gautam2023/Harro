frappe.ui.form.on("Job Card", {
    setup:(frm)=>{
        frm.set_df_property("custom_unproductive_work_timelogs", "cannot_add_rows", true);
    },
    refresh:(frm)=>{
        frm.set_df_property("custom_unproductive_work_timelogs", "cannot_add_rows", true);
    },
    start_job: function (frm, status, employee) {
        if (status == "Resume Job"){
            frappe.call({
                method: "harro.harro.docevents.job_card.resume_unproductive_log",
                args : {
                    to_time : frappe.datetime.now_datetime(),
                    job_card : frm.doc.name
                },
                callback:(r)=>{
                     const args = {
                        job_card_id: frm.doc.name,
                        start_time: frappe.datetime.now_datetime(),
                        employees: employee,
                        status: status,
                    };
                    frm.events.make_time_log(frm, args);
                }
            })
        }else{
            const args = {
                job_card_id: frm.doc.name,
                start_time: frappe.datetime.now_datetime(),
                employees: employee,
                status: status,
            };
            frm.events.make_time_log(frm, args);
        }
	},
    complete_job: function (frm, status, completed_qty) {
        if(status == 'On Hold'){
            let d = new frappe.ui.Dialog({
            title: 'Update Unproductive Activity',
            fields: [
                {
                    "fieldname" : "activity_type",
                    "label" : "Activity Type",
                    "options" : "Activity Type",
                    "reqd" :  1,
                    "fieldtype" : "Link",
                    get_query: function () {
						return {
							filters: [["custom_unproductive_work" , "=", 1]],
						};
					},
                },
                {
                    "fieldname" : "project",
                    "label" : "BA Number",
                    "options" : "Project",
                    "reqd" :  1,
                    "fieldtype" : "Link",
                    "default" : frm.doc.project
                },
                {
                    "fieldname" : "task",
                    "label" : "Task",
                    "options" : "Task",
                    "reqd" :  0,
                    "fieldtype" : "Link"
                },
                {
                    "fieldname" : "expected_hrs",
                    "label" : "Expected Hrs",
                    "reqd" :  0,
                    "fieldtype" : "Float"
                }
            ],
            size: 'small', // small, large, extra-large 
            primary_action_label: 'Update Time Log',
            primary_action(values) {
                let data = d.get_values();
                let arg = {
                    activity_type : data.activity_type,
                    from_time : frappe.datetime.now_datetime(),
                    project : data.project,
                    task : data.task
                }
                frappe.call({
                    method: "harro.harro.docevents.job_card.update_unproductive_log",
                    args : {
                        arg : arg,
                        job_card : frm.doc.name
                    },
                    callback:(r)=>{
                        frm.refresh_field("custom_unproductive_work_timelogs")
                        const args = {
                            job_card_id: frm.doc.name,
                            complete_time: frappe.datetime.now_datetime(),
                            status: status,
                            completed_qty: completed_qty,
                        };
                        frm.events.make_time_log(frm, args);
                        d.hide();
                    }
                })

                
            }
        });
        d.show();
        d.set_value("project", frm.doc.project)

        }else{
            const args = {
                job_card_id: frm.doc.name,
                complete_time: frappe.datetime.now_datetime(),
                status: status,
                completed_qty: completed_qty,
            };
            frm.events.make_time_log(frm, args);
        }
	},
})