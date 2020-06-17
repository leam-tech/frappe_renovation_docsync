# -*- coding: utf-8 -*-
from __future__ import unicode_literals

__version__ = '0.0.1'

# Patches
from frappe_renovation_docsync.utils.event_producer import get_request_data as _get_request_data
from frappe.event_streaming.doctype.event_producer.event_producer import EventProducer
EventProducer.get_request_data = _get_request_data