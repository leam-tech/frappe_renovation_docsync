# -*- coding: utf-8 -*-
from __future__ import unicode_literals

__version__ = '0.0.1'

# Patches
import frappe.event_streaming.doctype.event_producer.event_producer
from frappe.event_streaming.doctype.event_producer.event_producer import EventProducer
from frappe_renovation_docsync.utils.event_producer import get_request_data as _get_request_data, \
    update_event_consumer as _update_event_consumer, get_updates as _get_updates

from frappe_renovation_docsync.utils.update_log import notify_consumers as _notify_consumers
import frappe.event_streaming.doctype.event_update_log.event_update_log

# To send our conditions while creating Event Consumer
EventProducer.get_request_data = _get_request_data

# To send our conditions while updating EventConsumer
EventProducer.update_event_consumer = _update_event_consumer

# To provide the EventUpdateLog filtered.
frappe.event_streaming.doctype.event_producer.event_producer.get_updates = _get_updates

# To notify just those Consumers who can read the update log
frappe.event_streaming.doctype.event_update_log.event_update_log.notify_consumers = _notify_consumers
