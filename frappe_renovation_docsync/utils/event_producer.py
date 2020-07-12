import frappe
from six import string_types
from frappe.utils.data import get_url
from frappe.event_streaming.doctype.event_producer.event_producer import get_approval_status, get_producer_site


def get_request_data(doc):
  """
  This function is called when Consumer site is making `EventConsumer` on producer site.
  This function is actually defined in
    frappe.event_streaming.doctype.event_producer.event_producer.EventProducer.get_request_data

  We are patching the function so that we can send the `conditions` array while creating the `Consumer` on Producer site.
  """
  consumer_doctypes = []
  for entry in doc.producer_doctypes:
    if entry.has_mapping:
      # if mapping, subscribe to remote doctype on consumer's site
      consumer_doctypes.append(frappe.db.get_value(
          'Document Type Mapping', entry.mapping, 'remote_doctype'))
    else:
      consumer_doctypes.append(entry.ref_doctype)

  conditions = [
      frappe._dict(
          dt=x.dt,
          type=x.type,
          fieldname=x.fieldname,
          operator=x.operator,
          value=x.value,
          eval=x.eval
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
            'status': get_approval_status(config, ref_doctype)
        })
      if frappe.flags.in_test:
        event_consumer.in_test = True

      event_consumer.conditions = [
          frappe._dict(
              dt=x.dt,
              type=x.type,
              fieldname=x.fieldname,
              operator=x.operator,
              value=x.value,
              eval=x.eval
          )
          for x in self.get("conditions", [])
      ]

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
  from frappe_renovation_docsync.utils import is_consumer_uptodate, mark_consumer_read, notify_consumer_of_history

  if isinstance(doctypes, string_types):
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

  to_history_sync = []
  result = []
  for d in docs:
    if (d.ref_doctype, d.docname) in to_history_sync:
      # will be notified by background jobs
      continue
    if not frappe.has_permission(frappe.get_doc("Event Update Log", d.name)):
      continue

    if is_consumer_uptodate(update_log=d, consumer=consumer):
      frappe.enqueue(mark_consumer_read, update_log_name=d.name,
                     consumer_name=consumer.name, enqueue_after_commit=True)
      result.append(d)
    else:
      to_history_sync.append((d.ref_doctype, d.docname))
      frappe.enqueue(notify_consumer_of_history, consumer_name=consumer.name,
                     dt=d.ref_doctype, dn=d.docname, enqueue_after_commit=True)

  return result
