import frappe

def on_trash(doc, method):
  delete_event_consumer_selectors(doc.name)

def delete_event_consumer_selectors(event_consumer):
  for i in frappe.get_all("Event Consumer Selector", {"consumer": event_consumer}):
    frappe.delete_doc("Event Consumer Selector", i.name)