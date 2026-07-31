#!/usr/bin/env python3
"""
Build curated, human- and Kiro-readable catalog artifacts from `structure_report.json`.

Inputs
------
  output/structure_report.json   (produced by analyze_workflows.py)

Outputs (written to ../references/generated/)
--------------------------------------------
  workflow_format_spec.md            Canonical .icon structure with real presence stats
  step_type_contract.json            Per-step-type machine contract (required keys, schema rules)
  step_type_contract.md              Readable version of the contract
  plugin_capability_catalog.json     Usage-derived plugin -> actions/triggers + versions
  plugin_capability_catalog.md       Readable ranked catalog
  input_configuration_patterns.md    How input is configured (required vs optional themes)

These files are DERIVED from real known-good workflows. Regenerate them by re-running
analyze_workflows.py then this script whenever the insightconnect-workflows repo updates.
"""

from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).parent
REPORT = HERE / "output" / "structure_report.json"
OUT = HERE.parent / "references" / "generated"

# Human wording for the outputJSONSchema rule, derived from the data distributions.
OUTPUT_SCHEMA_RULE = {
    "action": "null (an object ONLY for custom-output actions like python_3_script/jq that expose named outputs)",
    "action_chatops": "null",
    "artifact": "null",
    "automated_decision": "null",
    "break": "null",
    "decision_chatops": "null",
    "filter": "null",
    "helpers": "null",
    "human_decision": "null",
    "join": "object ALWAYS (empty {properties:{},title:Variables,type:object} or populated) - NEVER null",
    "loop": "object ALWAYS (empty or populated with customOutput vars) - NEVER null",
    "pattern_match": "null",
    "trigger": "null",
}

STEP_BUCKET = {
    "action": "plugin_action",
    "action_chatops": "chatops",
    "decision_chatops": "chatops",
    "trigger": "native_or_plugin_trigger",
    "artifact": "native",
    "automated_decision": "native",
    "human_decision": "native",
    "pattern_match": "native",
    "loop": "native",
    "join": "native",
    "filter": "native",
    "break": "native",
    "helpers": "native",
}

STEP_NOTES = {
    "trigger": "The workflow's single entry point. Has triggerId matching the kom.triggers[] entry UUID. Plugin triggers add plugin+identifier+connection; Slack adds chatOpsAppName/chatOpsIdentifier; native API/scheduled triggers have neither.",
    "action": "Plugin action step. Always has plugin{name,slugVendor,slugName,slugVersion,imageData}, identifier (action name), connection, and isCloud. parameters.input mirrors the action's declared input schema.",
    "action_chatops": "Slack action step (send message / prompt). chatOpsAppName='slack' + chatOpsIdentifier at step root. No plugin object.",
    "decision_chatops": "Slack interactive decision (buttons). chatOpsAppName='slack' + chatOpsIdentifier.",
    "artifact": "Markdown output card. parameters={input:{content:'...markdown...'}, type:'markdown'}. All schema fields null.",
    "automated_decision": "Branching by expression. parameters.stepControlParams[] each with edgeId + expression AST + expressionText; plus defaultEdgeId.",
    "human_decision": "Waits for a human choice. parameters has defaultEdgeId, notifications, stepControlParams[], timeout, timeoutDisplayUnit, timeoutEdgeId.",
    "pattern_match": "Regex/variable extraction. parameters has expressions[], expressionText, input, captureAll, ignoreCase.",
    "loop": "Iterates a body subgraph. For collection loops: parameters.repeatVariable is a {{[uuid].[array_field]}} ref; the current item is {{[loop_uuid].[item]}}. For count loops: repeatCount + repeatDelay. Always has innerEdgeId + nextEdgeId. customOutput accumulates values per iteration. Carries an outputJSONSchema object (never null). DO NOT use forEach/selectedCollection.",
    "join": "Waits for parallel branches to converge; carries an outputJSONSchema object (and defaultOutputJSONSchema).",
    "filter": "Single-condition gate. parameters has stepControlParam (singular) + stopOnMatch.",
    "break": "Breaks out of an enclosing loop. Standard native step keys, no special params.",
    "helpers": "Global artifact / helper step. Adds helperIdentifier and (usually) globalArtifact keys.",
}


def load_report() -> dict:
    return json.loads(REPORT.read_text(encoding="utf-8"))


