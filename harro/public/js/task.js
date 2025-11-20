frappe.ui.form.on("Task", {
    refresh:function(frm){
        if(frm.doc.working_status != "Work In Progress" && frm.doc.status != "Completed" && frm.doc.working_status != "On Hold"){
            frm.add_custom_button(__("Start Timer"), function(){
                update_start_job_log(frm)
                frm.trigger("make_dashboard");
            }).addClass("btn-primary");
        }
        if(frm.doc.working_status == "Work In Progress"){
            frm.add_custom_button(__("Pause Timer"), function(){
                update_stop_job_log(frm)
                frm.trigger("make_dashboard");
            }).addClass("btn-primary");
        }
        if(frm.doc.working_status == "On Hold"){
            frm.add_custom_button(__("Resume Timer"), function(){
                update_start_job_log(frm)
                frm.trigger("make_dashboard");
            }).addClass("btn-primary");
        }
        frm.trigger("make_dashboard");
    },
    make_dashboard: function (frm) {
		if (frm.doc.__islocal) return;

		function setCurrentIncrement() {
			currentIncrement += 1;
			return currentIncrement;
		}

		function updateStopwatch(increment) {
			var hours = Math.floor(increment / 3600);
			var minutes = Math.floor((increment - hours * 3600) / 60);
			var seconds = increment - hours * 3600 - minutes * 60;

			$(section)
				.find(".hours")
				.text(hours < 10 ? "0" + hours.toString() : hours.toString());
			$(section)
				.find(".minutes")
				.text(minutes < 10 ? "0" + minutes.toString() : minutes.toString());
			$(section)
				.find(".seconds")
				.text(seconds < 10 ? "0" + seconds.toString() : seconds.toString());
		}

		function initialiseTimer() {
			const interval = setInterval(function () {
				var current = setCurrentIncrement();
				updateStopwatch(current);
			}, 1000);
		}

		frm.dashboard.refresh();
		const timer = `
			<div class="stopwatch" style="font-weight:bold;margin:0px 13px 0px 2px;
				color:#545454;font-size:18px;display:inline-block;vertical-align:text-bottom;>
				<span class="hours">00</span>
				<span class="colon">:</span>
				<span class="minutes">00</span>
				<span class="colon">:</span>
				<span class="seconds">00</span>
			</div>`;

		var section = frm.toolbar.page.add_inner_message(timer);

		let currentIncrement =  0;
        let started_time = null;

        if (frm.doc.unproductive_work_timelogs && frm.doc.unproductive_work_timelogs.length) {
            started_time = frm.doc.unproductive_work_timelogs[frm.doc.unproductive_work_timelogs.length - 1].from_time;
        }
        
		if (started_time) {
			if (frm.doc.working_status == "On Hold") {
				updateStopwatch(currentIncrement);
			} else {
                console.log(frappe.datetime.now_datetime())
                console.log(started_time)
				currentIncrement += moment(frappe.datetime.now_datetime()).diff(
					moment(started_time),
					"seconds"
				);
				initialiseTimer();
			}
		}
	},
})
function update_start_job_log(frm){
    let d = new frappe.ui.Dialog({
        title: 'Update Time log',
        fields: [
            {
                "fieldname" : "activity_type",
                "label" : "Activity Type",
                "options" : "Activity Type",
                "reqd" :  1,
                "fieldtype" : "Link"
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
                "fieldtype" : "Link",
                "read_only" : 1
            },
            {
                "fieldname" : "employee",
                "label" : "Employee",
                "options" : "Employee",
                "reqd" :  1,
                "fieldtype" : "Link",
                "read_only" : 0
            },
            {
                "fieldname" : "expected_hrs",
                "label" : "Expected Hrs",
                "reqd" :  0,
                "fieldtype" : "Float"
            }
        ],
        size: 'small', // small, large, extra-large 
        primary_action_label: 'Update Timesheet Log',
        primary_action(values) {
            let data = d.get_values();
            let arg = {
                activity_type : data.activity_type,
                from_time : frappe.datetime.now_datetime(),
                project : data.project,
                task : data.task,
                employee : data.employee
            }
            frappe.call({
                method: "harro.harro.docevents.task.update_time_log",
                args : {
                    arg : arg,
                },
                callback:(r)=>{
                    frm.refresh_field("custom_unproductive_work_timelogs")
                    frm.reload_doc()
                    d.hide();
                }
            })
        }
    });
    d.show()
    d.set_value("project", frm.doc.project)
    d.set_value("task", frm.doc.name)
    d.set_value("employee", frm.doc.custom_employee__assign_to_employee_)
}

function update_stop_job_log(frm){
    let arg = {
        task : frm.doc.name,
        to_time : frappe.datetime.now_datetime()
    }
    frappe.call({
        method : "harro.harro.docevents.task.update_stop_task_log",
        args : {
            arg: arg,
        },
        callback:(r)=>{
            frm.reload_doc()
        }
    })
}