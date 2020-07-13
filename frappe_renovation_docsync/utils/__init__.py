import frappe
import json
from frappe.utils.data import get_url
from six import string_types


def mark_consumer_read(update_log_name, consumer_name):
  """
  This function appends the Consumer to the list of Consumers that has 'read' an Update Log

  :param update_log_name: The name of the update_log document
  :param consumer_name: The name of the Consumer doc
  """
  update_log = frappe.get_doc("Event Update Log", update_log_name)
  if len([x for x in update_log.consumers if x.consumer == consumer_name]):
    return

  frappe.get_doc(frappe._dict(
      doctype="Event Consumer Selector",
      consumer=consumer_name,
      parent=update_log_name,
      parenttype="Event Update Log",
      parentfield="consumers"
  )).insert(ignore_permissions=True)


def is_consumer_uptodate(update_log, consumer):
  """
  Checks if Consumer has read all the UpdateLogs before the specified update_log

  :param update_log: The UpdateLog Doc in context
  :param consumer: The EventConsumer doc
  """
  if update_log.update_type == 'Create':
    # consumer is obviously up to date
    return True

  prev_logs = frappe.get_all(
    'Event Update Log',
    filters={
      'ref_doctype': update_log.ref_doctype,
      'docname': update_log.docname,
      'creation': ['<', update_log.creation]
    },
    order_by='creation desc',
    limit_page_length=1
  )

  if not len(prev_logs):
    return False

  prev_log_consumers = frappe.get_all(
    'Event Consumer Selector',
    fields=['consumer'],
    filters={
        'parent': prev_logs[0].name,
        'parenttype': 'Event Update Log',
        'consumer': consumer.name
    }
  )

  return len(prev_log_consumers) > 0