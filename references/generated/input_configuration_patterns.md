# Input Configuration Patterns (evidence-based)

Across **275** distinct plugin action/trigger configurations (1416 step occurrences):

- **274/275** always carry a populated `parameters.input` object. An empty input on a plugin step is essentially never correct - it is a red flag.
- The `input` object mirrors the action's declared input schema. Values are one of: a literal constant, a workflow-parameter reference `{{[$workflow].[Name]}}`, or an upstream reference `{{[step_uuid].[field]}}`.
- Known-good exports commonly set the **full declared input property set** for an action, including optional fields (often as empty string or a default), not just the required ones. When in doubt, include every declared input property and fill required ones.

## Required vs optional (inferred from real usage)

A field set in 100% of an action's uses is effectively required/always-set; a field set in a subset is optional. Confirm true `required` against `plugin.spec.yaml`.

| plugin::identifier | kind | uses | always-set (≈required) | optional (subset) |
| --- | --- | --- | --- | --- |
| microsoft_teams::send_html_message | action | 369 | channel_name, message_content, team_name, thread_id | - |
| microsoft_teams::new_message_received | trigger | 63 | channel_name, message_content, team_name | - |
| type_converter::combine_arrays | action | 36 | array1, array2, array3, array4, array5 | - |
| rapid7_insightidr::create_comment | action | 26 | attachments, body, target | - |
| microsoft_teams::send_message | action | 23 | channel_name, message, team_name, thread_id | chat_id(4/23) |
| html::text | action | 19 | doc, remove_scripts | - |
| python_3_script::run | action | 18 | function, input | timeout(4/18) |
| rapid7_insightidr::get_investigation | action | 18 | id | - |
| extractit::url_extractor | action | 17 | file, str | keep_original_urls(12/17) |
| math::calculate | action | 17 | equation | - |
| rapid7_insightidr::set_status_of_investigation_action | action | 17 | id, status | - |
| hashit::string | action | 16 | string | - |
| extractit::domain_extractor | action | 15 | file, str, subdomain | - |
| rapid7_insightvm::asset_search | action | 15 | searchCriteria | size(14/15), sort_criteria(14/15) |
| active_directory_ldap::query | action | 14 | attributes, search_base, search_filter | - |
| crowdstrike_falcon::blacklist_ioc | action | 12 | action, description, indicator, indicator_state, severity | - |
| rapid7_vulndb::get_content | action | 12 | identifier | - |
| active_directory_ldap::disable_user | action | 11 | distinguished_name | - |
| datetime::get_datetime | action | 10 | format_string, use_rfc3339_format | - |
| rapid7_insightidr::get_alert_evidence | action | 10 | alert_rrn, index, size | - |
| rapid7_insightidr::list_alerts_for_investigation | action | 10 | id, index, size | - |
| string::split_to_list | action | 10 | delimiter, string | - |
| type_converter::string_to_integer | action | 10 | input, strip | - |
| jira::create_issue | action | 8 | attachment_bytes, attachment_filename, description, fields, project, summary, type | - |
| rapid7_insightvm::generate_adhoc_sql_report | action | 8 | filters, query, scope, scope_ids | - |
| rapid7_insightvm::get_asset | action | 8 | - | id(6/8), asset_id(2/8) |
| rest::post | action | 8 | body, headers, route | - |
| storage::store | action | 8 | variable_name, variable_value | - |
| type_converter::string_to_object | action | 8 | input | - |
| virustotal::scan_url_report | action | 8 | url | - |


## Utility plugin notes (corrections from data)
- `python_3_script::run`: `function` and `input` are always set; `timeout` is **optional** (seen in only 4/18 uses). Root input is limited to `function`, `input`, `timeout`.
- `rest` fallback: shipped workflows use input keys `body`, `headers`, `route` (only the `post` action appears in the corpus). The `body_object`/`body_any` guidance depends on the plugin version - always confirm the current `rest` input schema in `plugin.spec.yaml` before generating, rather than assuming.
- Slack is modeled as ChatOps step types (`action_chatops`/`decision_chatops`, `chatOpsAppName='slack'`). Microsoft Teams is a **normal plugin** (`microsoft_teams`, actions `send_html_message`/`send_message`), NOT ChatOps.
