import json
import frappe
from frappe.event_streaming.doctype.event_consumer.event_consumer import get_last_update

@frappe.whitelist(allow_guest=True)
def register_consumer(data):
  """
  This function overwrites the frappe function at:
    frappe.event_streaming.doctype.event_consumer.event_consumer.register_consumer
  We have to override so that we can save the incoming `conditions` array

  create an event consumer document for registering a consumer
  """
  data = json.loads(data)
  # to ensure that consumer is created only once
  if frappe.db.exists('Event Consumer', data['event_consumer']):
    return None
  consumer = frappe.new_doc('Event Consumer')
  consumer.callback_url = data['event_consumer']
  consumer.user = data['user']
  consumer.incoming_change = True
  consumer_doctypes = json.loads(data['consumer_doctypes'])

  for entry in consumer_doctypes:
    consumer.append('consumer_doctypes', {
      'ref_doctype': entry.ref_doctype,
      'status': 'Pending',
      'condition': entry.condition
    })

  api_key = frappe.generate_hash(length=10)
  api_secret = frappe.generate_hash(length=10)
  consumer.api_key = api_key
  consumer.api_secret = api_secret
  consumer.in_test = data['in_test']
  consumer.insert(ignore_permissions=True)
  frappe.db.commit()

  # consumer's 'last_update' field should point to the latest update
  # in producer's update log when subscribing
  # so that, updates after subscribing are consumed and not the old ones.
  last_update = str(get_last_update())
  return json.dumps({'api_key': api_key, 'api_secret': api_secret, 'last_update': last_update})
