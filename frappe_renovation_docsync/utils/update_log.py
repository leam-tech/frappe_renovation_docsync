import frappe

def consumer_perm_check(doc, ptype, user):
  consumer = get_consumer(user=user)

  # Global Perms
  for dt_condn in frappe.get_all("Event DocType Condition", {"dt": doc.doctype}):
    dt_condn = frappe.get_doc("Event DocType Condition")
    for condition in dt_condn.conditions:
      if not condition_satisfied(doc, consumer, condition):
        return False

  # Consumer Level Perms
  if consumer.get("conditions") and len(consumer.conditions):
    for condition in consumer.conditions:
      if not condition_satisfied(doc, consumer, condition):
        return False

  return True

def condition_satisfied(doc, consumer, condition):
  if condition.type == "DocField Value":
    return doc[condition.fieldname] == condition.value
  elif condition.type == "Eval Condition":
    return True

def get_consumer(user):
  api_key = frappe.db.get_value(
		doctype="User",
		filters={"name": user},
		fieldname=["api_key"]
	)

  consumer = frappe.db.get_value(
    doctype="Event Consumer",
    filters={"api_key": api_key}
  )

  return frappe.get_doc("Event Consumer", consumer)