import frappe
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

  # Global Perms
  for dt_condn in frappe.get_all("Event DocType Condition", {"dt": doc.doctype}):
    dt_condn = frappe.get_doc("Event DocType Condition")
    for condition in dt_condn.conditions:
      if not event_condition_satisfied(doc, consumer, condition):
        return False

  # Consumer Level Perms
  if consumer.get("conditions") and len(consumer.conditions):
    for condition in consumer.conditions:
      if not event_condition_satisfied(doc, consumer, condition):
        return False

  if is_consumer_uptodate(update_log, consumer):
    frappe.enqueue(mark_consumer_read, update_log_name=doc.name,
                   consumer_name=consumer.name, enqueue_after_commit=True)
  else:
    # we notify
    frappe.enqueue()
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
    return doc[condition.fieldname] == condition.value
  elif condition.type == "Eval Condition":
    return True


def get_consumer(user):
  """
  This function will get the EventConsumer associated with the user
  :param user: The user 
  """
  api_key = frappe.db.get_value(
      doctype="User",
      filters={"name": user},
      fieldname=["api_key"]
  )
  if not api_key:
    return None

  consumer = frappe.db.get_value(
      doctype="Event Consumer",
      filters={"api_key": api_key}
  )
  if not consumer:
    return None

  return frappe.get_doc("Event Consumer", consumer)


def mark_consumer_read(update_log_name, consumer_name):
  """
  This function appends the Consumer to the list of Consumers that has 'read' an Update Log

  :param update_log_name: The name of the update_log document
  :param consumer_name: The name of the Consumer doc
  """
  update_log = frappe.get_doc("Event Update Log", update_log)
  if len([x for x in update_log.consumers if x.consumer == consumer_name]):
    return

  update_log.append("consumers", {"consumer": consumer_name})
  update_log.save(ignore_permissions=True)


def is_consumer_uptodate(update_log, consumer):
  """
  Checks if Consumer has read all the UpdateLogs before the specified update_log

  :param update_log: The UpdateLog Doc in context
  :param consumer: The EventConsumer doc
  """
  if update_log.update_type == "Create":
    # consumer is obviously up to date then :P
    return True

  prev_logs = frappe.get_all(
      "Event Update Log",
      fields=["name", "ref_doctype", "docname"],
      filters={
          "ref_doctype": update_log.ref_doctype,
          "docname": update_log.docname,
          "name": ["!=", update_log.name]
      }
  )

  for prev_log in prev_logs:
    prev_log_consumers = [
        x.consumer
        for x in frappe.get_all(
            "Event Consumer Selector",
            fields=["consumer"],
            filters={
                "parent": prev_log.name,
                "parenttype": "Event Update Log"
            }
        )
    ]

    if consumer.name not in prev_log_consumers:
      return False

  return True


def notify_consumer(consumer_name, dt, dn):
  """
  Notify the consumer of all the earlier Update Logs

  :param consumer_name: The name of the consumer
  :param dt: The doctype in context
  :param dn: The docname in context
  """

  consumer = frappe.get_doc("Event Consumer", consumer_name)

  # We have to fetch all the update logs that this particular Consumer didnt consume yet.
  already_consumed = frappe.db.sql("""
    SELECT
      update_log.name
    FROM `tabEvent Update Log` update_log
    JOIN `tabEvent Consumer Selector` consumer ON consumer.parent = update_log.name
    WHERE
      consumer.consumer = %(consumer)s
  """, {"consumer": consumer_name}, as_dict=0)

  logs = frappe.get_all(
      "Event Update Log",
      fields=['update_type', 'ref_doctype',
              'docname', 'data', 'name', 'creation'],
      filters={
          "ref_doctype": dt,
          "docname": dn,
          "name": ["not in", already_consumed]
      },
      order_by="creation"
  )

  from frappe.event_streaming.doctype.event_consumer.event_consumer import get_consumer_site
  consumer_site = get_consumer_site(consumer.callback_url)

  try:
    client.post_request({
        'cmd': 'frappe_renovation_docsync.utils.update_logs.consume_update_logs',
        'producer_url': get_url(),
        'update_logs': logs
    })

    for l in logs:
      frappe.enqueue(mark_consumer_read, update_log_name=l.name,
                     consumer_name=consumer_name, enqueue_after_commit=True)
  except Exception as e:
    frappe.log_error(title="Consume Update Logs",
                     message=f"{e}\n\n{frappe.get_traceback()}")
    return False

  return True


def consume_update_logs(producer_url, update_logs):
  """
  This function is executed on the Consumer.
  The update_logs passed as param will have old Update Logs that is yet to be processed.

  This function is heavily similar to event_producer.pull_from_node

  :param producer_url: The url of the Producer Site
  :param update_logs: Array of UpdateLogs
  """
  if isinstance(update_logs, string_types):
    updates = frappe.parse_json(update_logs)

  from frappe.event_streaming.doctype.event_producer.event_producer import get_producer_site, get_config, sync

  event_producer = frappe.get_doc('Event Producer', producer_url)
  producer_site = get_producer_site(event_producer.producer_url)
  last_update = event_producer.last_update

  (doctypes, mapping_config, naming_config) = get_config(
      event_producer.producer_doctypes)

  for update in updates:
    update.use_same_name = naming_config.get(update.ref_doctype)
    mapping = mapping_config.get(update.ref_doctype)
    if mapping:
      update.mapping = mapping
      update = get_mapped_update(update, producer_site)
    if not update.update_type == 'Delete':
      update.data = json.loads(update.data)

    sync(update, producer_site, event_producer)
  
  # sync calls event_producer.reload()
  if event_producer.last_update < last_update:
    frappe.db.set_value('Event Producer', event_producer.name, 'last_update', last_update)
    frappe.db.commit()
  
  return True