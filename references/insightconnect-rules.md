# InsightConnect Generation Rules

Use this file as the detailed rulebook when generating or validating Rapid7 InsightConnect `.icon` workflow JSON.

## Required artifacts

Load these local files before generating a workflow:

- `insightconnect_knowledge_base.jsonl`: plugin, action, trigger, and schema source of truth
- `insightconnect_native_steps.json`: exact native step structures
- `sample_workflow.json`: exact workflow hierarchy and field layout
- `sample_description.md`: markdown template and tone guide for the workflow `description` field

If any required artifact is missing and the missing content would force guessing, stop and say: `I do not have enough verified information to answer this.`

## Fact integrity

- Never guess.
- Never invent plugin names, action identifiers, schema properties, JSON keys, or platform structure.
- Decline any portion of a request that would require speculation.
- Prefer a short refusal over an unverified answer.

## Plugin and trigger lookup

- Query `insightconnect_knowledge_base.jsonl` for every requested integration, action, and trigger.
- Extract `plugin_vendor`, `plugin_slug`, `plugin_version`, and `identifier` directly from the knowledge base.
- Build each plugin object with exactly these keys: `name`, `slugVendor`, `slugName`, `slugVersion`, `imageData`.
- If an integration is missing, reply with: `The requested integration does not have an existing plugin in the library. A custom HTTP request workflow will need to be created.`

## Schema rules

- Fully populate every `defaultInputJSONSchema` and `defaultOutputJSONSchema` for steps.
- Fully populate every `inputJsonSchema` and `outputJsonSchema` for triggers.
- If a property requires a complex nested object, you MUST set its type to `object` or use a `$ref` pointer (e.g. "$ref": "#/definitions/investigation")
  - You MUST fully build out the corresponding `definitions` dictionary at the bottom of that specific schema block.
- Never abbreviate, truncate, or replace schema sections with placeholders.
- The `type` key in any schema property MUST ONLY be a standard JSON primitive (string, integer, boolean, object, array, number)
- You are STRICTLY FORBIDDEN from inventing custom types.

## Graph and identifier rules

- Use unique UUIDv4 values for every node, edge, step, and trigger identifier.
- Keep UUIDs strictly hexadecimal in `8-4-4-4-12` form.
- Include a `graph` object with `nodes` and `edges`.
- Ensure every graph node has a corresponding step entry.
- In `graph.nodes`, include only `id` and `parentNodeId`.
- In `graph.edges`, include `id`, `name`, `description`, `parentNodeId`, `fromNodeId`, and `toNodeId`.

## Trigger and step mapping rules

- The trigger object in the `triggers` array must include its own UUID and the exact `identifier`.
- The starting step in `steps` must have its own unique `nodeId`.
- The starting step must also include `triggerId` that exactly matches the trigger UUID.
- Use UUID-based interpolation syntax such as `{{[27045b73-0441-470a-9d62-f94602f928e4].[investigation].[id]}}`.
- Never use human-readable step names in variable mappings.

## Native step rules

Native platform steps are:

- `artifact`
- `automated_decision`
- `human_decision`
- `pattern_match`
- `loop`
- `join`

For these steps:

- Read `insightconnect_native_steps.json`.
- Reuse the exact structure and required parameters from that file.
- Still include `defaultInputJSONSchema`, `defaultOutputJSONSchema`, and `outputJSONSchema`, even if empty.

For `automated_decision`:

- Every item in `stepControlParams` must include both `expressionText` and a fully built `expression` AST object with `left`, `op`, `right`, and `type`.

For `loop`:

- Set `innerEdgeId` to the first edge inside the loop.
- Set `nextEdgeId` to the edge that continues after the loop.
- Set `parentNodeId` on every nested step and nested edge to the loop UUID.
- End the loop body with an edge whose `toNodeId` is an empty string to indicate repetition.

## Standard step defaults

Every step should include:

- `continueOnFailure: false`
- `isDisabled: false`
- `isCloud: false`
- `outputJSONSchema`

## Workflow parameter rules

- Do not hardcode environment-specific values such as channels, addresses, project IDs, or tokens.
- Define those values in the global `parameters.definitionSchema` block.
- Reference them with the exact syntax: `{{[$workflow].[Parameter Name]}}`. Never drop the `$workflow` keyword

## Description field rules

- Read `sample_description.md` before drafting the workflow `description`.
- Treat `description` as formatted markdown content, not a one-line summary.
- Mirror the sample's section order and style, then rewrite the content so it accurately matches the generated workflow.
- Use only verified workflow details from the request, attached artifacts, and generated workflow structure.
- Include a plugin summary table in the description when the workflow details support it.
- For newly created workflows, set the version history entry to `1.0.0 - Initial workflow` unless the user explicitly provides different version details.
- Do not copy the sample text verbatim except for reusable section headings.

## Optimization rules

- Prefer built-in trigger filtering over a separate decision step when the trigger supports filtering.

## REST plugin rules

- Use either `body_object` or `body_any`, never both.
- Use `body_object` for normal JSON objects.
- Use `body_any` for arrays, raw strings, form-encoded bodies, or GraphQL payloads.
- Set explicit headers whenever the API requires them.

## Python 3 Script rules

When using the Python 3 Script plugin action `run`:

- Keep root input limited to `function`, `input`, and `timeout`.
- Put custom values inside the nested `input` object and mirror them in the nested schema.
- Start the function with `def run(params={}):`.
- Return a dictionary.
- Never hardcode secrets; use connection-injected variables such as `username`, `password`, `secret_key`, `secret_credential_1`, `secret_credential_2`, and `secret_credential_3`.
- After the JSON workflow, include a short markdown note that lists:
  - which connection secret fields must be populated
  - which third-party PyPI modules must be added

## ChatOps rule

When the requested tool is Slack:

- Do not model it as a standard plugin step.
- Use `type` values such as `action_chatops`, `trigger_chatops`, or `decision_chatops`.
- Include `chatOpsAppName: "slack"` and the required `chatOpsIdentifier` at the step root.
- Use the `slack_workflow_template.json` as a reference for how to setup the triggers and actions for slack.

## Output format

- Mirror the hierarchy from `sample_workflow.json`.
- Use `komFileVersion: "2.0.0"`.
- Write the final workflow JSON to a real `.icon` file in the current workspace instead of only returning it in a code block.
- Default the filename to a filesystem-safe version of the workflow name with a `.icon` extension unless the user specifies a different filename.
- After writing the file, report the saved file path.
- Add a short markdown note after the path only when the workflow uses Python 3 Script and the note is required.
