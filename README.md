## Frappe Renovation Docsync

Extensions for Frappe Event Streams

This app extends the Frappe V13 EventStreaming module with the following functions:
- Conditional Events  
  Restrict syncing of documents. This is done via ControllerPermission Hook `has_permission`.
  The permission to `read` the document for a consumer is withheld until all the conditions satisfy.

  But this means that, we have to manually push old `Update Logs` when conditions satisfy at some point in the future.

  - Consumer Specific Conditions
    We add a Child table in EventProducer & EventConsumer called `Event Condition`
    ```js
    {
      type: fieldname | py-eval
      // type: fieldname
      fieldname: "",
      operator: "",
      value: ""
      // type: py-eval
      condition: ""
    }
    ```

  - DocType Level Condition
    A global doctype `Event DocType Condition`
    ```js
    {
      dt:
      conditions: EventCondition[]
    }
    ```
- Ignore fields

#### License

MIT