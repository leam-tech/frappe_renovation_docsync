import frappe, json
from six import string_types
from frappe.utils.data import get_url


def consumer_perm_check(doc, ptype, user):
  """
  This function is specified in the has_permission hook for `Event Update Log`
  If the current user is not linked to a consumer, we return  True.

  UpdateLog.consumers is updated if we give perm

  :param doc: The EventUpdateLog doc
  :param ptype: Permission type; read, write etc.
  :param user: The user against which permission is checked
  """
  consumer = get_consumer(user=user)
  if not consumer:
    return True

  ref_doc = frappe.get_doc(doc.ref_doctype, doc.docname)

  # Global Perms
  for dt_condn in frappe.get_all("Event DocType Condition", {"dt": doc.doctype}):
    dt_condn = frappe.get_doc("Event DocType Condition")
    for condition in dt_condn.conditions:
      if not event_condition_satisfied(ref_doc, consumer, condition):
        return False

  # Consumer Level Perms
  if consumer.get("conditions") and len(consumer.conditions):
    for condition in consumer.conditions:
      if not event_condition_satisfied(ref_doc, consumer, condition):
        return False

  return True


def event_condition_satisfied(doc, consumer, condition):
  """
  This functions evaluates the `Event Condition` and returns if it passes

  :param doc: the Document object in sync
  :param consumer: The Consumer doc object to which the doc will be synced to
  :condition: The `EventCondition` doc object
  """
  if condition.type == "DocField Value":
    return str(doc.get(condition.fieldname, "")) == condition.value
  elif condition.type == "Eval Condition":
    return True


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
