import frappe
from six import string_types
from frappe.utils.data import get_url
from six import iteritems
from frappe.event_streaming.doctype.event_producer.event_producer import get_approval_status, get_producer_site


def update_row_changed(local_doc, changed):
  """Sync child table row updation type update"""
  for tablename, rows in iteritems(changed):
    old = local_doc.get(tablename)
    if not old:
      continue
    for doc in old:
      for row in rows:
        if row['name'] == doc.get('name'):
          doc.update(row)


def get_request_data(doc):
  """
  This function is called when Consumer site is making `EventConsumer` on producer site.
  This function is actually defined in
    frappe.event_streaming.doctype.event_producer.event_producer.EventProducer.get_request_data

  We are patching the function so that we can send the `condition` field while creating the `Consumer` on Producer site.
  """
  consumer_doctypes = []
  for entry in doc.producer_doctypes:
    if entry.has_mapping:
      # if mapping, subscribe to remote doctype on consumer's site
      consumer_doctypes.append({"ref_doctype": frappe.db.get_value(
          'Document Type Mapping', entry.mapping, 'remote_doctype'), "condition": entry.condition})
    else:
      consumer_doctypes.append(
          {"ref_doctype": entry.ref_doctype, "condition": entry.condition})

  return {
      'event_consumer': get_url(),
      'consumer_doctypes': frappe.as_json(consumer_doctypes),
      'user': doc.user,
      'in_test': frappe.flags.in_test
  }


def update_event_consumer(self):
  """
  This function is called when Consumer wants to update the `EventConsumer` doc on Producer
  This overrides the frappe function:
    frappe.event_streaming.doctype.event_producer.event_producer.EventProducer.update_event_consumer

  We are patching this function to update the Conditions along with the new doctypes
  """
  if self.is_producer_online():
    producer_site = get_producer_site(self.producer_url)
    event_consumer = producer_site.get_doc('Event Consumer', get_url())
    event_consumer = frappe._dict(event_consumer)
    if event_consumer:
      config = event_consumer.consumer_doctypes
      event_consumer.consumer_doctypes = []
      for entry in self.producer_doctypes:
        if entry.has_mapping:
          # if mapping, subscribe to remote doctype on consumer's site
          ref_doctype = frappe.db.get_value(
              'Document Type Mapping', entry.mapping, 'remote_doctype')
        else:
          ref_doctype = entry.ref_doctype

        event_consumer.consumer_doctypes.append({
            'ref_doctype': ref_doctype,
            'condition': entry.condition,
            'status': get_approval_status(config, ref_doctype)
        })
      if frappe.flags.in_test:
        event_consumer.in_test = True

      event_consumer.user = self.user
      event_consumer.incoming_change = True
      producer_site.update(event_consumer)


def get_updates(producer_site, last_update, doctypes):
  """Get all updates generated after the last update timestamp"""
  docs = producer_site.post_request({
      'cmd': 'frappe_renovation_docsync.utils.event_producer.get_producer_updates',
      'event_consumer': get_url(),
      'doctypes': frappe.as_json(doctypes),
      'last_update': last_update
  })

  return [frappe._dict(d) for d in docs]


def get_unread_update_logs(consumer_name, dt, dn):
  """
  Get old logs unread by the consumer on a particular document
  """
  already_consumed = [x[0] for x in frappe.db.sql("""
    SELECT
      update_log.name
    FROM `tabEvent Update Log` update_log
    JOIN `tabEvent Consumer Selector` consumer ON consumer.parent = update_log.name
    WHERE
      consumer.consumer = %(consumer)s
  """, {"consumer": consumer_name}, as_dict=0)]

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

  return logs


@frappe.whitelist()
def get_producer_updates(event_consumer, doctypes, last_update):
  """
  This function is invoked by the Consumer on the Producer site.
  It returns filtered EventUpdateLogs.
  This also handles notifying Consumer of all the past History if the Consumer is not upto date on a particular Update Log

  :param event_consumer: The Name/Url of the Consumer
  :param doctypes: List of doctypes to stream
  :param last_update: the date
  """
  from frappe_renovation_docsync.utils.update_log import has_consumer_access
  from frappe_renovation_docsync.utils import is_consumer_uptodate, mark_consumer_read

  if isinstance(doctypes, str):
    doctypes = frappe.parse_json(doctypes)

  consumer = frappe.get_doc("Event Consumer", event_consumer)
  docs = frappe.get_list(
      doctype='Event Update Log',
      filters={'ref_doctype': ('in', doctypes),
               'creation': ('>', last_update)},
      fields=['update_type', 'ref_doctype',
              'docname', 'data', 'name', 'creation'],
      order_by='creation desc'
  )

  result = []
  to_update_history = []
  for d in docs:
    if (d.ref_doctype, d.docname) in to_update_history:
      continue

    if not has_consumer_access(consumer=consumer, update_log=d):
      continue

    if not is_consumer_uptodate(d, consumer):
      to_update_history.append((d.ref_doctype, d.docname))
      # get_unread_update_logs will have the current log
      old_logs = get_unread_update_logs(
          consumer.name, d.ref_doctype, d.docname)
      old_logs.reverse()
      result.extend(old_logs)
    else:
      result.append(d)

  for d in result:
    mark_consumer_read(update_log_name=d.name, consumer_name=consumer.name)

  result.reverse()

  return result