def build_step_contract(r: dict) -> dict:
    keys_by_type = r["step_types"]["keys_by_type"]
    raw_counts = r["step_types"]["raw_counts"]
    schema_states = r["schema_nullness_by_step_type"]

    contract = {}
    for stype, keys in keys_by_type.items():
        total = raw_counts.get(stype, 0)
        required = sorted(k for k, c in keys.items() if c == total)
        optional = sorted(
            (k for k, c in keys.items() if c < total),
            key=lambda k: -keys[k],
        )
        contract[stype] = {
            "occurrences": total,
            "bucket": STEP_BUCKET.get(stype, "unknown"),
            "always_present_keys": required,
            "sometimes_present_keys": {k: keys[k] for k in optional},
            "outputJSONSchema_rule": OUTPUT_SCHEMA_RULE.get(stype, "unknown"),
            "schema_state_distribution": schema_states.get(stype, {}),
            "notes": STEP_NOTES.get(stype, ""),
        }
    return contract


def md_table(headers, rows) -> str:
    out = "| " + " | ".join(headers) + " |\n"
    out += "| " + " | ".join("---" for _ in headers) + " |\n"
    for row in rows:
        out += "| " + " | ".join(str(c) for c in row) + " |\n"
    return out


def build_format_spec_md(r: dict) -> str:
    c = r["corpus"]
    tl = r["top_level"]
    wfv = r["workflow_version_item"]
    gs = r["graph_shape"]
    tae = r["trigger_array_entry"]
    interp = r["interpolation_usage_files"]
    n = c["total_icon_files"]

    def pct(x):
        return f"{x} ({round(100*x/n)}%)"

    lines = []
    lines.append("# InsightConnect `.icon` Workflow Format Spec (evidence-based)\n")
    lines.append(
        f"Derived deterministically from **{n}** known-good, importable workflows in "
        "`insightconnect-workflows`. Percentages are how often a field/value appears across the "
        f"corpus. Parse errors: {len(c['parse_errors'])}.\n"
    )
    lines.append("> Regenerate: `python3 analyze_workflows.py && python3 build_catalogs.py`\n")

    lines.append("## 1. Top level\n")
    lines.append(
        "Every file is a single top-level `kom` object. These keys appear in 100% of files:\n"
    )
    lines.append(md_table(["kom key", "presence"], [[k, pct(v)] for k, v in tl["kom_keys"].items()]))
    lines.append(f"\n- `komFileVersion` is always `\"2.0.0\"`.")
    lines.append(
        "- `komandVersion` is the exporting platform build; it varies widely and is cosmetic. "
        "Use a recent value (newest observed ~`1.183.x`). It does not affect import.\n"
    )

    lines.append("## 2. `workflowVersions[]` item\n")
    lines.append("Exactly one item per workflow. Key presence:\n")
    lines.append(md_table(["key", "presence", "required?"],
                          [[k, pct(v), "required" if v == n else "optional"]
                           for k, v in wfv["keys"].items()]))
    lines.append("\n- `type` is always `\"runnable\"`.")
    lines.append(f"- `humanCostDisplayUnit`: {wfv['humanCostDisplayUnit_values']} (use `minutes`).")
    lines.append(f"- `tags` state across corpus: {wfv['tags_state']} (null is acceptable).")
    lines.append(f"- `parameters` state: {wfv['parameters_state']}.")
    lines.append(
        "- When `parameters.definitionSchema` is populated it always has exactly these keys: "
        f"{list(wfv['definitionSchema_keys'].keys())} (no root `title`).\n"
    )

    lines.append("## 3. Graph shape\n")
    lines.append(
        f"- Nodes per workflow: {gs['nodes_per_workflow']}.\n"
        f"- Edges per workflow: {gs['edges_per_workflow']}.\n"
        f"- Steps per workflow: {gs['steps_per_workflow']}.\n"
        "- **Invariant:** `len(graph.nodes) == len(steps)` in every file. Every node has a matching "
        "step keyed by the same UUID; every step has a matching node.\n"
        f"- Triggers per workflow: always exactly 1.\n"
    )

    lines.append("## 4. `kom.triggers[]` entry\n")
    lines.append("Exactly one entry. Key presence:\n")
    lines.append(md_table(["key", "presence"], [[k, pct(v)] for k, v in tae["keys"].items()]))
    lines.append("\nAlways-present keys (100%): `id, name, description, input, inputJsonSchema, "
                 "outputJsonSchema, tags, type`.\n")
    lines.append(f"- `type` values observed: {tae['type_values']}.")
    lines.append(f"- `identifier` present only for plugin/idr/webhook triggers ({tae['keys'].get('identifier',0)}/{n}).")
    lines.append(f"- `plugin` object present for plugin triggers ({tae['keys'].get('plugin',0)}/{n}).")
    lines.append(f"- `chatOpsAppName`/`chatOpsIdentifier` for Slack triggers ({tae['keys'].get('chatOpsAppName',0)}/{n}).")
    lines.append(f"- `options` appears in only {tae['options_present'].get('present',0)}/{n} files, "
                 f"always `{list(tae['options_keys'].keys())}`. **Do not add `options` unless the "
                 "reference trigger type uses it** (webhook-style triggers).")
    lines.append(f"- Trigger `input` state: {tae['input_state']} - populated is the norm; `null` is "
                 "used by simple API triggers. Empty object is rare.\n")

    lines.append("## 5. Data interpolation\n")
    lines.append(
        f"- UUID references `{{{{[step_uuid].[field]}}}}`: used in {interp['uuid_ref']}/{n} files (the norm).\n"
        f"- Job references `{{{{[$job]...}}}}`: {interp['job_ref_{{[$job]}}']}/{n}.\n"
        f"- Workflow parameters `{{{{[$workflow].[Name]}}}}`: {interp['workflow_param_{{[$workflow]}}']}/{n}.\n"
        "- Never reference steps by human name; always by node UUID.\n"
    )

    lines.append("## 6. connectionType\n")
    lines.append(
        f"Observed values across all steps: {r['step_types']['connectionType_values']}.\n"
        "- `NONE` for native steps and API triggers.\n"
        "- `CONNECTION` for plugin actions/triggers that use a plugin connection.\n"
        "- `ORCHESTRATOR` for steps pinned to run on an on-prem orchestrator.\n"
    )
    return "\n".join(lines)


