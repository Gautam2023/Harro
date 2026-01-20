(() => {
  // ../harro/harro/public/js/frappe/views/gantt/gantt_view.js
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
          this.sort_by = this.view_user_settings.sort_by || this.calendar_settings.field_map.start;
          this.sort_order = this.view_user_settings.sort_order || "asc";
        }
      });
    }
    setup_view() {
    }
    prepare_data(data) {
      super.prepare_data(data);
      this.prepare_tasks();
    }
    prepare_tasks() {
      var me = this;
      var meta = this.meta;
      var field_map = this.calendar_settings.field_map;
      this.tasks = this.data.flatMap(function(item) {
        var progress = 0;
        if (field_map.progress && $.isFunction(field_map.progress)) {
          progress = field_map.progress(item);
        } else if (field_map.progress) {
          progress = item[field_map.progress];
        }
        var label;
        if (meta.title_field) {
          label = item.progress ? __("{0} ({1}) - {2}%", [item[meta.title_field], item.name, item.progress]) : __("{0} ({1})", [item[meta.title_field], item.name]);
        } else {
          label = item[field_map.title];
        }
        let planned_bar = {
          start: item[field_map.start],
          end: item[field_map.end],
          name: label + " (Planned)",
          id: item[field_map.id || "name"],
          doctype: me.doctype,
          progress,
          dependencies: item.depends_on_tasks || "",
          bar_type: "planned"
        };
        let actual_bar = null;
        const has_actual = field_map.actual_start && field_map.actual_end && item[field_map.actual_start] && item[field_map.actual_end] && moment(item[field_map.actual_start]).isValid() && moment(item[field_map.actual_end]).isValid();
        if (has_actual) {
          actual_bar = {
            start: item[field_map.actual_start],
            end: item[field_map.actual_end],
            name: label + " (Actual)",
            id: (item[field_map.id || "name"] || item.name) + "_actual",
            doctype: me.doctype,
            progress,
            bar_type: "actual",
            custom_class: "bar-actual"
          };
        }
        planned_bar.custom_class = (planned_bar.custom_class || "") + " planned";
        if (has_actual) {
          actual_bar.custom_class = (actual_bar.custom_class || "") + " actual";
        }
        [planned_bar, actual_bar].forEach((bar) => {
          if (!bar)
            return;
          if (item.color && frappe.ui.color.validate_hex(item.color) && bar["bar_type"] === "actual") {
            bar["custom_class"] = "color-" + (item.actual_progress ? item.actual_progress.replace("#", "") : "FFC067");
          } else if (item.color && frappe.ui.color.validate_hex(item.color) && bar["bar_type"] != "actual") {
            bar["custom_class"] = "color-" + item.color.substr(1);
          }
          if (item.is_milestone) {
            bar["custom_class"] = "bar-milestone";
          }
        });
        return actual_bar ? [planned_bar, actual_bar] : [planned_bar];
      });
    }
    inject_hatch_pattern() {
      const svg = this.$result.find("svg")[0];
      if (!svg)
        return;
      let defs = svg.querySelector("defs");
      if (!defs) {
        defs = document.createElementNS("http://www.w3.org/2000/svg", "defs");
        svg.insertBefore(defs, svg.firstChild);
      }
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
      const actualBars = document.querySelectorAll('g.bar-wrapper[data-id$="_actual"] .bar');
      actualBars.forEach((bar) => {
        bar.setAttribute("fill", "url(#diagonalHatch)");
      });
    }
    render() {
      this.load_lib.then(() => {
        this.render_gantt();
      });
    }
    render_header() {
    }
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
          if (!me.can_write)
            return;
          frappe.db.set_value(task.doctype, task.id, {
            [field_map.start]: moment(start).format(date_format),
            [field_map.end]: moment(end).format(date_format)
          });
        },
        on_progress_change: (task, progress) => {
          if (!me.can_write)
            return;
          var progress_fieldname = "progress";
          if ($.isFunction(field_map.progress)) {
            progress_fieldname = null;
          } else if (field_map.progress) {
            progress_fieldname = field_map.progress;
          }
          if (progress_fieldname) {
            frappe.db.set_value(task.doctype, task.id, {
              [progress_fieldname]: parseInt(progress)
            });
          }
        },
        on_view_change: (mode) => {
          me.save_view_user_settings({
            gantt_view_mode: mode
          });
        },
        custom_popup_html: (task) => {
          var item = me.get_item(task.id);
          var html = `<div class="title">${task.name}</div>
					<div class="subtitle">${moment(task._start).format("MMM D")} - ${moment(task._end).format(
            "MMM D"
          )}</div>`;
          var custom = me.settings.gantt_custom_popup_html;
          if (custom && $.isFunction(custom)) {
            var ganttobj = task;
            html = custom(ganttobj, item);
          }
          return '<div class="details-container">' + html + "</div>";
        }
      });
      this.setup_view_mode_buttons();
      this.set_colors();
      this.inject_hatch_pattern();
    }
    setup_view_mode_buttons() {
      let $btn_group = this.$paging_area.find(".gantt-view-mode");
      if ($btn_group.length > 0)
        return;
      const view_modes = this.gantt.options.view_modes || [];
      const active_class = (view_mode) => this.gantt.view_is(view_mode) ? "btn-info" : "";
      const html = `<div class="btn-group gantt-view-mode">
				${view_modes.map(
        (value) => `<button type="button"
						class="btn btn-default btn-sm btn-view-mode ${active_class(value)}"
						data-value="${value}">
						${__(value)}
					</button>`
      ).join("")}
			</div>`;
      this.$paging_area.find(".level-left").append(html);
      const change_view_mode = (value) => setTimeout(() => this.gantt.change_view_mode(value), 0);
      this.$paging_area.on("click", ".btn-view-mode", (e) => {
        const $btn = $(e.currentTarget);
        this.$paging_area.find(".btn-view-mode").removeClass("btn-info");
        $btn.addClass("btn-info");
        const value = $btn.data().value;
        change_view_mode(value);
      });
    }
    set_colors() {
      const classes = [...new Set(this.tasks.map((t) => t.custom_class).filter((c) => c && c.startsWith("color-")))];
      let pattern_defs = "";
      let css_rules = "";
      classes.forEach((c) => {
        const class_name = c.replace("#", "");
        const hex = c.replace("color-", "").replace("#", "");
        const bar_color = "#" + hex;
        const pattern_id = `pattern_${hex}`;
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
        css_rules += `
			.gantt .bar-wrapper.bar-actual .bar {
				fill: url(#diagonalHatch) !important;
				stroke: #333 !important;
				stroke-width: 1px;
				height: 16px !important;
				y: 10px !important;
			}
			`;
        const progress_color = frappe.ui.color.get_contrast_color(bar_color);
        css_rules += `
			.gantt .bar-wrapper.${class_name} .bar-progress {
				fill: ${progress_color};
			}
			`;
      });
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
        "assets/frappe/node_modules/frappe-gantt/dist/frappe-gantt.min.js"
      ];
    }
  };

  // ../harro/harro/public/js/hierarchy_chart/harro_hierarchy_chart_desktop.js
  window.HierarchyChart = class {
    constructor(doctype, wrapper, method) {
      this.wrapper = $(wrapper);
      this.method = method;
      this.doctype = doctype;
      this.page = {
        main: this.wrapper,
        clear_inner_toolbar: () => {
          this.wrapper.find(".chart-toolbar").remove();
        },
        add_inner_button: (label, onClick) => {
          let toolbar = this.wrapper.find(".chart-toolbar");
          if (!toolbar.length) {
            toolbar = $('<div class="chart-toolbar" style="margin-bottom: 15px;"></div>');
            this.wrapper.prepend(toolbar);
          }
          $('<button class="btn btn-default btn-sm">' + label + "</button>").appendTo(toolbar).click(onClick);
        },
        remove_inner_button: (label) => {
          this.wrapper.find('.chart-toolbar button:contains("' + label + '")').remove();
        },
        add_field: () => {
          console.log("add_field not implemented for HTML field wrapper");
        },
        find: (selector) => {
          return this.wrapper.find(selector);
        }
      };
      this.setup_page_style();
      this.page.main.addClass("frappe-card");
      this.nodes = {};
      this.setup_node_class();
      this.args = {};
    }
    setup_page_style() {
      this.page.main.css({
        "min-height": "300px",
        "max-height": "700px",
        overflow: "auto",
        position: "relative"
      });
    }
    setup_node_class() {
      let me = this;
      this.Node = class {
        constructor({
          id,
          parent,
          parent_id,
          image,
          name,
          title,
          expandable,
          connections,
          is_root
        }) {
          $.extend(this, arguments[0]);
          this.expanded = 0;
          me.nodes[this.id] = this;
          me.make_node_element(this);
          if (!me.all_nodes_expanded) {
            me.setup_node_click_action(this);
          }
          me.setup_edit_node_action(this);
        }
      };
    }
    make_node_element(node) {
      let node_card = frappe.render_template("node_card", {
        id: node.id,
        name: node.name,
        title: node.title,
        image: node.image,
        parent: node.parent_id,
        connections: node.connections,
        is_mobile: false
      });
      node.parent.append(node_card);
      node.$link = $(`[id="${node.id}"]`);
    }
    show() {
      this.setup_actions();
      let me = this;
      me.project = this.args.project || "";
      if (!me.project) {
        frappe.throw(__("Project is required."));
      }
      me.make_svg_markers();
      me.setup_hierarchy();
      me.render_root_nodes();
      me.all_nodes_expanded = false;
    }
    setup_actions() {
      let me = this;
      this.page.clear_inner_toolbar();
      this.page.add_inner_button(__("Export"), function() {
        me.export_chart();
      });
      this.page.add_inner_button(__("Expand All"), function() {
        me.load_children(me.root_node, true);
        me.all_nodes_expanded = true;
        me.page.remove_inner_button(__("Expand All"));
        me.page.add_inner_button(__("Collapse All"), function() {
          me.setup_hierarchy();
          me.render_root_nodes();
          me.all_nodes_expanded = false;
          me.page.remove_inner_button(__("Collapse All"));
          me.setup_actions();
        });
      });
    }
    export_chart() {
      if (typeof html2canvas === "undefined" && typeof window.html2canvas !== "undefined") {
        window.html2canvas(document.querySelector("#hierarchy-chart-wrapper"), {
          scrollY: -window.scrollY,
          scrollX: 0
        }).then(function(canvas) {
          let dataURL = canvas.toDataURL("image/png");
          let a = document.createElement("a");
          a.href = dataURL;
          a.download = "hierarchy_chart";
          a.click();
        }).finally(() => {
          frappe.dom.unfreeze();
          this.setup_page_style();
          $(".node-card").removeClass("exported");
        });
      } else {
        frappe.msgprint(__("Export feature is not available. Please refresh the page."));
        frappe.dom.unfreeze();
        this.setup_page_style();
        $(".node-card").removeClass("exported");
        return;
      }
      frappe.dom.freeze(__("Exporting..."));
      this.page.main.css({
        "min-height": "",
        "max-height": "",
        overflow: "visible",
        position: "fixed",
        left: "0",
        top: "0"
      });
      $(".node-card").addClass("exported");
    }
    setup_hierarchy() {
      if (this.$hierarchy)
        this.$hierarchy.remove();
      $(`#connectors`).empty();
      this.$hierarchy = $(
        `<ul class="hierarchy">
                <li class="root-level level">
                    <ul class="node-children"></ul>
                </li>
            </ul>`
      );
      this.wrapper.find("#hierarchy-chart").empty().append(this.$hierarchy);
      this.nodes = {};
    }
    make_svg_markers() {
      $("#hierarchy-chart-wrapper").remove();
      this.wrapper.append(`
            <div id="hierarchy-chart-wrapper">
                <svg id="arrows" width="100%" height="100%">
                    <defs>
                        <marker id="arrowhead-active" viewBox="0 0 10 10" refX="3" refY="5" markerWidth="6" markerHeight="6" orient="auto" fill="var(--gray-600)">
                            <path d="M 0 0 L 10 5 L 0 10 z"></path>
                        </marker>
                        <marker id="arrowhead-collapsed" viewBox="0 0 10 10" refX="3" refY="5" markerWidth="6" markerHeight="6" orient="auto" fill="var(--gray-400)">
                            <path d="M 0 0 L 10 5 L 0 10 z"></path>
                        </marker>

                        <marker id="arrowstart-active" viewBox="0 0 10 10" refX="3" refY="5" markerWidth="8" markerHeight="8" orient="auto" fill="var(--gray-600)">
                            <circle cx="4" cy="4" r="3.5" fill="white" stroke="var(--gray-600)"/>
                        </marker>
                        <marker id="arrowstart-collapsed" viewBox="0 0 10 10" refX="3" refY="5" markerWidth="8" markerHeight="8" orient="auto" fill="var(--gray-400)">
                            <circle cx="4" cy="4" r="3.5" fill="white" stroke="var(--gray-400)"/>
                        </marker>
                    </defs>
                    <g id="connectors" fill="none">
                    </g>
                </svg>
                <div id="hierarchy-chart">
                </div>
            </div>`);
    }
    render_root_nodes(expanded_view = false) {
      let me = this;
      return frappe.call({
        method: me.method,
        args: {
          project: me.project
        }
      }).then((r) => {
        if (r.message.length) {
          let expand_node;
          let node;
          $.each(r.message, (_i, data) => {
            if ($(`[id="${data.id}"]`).length)
              return;
            node = new me.Node({
              id: data.id,
              parent: $('<li class="child-node"></li>').appendTo(
                me.$hierarchy.find(".node-children")
              ),
              parent_id: "",
              image: data.image,
              name: data.name,
              title: data.title,
              expandable: true,
              connections: data.connections,
              is_root: true
            });
            if (!expand_node && data.connections)
              expand_node = node;
          });
          me.root_node = expand_node;
          if (!expanded_view) {
            me.expand_node(expand_node);
          }
        }
      });
    }
    expand_node(node) {
      const is_sibling = this.selected_node && this.selected_node.parent_id === node.parent_id;
      this.set_selected_node(node);
      this.show_active_path(node);
      this.collapse_previous_level_nodes(node);
      if (!is_sibling) {
        this.refresh_connectors(node.parent_id);
        let grandparent = $(`[id="${node.parent_id}"]`).attr("data-parent");
        this.refresh_connectors(grandparent);
      }
      if (node.expandable && !node.expanded) {
        return this.load_children(node);
      }
    }
    collapse_node() {
      if (this.selected_node.expandable) {
        this.selected_node.$children.hide();
        $(`path[data-parent="${this.selected_node.id}"]`).hide();
        this.selected_node.expanded = false;
      }
    }
    show_active_path(node) {
      $(`[id="${node.parent_id}"]`).addClass("active-path");
    }
    load_children(node, deep = false) {
      if (!this.project) {
        frappe.throw(__("Project is required."));
      }
      if (!deep) {
        frappe.run_serially([
          () => this.get_child_nodes(node.id),
          (child_nodes) => this.render_child_nodes(node, child_nodes)
        ]);
      } else {
        frappe.run_serially([
          () => frappe.dom.freeze(),
          () => this.setup_hierarchy(),
          () => this.render_root_nodes(true),
          () => this.get_all_nodes(),
          (data_list) => this.render_children_of_all_nodes(data_list),
          () => frappe.dom.unfreeze()
        ]);
      }
    }
    get_child_nodes(node_id) {
      let me = this;
      return new Promise((resolve) => {
        frappe.call({
          method: me.method,
          args: {
            parent: node_id,
            project: me.project
          }
        }).then((r) => resolve(r.message));
      });
    }
    render_child_nodes(node, child_nodes) {
      const last_level = this.$hierarchy.find(".level:last").index();
      const current_level = $(`[id="${node.id}"]`).parent().parent().parent().index();
      if (last_level === current_level) {
        this.$hierarchy.append(`
                <li class="level"></li>
            `);
      }
      if (!node.$children) {
        node.$children = $('<ul class="node-children"></ul>').hide().appendTo(this.$hierarchy.find(".level:last"));
        node.$children.empty();
        if (child_nodes) {
          $.each(child_nodes, (_i, data) => {
            if (!$(`[id="${data.id}"]`).length) {
              this.add_node(node, data);
              setTimeout(() => {
                this.add_connector(node.id, data.id);
              }, 250);
            }
          });
        }
      }
      node.$children.show();
      $(`path[data-parent="${node.id}"]`).show();
      node.expanded = true;
    }
    get_all_nodes() {
      let me = this;
      return new Promise((resolve) => {
        frappe.call({
          method: "harro.harro.docevents.project.get_all_project_nodes",
          args: {
            project: me.project
          },
          callback: (r) => {
            resolve(r.message);
          }
        });
      });
    }
    render_children_of_all_nodes(data_list) {
      let entry;
      let node;
      while (data_list.length) {
        entry = data_list.shift();
        node = this.nodes[entry.parent];
        if (node) {
          this.render_child_nodes_for_expanded_view(node, entry.data);
        } else if (data_list.length) {
          data_list.push(entry);
        }
      }
    }
    render_child_nodes_for_expanded_view(node, child_nodes) {
      node.$children = $('<ul class="node-children"></ul>');
      const last_level = this.$hierarchy.find(".level:last").index();
      const node_level = $(`[id="${node.id}"]`).parent().parent().parent().index();
      if (last_level === node_level) {
        this.$hierarchy.append(`
                <li class="level"></li>
            `);
        node.$children.appendTo(this.$hierarchy.find(".level:last"));
      } else {
        node.$children.appendTo(this.$hierarchy.find(".level:eq(" + (node_level + 1) + ")"));
      }
      node.$children.hide().empty();
      if (child_nodes) {
        $.each(child_nodes, (_i, data) => {
          this.add_node(node, data);
          setTimeout(() => {
            this.add_connector(node.id, data.id);
          }, 250);
        });
      }
      node.$children.show();
      $(`path[data-parent="${node.id}"]`).show();
      node.expanded = true;
    }
    add_node(node, data) {
      return new this.Node({
        id: data.id,
        parent: $('<li class="child-node"></li>').appendTo(node.$children),
        parent_id: node.id,
        image: data.image,
        name: data.name,
        title: data.title,
        expandable: data.expandable,
        connections: data.connections,
        children: null
      });
    }
    add_connector(parent_id, child_id) {
      const parent_node = document.getElementById(`${parent_id}`);
      const child_node = document.getElementById(`${child_id}`);
      let path = document.createElementNS("http://www.w3.org/2000/svg", "path");
      const pos_parent_right = {
        x: parent_node.offsetLeft + parent_node.offsetWidth,
        y: parent_node.offsetTop + parent_node.offsetHeight / 2
      };
      const pos_child_left = {
        x: child_node.offsetLeft - 5,
        y: child_node.offsetTop + child_node.offsetHeight / 2
      };
      const connector = this.get_connector(pos_parent_right, pos_child_left);
      path.setAttribute("d", connector);
      this.set_path_attributes(path, parent_id, child_id);
      document.getElementById("connectors").appendChild(path);
    }
    get_connector(pos_parent_right, pos_child_left) {
      if (pos_parent_right.y === pos_child_left.y) {
        return "M" + pos_parent_right.x + "," + pos_parent_right.y + " L" + pos_child_left.x + "," + pos_child_left.y;
      } else {
        let arc_1 = "";
        let arc_2 = "";
        let offset = 0;
        if (pos_parent_right.y > pos_child_left.y) {
          arc_1 = "a10,10 1 0 0 10,-10 ";
          arc_2 = "a10,10 0 0 1 10,-10 ";
          offset = 10;
        } else {
          arc_1 = "a10,10 0 0 1 10,10 ";
          arc_2 = "a10,10 1 0 0 10,10 ";
          offset = -10;
        }
        return "M" + pos_parent_right.x + "," + pos_parent_right.y + " L" + (pos_parent_right.x + 40) + "," + pos_parent_right.y + " " + arc_1 + "L" + (pos_parent_right.x + 50) + "," + (pos_child_left.y + offset) + " " + arc_2 + "L" + pos_child_left.x + "," + pos_child_left.y;
      }
    }
    set_path_attributes(path, parent_id, child_id) {
      path.setAttribute("data-parent", parent_id);
      path.setAttribute("data-child", child_id);
      const parent = $(`[id="${parent_id}"]`);
      if (parent.hasClass("active")) {
        path.setAttribute("class", "active-connector");
        path.setAttribute("marker-start", "url(#arrowstart-active)");
        path.setAttribute("marker-end", "url(#arrowhead-active)");
      } else {
        path.setAttribute("class", "collapsed-connector");
        path.setAttribute("marker-start", "url(#arrowstart-collapsed)");
        path.setAttribute("marker-end", "url(#arrowhead-collapsed)");
      }
    }
    set_selected_node(node) {
      if (this.selected_node)
        this.selected_node.$link.removeClass("active");
      this.selected_node = node;
      node.$link.addClass("active");
    }
    collapse_previous_level_nodes(node) {
      let node_parent = $(`[id="${node.parent_id}"]`);
      let previous_level_nodes = node_parent.parent().parent().children("li");
      let node_card;
      previous_level_nodes.each(function() {
        node_card = $(this).find(".node-card");
        if (!node_card.hasClass("active-path")) {
          node_card.addClass("collapsed");
        }
      });
    }
    refresh_connectors(node_parent) {
      if (!node_parent)
        return;
      $(`path[data-parent="${node_parent}"]`).remove();
      frappe.run_serially([
        () => this.get_child_nodes(node_parent),
        (child_nodes) => {
          if (child_nodes) {
            $.each(child_nodes, (_i, data) => {
              this.add_connector(node_parent, data.id);
            });
          }
        }
      ]);
    }
    setup_node_click_action(node) {
      let me = this;
      let node_element = $(`[id="${node.id}"]`);
      node_element.click(function() {
        const is_sibling = me.selected_node.parent_id === node.parent_id;
        if (is_sibling) {
          me.collapse_node();
        } else if (node_element.is(":visible") && (node_element.hasClass("collapsed") || node_element.hasClass("active-path"))) {
          me.remove_levels_after_node(node);
          me.remove_orphaned_connectors();
        }
        me.expand_node(node);
      });
    }
    setup_edit_node_action(node) {
      let node_element = $(`[id="${node.id}"]`);
      let me = this;
      node_element.find(".btn-edit-node").click(function() {
        frappe.set_route("Form", me.doctype, node.id);
      });
    }
    remove_levels_after_node(node) {
      let level = $(`[id="${node.id}"]`).parent().parent().parent().index();
      level = $(".hierarchy > li:eq(" + level + ")");
      level.nextAll("li").remove();
      let nodes = level.find(".node-card");
      let node_object;
      $.each(nodes, (_i, element) => {
        node_object = this.nodes[element.id];
        node_object.expanded = 0;
        node_object.$children = null;
      });
      nodes.removeClass("collapsed active-path");
    }
    remove_orphaned_connectors() {
      let paths = $("#connectors > path");
      $.each(paths, (_i, path) => {
        const parent = $(path).data("parent");
        const child = $(path).data("child");
        if ($(`[id="${parent}"]`).length && $(`[id="${child}"]`).length)
          return;
        $(path).remove();
      });
    }
  };

  // frappe-html:/Users/viralkansodiya/frappe-bench/apps/harro/harro/public/js/templates/node_card.html
  frappe.templates["node_card"] = `<div class="node-card card cursor-pointer" id="{%= id %}" data-parent="{%= parent %}">
	<div class="node-meta d-flex flex-row">
		<div class="mr-3">
			<span class="avatar node-image" title="{{ name }}">
				<span class="avatar-frame" src={{image}} style="background-image: url('{{ image }}')"></span>
			</span>
		</div>
		<div>
			<div class="node-name d-flex flex-row mb-1">
				<span class="ellipsis">{{ name }}</span>
				<div class="btn-sm btn-edit-node">
					<a class="node-edit-icon">
						<svg class="es-icon es-line icon-xs icon">
							<use href="#es-line-edit"></use>
						</svg>
					</a>
					<span class="edit-chart-node text-lg">{{ __("Edit") }}</span>
				</div>
			</div>
			<div class="node-info d-flex flex-row mb-1">
				{% if title %}
					<div class="node-title text-muted ellipsis">{{ title }}&nbsp;&middot;&nbsp;</div>
				{% endif %}

				{% if is_mobile %}
					<div class="node-connections text-muted ellipsis">
						&nbsp;{{ connections }} <span class="fa fa-level-down"></span>
					</div>
				{% else %}
					{% if connections == 1 %}
						<div class="node-connections text-muted ellipsis">{{ connections }} Connection</div>
					{% else %}
						<div class="node-connections text-muted ellipsis">{{ connections }} Connections</div>
					{% endif %}
				{% endif %}
			</div>
		</div>
	</div>
</div>
`;
})();
//# sourceMappingURL=harro.bundle.WZAAR374.js.map
