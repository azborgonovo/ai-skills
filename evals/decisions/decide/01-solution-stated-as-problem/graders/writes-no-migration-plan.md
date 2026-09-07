---
type: regex
target: last_message
pattern: '\b(?:migration|cutover|rollout)\s+plan\b|(?:^|\n)[#*_\s]*(?:Phase|Step|Stage)\s*\d'
flags: im
match: not_contains
---
