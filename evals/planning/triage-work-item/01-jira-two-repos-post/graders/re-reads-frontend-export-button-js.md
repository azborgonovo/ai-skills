---
type: llm
focus: trace
---
Re-reads frontend/export-button.js itself and cites the real mechanism there: window.showSaveFilePicker is unavailable in Safari, and the catch written for the picker-cancel case swallows the resulting error, so the click does nothing and shows nothing.
