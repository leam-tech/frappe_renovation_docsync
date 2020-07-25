# -*- coding: utf-8 -*-
from __future__ import unicode_literals

__version__ = '0.0.1'

# Patches
import frappe.event_streaming.doctype.event_producer.event_producer
import frappe.event_streaming.doctype.event_update_log.event_update_log
from frappe.event_streaming.doctype.event_producer.event_producer import EventProducer
from frappe.event_streaming.doctype.document_type_mapping.document_type_mapping import DocumentTypeMapping
from frappe_renovation_docsync.utils.event_producer import get_request_data as _get_request_data, \
    update_event_consumer as _update_event_consumer, get_updates as _get_updates, update_row_changed as _update_row_changed
from frappe_renovation_docsync.utils.update_log import notify_consumers as _notify_consumers
from frappe_renovation_docsync.utils.document_type_mapping import get_mapped_dependency, get_mapping, map_rows, map_rows_removed

# To send our conditions while creating Event Consumer
EventProducer.get_request_data = _get_request_data

# To send our conditions while updating EventConsumer
EventProducer.update_event_consumer = _update_event_consumer

# To provide the EventUpdateLog filtered.
frappe.event_streaming.doctype.event_producer.event_producer.get_updates = _get_updates

# To notify just those Consumers who can read the update log
frappe.event_streaming.doctype.event_update_log.event_update_log.notify_consumers = _notify_consumers

# To prevent streaming DocType 'DocType'
DocumentTypeMapping.get_mapped_dependency = get_mapped_dependency

# Fix for incoming diffs with table fields that doesnt exist on local site
DocumentTypeMapping.get_mapping = get_mapping
DocumentTypeMapping.map_rows = map_rows
DocumentTypeMapping.map_rows_removed = map_rows_removed
frappe.event_streaming.doctype.event_producer.event_producer.update_row_changed = _update_row_changed