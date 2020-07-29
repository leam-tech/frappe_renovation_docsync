import frappe
from frappe.utils import get_url

def before_insert(doc, method):
  update_file_urls(update_log=doc)


def update_file_urls(update_log):
  """
  Prepends all file urls with the Producer's URL
  :param update_log: The event update log that is being inserted
  """
  if update_log.update_type == "Delete":
    return

  meta = frappe.get_meta(update_log.ref_doctype)
  data = frappe.parse_json(update_log.data)
  if update_log.update_type == "Create":
    update_log.data = frappe.as_json(_update_file_url(update_log.ref_doctype, data))
  elif update_log.update_type == "Update":
    # changed
    data.changed = _update_file_url(doctype=update_log.ref_doctype, doc=data.changed)

    # row_changed
    for table_df, rows in data.row_changed.items():
      cdt = meta.get_field(table_df).options
      for r in rows:
        r.update(_update_file_url(doctype=cdt, doc=r))

    # added
    for table_df, rows in data.added.items():
      cdt = meta.get_field(table_df).options
      for r in rows:
        r.update(_update_file_url(doctype=cdt, doc=r))

    # removed
    # nothing to do

    update_log.data = frappe.as_json(data)


def _update_file_url(doctype, doc):
  file_df = [	'Attach',	'Attach Image']
  meta = frappe.get_meta(doctype)

  doc = frappe._dict(doc)
  for i, v in doc.items():
      if not meta.get_field(i):
        continue
      if meta.get_field(i).fieldtype in file_df:
        doc[i] = get_file_url(v)

  for table_df in meta.get_table_fields():
    if not table_df.fieldname in doc:
      continue
    
    if not isinstance(doc[table_df.fieldname], (list, tuple)):
      continue

    for cd in doc[table_df.fieldname]:
      cd.update(_update_file_url(table_df.options, cd))

  return doc

def get_file_url(v):
  if "http" not in v:
    return f"{get_url()}{v}"
  return v