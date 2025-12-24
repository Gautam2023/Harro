frappe.pages['task-gantt-chart'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Task Gantt Chart',
		single_column: true
	});
	
	// Initialize the page
	new TaskGanttChart(page, wrapper);
}

class TaskGanttChart {
	constructor(page, wrapper) {
		this.page = page;
		this.wrapper = wrapper;
		this.tasks = [];
		this.filters = {};
		
		this.init();
	}

	init() {
		this.make_filters();
		this.make_chart_container();
		this.load_data();
	}

	make_filters() {
		let me = this;
		
		// Create filter fields
		this.filters.project = this.page.add_field({
			fieldtype: 'Link',
			label: 'Project',
			fieldname: 'project',
			options: 'Project',
			change: function() {
				me.load_data();
			}
		});
		
		this.filters.status = this.page.add_field({
			fieldtype: 'Select',
			label: 'Status',
			fieldname: 'status',
			options: '\nOpen\nWorking\nPending Review\nCompleted\nCancelled',
			change: function() {
				me.load_data();
			}
		});
		
		// Add refresh button
		this.page.add_inner_button(__('Refresh'), function() {
			me.load_data();
		}, '.page-actions');
	}

	make_chart_container() {
		this.chart_container = $('<div id="gantt-container" style="width: 100%; height: 700px; margin-top: 20px;"></div>');
		$(this.wrapper).append(this.chart_container);
	}

	load_data() {
		let me = this;
		
		frappe.call({
			method: 'frappe.client.get_list',
			args: {
				doctype: 'Task',
				filters: me.get_filters(),
				fields: [
					'name', 'subject', 'project', 'status', 'priority',
					'exp_start_date', 'exp_end_date', 
					'act_start_date', 'act_end_date',
					'progress', 'description', 'is_group'
				],
				order_by: 'exp_start_date asc'
			},
			callback: function(r) {
				if (r.message) {
					me.tasks = r.message;
					me.render_gantt_chart();
				}
			}
		});
	}

	get_filters() {
		let filters = {};
		
		if (this.filters.project.get_value()) {
			filters['project'] = this.filters.project.get_value();
		}
		
		if (this.filters.status.get_value()) {
			filters['status'] = this.filters.status.get_value();
		}
		
		return filters;
	}

	render_gantt_chart() {
		let me = this;
		
		// Clear previous chart
		if (this.ganttChart) {
			this.ganttChart.dispose();
		}
		
		// Prepare data tree
		let treeData = this.prepare_gantt_data();
		
		// Create Gantt chart
		anychart.onDocumentReady(function() {
			// Create data tree
			let tree = anychart.data.tree(treeData, 'as-table');
			
			// Create Gantt chart
			me.ganttChart = anychart.ganttProject();
			me.ganttChart.data(tree);
			
			// Configure timeline
			me.ganttChart.getTimeline().scale().maximum(Date.now() + 120 * 24 * 60 * 60 * 1000);
			
			// Configure chart
			me.configure_chart();
			
			// Draw chart
			me.ganttChart.container('gantt-container');
			me.ganttChart.draw();
			
			// Fit to content
			me.ganttChart.fitAll();
		});
	}

	prepare_gantt_data() {
		let data = [];
		
		this.tasks.forEach(task => {
			let taskData = {
				id: task.name,
				name: task.subject,
				progressValue: task.progress || 0,
				actualStart: task.act_start_date,
				actualEnd: task.act_end_date,
				baselineStart: task.exp_start_date,
				baselineEnd: task.exp_end_date,
				status: task.status,
				priority: task.priority,
				description: task.description
			};
			
			// Add timeline data with both expected and actual dates
			if (task.act_start_date && task.act_end_date) {
				taskData['actual'] = [
					{
						start: task.act_start_date,
						end: task.act_end_date,
						name: 'Actual'
					}
				];
			}
			
			if (task.exp_start_date && task.exp_end_date) {
				taskData['expected'] = [
					{
						start: task.exp_start_date,
						end: task.exp_end_date,
						name: 'Expected'
					}
				];
			}
			
			data.push(taskData);
		});
		
		return data;
	}

	configure_chart() {
		let me = this;
		
		// Configure data grid
		let dataGrid = this.ganttChart.dataGrid();
		dataGrid.column(0).width(50).setTitle('#');
		dataGrid.column(1).width(200).setTitle('Task Name');
		dataGrid.column(2).width(100).setTitle('Status');
		dataGrid.column(3).width(100).setTitle('Progress');
		
		// Configure timeline
		let timeline = this.ganttChart.getTimeline();
		
		// Configure scales
		let scale = timeline.scale();
		scale.minimum('2024-01-01');
		scale.maximum('2024-12-31');
		
		// Configure coloring based on status
		this.ganttChart.splitterPosition(350);
		
		// Customize appearance
		this.ganttChart.interactivity().selectionMode('multiple');
		
		// Add event listeners
		this.ganttChart.listen('pointClick', function(e) {
			let taskId = e.item.get('id');
			frappe.set_route('Form', 'Task', taskId);
		});
		
		// Configure coloring function for bars
		this.ganttChart.splitterPosition(350);
		
		// Custom palette for different status
		let customPalette = anychart.palettes.distinctColors();
		customPalette.items([
			{ color: '#4CAF50' },  // Green for Completed
			{ color: '#2196F3' },  // Blue for Working
			{ color: '#FF9800' },  // Orange for Pending Review
			{ color: '#F44336' },  // Red for Overdue
			{ color: '#9E9E9E' }   // Gray for Open
		]);
		
		this.ganttChart.palette(customPalette);
		
		// Configure tooltip
		this.ganttChart.tooltip().titleFormat(function() {
			return this.item.get('name');
		});
		
		this.ganttChart.tooltip().format(function() {
			let html = '<div style="padding: 5px">';
			html += '<b>Task:</b> ' + this.item.get('name') + '<br/>';
			html += '<b>Status:</b> ' + this.item.get('status') + '<br/>';
			
			if (this.item.get('actualStart')) {
				html += '<b>Actual Start:</b> ' + this.item.get('actualStart') + '<br/>';
			}
			if (this.item.get('actualEnd')) {
				html += '<b>Actual End:</b> ' + this.item.get('actualEnd') + '<br/>';
			}
			if (this.item.get('baselineStart')) {
				html += '<b>Expected Start:</b> ' + this.item.get('baselineStart') + '<br/>';
			}
			if (this.item.get('baselineEnd')) {
				html += '<b>Expected End:</b> ' + this.item.get('baselineEnd') + '<br/>';
			}
			
			html += '<b>Progress:</b> ' + (this.item.get('progressValue') || 0) + '%';
			html += '</div>';
			
			return html;
		});
	}
}