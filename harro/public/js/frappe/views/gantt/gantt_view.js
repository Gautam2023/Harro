frappe.provide("frappe.views");

frappe.views.GanttView = class GanttView extends frappe.views.ListView {
	get view_name() {
		return "Gantt";
	}

	setup_defaults() {
		return super.setup_defaults().then(() => {
			this.page_title = this.page_title + " " + __("Gantt");
			this.calendar_settings = frappe.views.calendar[this.doctype] || {};

			if (typeof this.calendar_settings.gantt == "object") {
				Object.assign(this.calendar_settings, this.calendar_settings.gantt);
			}

			if (this.calendar_settings.order_by) {
				this.sort_by = this.calendar_settings.order_by;
				this.sort_order = "asc";
			} else {
				this.sort_by =
					this.view_user_settings.sort_by || this.calendar_settings.field_map.start;
				this.sort_order = this.view_user_settings.sort_order || "asc";
			}
		});
	}

	setup_view() {}

	prepare_data(data) {
		super.prepare_data(data);
		this.prepare_tasks();
	}

	prepare_tasks() {
		var me = this;
		var meta = this.meta;
		var field_map = this.calendar_settings.field_map;

		this.tasks = this.data.flatMap(function (item) {
			// set progress
			var progress = 0;
			if (field_map.progress && $.isFunction(field_map.progress)) {
				progress = field_map.progress(item);
			} else if (field_map.progress) {
				progress = item[field_map.progress];
			}

			// label
			var label;
			if (meta.title_field) {
				label = item.progress
					? __("{0} ({1}) - {2}%", [item[meta.title_field], item.name, item.progress])
					: __("{0} ({1})", [item[meta.title_field], item.name]);
			} else {
				label = item[field_map.title];
			}

			// -----------------------------
			// BAR 1: PLANNED
			// -----------------------------
			let planned_bar = {
				start: item[field_map.start],
				end: item[field_map.end],
				name: label + " (Planned)",
				id: item[field_map.id || "name"],
				doctype: me.doctype,
				progress: progress,
				dependencies: item.depends_on_tasks || "",
				bar_type: "planned"
			};

			let actual_bar = null;

			const has_actual =
				field_map.actual_start &&
				field_map.actual_end &&
				item[field_map.actual_start] &&
				item[field_map.actual_end] &&
				moment(item[field_map.actual_start]).isValid() &&
				moment(item[field_map.actual_end]).isValid();

			if (has_actual) {
				actual_bar = {
					start: item[field_map.actual_start],
					end: item[field_map.actual_end],
					name: label + " (Actual)",
					id: (item[field_map.id || "name"] || item.name) + "_actual",
					doctype: me.doctype,
					progress: progress,
					bar_type: "actual",
					custom_class: "bar-actual"
				};
			}

			planned_bar.custom_class = (planned_bar.custom_class || "") + " planned";
			if(has_actual){
				actual_bar.custom_class = (actual_bar.custom_class || "") + " actual";
			}


			// apply custom colors/classes from original code
			[planned_bar, actual_bar].forEach(bar => {
				if (!bar) return;

				if (item.color && frappe.ui.color.validate_hex(item.color) && bar["bar_type"] === "actual") {
					bar["custom_class"] = "color-" + 
						(item.actual_progress ? item.actual_progress.replace("#", "") : "FFC067");
				}

				else if(item.color && frappe.ui.color.validate_hex(item.color) && bar["bar_type"] != "actual"){
					bar["custom_class"] = "color-" + item.color.substr(1);
				}

				if (item.is_milestone) {
					bar["custom_class"] = "bar-milestone";
				}
			});

			// return 2 bars (if actual exists), else only planned
			return actual_bar ? [planned_bar, actual_bar] : [planned_bar];
		});
	}

	inject_hatch_pattern() {
		const svg = this.$result.find("svg")[0];
		if (!svg) return;

		// Ensure <defs> exists
		let defs = svg.querySelector("defs");
		if (!defs) {
			defs = document.createElementNS("http://www.w3.org/2000/svg", "defs");
			svg.insertBefore(defs, svg.firstChild);
		}

		// Inject pattern once (if it does not already exist)
		if (!svg.querySelector("#diagonalHatch")) {
			const pattern = document.createElementNS("http://www.w3.org/2000/svg", "pattern");
			pattern.setAttribute("id", "diagonalHatch");
			pattern.setAttribute("patternUnits", "userSpaceOnUse");
			pattern.setAttribute("width", "6");
			pattern.setAttribute("height", "6");

			pattern.innerHTML = `
				<path d="M0,0 l6,6 M-6,0 l6,6 M0,-6 l6,6"
					stroke="#555" stroke-width="1" />
			`;
			defs.appendChild(pattern);
		}

		// Apply hatch pattern to all bars whose data-id ends with "_actual"
		const actualBars = document.querySelectorAll('g.bar-wrapper[data-id$="_actual"] .bar');
		actualBars.forEach(bar => {
			bar.setAttribute("fill", "url(#diagonalHatch)");
		});
	}

	render() {
		this.load_lib.then(() => {
			this.render_gantt();
		});
	}

	render_header() {}

	render_gantt() {
		const me = this;
		const gantt_view_mode = this.view_user_settings.gantt_view_mode || "Day";
		const field_map = this.calendar_settings.field_map;
		const date_format = "YYYY-MM-DD";

		this.$result.empty();
		this.$result.addClass("gantt-modern");

		this.gantt = new Gantt(this.$result[0], this.tasks, {
			bar_height: 35,
			bar_corner_radius: 4,
			resize_handle_width: 8,
			resize_handle_height: 28,
			resize_handle_corner_radius: 3,
			resize_handle_offset: 4,
			view_mode: gantt_view_mode,
			date_format: "YYYY-MM-DD",
			on_click: (task) => {
				frappe.set_route("Form", task.doctype, task.id.replace("_actual", ""));
			},
			on_date_change: (task, start, end) => {
				if (!me.can_write) return;
				frappe.db.set_value(task.doctype, task.id, {
					[field_map.start]: moment(start).format(date_format),
					[field_map.end]: moment(end).format(date_format),
				});
			},
			on_progress_change: (task, progress) => {
				if (!me.can_write) return;
				var progress_fieldname = "progress";

				if ($.isFunction(field_map.progress)) {
					progress_fieldname = null;
				} else if (field_map.progress) {
					progress_fieldname = field_map.progress;
				}

				if (progress_fieldname) {
					frappe.db.set_value(task.doctype, task.id, {
						[progress_fieldname]: parseInt(progress),
					});
				}
			},
			on_view_change: (mode) => {
				// save view mode
				me.save_view_user_settings({
					gantt_view_mode: mode,
				});
			},
			custom_popup_html: (task) => {
				var item = me.get_item(task.id);

				var html = `<div class="title">${task.name}</div>
					<div class="subtitle">${moment(task._start).format("MMM D")} - ${moment(task._end).format(
					"MMM D"
				)}</div>`;

				// custom html in doctype settings
				var custom = me.settings.gantt_custom_popup_html;
				if (custom && $.isFunction(custom)) {
					var ganttobj = task;
					html = custom(ganttobj, item);
				}
				return '<div class="details-container">' + html + "</div>";
			},
		});
		this.setup_view_mode_buttons();
		this.set_colors();
		this.inject_hatch_pattern();
	}

	setup_view_mode_buttons() {
		// view modes (for translation) __("Day"), __("Week"), __("Month"),
		//__("Half Day"), __("Quarter Day")

		let $btn_group = this.$paging_area.find(".gantt-view-mode");
		if ($btn_group.length > 0) return;

		const view_modes = this.gantt.options.view_modes || [];
		const active_class = (view_mode) => (this.gantt.view_is(view_mode) ? "btn-info" : "");
		const html = `<div class="btn-group gantt-view-mode">
				${view_modes
					.map(
						(value) => `<button type="button"
						class="btn btn-default btn-sm btn-view-mode ${active_class(value)}"
						data-value="${value}">
						${__(value)}
					</button>`
					)
					.join("")}
			</div>`;

		this.$paging_area.find(".level-left").append(html);

		// change view mode asynchronously
		const change_view_mode = (value) =>
			setTimeout(() => this.gantt.change_view_mode(value), 0);

		this.$paging_area.on("click", ".btn-view-mode", (e) => {
			const $btn = $(e.currentTarget);
			this.$paging_area.find(".btn-view-mode").removeClass("btn-info");
			$btn.addClass("btn-info");

			const value = $btn.data().value;
			change_view_mode(value);
		});
	}

	set_colors() {
		const classes = [...new Set(this.tasks
			.map(t => t.custom_class)
			.filter(c => c && c.startsWith("color-")))];
		
		let pattern_defs = "";
		let css_rules = "";
			
		classes.forEach(c => {
			const class_name = c.replace("#", "");
			const hex = c.replace("color-", "").replace("#", "");

			const bar_color = "#" + hex;
			const pattern_id = `pattern_${hex}`;
			// SOLID planned bar
			css_rules += `
			.gantt .bar-wrapper.${class_name} .bar {
				fill: ${bar_color};
			}
			.gantt .bar-wrapper.${class_name}.bar-planned .bar {
				fill: ${bar_color};
			}
			`;
			pattern_defs += `
				<pattern id="${pattern_id}" patternUnits="userSpaceOnUse" width="6" height="6" patternTransform="rotate(45)">
					<rect width="6" height="6" fill="white" opacity="0"></rect>
					<line x1="0" y1="0" x2="0" y2="6" stroke="${bar_color}" stroke-width="1"></line>
				</pattern>
			`;
			// BLACK HATCH style for ALL ACTUAL bars
			css_rules += `
			.gantt .bar-wrapper.bar-actual .bar {
				fill: url(#diagonalHatch) !important;
				stroke: #333 !important;
				stroke-width: 1px;
				height: 16px !important;
				y: 10px !important;
			}
			`;

			// Progress color
			const progress_color = frappe.ui.color.get_contrast_color(bar_color);
			css_rules += `
			.gantt .bar-wrapper.${class_name} .bar-progress {
				fill: ${progress_color};
			}
			`;
		});

		// General CSS for actual bars (all black, regardless of color class)
		css_rules += `
		.gantt .bar-wrapper.bar-actual .bar {
			fill: url(#diagonalHatch) !important;
			stroke: #333 !important;
			stroke-width: 1px;
			height: 16px !important;
			y: 10px !important;
		}
		
		.gantt .bar-wrapper.bar-actual.color-* .bar {
			fill: url(#diagonalHatch) !important;
			stroke: #333 !important;
			stroke-width: 1px;
			height: 16px !important;
			y: 10px !important;
		}
		`;

		// Remove the duplicate inject_hatch_pattern() call from render()
		const style = `
		<svg width="0" height="0" style="position:absolute">
			<defs>${pattern_defs}</defs>
			</svg>
			<style>${css_rules}</style>
		`;

		this.$result.prepend(style);
	}

	get_item(name) {
		return this.data.find((item) => item.name === name);
	}

	get required_libs() {
		return [
			"assets/frappe/node_modules/frappe-gantt/dist/frappe-gantt.css",
			"assets/frappe/node_modules/frappe-gantt/dist/frappe-gantt.min.js",
		];
	}
};