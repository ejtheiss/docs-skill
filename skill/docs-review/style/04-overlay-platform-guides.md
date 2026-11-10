<!-- Compiled from Notion by scripts/notion_sync.py. Do not edit; edit https://app.notion.com/p/3c8d6bfc26838075bcabe168ff4563d1
     policy 718466089eff · synced 2026-09-03T21:34:37+00:00 -->
`docs-readme-platform/docs`. Read with **01 — Base Style**; this page covers only what is specific to platform guides. It does **not** apply to `reference/**` in the same repo — see **05**.
Platform guides get someone through a setup task: dashboard configuration, permissions, users, integrations, reporting. They are the most procedural pages we write.
## **Voice**
### **Number the steps and open each with a verb — Strict**
One action per step. No step contains two actions joined by "and then".
> Navigate to **Settings**.<br>Select the user's role.<br>Save the change.
### **Address the reader as "you"; avoid "we" — Strict**
Platform tasks are the reader's work in their own organization's settings.
### **No contractions — Strict**
Write *do not*, *cannot*, *it is*. This is administrative documentation read by people with production access.
### **Say what the reader needs before they start — Strict**
Permissions, plan requirements and prerequisites go in a 📘 callout above step 1, never buried inside a step.
## **Formatting**
### **UI elements take their visible label, in bold — Strict**
*click **Reconcile***, *open the **Approvals** tab*, *enter the **Routing Number***. Use the exact on-screen label. Never quotes, never inline code, never a paraphrase.
### **Callouts carry prerequisites and limits — Flexible**
Platform guides use callouts more than any other project, and that is right: 📘 for prerequisites, 🚧 for plan limits and early access. Keep them short enough to read at a glance.
### **`sql`**** for queries, ****`shell`**** for requests — Strict**
Reporting and warehouse pages are the only place SQL appears. Tag it `sql`.
### **Guides stay within two levels — Strict**
`docs/<area>/<page>.md`. Platform guides are flat; a third level needs a discussion.
### **Spell out Modern Treasury — Strict**
Called out again because this is the project where `MT` shows up.
