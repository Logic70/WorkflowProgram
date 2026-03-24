---
name: core-review-pipeline
description: Internal building block for multi-lane review orchestration.
version: 1.0.0
internal: true
---

# Core Review Pipeline

Internal reusable guidance for commands that need fan-out review and fan-in
aggregation.

## Responsibilities

- define the standard four review lanes
- enforce shared severity ordering
- normalize JSON Lines output
- keep command-level review orchestration consistent
