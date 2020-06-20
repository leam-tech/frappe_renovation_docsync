# Frappe Renovation Docsync

This app is an extension for `Frappe Event Streaming` module.   
This README is split into
- [Customizations](#Customizations)
- [Concerns](#Concerns)

## Customizations
This app extends the Frappe V13 EventStreaming module with the following functions:
- Conditional Events  
  Restrict syncing of documents. This is done via ControllerPermission Hook `has_permission`.
  The permission to `read` the document for a consumer is withheld until all the conditions satisfy.

  But this means that, we have to manually push old `Update Logs` when conditions satisfy at some point in the future.
  Now, how do we know when to push old update logs ?
  We add a child Table MultiSelect listing all the Consumers to which a particular Update Log was read by.

  - Consumer Specific Conditions
    We add a Child table in EventProducer & EventConsumer called `Event Condition`
    ```js
    {
      dt: "Link/DocType",
      type: "fieldname | py-eval",
      // type: fieldname
      fieldname: "",
      operator: "",
      value: "",
      // type: py-eval
      condition: ""
    }
    ```

  - DocType Level Condition
    A global doctype `Event DocType Condition`
    ```js
    {
      dt: ""
      conditions: EventCondition[]
    }
    ```

- Ignore fields

## Concerns
### `has_permission` has no effect on get_list
`Conditional Events` feature is implemented by restricting read-access to `Event Update Log` via `has_permission` hook. The issue is that this hook is run only when `frappe.get_doc` is called, and ignore on `frappe.get_list`. In order to workaround this, `frappe.event_producer.get_updates` had to be updated
[a link](https://github.com/leam-tech/frappe_renovation_docsync/blob/master/frappe_renovation_docsync/utils/update_log.py#L33)

## License

MIT