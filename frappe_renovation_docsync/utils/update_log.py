import frappe, json
from six import string_types
from frappe.utils.data import get_url, flt, get_datetime


def consumer_perm_check(doc, ptype, user):
  """
  This function is specified in the has_permission hook for `Event Update Log`
  If the current user is not linked to a consumer, we return  True.

  UpdateLog.consumers is updated if we give perm

  :param doc: The EventUpdateLog doc
  :param ptype: Permission type; read, write etc.
  :param user: The user against which permission is checked
  """
  consumer = get_consumer(user)
  update_log = doc

  def event_condition_satisfied(doc, consumer, condition):
    import operator
    from frappe.model import numeric_fieldtypes
    try:
      if condition.type == 'DocField':
        """==, !=, >, >=, <, <="""
        op_map = {
          '==': operator.eq,
          '!=': operator.ne,
          '>': operator.gt,
          '>=': operator.ge,
          '<': operator.lt,
          '<=': operator.le
        }
        df = doc.meta.get_field(condition.fieldname)
        if df.fieldtype in numeric_fieldtypes:
          condition.value = flt(condition.value)
        elif df.fieldtype in ('Date', 'Datetime'):
          condition.value = get_datetime(condition.value)

        return op_map[condition.operator](doc.get(df.fieldname), condition.value)
      elif condition.type == 'Eval':
        return frappe.safe_eval(condition.eval, frappe._dict(doc=doc))
    except Exception:
      pass
    return False

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

    last_update_log = frappe.get_doc("Event Update Log", last_update_log[0].name)
    return len([x for x in last_update_log.consumers if x.consumer == consumer.name])

  doc = frappe.get_doc(update_log.ref_doctype, update_log.docname)

  # Global Perms
  for dt_condn in frappe.get_all('Event DocType Condition', {'dt': doc.doctype}):
    dt_condn = frappe.get_doc('Event DocType Condition', dt_condn.name)
    for condition in dt_condn.conditions:
      if not event_condition_satisfied(doc, consumer, condition):
        return False

  if isinstance(consumer, str):
    consumer = frappe.get_doc('Event Consumer', consumer)

  # Consumer Level Perms
  if consumer.get('conditions') and len(consumer.conditions):
    for condition in consumer.conditions:
      if condition.dt != doc.doctype:
        continue
      if not event_condition_satisfied(doc, consumer, condition):
        return False

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
