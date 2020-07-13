import frappe
import json
from six import string_types
from frappe.utils.data import get_url, flt, get_datetime


def has_consumer_access(consumer, update_log):
  """Checks if consumer has completely satisfied all the conditions on the doc"""

  if isinstance(consumer, str):
    consumer = frappe.get_doc('Event Consumer', consumer)

  if not frappe.db.exists(update_log.ref_doctype, update_log.docname):
    # Delete Log
    # Check if the last Update Log of this document was read by this consumer
    last_update_log = frappe.get_all(
        'Event Update Log',
        filters={
            'ref_doctype': update_log.ref_doctype,
            'docname': update_log.docname,
            'creation': ['<', update_log.creation]
        },
        order_by="creation desc",
        limit_page_length=1
    )
    if not len(last_update_log):
      return False

    last_update_log = frappe.get_doc(
        "Event Update Log", last_update_log[0].name)
    return len([x for x in last_update_log.consumers if x.consumer == consumer.name])

  doc = frappe.get_doc(update_log.ref_doctype, update_log.docname)
  for dt_entry in consumer.consumer_doctypes:
    if dt_entry.ref_doctype != update_log.ref_doctype:
      continue

    if not dt_entry.condition:
      return True

    condition: str = dt_entry.condition
    if condition.startswith("cmd:"):
      return frappe.call(frappe.get_attr(condition.split("cmd:")[1].strip()), consumer=consumer, update_log=update_log)
    else:
      return frappe.safe_eval(condition.eval, frappe._dict(doc=doc))

  return False


def get_consumer(user):
  """
  This function will get the EventConsumer associated with the user
  :param user: The user 
  """
  consumer = frappe.db.get_value(
      doctype="Event Consumer",
      filters={"user": user}
  )
  if not consumer:
    return None

  return frappe.get_doc("Event Consumer", consumer)
