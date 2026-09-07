---
type: llm
focus: trace
---
Identifies the tracker as Jira from the atlassian.net/browse URL and drives it through the twg backend of the adapter (`twg jira workitem bulk-get` to fetch, `twg jira workitem comment create` to post), not the gh CLI.
