# -*- coding: utf-8 -*-
from __future__ import unicode_literals

__version__ = '0.0.1'

# Patches
import frappe.event_streaming.doctype.event_producer.event_producer
from frappe.event_streaming.doctype.event_producer.event_producer import EventProducer
from frappe_renovation_docsync.utils.event_producer import get_request_data as _get_request_data, \
  update_event_consumer as _update_event_consumer, get_updates as _get_updates
EventProducer.get_request_data = _get_request_data
EventProducer.update_event_consumer = _update_event_consumer
frappe.event_streaming.doctype.event_producer.event_producer.get_updates = _get_updates