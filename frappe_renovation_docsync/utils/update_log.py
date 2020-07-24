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

  doc = frappe.get_cached_doc(update_log.ref_doctype, update_log.docname)
  try:
    for dt_entry in consumer.consumer_doctypes:
      if dt_entry.ref_doctype != update_log.ref_doctype:
        continue

      if not dt_entry.condition:
        return True

      condition: str = dt_entry.condition
      if condition.startswith("cmd:"):
        cmd, args = get_cmd_and_args(condition)
        args["consumer"] = consumer
        args["update_log"] = update_log
        return frappe.call(cmd, **args)
      else:
        return frappe.safe_eval(condition, frappe._dict(doc=doc))
  except Exception as e:
    frappe.log_error(title="has_consumer_access error", message=e)
  return False


def get_cmd_and_args(condition):
  """
  cmd: ____________________
  args: {

  }
  """
  cmd = condition.split("cmd:")[1]
  args = frappe._dict()
  if "args:" in cmd:
    cmd = cmd.split("args:")
    args = cmd[1]
    cmd = cmd[0]
    try:
      print(args)
      args = frappe.parse_json(args)
    except:
      args = frappe._dict()

  if "\n" in cmd:
    cmd = cmd.split("\n")[0]

  cmd = cmd.strip()
  return cmd, args


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


def notify_consumers(doc, method):
  """
  Notify just those consumers who can actually consume the logs.
  :param doc: Event Update Log instance
  :param method: after_insert
  """

  # We have to enqueue_after_commit, otherwise the UpdateLog wont be in db anytime
  frappe.enqueue(notify_event_consumers,
                 update_log=doc.as_dict(), enqueue_after_commit=True)


def notify_event_consumers(update_log):
  """
  Notify those Consumers who has access to the update log
  """
  from frappe.event_streaming.doctype.event_consumer.event_consumer import notify
  event_consumers = frappe.get_all('Event Consumer Document Type', ['parent'], {
                                   'ref_doctype': update_log.ref_doctype, 'status': 'Approved'})
  for entry in event_consumers:
    consumer = frappe.get_doc('Event Consumer', entry.parent)
    if not has_consumer_access(consumer=consumer, update_log=update_log):
      continue
    consumer.flags.notified = False
    notify(consumer)