def build_contract_md(contract: dict) -> str:
    lines = ["# Step Type Contract (evidence-based)\n"]
    lines.append(
        "Per step `type`, derived from real workflows: how many times it appears, which keys are "
        "ALWAYS present, which are sometimes present, and the critical `outputJSONSchema` rule. "
        "The `outputJSONSchema` rule is the #1 cause of silent import failures.\n"
    )
    order = sorted(contract.items(), key=lambda kv: -kv[1]["occurrences"])
    for stype, info in order:
        lines.append(f"## `{stype}`  ({info['bucket']}, {info['occurrences']} uses)\n")
        lines.append(f"{info['notes']}\n")
        lines.append(f"- **`outputJSONSchema`**: {info['outputJSONSchema_rule']}")
        lines.append(f"- **Always present keys**: `{', '.join(info['always_present_keys'])}`")
        if info["sometimes_present_keys"]:
            sp = ", ".join(f"{k} ({v})" for k, v in info["sometimes_present_keys"].items())
            lines.append(f"- **Sometimes present**: {sp}")
        lines.append(f"- Schema-state distribution: `{json.dumps(info['schema_state_distribution'])}`\n")
    return "\n".join(lines)


def build_plugin_catalog(r: dict) -> tuple[dict, str]:
    pc = r["plugin_catalog"]
    ranked = sorted(
        pc.items(),
        key=lambda kv: kv[1]["total_action_uses"] + kv[1]["total_trigger_uses"],
        reverse=True,
    )
    # JSON: keep newest-observed version as a hint (highest count first already ordered by count;
    # we cannot infer semver ordering safely, so expose the full version->count map).
    catalog_json = {
        "generated_from": "insightconnect-workflows usage",
        "note": "USAGE-DERIVED, not exhaustive. It lists only plugins/actions/triggers that appear "
                "in shipped workflows. Always confirm the current version + full input schema from "
                "plugin.spec.yaml on origin/master before generating.",
        "plugin_count": len(pc),
        "plugins": {slug: info for slug, info in ranked},
    }

    lines = ["# Plugin Capability Catalog (usage-derived)\n"]
    lines.append(
        f"{len(pc)} plugins actually used across the workflow library, ranked by usage. This is a "
        "**discovery aid, not a schema source**: it shows which plugin slug + action/trigger "
        "identifiers are real and commonly used. Always pull the exact current version and full "
        "input/output schema from `plugins/<slug>/plugin.spec.yaml` on `origin/master`.\n"
    )
    lines.append("> Vendor is `rapid7` for the entire first-party library (only exception observed: "
                 "`automox`). Build the plugin object as "
                 "`{name, slugVendor, slugName, slugVersion, imageData}`.\n")
    rows = []
    for slug, info in ranked:
        vendor = ",".join(info["vendor"])
        versions = list(info["versions"].keys())
        rows.append([
            slug,
            vendor,
            info["total_action_uses"],
            info["total_trigger_uses"],
            len(info["versions"]),
            (versions[0] if versions else ""),
        ])
    lines.append(md_table(
        ["slug", "vendor", "action uses", "trigger uses", "#versions", "most-common version"],
        rows,
    ))
    lines.append("\n## Actions & triggers per plugin\n")
    for slug, info in ranked:
        acts = ", ".join(info["actions"].keys()) or "-"
        trigs = ", ".join(info["triggers"].keys()) or "-"
        lines.append(f"### `{slug}` ({', '.join(info['display_names'])})")
        lines.append(f"- Actions: {acts}")
        lines.append(f"- Triggers: {trigs}\n")
    return catalog_json, "\n".join(lines)


