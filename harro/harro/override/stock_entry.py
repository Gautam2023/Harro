import frappe
from frappe import msgprint, _
from erpnext.stock.doctype.stock_entry.stock_entry import StockEntry


class CustomStockEntry(StockEntry):
	def submit(self):
		if len(self.items) > 100:
			msgprint(
				_(
					"The task has been enqueued as a background job. In case there is any issue on processing in background, the system will add a comment about the error on this Stock Entry and revert to the Draft stage"
				)
			)
			self.queue_action("submit", queue="long", timeout=4600)
		else:
			super().submit()
