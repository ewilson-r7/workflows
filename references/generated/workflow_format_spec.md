# InsightConnect `.icon` Workflow Format Spec (evidence-based)

Derived deterministically from **234** known-good, importable workflows in `insightconnect-workflows`. Percentages are how often a field/value appears across the corpus. Parse errors: 0.

> Regenerate: `python3 analyze_workflows.py && python3 build_catalogs.py`

## 1. Top level

Every file is a single top-level `kom` object. These keys appear in 100% of files:

| kom key | presence |
| --- | --- |
| komandVersion | 234 (100%) |
| komFileVersion | 234 (100%) |
| exportedAt | 234 (100%) |
| workflowVersions | 234 (100%) |
| triggers | 234 (100%) |


- `komFileVersion` is always `"2.0.0"`.
- `komandVersion` is the exporting platform build; it varies widely and is cosmetic. Use a recent value (newest observed ~`1.183.x`). It does not affect import.

## 2. `workflowVersions[]` item

Exactly one item per workflow. Key presence:

| key | presence | required? |
| --- | --- | --- |
| name | 234 (100%) | required |
| type | 234 (100%) | required |
| version | 234 (100%) | required |
| description | 234 (100%) | required |
| graph | 234 (100%) | required |
| steps | 234 (100%) | required |
| tags | 234 (100%) | required |
| humanCostSeconds | 234 (100%) | required |
| humanCostDisplayUnit | 234 (100%) | required |
| parameters | 186 (79%) | optional |
| summary | 147 (63%) | optional |


- `type` is always `"runnable"`.
- `humanCostDisplayUnit`: {'minutes': 178, '': 54, 'hours': 2} (use `minutes`).
- `tags` state across corpus: {'populated': 122, 'null': 91, 'empty_list': 21} (null is acceptable).
- `parameters` state: {'populated_definitionSchema': 149, 'absent': 48, 'null_definitionSchema': 33, 'empty_definitionSchema': 4}.
- When `parameters.definitionSchema` is populated it always has exactly these keys: ['type', 'required', 'properties', 'definitions'] (no root `title`).

## 3. Graph shape

- Nodes per workflow: {'count': 234, 'min': 2, 'max': 54, 'mean': 16.09, 'median': 14}.
- Edges per workflow: {'count': 234, 'min': 2, 'max': 67, 'mean': 20.09, 'median': 18}.
- Steps per workflow: {'count': 234, 'min': 2, 'max': 54, 'mean': 16.09, 'median': 14}.
- **Invariant:** `len(graph.nodes) == len(steps)` in every file. Every node has a matching step keyed by the same UUID; every step has a matching node.
- Triggers per workflow: always exactly 1.

## 4. `kom.triggers[]` entry

Exactly one entry. Key presence:

| key | presence |
| --- | --- |
| id | 234 (100%) |
| name | 234 (100%) |
| description | 234 (100%) |
| input | 234 (100%) |
| inputJsonSchema | 234 (100%) |
| outputJsonSchema | 234 (100%) |
| tags | 234 (100%) |
| type | 234 (100%) |
| identifier | 103 (44%) |
| plugin | 91 (39%) |
| chatOpsAppName | 82 (35%) |
| chatOpsIdentifier | 82 (35%) |
| options | 16 (7%) |


Always-present keys (100%): `id, name, description, input, inputJsonSchema, outputJsonSchema, tags, type`.

- `type` values observed: {'trigger_plugin': 91, 'trigger_chatops': 82, 'trigger_api_idr': 27, 'trigger_api': 18, 'trigger_api_vm_webhook': 12, 'trigger_aba_alert': 2, 'trigger_api_rh': 2}.
- `identifier` present only for plugin/idr/webhook triggers (103/234).
- `plugin` object present for plugin triggers (91/234).
- `chatOpsAppName`/`chatOpsIdentifier` for Slack triggers (82/234).
- `options` appears in only 16/234 files, always `['webhookEnabled']`. **Do not add `options` unless the reference trigger type uses it** (webhook-style triggers).
- Trigger `input` state: {'populated': 173, 'null': 58, 'empty_object': 3} - populated is the norm; `null` is used by simple API triggers. Empty object is rare.

## 5. Data interpolation

- UUID references `{{[step_uuid].[field]}}`: used in 233/234 files (the norm).
- Job references `{{[$job]...}}`: 96/234.
- Workflow parameters `{{[$workflow].[Name]}}`: 38/234.
- Never reference steps by human name; always by node UUID.

## 6. connectionType

Observed values across all steps: {'NONE': 2348, 'CONNECTION': 1099, 'ORCHESTRATOR': 317}.
- `NONE` for native steps and API triggers.
- `CONNECTION` for plugin actions/triggers that use a plugin connection.
- `ORCHESTRATOR` for steps pinned to run on an on-prem orchestrator.
