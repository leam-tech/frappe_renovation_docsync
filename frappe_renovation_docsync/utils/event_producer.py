import frappe
from frappe.utils.data import get_url

def get_request_data(doc):
  """
  This function is actually defined in
    frappe.event_streaming.doctype.event_producer.event_producer.EventProducer.get_request_data
  
  We are patching the function so that we can send the `conditions` array while creating the `Consumer` on Producer site.
  """
  consumer_doctypes = []
  for entry in doc.producer_doctypes:
    if entry.has_mapping:
      # if mapping, subscribe to remote doctype on consumer's site
      consumer_doctypes.append(frappe.db.get_value('Document Type Mapping', entry.mapping, 'remote_doctype'))
    else:
      consumer_doctypes.append(entry.ref_doctype)

  conditions = [
    frappe._dict(
      type=x.type,
      fieldname=x.fieldname,
      operator=x.operator,
      value=x.value,
      condition=x.condition
    )
    for x in doc.get("conditions", [])
  ]

  return {
    'event_consumer': get_url(),
    'consumer_doctypes': frappe.as_json(consumer_doctypes),
    'conditions': frappe.as_json(conditions),
    'user': doc.user,
    'in_test': frappe.flags.in_test
  }