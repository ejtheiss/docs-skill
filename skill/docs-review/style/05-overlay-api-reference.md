`docs-readme-platform/reference`. Read with **01 — Base Style**; this page covers only what is specific to the API reference.
Reference pages define objects, fields and behavior. They do not teach workflows — guides do that. These pages track the OpenAPI specification, so a wording fix belongs at the source of truth (`platform/swagger/v1/swagger.yaml` in the monorepo) or it will be overwritten.
## **Voice**
### **Describe, do not instruct — Strict**
No procedures, no tutorials, no "let's", no "we". When the reader needs a workflow, link the guide.
> The ID of one of the lines in the statement. `nil` if the statement is not itemized.
### **One sentence per field where possible — Strict**
A field description says what the field is and its constraint. Nothing else.
**Don't**
> This field is used to store the identifier of the ledger account that you want to associate with this transaction, and it is required whenever you are creating entries.
**Do**
> The ID of the Ledger Account this entry posts to. Required.
### **Capitalize the object, inline-code the field — Strict**
The concept is a Ledger Account; the field is `ledger_account_id`. They are never written the same way.
## **Structure**
### **No numbered lists — Strict**
Reference pages use bullets. A numbered list means the content belongs in a guide.
### **`json`**** is the fence language — Strict**
Show request and response bodies as `json` and leave language-specific request examples to ReadMe's generated snippets. Do not add `shell` or `curl` blocks to reference pages.
### **Headings name the object and its operations — Strict**
The page opens with the object name, and section headings follow the established pattern: `Working with X`, `Initiating X`, `X Object`.
### **No ****`excerpt`**** — Flexible**
Base style applies here unchanged: reference pages carry no excerpt either. Delete the one you find on a page you are editing — ReadMe builds the search snippet from the page body. Flexible for the same reason as base style: removal is cleanup, not a condition a page must meet to ship.
### Project shorthand within API reference — Strict (`link-absolute-internal`, reported flexible)
Use `ref:slug` within reference. Use absolute `https://docs.moderntreasury.com` URLs across projects, including links to platform guides, Ledgers and Payments. Generated endpoint pages change through `reference/modern-treasury-api.json`, not direct Markdown edits; coordinate upstream spec changes with the monorepo source of truth.
