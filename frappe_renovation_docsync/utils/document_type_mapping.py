import frappe
import json
from six import iteritems
from frappe.event_streaming.doctype.document_type_mapping.document_type_mapping import get_mapped_child_table_docs

def get_mapping(self, doc, producer_site, update_type):

  remote_fields = []
  # list of tuples (local_fieldname, dependent_doc)
  dependencies = []

  for mapping in self.field_mapping:
    if doc.get(mapping.remote_fieldname):
      if mapping.mapping_type == 'Document':
        if not mapping.default_value:
          dependency = self.get_mapped_dependency(mapping, producer_site, doc)
          if dependency:
            dependencies.append((mapping.local_fieldname, dependency))
        else:
          doc[mapping.local_fieldname] = mapping.default_value

      if mapping.mapping_type == 'Child Table' and update_type != 'Update':
        doc[mapping.local_fieldname] = get_mapped_child_table_docs(
            mapping.mapping, doc[mapping.remote_fieldname], producer_site)
      else:
        # copy value into local fieldname key and remove remote fieldname key
        doc[mapping.local_fieldname] = doc[mapping.remote_fieldname]

      if mapping.local_fieldname != mapping.remote_fieldname:
        remote_fields.append(mapping.remote_fieldname)

    if not doc.get(mapping.remote_fieldname) and mapping.default_value and update_type != 'Update':
      doc[mapping.local_fieldname] = mapping.default_value

  # remove the remote fieldnames
  for field in remote_fields:
    doc.pop(field, None)

  if update_type != 'Update':
    doc['doctype'] = self.local_doctype

  """
  EDIT START
  When table fields come in that do not exist on local doctype even after mapping,
  We will have to hard remove it
  """

  from frappe.model import default_fields
  valid_fields = tuple([x.fieldname for x in frappe.get_meta(
      self.local_doctype).fields]) + default_fields
  for k in list(doc.keys()):
    if k not in valid_fields:
      del doc[k]
  """
  CHANGE
  """

  mapping = {'doc': frappe.as_json(doc)}
  if len(dependencies):
    mapping['dependencies'] = dependencies
  return mapping


def get_mapped_dependency(self, mapping, producer_site, doc):
  inner_mapping = frappe.get_doc('Document Type Mapping', mapping.mapping)

  """EDIT"""
  if inner_mapping.remote_doctype == "DocType":
    # Lets not sync DocTypes under no conditions
    # Assume doctype as it is present in the local site
    return
  """EDIT"""

  filters = json.loads(mapping.remote_value_filters)
  for key, value in iteritems(filters):
    if value.startswith('eval:'):
      val = frappe.safe_eval(value[5:], dict(frappe=frappe))
      filters[key] = val
    if doc.get(value):
      filters[key] = doc.get(value)
  matching_docs = producer_site.get_doc(
      inner_mapping.remote_doctype, filters=filters)
  if len(matching_docs):
    remote_docname = matching_docs[0].get('name')
    remote_doc = producer_site.get_doc(
        inner_mapping.remote_doctype, remote_docname)
    doc = inner_mapping.get_mapping(
        remote_doc, producer_site, 'Insert').get('doc')
    return doc
  return


def map_rows_removed(self, update_diff, mapping):
  removed = []
  mapping['removed'] = update_diff.removed
  for key, value in iteritems(update_diff.removed.copy()):
    local_table_name = frappe.db.get_value('Document Type Field Mapping', {
        'remote_fieldname': key,
        'parent': self.name
    }, 'local_fieldname')
    """EDIT"""
    if not local_table_name:
      continue
    """EDIT"""
    mapping.removed[local_table_name] = value
    if local_table_name != key:
      removed.append(key)

  # remove the remote fieldnames
  for field in removed:
    mapping.removed.pop(field, None)
  return mapping


def map_rows(self, update_diff, mapping, producer_site, operation):
  remote_fields = []
  for tablename, entries in iteritems(update_diff.get(operation).copy()):
    local_table_name = frappe.db.get_value('Document Type Field Mapping', {
                                           'remote_fieldname': tablename}, 'local_fieldname')
    """EDIT"""
    if not local_table_name:
      continue
    """EDIT"""
    table_map = frappe.db.get_value('Document Type Field Mapping', {
                                    'local_fieldname': local_table_name, 'parent': self.name}, 'mapping')
    table_map = frappe.get_doc('Document Type Mapping', table_map)
    docs = []
    for entry in entries:
      mapped_doc = table_map.get_mapping(
          entry, producer_site, 'Update').get('doc')
      docs.append(json.loads(mapped_doc))
    mapping.get(operation)[local_table_name] = docs
    if local_table_name != tablename:
      remote_fields.append(tablename)

  # remove the remote fieldnames
  for field in remote_fields:
    mapping.get(operation).pop(field, None)

  return mapping
