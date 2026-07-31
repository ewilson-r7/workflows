---
inclusion: fileMatch
fileMatchPattern: '*.icon'
---

# InsightConnect `.icon` workflow building

This steering fires when an `.icon` file is in context. The full authority is the
`workflow-builder` skill and its evidence-based catalogs under `references/generated/`.

## Build as deterministic scaffolding + reasoning

Reason out a workflow **plan** (trigger + steps + edges + parameters), then generate:

```
python3 scripts/build_workflow.py plan.json --bundle --bundle-dir output/
```

## Non-negotiable rules

- Single `kom` with `komFileVersion: "2.0.0"`, one `workflowVersions[]`, one `triggers[]`.
- `summary` field always present (empty string if no value).
- `caseManagementInputJsonSchema: null` and `caseManagementOutputJsonSchema: null` on every step.
- No `connection` key on steps.
- `len(graph.nodes) == len(steps)`. Reference data by UUID only.
- **`outputJSONSchema`**: `null` for most step types. OBJECT for `loop`/`join` and custom-output actions.
- Expression operator: single `=` for equality. String literals quoted in `expressionText`.
- Decision edges get names (`"Yes"`, `"No"`). Other edges have empty `name`.
- Loop: `repeatVariable` for collections, `[$item]` for current item. No `forEach`/`selectedCollection`.
- Slack = ChatOps. Teams = `microsoft_teams` plugin (NOT ChatOps).
- `defaultImageData`: populate with CDN URLs for native step types.