def build_input_patterns_md(r: dict) -> str:
    io = r["io_config_catalog"]
    configs = list(io.values())
    total = len(configs)
    always_pop = sum(1 for v in configs if v["input_populated"] and not v["input_empty"])

    # Build required/optional inference for high-use actions.
    hi = [v for v in configs if v["occurrences"] >= 5]
    hi.sort(key=lambda v: -v["occurrences"])

    lines = ["# Input Configuration Patterns (evidence-based)\n"]
    lines.append(
        f"Across **{total}** distinct plugin action/trigger configurations ({sum(v['occurrences'] for v in configs)} "
        "step occurrences):\n"
    )
    lines.append(
        f"- **{always_pop}/{total}** always carry a populated `parameters.input` object. An empty "
        "input on a plugin step is essentially never correct - it is a red flag.\n"
        "- The `input` object mirrors the action's declared input schema. Values are one of: a "
        "literal constant, a workflow-parameter reference `{{[$workflow].[Name]}}`, or an upstream "
        "reference `{{[step_uuid].[field]}}`.\n"
        "- Known-good exports commonly set the **full declared input property set** for an action, "
        "including optional fields (often as empty string or a default), not just the required ones. "
        "When in doubt, include every declared input property and fill required ones.\n"
    )
    lines.append("## Required vs optional (inferred from real usage)\n")
    lines.append(
        "A field set in 100% of an action's uses is effectively required/always-set; a field set "
        "in a subset is optional. Confirm true `required` against `plugin.spec.yaml`.\n"
    )
    rows = []
    for v in hi[:30]:
        occ = v["occurrences"]
        req = [k for k, f in v["top_input_keys"].items() if f == occ]
        opt = [f"{k}({f}/{occ})" for k, f in v["top_input_keys"].items() if f < occ]
        rows.append([
            f"{v['slug']}::{v['identifier']}",
            v["kind"],
            occ,
            ", ".join(req) or "-",
            ", ".join(opt) or "-",
        ])
    lines.append(md_table(["plugin::identifier", "kind", "uses", "always-set (≈required)", "optional (subset)"], rows))
    lines.append(
        "\n## Utility plugin notes (corrections from data)\n"
        "- `python_3_script::run`: `function` and `input` are always set; `timeout` is **optional** "
        "(seen in only 4/18 uses). Root input is limited to `function`, `input`, `timeout`.\n"
        "- `rest` fallback: shipped workflows use input keys `body`, `headers`, `route` (only the "
        "`post` action appears in the corpus). The `body_object`/`body_any` guidance depends on the "
        "plugin version - always confirm the current `rest` input schema in `plugin.spec.yaml` "
        "before generating, rather than assuming.\n"
        "- Slack is modeled as ChatOps step types (`action_chatops`/`decision_chatops`, "
        "`chatOpsAppName='slack'`). Microsoft Teams is a **normal plugin** (`microsoft_teams`, "
        "actions `send_html_message`/`send_message`), NOT ChatOps.\n"
    )
    return "\n".join(lines)


def main() -> int:
    r = load_report()
    OUT.mkdir(parents=True, exist_ok=True)

    contract = build_step_contract(r)
    (OUT / "step_type_contract.json").write_text(json.dumps(contract, indent=2), encoding="utf-8")
    (OUT / "step_type_contract.md").write_text(build_contract_md(contract), encoding="utf-8")
    (OUT / "workflow_format_spec.md").write_text(build_format_spec_md(r), encoding="utf-8")

    cat_json, cat_md = build_plugin_catalog(r)
    (OUT / "plugin_capability_catalog.json").write_text(json.dumps(cat_json, indent=2), encoding="utf-8")
    (OUT / "plugin_capability_catalog.md").write_text(cat_md, encoding="utf-8")

    (OUT / "input_configuration_patterns.md").write_text(build_input_patterns_md(r), encoding="utf-8")

    print("Wrote catalog artifacts to", OUT)
    for p in sorted(OUT.glob("*")):
        print("  -", p.name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
