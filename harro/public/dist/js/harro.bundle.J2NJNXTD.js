(()=>{frappe.provide("frappe.views");frappe.views.GanttView=class extends frappe.views.ListView{get view_name(){return"Gantt"}setup_defaults(){return super.setup_defaults().then(()=>{this.page_title=this.page_title+" "+__("Gantt"),this.calendar_settings=frappe.views.calendar[this.doctype]||{},typeof this.calendar_settings.gantt=="object"&&Object.assign(this.calendar_settings,this.calendar_settings.gantt),this.calendar_settings.order_by?(this.sort_by=this.calendar_settings.order_by,this.sort_order="asc"):(this.sort_by=this.view_user_settings.sort_by||this.calendar_settings.field_map.start,this.sort_order=this.view_user_settings.sort_order||"asc")})}setup_view(){}prepare_data(r){super.prepare_data(r),this.prepare_tasks()}prepare_tasks(){var r=this,i=this.meta,e=this.calendar_settings.field_map;this.tasks=this.data.flatMap(function(t){var a=0;e.progress&&$.isFunction(e.progress)?a=e.progress(t):e.progress&&(a=t[e.progress]);var s;i.title_field?s=t.progress?__("{0} ({1}) - {2}%",[t[i.title_field],t.name,t.progress]):__("{0} ({1})",[t[i.title_field],t.name]):s=t[e.title];let n={start:t[e.start],end:t[e.end],name:s+" (Planned)",id:t[e.id||"name"],doctype:r.doctype,progress:a,dependencies:t.depends_on_tasks||"",bar_type:"planned"},o=null,p=e.actual_start&&e.actual_end&&t[e.actual_start]&&t[e.actual_end]&&moment(t[e.actual_start]).isValid()&&moment(t[e.actual_end]).isValid();return p&&(o={start:t[e.actual_start],end:t[e.actual_end],name:s+" (Actual)",id:(t[e.id||"name"]||t.name)+"_actual",doctype:r.doctype,progress:a,bar_type:"actual",custom_class:"bar-actual"}),n.custom_class=(n.custom_class||"")+" planned",p&&(o.custom_class=(o.custom_class||"")+" actual"),[n,o].forEach(l=>{!l||(t.color&&frappe.ui.color.validate_hex(t.color)&&l.bar_type==="actual"?l.custom_class="color-"+(t.actual_progress?t.actual_progress.replace("#",""):"FFC067"):t.color&&frappe.ui.color.validate_hex(t.color)&&l.bar_type!="actual"&&(l.custom_class="color-"+t.color.substr(1)),t.is_milestone&&(l.custom_class="bar-milestone"))}),o?[n,o]:[n]})}inject_hatch_pattern(){let r=this.$result.find("svg")[0];if(!r)return;let i=r.querySelector("defs");if(i||(i=document.createElementNS("http://www.w3.org/2000/svg","defs"),r.insertBefore(i,r.firstChild)),!r.querySelector("#diagonalHatch")){let t=document.createElementNS("http://www.w3.org/2000/svg","pattern");t.setAttribute("id","diagonalHatch"),t.setAttribute("patternUnits","userSpaceOnUse"),t.setAttribute("width","6"),t.setAttribute("height","6"),t.innerHTML=`
				<path d="M0,0 l6,6 M-6,0 l6,6 M0,-6 l6,6"
					stroke="#555" stroke-width="1" />
			`,i.appendChild(t)}document.querySelectorAll('g.bar-wrapper[data-id$="_actual"] .bar').forEach(t=>{t.setAttribute("fill","url(#diagonalHatch)")})}render(){this.load_lib.then(()=>{this.render_gantt()})}render_header(){}render_gantt(){let r=this,i=this.view_user_settings.gantt_view_mode||"Day",e=this.calendar_settings.field_map,t="YYYY-MM-DD";this.$result.empty(),this.$result.addClass("gantt-modern"),this.gantt=new Gantt(this.$result[0],this.tasks,{bar_height:35,bar_corner_radius:4,resize_handle_width:8,resize_handle_height:28,resize_handle_corner_radius:3,resize_handle_offset:4,view_mode:i,date_format:"YYYY-MM-DD",on_click:a=>{frappe.set_route("Form",a.doctype,a.id.replace("_actual",""))},on_date_change:(a,s,n)=>{!r.can_write||frappe.db.set_value(a.doctype,a.id,{[e.start]:moment(s).format(t),[e.end]:moment(n).format(t)})},on_progress_change:(a,s)=>{if(!!r.can_write){var n="progress";$.isFunction(e.progress)?n=null:e.progress&&(n=e.progress),n&&frappe.db.set_value(a.doctype,a.id,{[n]:parseInt(s)})}},on_view_change:a=>{r.save_view_user_settings({gantt_view_mode:a})},custom_popup_html:a=>{var s=r.get_item(a.id),n=`<div class="title">${a.name}</div>
					<div class="subtitle">${moment(a._start).format("MMM D")} - ${moment(a._end).format("MMM D")}</div>`,o=r.settings.gantt_custom_popup_html;if(o&&$.isFunction(o)){var p=a;n=o(p,s)}return'<div class="details-container">'+n+"</div>"}}),this.setup_view_mode_buttons(),this.set_colors(),this.inject_hatch_pattern()}setup_view_mode_buttons(){if(this.$paging_area.find(".gantt-view-mode").length>0)return;let i=this.gantt.options.view_modes||[],e=s=>this.gantt.view_is(s)?"btn-info":"",t=`<div class="btn-group gantt-view-mode">
				${i.map(s=>`<button type="button"
						class="btn btn-default btn-sm btn-view-mode ${e(s)}"
						data-value="${s}">
						${__(s)}
					</button>`).join("")}
			</div>`;this.$paging_area.find(".level-left").append(t);let a=s=>setTimeout(()=>this.gantt.change_view_mode(s),0);this.$paging_area.on("click",".btn-view-mode",s=>{let n=$(s.currentTarget);this.$paging_area.find(".btn-view-mode").removeClass("btn-info"),n.addClass("btn-info");let o=n.data().value;a(o)})}set_colors(){let r=[...new Set(this.tasks.map(a=>a.custom_class).filter(a=>a&&a.startsWith("color-")))],i="",e="";r.forEach(a=>{let s=a.replace("#",""),n=a.replace("color-","").replace("#",""),o="#"+n,p=`pattern_${n}`;e+=`
			.gantt .bar-wrapper.${s} .bar {
				fill: ${o};
			}
			.gantt .bar-wrapper.${s}.bar-planned .bar {
				fill: ${o};
			}
			`,i+=`
				<pattern id="${p}" patternUnits="userSpaceOnUse" width="6" height="6" patternTransform="rotate(45)">
					<rect width="6" height="6" fill="white" opacity="0"></rect>
					<line x1="0" y1="0" x2="0" y2="6" stroke="${o}" stroke-width="1"></line>
				</pattern>
			`,e+=`
			.gantt .bar-wrapper.bar-actual .bar {
				fill: url(#diagonalHatch) !important;
				stroke: #333 !important;
				stroke-width: 1px;
				height: 16px !important;
				y: 10px !important;
			}
			`;let l=frappe.ui.color.get_contrast_color(o);e+=`
			.gantt .bar-wrapper.${s} .bar-progress {
				fill: ${l};
			}
			`}),e+=`
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
		`;let t=`
		<svg width="0" height="0" style="position:absolute">
			<defs>${i}</defs>
			</svg>
			<style>${e}</style>
		`;this.$result.prepend(t)}get_item(r){return this.data.find(i=>i.name===r)}get required_libs(){return["assets/frappe/node_modules/frappe-gantt/dist/frappe-gantt.css","assets/frappe/node_modules/frappe-gantt/dist/frappe-gantt.min.js"]}};})();
//# sourceMappingURL=harro.bundle.J2NJNXTD.js.map
