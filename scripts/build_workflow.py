#!/usr/bin/env python3
"""
Deterministic InsightConnect `.icon` generator.

This is the "deterministic file generation" half of the workflow-builder: Kiro reasons out a
plain workflow *plan* (which trigger, which steps, the wiring, the field mappings) and this script
turns that plan into a structurally correct, import-ready `.icon`. It owns every error-prone
mechanical detail so Kiro never has to hand-write them:

  * UUIDv4 assignment for the trigger, every step (nodeId), and every edge
  * graph.nodes + graph.edges construction (and the len(nodes)==len(steps) invariant)
  * per-step-type schema nullness (the #1 cause of silent import failures):
        - outputJSONSchema is null for standard/native steps
        - outputJSONSchema is an OBJECT (never null) for `loop` and `join`
        - action custom-output steps (python_3_script, jq) carry an object
        - defaultInput/OutputJSONSchema populated for plugin/chatops/trigger steps
  * kom.triggers[] entry kept in sync with the trigger step (id/identifier/plugin/input)
  * reference resolution: friendly `{{step_key.field.subfield}}` -> `{{[node_uuid].[field].[subfield]}}`
    ($trigger, $workflow, $job, $global are passed through untouched)
  * a structural self-check before writing

Design intent: the plan is intentionally small and human/LLM-friendly. Anything this script can
derive deterministically is NOT required in the plan. Advanced native steps (loop/human_decision
bodies) may pass a raw `parameters` object through; edge references inside them can use edge
`label`s which are resolved to edge UUIDs.

The plan schema and a runnable example are at the bottom (`--example`). Validate any plan with
`--check-only`.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

KOMAND_VERSION = "1.183.51-477bc97a1"  # cosmetic; recent observed build
EMPTY_VARS_SCHEMA = {"properties": {}, "title": "Variables", "type": "object"}
EMPTY_OBJECT_SCHEMA = {"definitions": {}, "properties": {}, "type": "object"}

# Step types whose outputJSONSchema MUST be an object (never null).
OBJECT_OUTPUT_TYPES = {"loop", "join"}
# Plugin action slugs whose action step exposes named custom output (object outputJSONSchema).
CUSTOM_OUTPUT_SLUGS = {"python_3_script", "jq"}
# Step types that carry a plugin object / identifier.
PLUGIN_STEP_TYPES = {"action"}
CHATOPS_STEP_TYPES = {"action_chatops", "decision_chatops", "trigger_chatops"}
# Native (platform) step types.
NATIVE_STEP_TYPES = {
    "artifact", "automated_decision", "human_decision", "pattern_match",
    "loop", "join", "filter", "break", "helpers",
}

STEP_ICON = "https://us.cdn-assets.connect.insight.rapid7.com/step-type-icons/{}.svg"
DEFAULT_TRIGGER_ICON = STEP_ICON.format("trigger-api")

# friendly reference: {{key.a.b}}  (key = step key or $trigger/$workflow/$job/$global)
REF_RE = re.compile(r"\{\{([^}]+)\}\}")
PASSTHROUGH_PREFIXES = ("$workflow", "$job", "$global")


class PlanError(Exception):
    pass


def new_uuid() -> str:
    return str(uuid.uuid4())


# --------------------------------------------------------------------------------------
# Reference resolution
# --------------------------------------------------------------------------------------
def resolve_refs(value: Any, key_to_uuid: dict[str, str], trigger_key: str) -> Any:
    """Recursively rewrite friendly {{key.field}} refs to {{[uuid].[field]}} form."""
    if isinstance(value, str):
        return _resolve_str(value, key_to_uuid, trigger_key)
    if isinstance(value, dict):
        return {k: resolve_refs(v, key_to_uuid, trigger_key) for k, v in value.items()}
    if isinstance(value, list):
        return [resolve_refs(v, key_to_uuid, trigger_key) for v in value]
    return value


def _resolve_str(s: str, key_to_uuid: dict[str, str], trigger_key: str) -> str:
    def repl(m: re.Match) -> str:
        inner = m.group(1).strip()
        # already UUID form: {{[...]. ...}} -> leave as-is
        if inner.startswith("["):
            return m.group(0)
        parts = inner.split(".")
        head = parts[0]
        # passthrough platform keywords
        if head in PASSTHROUGH_PREFIXES:
            segs = [f"[{head}]"] + [f"[{p}]" for p in parts[1:]]
            return "{{" + ".".join(segs) + "}}"
        if head == "$trigger":
            head = trigger_key
        if head not in key_to_uuid:
            raise PlanError(
                f"Reference '{{{{{inner}}}}}' points to unknown step key '{head}'. "
                f"Known keys: {sorted(key_to_uuid)} (+ $trigger/$workflow/$job/$global)"
            )
        # Resolve remaining path segments; `item` on a loop becomes `$item`
        tail_segs = []
        for p in parts[1:]:
            if p == "item":
                tail_segs.append("[$item]")
            else:
                tail_segs.append(f"[{p}]")
        segs = [f"[{key_to_uuid[head]}]"] + tail_segs
        return "{{" + ".".join(segs) + "}}"

    return REF_RE.sub(repl, s)


# --------------------------------------------------------------------------------------
# Schema helpers
# --------------------------------------------------------------------------------------
def as_schema(obj: Any) -> dict:
    """Coerce a plan-provided schema (or None) into a populated JSON-schema object."""
    if obj is None:
        return dict(EMPTY_OBJECT_SCHEMA)
    if not isinstance(obj, dict):
        raise PlanError(f"schema must be an object, got {type(obj).__name__}")
    out = dict(obj)
    out.setdefault("type", "object")
    out.setdefault("properties", {})
    out.setdefault("definitions", {})
    return out


# --------------------------------------------------------------------------------------
# Step builders
# --------------------------------------------------------------------------------------
def build_plugin_object(p: dict) -> dict:
    for req in ("slugName", "slugVersion"):
        if not p.get(req):
            raise PlanError(f"plugin object missing '{req}': {p}")
    return {
        "name": p.get("name", p["slugName"]),
        "slugVendor": p.get("slugVendor", "rapid7"),
        "slugName": p["slugName"],
        "slugVersion": p["slugVersion"],
        "imageData": p.get("imageData", ""),
    }


def _build_loop_parameters(step: dict, key_to_uuid: dict, trigger_key: str,
                           edge_label_to_id: dict) -> dict:
    """Build loop step parameters from the plan's loop specification.

    The plan can provide loop config in two forms:
    1. Friendly form (preferred): `repeatVariable` with a `{{step_key.field}}` ref, plus
       `innerEdgeLabel` and `nextEdgeLabel` (resolved to UUIDs from edge labels).
    2. Raw form: a full `parameters` dict that gets ref-resolved and edge-label-resolved.

    Key finding from real exports: the platform uses `repeatVariable` (a string interpolation
    pointing to the collection) for collection loops. NOT `forEach`/`selectedCollection` or
    `repeatCount`/`repeatDelay` (those are for count-based timed loops only).
    """
    if "parameters" in step:
        # Raw passthrough: resolve refs and edge labels
        params = resolve_refs(step["parameters"], key_to_uuid, trigger_key)
        return _resolve_edge_labels(params, edge_label_to_id)

    # Friendly form
    params: dict[str, Any] = {}

    # repeatVariable: the collection to iterate (e.g. "{{extract_hashes.sha256}}")
    rv = step.get("repeatVariable")
    if rv:
        params["repeatVariable"] = resolve_refs(rv, key_to_uuid, trigger_key)

    # For count-based loops (no collection): use repeatCount + repeatDelay
    if not rv and step.get("repeatCount"):
        params["repeatCount"] = step["repeatCount"]
        params["repeatDelay"] = step.get("repeatDelay", 0)

    # Edge IDs (resolved from edge labels)
    inner_label = step.get("innerEdgeLabel")
    next_label = step.get("nextEdgeLabel")
    if inner_label:
        if inner_label not in edge_label_to_id:
            raise PlanError(f"loop innerEdgeLabel '{inner_label}' not found among edge labels")
        params["innerEdgeId"] = edge_label_to_id[inner_label]
    if next_label:
        if next_label not in edge_label_to_id:
            raise PlanError(f"loop nextEdgeLabel '{next_label}' not found among edge labels")
        params["nextEdgeId"] = edge_label_to_id[next_label]

    # customOutput: optional array; resolve refs inside
    custom_output = step.get("customOutput")
    if custom_output:
        resolved = resolve_refs(custom_output, key_to_uuid, trigger_key)
        # Also resolve bare dotted refs in expression args (name: "step_key.field" -> "uuid.field")
        resolved = _resolve_expression_arg_names(resolved, key_to_uuid, trigger_key)
        params["customOutput"] = resolved

    return params


def _resolve_expression_arg_names(obj: Any, key_to_uuid: dict, trigger_key: str) -> Any:
    """Resolve bare dotted step_key.field references in expression variable `name` fields.

    In expressions (customOutput, stepControlParams), variable nodes use "step_key.field.subfield"
    format (no {{}} wrapper) in their `name` field. The platform expects "uuid.field.subfield" form.
    This handles `args[].name`, `left.name`, `right.name`, and any nested expression nodes.
    """
    if isinstance(obj, dict):
        result = {}
        for k, v in obj.items():
            if k == "name" and isinstance(v, str) and "." in v:
                # Skip if already UUID-resolved
                if re.match(r"[0-9a-f]{8}-[0-9a-f]{4}-", v):
                    result[k] = v
                else:
                    parts = v.split(".", 1)
                    head = parts[0]
                    if head == "$trigger":
                        head = trigger_key
                    if head in key_to_uuid:
                        result[k] = key_to_uuid[head] + "." + parts[1]
                    else:
                        result[k] = v
            else:
                result[k] = _resolve_expression_arg_names(v, key_to_uuid, trigger_key)
        return result
    if isinstance(obj, list):
        return [_resolve_expression_arg_names(item, key_to_uuid, trigger_key) for item in obj]
    return obj


def build_step(step: dict, node_id: str, key_to_uuid: dict, trigger_key: str,
               edge_label_to_id: dict) -> dict:
    stype = step["type"]
    name = step.get("name") or step.get("key") or stype

    base: dict[str, Any] = {
        "nodeId": node_id,
        "name": name,
        "type": stype,
        "continueOnFailure": step.get("continueOnFailure", False),
        "isDisabled": step.get("isDisabled", False),
    }

    # ---- parameters / input ----
    if stype in PLUGIN_STEP_TYPES or stype in CHATOPS_STEP_TYPES:
        inp = resolve_refs(step.get("input", {}) or {}, key_to_uuid, trigger_key)
        base["parameters"] = {"input": inp}
    elif stype == "artifact":
        content = resolve_refs(step.get("content", ""), key_to_uuid, trigger_key)
        base["parameters"] = {"input": {"content": content}, "type": "markdown"}
    elif stype == "loop":
        base["parameters"] = _build_loop_parameters(step, key_to_uuid, trigger_key, edge_label_to_id)
    elif "parameters" in step:
        params = resolve_refs(step["parameters"], key_to_uuid, trigger_key)
        params = _resolve_edge_labels(params, edge_label_to_id)
        params = _resolve_expression_arg_names(params, key_to_uuid, trigger_key)
        base["parameters"] = params
    else:
        base["parameters"] = {}

    # ---- plugin action specifics ----
    if stype in PLUGIN_STEP_TYPES:
        base["plugin"] = build_plugin_object(step["plugin"])
        base["identifier"] = step["identifier"]
        base["isCloud"] = step.get("isCloud", True)

    # ---- chatops specifics ----
    if stype in CHATOPS_STEP_TYPES:
        base["chatOpsAppName"] = step.get("chatOpsAppName", "slack")
        base["chatOpsIdentifier"] = step["chatOpsIdentifier"]

    # ---- helpers specifics ----
    if stype == "helpers":
        base["helperIdentifier"] = step["helperIdentifier"]
        if "globalArtifact" in step:
            base["globalArtifact"] = step["globalArtifact"]

    # ---- schemas (the critical part) ----
    populated_defaults = stype in PLUGIN_STEP_TYPES or stype in CHATOPS_STEP_TYPES
    if populated_defaults:
        base["defaultInputJSONSchema"] = as_schema(step.get("defaultInputJSONSchema"))
        base["defaultOutputJSONSchema"] = as_schema(step.get("defaultOutputJSONSchema"))
    else:
        base["defaultInputJSONSchema"] = step.get("defaultInputJSONSchema")
        base["defaultOutputJSONSchema"] = step.get("defaultOutputJSONSchema")
        # join carries a default output object
        if stype == "join":
            base["defaultOutputJSONSchema"] = as_schema(step.get("defaultOutputJSONSchema"))

    # outputJSONSchema rule
    base["outputJSONSchema"] = _output_schema_for(step, stype)

    base["defaultImageData"] = step.get("defaultImageData") or _default_image_for(stype)
    base["connectionType"] = step.get(
        "connectionType",
        "CONNECTION" if stype in PLUGIN_STEP_TYPES else "NONE",
    )

    # caseManagement schemas (always present, always null in generated workflows)
    base["caseManagementInputJsonSchema"] = None
    base["caseManagementOutputJsonSchema"] = None

    return base


# CDN URLs for step type icons (derived from real exports).
STEP_TYPE_ICONS = {
    "artifact": "https://us2.cdn-assets.connect.insight.rapid7.com/step-type-icons/artifact.svg",
    "automated_decision": "https://us2.cdn-assets.connect.insight.rapid7.com/step-type-icons/automated-decision.svg",
    "human_decision": "https://us2.cdn-assets.connect.insight.rapid7.com/step-type-icons/human-decision.svg",
    "pattern_match": "https://us2.cdn-assets.connect.insight.rapid7.com/step-type-icons/pattern-match.svg",
    "filter": "https://us2.cdn-assets.connect.insight.rapid7.com/step-type-icons/filter.svg",
    "trigger": "https://us2.cdn-assets.connect.insight.rapid7.com/step-type-icons/default.svg",
}


def _default_image_for(stype: str) -> str:
    return STEP_TYPE_ICONS.get(stype, "")


def _output_schema_for(step: dict, stype: str) -> Any:
    if stype in OBJECT_OUTPUT_TYPES:
        # loop/join always an object; use provided custom-output schema or empty vars
        return as_schema_vars(step.get("outputJSONSchema"))
    if stype in PLUGIN_STEP_TYPES:
        slug = step.get("plugin", {}).get("slugName", "")
        if slug in CUSTOM_OUTPUT_SLUGS and step.get("outputJSONSchema") is not None:
            return as_schema_vars(step.get("outputJSONSchema"))
        return None
    # every other native/chatops/trigger step
    return None


def as_schema_vars(obj: Any) -> dict:
    if obj is None:
        return dict(EMPTY_VARS_SCHEMA)
    if not isinstance(obj, dict):
        raise PlanError("outputJSONSchema override must be an object")
    out = dict(obj)
    out.setdefault("title", "Variables")
    out.setdefault("type", "object")
    out.setdefault("properties", {})
    return out


def _resolve_edge_labels(params: Any, edge_label_to_id: dict) -> Any:
    """Replace {"edgeLabel": "Yes"} sentinels with the resolved edge UUID."""
    if isinstance(params, dict):
        if set(params.keys()) == {"edgeLabel"}:
            label = params["edgeLabel"]
            if label not in edge_label_to_id:
                raise PlanError(f"edgeLabel '{label}' not found among edge labels")
            return edge_label_to_id[label]
        return {k: _resolve_edge_labels(v, edge_label_to_id) for k, v in params.items()}
    if isinstance(params, list):
        return [_resolve_edge_labels(v, edge_label_to_id) for v in params]
    return params


# --------------------------------------------------------------------------------------
# Trigger builders
# --------------------------------------------------------------------------------------
def build_trigger_step(trig: dict, node_id: str, trigger_uuid: str) -> dict:
    ttype_kind = trig.get("kind", "api")
    is_plugin = ttype_kind == "plugin"
    is_chatops = ttype_kind == "chatops_slack"

    step: dict[str, Any] = {
        "nodeId": node_id,
        "name": trig.get("name", "Trigger"),
        "type": "trigger",
        "continueOnFailure": False,
        "isDisabled": False,
        "triggerId": trigger_uuid,
    }
    if trig.get("input") is not None:
        step["parameters"] = {"input": trig["input"]}
    step["defaultInputJSONSchema"] = as_schema(trig.get("inputJsonSchema"))
    step["defaultOutputJSONSchema"] = as_schema(trig.get("outputJsonSchema"))
    step["outputJSONSchema"] = None
    if is_plugin:
        step["plugin"] = build_plugin_object(trig["plugin"])
        step["identifier"] = trig["identifier"]
        step["connectionType"] = trig.get("connectionType", "CONNECTION")
        step["defaultImageData"] = trig.get("plugin", {}).get("imageData", "") or STEP_TYPE_ICONS.get("trigger", "")
    elif is_chatops:
        step["chatOpsAppName"] = "slack"
        step["chatOpsIdentifier"] = trig["chatOpsIdentifier"]
        step["connectionType"] = "NONE"
        step["defaultImageData"] = trig.get("defaultImageData", "")
    else:
        if trig.get("identifier"):
            step["identifier"] = trig["identifier"]
        step["connectionType"] = "NONE"
        step["defaultImageData"] = trig.get("defaultImageData", DEFAULT_TRIGGER_ICON)

    # caseManagement schemas (always present, always null)
    step["caseManagementInputJsonSchema"] = None
    step["caseManagementOutputJsonSchema"] = None
    return step


def build_trigger_entry(trig: dict, trigger_uuid: str) -> dict:
    ttype_kind = trig.get("kind", "api")
    type_map = {
        "api": "trigger_api",
        "plugin": "trigger_plugin",
        "chatops_slack": "trigger_chatops",
        "api_idr": "trigger_api_idr",
        "api_vm_webhook": "trigger_api_vm_webhook",
    }
    ttype = trig.get("type") or type_map.get(ttype_kind, "trigger_api")

    entry: dict[str, Any] = {
        "id": trigger_uuid,
        "name": trig.get("name", "Trigger"),
        "description": trig.get("description", ""),
        "input": trig.get("input", None),
        "inputJsonSchema": as_schema(trig.get("inputJsonSchema")),
        "outputJsonSchema": as_schema(trig.get("outputJsonSchema")),
        "tags": trig.get("tags", []),
        "type": ttype,
    }
    if ttype_kind == "plugin":
        entry["identifier"] = trig["identifier"]
        entry["plugin"] = build_plugin_object(trig["plugin"])
    elif ttype_kind == "chatops_slack":
        entry["chatOpsAppName"] = "slack"
        entry["chatOpsIdentifier"] = trig["chatOpsIdentifier"]
    elif trig.get("identifier"):
        entry["identifier"] = trig["identifier"]

    # options only when explicitly requested (e.g. webhook triggers)
    if trig.get("options"):
        entry["options"] = trig["options"]
    return entry


# --------------------------------------------------------------------------------------
# Graph
# --------------------------------------------------------------------------------------
def build_graph_and_edges(edges: list[dict], key_to_uuid: dict, trigger_key: str):
    """Return (graph_nodes, graph_edges, edge_label_to_id).

    Each plan edge: {from, to, label?, description?, parentKey?}
    `from`/`to` are step keys ($trigger allowed as from); to="" ends the branch.
    """
    graph_edges: dict[str, dict] = {}
    edge_label_to_id: dict[str, str] = {}

    def kid(k: str) -> str:
        if k in ("", None):
            return ""
        if k == "$trigger":
            k = trigger_key
        if k not in key_to_uuid:
            raise PlanError(f"edge references unknown step key '{k}'")
        return key_to_uuid[k]

    for e in edges:
        eid = new_uuid()
        parent = e.get("parentKey")
        graph_edges[eid] = {
            "id": eid,
            "name": e.get("edgeName", ""),
            "description": "",
            "parentNodeId": kid(parent) if parent else "",
            "fromNodeId": kid(e["from"]),
            "toNodeId": kid(e.get("to", "")),
        }
        if e.get("label"):
            edge_label_to_id[e["label"]] = eid

    # nodes: one per step key (incl trigger), parentNodeId from any edge that nests it
    graph_nodes: dict[str, dict] = {}
    parent_of: dict[str, str] = {}
    for e in edges:
        if e.get("parentKey") and e.get("to"):
            parent_of[e["to"]] = e["parentKey"]
    for key, node_uuid in key_to_uuid.items():
        pk = parent_of.get(key)
        graph_nodes[node_uuid] = {
            "id": node_uuid,
            "parentNodeId": key_to_uuid[pk] if pk else "",
        }
    return graph_nodes, graph_edges, edge_label_to_id


# --------------------------------------------------------------------------------------
# Top-level build
# --------------------------------------------------------------------------------------
def build_workflow(plan: dict) -> dict:
    if "trigger" not in plan:
        raise PlanError("plan requires a 'trigger'")
    if "steps" not in plan:
        raise PlanError("plan requires 'steps' (may be empty list)")

    trigger = plan["trigger"]
    trigger_key = trigger.get("key", "$trigger_step")

    # Assign node UUIDs to trigger + steps
    key_to_uuid: dict[str, str] = {trigger_key: new_uuid()}
    for s in plan["steps"]:
        if "key" not in s:
            raise PlanError(f"every step needs a 'key': {s}")
        if s["key"] in key_to_uuid:
            raise PlanError(f"duplicate step key '{s['key']}'")
        key_to_uuid[s["key"]] = new_uuid()

    trigger_uuid = new_uuid()

    # Edges default to a linear chain trigger -> step0 -> step1 ... -> end
    edges = plan.get("edges")
    if edges is None:
        edges = _linear_edges(trigger_key, [s["key"] for s in plan["steps"]])

    graph_nodes, graph_edges, edge_label_to_id = build_graph_and_edges(
        edges, key_to_uuid, trigger_key
    )

    # Steps dict
    steps: dict[str, dict] = {}
    trig_node = key_to_uuid[trigger_key]
    steps[trig_node] = build_trigger_step(trigger, trig_node, trigger_uuid)
    for s in plan["steps"]:
        nid = key_to_uuid[s["key"]]
        steps[nid] = build_step(s, nid, key_to_uuid, trigger_key, edge_label_to_id)

    wfv = {
        "name": plan["name"],
        "type": "runnable",
        "version": plan.get("version", ""),
        "description": plan.get("description", ""),
        "graph": {"edges": graph_edges, "nodes": graph_nodes},
        "steps": steps,
        "tags": plan.get("tags", None),
        "humanCostSeconds": plan.get("humanCostSeconds", 0),
        "humanCostDisplayUnit": plan.get("humanCostDisplayUnit", "minutes"),
    }
    # parameters (workflow-level definitionSchema)
    params_def = plan.get("parameters")
    if params_def:
        wfv["parameters"] = {"definitionSchema": _build_definition_schema(params_def)}
    wfv["summary"] = plan.get("summary", "")

    kom = {
        "kom": {
            "komandVersion": plan.get("komandVersion", KOMAND_VERSION),
            "komFileVersion": "2.0.0",
            "exportedAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "workflowVersions": [wfv],
            "triggers": [build_trigger_entry(trigger, trigger_uuid)],
        }
    }
    validate_structure(kom["kom"], trigger_uuid, trig_node)
    return kom


def _linear_edges(trigger_key: str, step_keys: list[str]) -> list[dict]:
    chain = [trigger_key] + step_keys
    edges = []
    for i in range(len(chain) - 1):
        edges.append({"from": chain[i], "to": chain[i + 1]})
    if step_keys:
        edges.append({"from": step_keys[-1], "to": ""})
    else:
        edges.append({"from": trigger_key, "to": ""})
    return edges


def _build_definition_schema(params_def: dict) -> dict:
    """params_def: {"Param Name": {"type":..,"description":..}} -> definitionSchema block."""
    properties = {}
    required = []
    for name, spec in params_def.items():
        prop = {"type": spec.get("type", "string"), "description": spec.get("description", "")}
        properties[name] = prop
        if spec.get("required", True):
            required.append(name)
    return {
        "type": "object",
        "required": required,
        "properties": properties,
        "definitions": {},
    }


# --------------------------------------------------------------------------------------
# Validation
# --------------------------------------------------------------------------------------
def validate_structure(kom: dict, trigger_uuid: str, trig_node: str) -> None:
    errors = []
    wfv = kom["workflowVersions"][0]
    steps = wfv["steps"]
    nodes = wfv["graph"]["nodes"]
    edges = wfv["graph"]["edges"]

    if len(nodes) != len(steps):
        errors.append(f"node count {len(nodes)} != step count {len(steps)}")
    for nid in nodes:
        if nid not in steps:
            errors.append(f"graph node {nid} has no matching step")
    for nid in steps:
        if nid not in nodes:
            errors.append(f"step {nid} has no matching graph node")

    node_ids = set(nodes) | {""}
    for eid, e in edges.items():
        if e["fromNodeId"] not in node_ids:
            errors.append(f"edge {eid} fromNodeId not a node: {e['fromNodeId']}")
        if e["toNodeId"] not in node_ids:
            errors.append(f"edge {eid} toNodeId not a node: {e['toNodeId']}")

    # trigger sync
    if steps[trig_node].get("triggerId") != trigger_uuid:
        errors.append("trigger step triggerId != trigger entry id")
    if kom["triggers"][0]["id"] != trigger_uuid:
        errors.append("trigger entry id mismatch")

    # schema-nullness invariants
    for nid, st in steps.items():
        t = st["type"]
        oj = st.get("outputJSONSchema", "MISSING")
        if t in OBJECT_OUTPUT_TYPES and not isinstance(oj, dict):
            errors.append(f"step {nid} ({t}) outputJSONSchema must be an object, got {oj!r}")
        if t in NATIVE_STEP_TYPES - OBJECT_OUTPUT_TYPES and oj is not None:
            errors.append(f"step {nid} ({t}) outputJSONSchema must be null, got {oj!r}")

    if errors:
        raise PlanError("Structural validation failed:\n  - " + "\n  - ".join(errors))


# --------------------------------------------------------------------------------------
# Example plan
# --------------------------------------------------------------------------------------
EXAMPLE_PLAN = {
    "name": "Enrich Hash and Post to Teams",
    "description": "Look up a file hash reputation and post the result to Microsoft Teams.",
    "humanCostSeconds": 300,
    "parameters": {
        "Teams Channel": {"type": "string", "description": "Target Teams channel name"},
        "Teams Team": {"type": "string", "description": "Target Teams team name"},
    },
    "trigger": {
        "key": "trigger",
        "kind": "api",
        "name": "API Trigger",
        "input": None,
        "inputJsonSchema": {"properties": {"hash": {"type": "string"}}},
        "outputJsonSchema": {"properties": {"hash": {"type": "string"}}},
    },
    "steps": [
        {
            "key": "lookup",
            "type": "action",
            "name": "Lookup Hash",
            "plugin": {"slugName": "virustotal", "slugVersion": "5.1.4", "name": "VirusTotal"},
            "identifier": "lookup_hash",
            "input": {"hash": "{{$trigger.hash}}"},
            "defaultInputJSONSchema": {"properties": {"hash": {"type": "string"}}},
            "defaultOutputJSONSchema": {"properties": {"positives": {"type": "integer"}}},
        },
        {
            "key": "notify",
            "type": "action",
            "name": "Send HTML Message",
            "plugin": {"slugName": "microsoft_teams", "slugVersion": "6.2.0", "name": "Microsoft Teams"},
            "identifier": "send_html_message",
            "input": {
                "channel_name": "{{$workflow.Teams Channel}}",
                "team_name": "{{$workflow.Teams Team}}",
                "message_content": "Hash reputation positives: {{lookup.positives}}",
                "thread_id": "",
            },
            "defaultInputJSONSchema": {"properties": {
                "channel_name": {"type": "string"}, "team_name": {"type": "string"},
                "message_content": {"type": "string"}, "thread_id": {"type": "string"},
            }},
            "defaultOutputJSONSchema": {"properties": {"status": {"type": "string"}}},
        },
        {
            "key": "card",
            "type": "artifact",
            "name": "Summary",
            "content": "## Result\nPositives: `{{lookup.positives}}`",
        },
    ],
    # edges omitted -> auto linear: trigger -> lookup -> notify -> card -> end
}


# --------------------------------------------------------------------------------------
# Bundle generation
# --------------------------------------------------------------------------------------
# Canonical extension.png location (relative to this script's repo, assuming sibling repos).
EXTENSION_PNG_SOURCE = Path(__file__).resolve().parent.parent.parent / "insightconnect-workflows" / "workflows" / "Hello_World" / "extension.png"

# Approved use_cases the validator accepts (lowercase_snake).
APPROVED_USE_CASES = {
    "alerting_and_notifications", "application_development", "asset_management",
    "case_management", "cloud_service_provider", "cloud_security", "collaboration",
    "credential_management", "database", "endpoint_detection_response",
    "endpoint_management", "external_attack_surface", "iam", "network_firewall",
    "phishing", "privileged_access_management", "remediation_management",
    "security_operations", "threat_intel", "ticketing", "utility", "vulnerability_management",
}


def _dir_name(plan_name: str) -> str:
    """Snake_Case_With_Capitals directory name from the workflow name."""
    return re.sub(r"[^A-Za-z0-9]+", "_", plan_name).strip("_")


def _extract_plugins(kom: dict) -> list[dict]:
    """Derive plugin utilization list [{name, version, count}] from the built .icon.

    The validator counts plugins appearing in steps (including the trigger step if it has a
    plugin object). It does NOT separately count the top-level triggers[] array entry.
    """
    wfv = kom["kom"]["workflowVersions"][0]
    counts: dict[str, dict] = {}  # key = slug -> {name, version, count}
    for step in wfv["steps"].values():
        plugin = step.get("plugin")
        if not isinstance(plugin, dict):
            continue
        slug = plugin.get("slugName", "")
        if slug not in counts:
            counts[slug] = {
                "name": plugin.get("name", slug),
                "version": plugin.get("slugVersion", ""),
                "count": 0,
            }
        counts[slug]["count"] += 1
    return list(counts.values())


def _generate_help_md(plan: dict, plugins: list[dict]) -> str:
    """Generate a valid help.md from plan metadata and derived plugin list."""
    name = plan["name"]
    desc = plan.get("help_description") or plan.get("description") or f"Workflow: {name}"
    # Strip markdown from description for the short blurb if it's full-form
    short_desc = desc.split("\n")[0] if "\n" in desc else desc

    features = plan.get("help_features") or [
        "Automated workflow triggered by platform events",
        "Enriches data from multiple sources",
        "Posts results for team visibility",
    ]
    requirements = plan.get("help_requirements") or _derive_requirements(plugins)
    setup = plan.get("help_setup") or _derive_setup(plan)
    troubleshooting = plan.get("help_troubleshooting") or (
        "_There is no troubleshooting information at this time._"
    )
    links = plan.get("help_links") or []

    plugin_table = "|Plugin|Version|Count|\n|----|----|--------|\n"
    for p in plugins:
        plugin_table += f"|{p['name']}|{p['version']}|{p['count']}|\n"

    sections = [
        f"# Description\n\n{short_desc}",
        "# Key Features\n\n" + "\n".join(f"* {f}" for f in features),
        "# Requirements\n\n" + "\n".join(f"* {r}" for r in requirements),
        "# Documentation\n\n## Setup\n\n" + setup,
        "## Technical Details\n\nPlugins utilized by workflow:\n\n" + plugin_table,
        "## Troubleshooting\n\n" + troubleshooting,
        "# Version History\n\n* 1.0.0 - Initial workflow",
    ]
    if links:
        refs = "\n".join(f"* [{l['title']}]({l['url']})" for l in links)
        sections.append(f"# Links\n\n## References\n\n{refs}")
    else:
        sections.append("# Links\n\n## References\n")

    return "\n\n".join(sections) + "\n"


def _derive_requirements(plugins: list[dict]) -> list[str]:
    reqs = []
    for p in plugins:
        reqs.append(f"{p['name']} connection configured")
    reqs.append("InsightConnect")
    return reqs


def _derive_setup(plan: dict) -> str:
    lines = [
        "Import the workflow from the Rapid7 Extension Library and proceed through the "
        "Import Workflow wizard in InsightConnect. Import plugins, create or select connections, "
        "and rename the workflow as necessary."
    ]
    params = plan.get("parameters")
    if params:
        lines.append("")
        lines.append(
            "This workflow leverages InsightConnect's Parameters feature. "
            "Configure the following parameters:"
        )
        lines.append("")
        for pname, pspec in params.items():
            desc = pspec.get("description", "")
            lines.append(f"* {pname}: {desc}")
        lines.append("")
        lines.append("After configuring connections and parameters, activate the workflow.")
    else:
        lines.append("\nAfter configuring connections, activate the workflow.")
    return "\n".join(lines)


def _generate_spec_yaml(plan: dict, dir_name: str, plugins: list[dict]) -> str:
    """Generate a valid workflow.spec.yaml."""
    title = plan["name"]
    desc = plan.get("spec_description") or plan.get("description", "").split("\n")[0]
    # Validator requires description ends with a period
    if desc and not desc.endswith("."):
        desc = desc.rstrip() + "."
    version = plan.get("spec_version", "1.0.0")

    # use_cases: from plan or derive from plugins
    use_cases = plan.get("use_cases")
    if not use_cases:
        use_cases = ["security_operations"]
    # validate
    use_cases = [uc for uc in use_cases if uc in APPROVED_USE_CASES]
    if not use_cases:
        use_cases = ["security_operations"]

    # keywords
    keywords = plan.get("keywords")
    if not keywords:
        keywords = list({p.get("slugName", "") for p in
                        (plan.get("trigger", {}).get("plugin") or {},
                         *(s.get("plugin") or {} for s in plan.get("steps", [])))
                        if p.get("slugName")})
    has_params = bool(plan.get("parameters"))
    if has_params and "parameters" not in keywords:
        keywords.append("parameters")

    # products: always insightconnect, derive from plugin names
    products = ["insightconnect"]
    hub_products = ["insightconnect"]
    slug_to_product = {
        "rapid7_insightidr": "insightidr",
        "rapid7_insightvm": "insightvm",
    }
    for p in plugins:
        slug = next(
            (s.get("plugin", {}).get("slugName", "")
             for s in plan.get("steps", []) if s.get("plugin", {}).get("name") == p["name"]),
            "",
        )
        if slug in slug_to_product:
            hub_products.append(slug_to_product[slug])
            if slug_to_product[slug] not in products:
                products.append(slug_to_product[slug])

    # vendors (from plugins)
    vendors = list({p.get("name", "").split()[0].lower() for p in plugins if p.get("name")})

    lines = [
        f"extension: workflow",
        f"products: {json.dumps(products)}",
        f"name: {dir_name}",
        f'title: "{title}"',
        f'description: "{desc}"',
        f"version: {version}",
        f"vendor: rapid7",
        f"support: rapid7",
        f"status: []",
        f"hub_tags:",
        f"  use_cases: {json.dumps(use_cases)}",
        f"  keywords: {json.dumps(keywords)}",
        f"  features: []",
        f"  vendors: {json.dumps(vendors)}",
        f"  products: {json.dumps(hub_products)}",
        f"resources:",
        f"  source_url: https://github.com/rapid7/insightconnect-workflows/tree/master/workflows/{dir_name}",
        f"  license_url: https://github.com/rapid7/insightconnect-workflows/blob/master/LICENSE",
        f"  screenshots:",
        f"  - name: workflow.png",
        f"    title: Workflow Builder View",
    ]
    return "\n".join(lines) + "\n"


def build_bundle(plan: dict, kom: dict, out_dir: Path | None = None) -> Path:
    """Generate the complete 5-file bundle directory. Returns the bundle path."""
    dir_name = _dir_name(plan["name"])
    bundle = (out_dir or Path.cwd()) / dir_name
    bundle.mkdir(parents=True, exist_ok=True)
    screenshots = bundle / "screenshots"
    screenshots.mkdir(exist_ok=True)

    # 1. .icon file
    icon_path = bundle / f"{dir_name}.icon"
    icon_path.write_text(json.dumps(kom, indent=2), encoding="utf-8")

    # 2. extension.png (canonical)
    ext_dst = bundle / "extension.png"
    if EXTENSION_PNG_SOURCE.exists():
        import shutil
        shutil.copy2(EXTENSION_PNG_SOURCE, ext_dst)
    else:
        # create a minimal placeholder
        ext_dst.write_bytes(b"")
        print(f"  WARNING: canonical extension.png not found at {EXTENSION_PNG_SOURCE}", file=sys.stderr)

    # 3. screenshots/workflow.png (placeholder)
    ss_path = screenshots / "workflow.png"
    if not ss_path.exists():
        import shutil
        if EXTENSION_PNG_SOURCE.exists():
            shutil.copy2(EXTENSION_PNG_SOURCE, ss_path)
        else:
            ss_path.write_bytes(b"")

    # 4. help.md
    plugins = _extract_plugins(kom)
    help_md = _generate_help_md(plan, plugins)
    (bundle / "help.md").write_text(help_md, encoding="utf-8")

    # 5. workflow.spec.yaml
    spec_yaml = _generate_spec_yaml(plan, dir_name, plugins)
    (bundle / "workflow.spec.yaml").write_text(spec_yaml, encoding="utf-8")

    return bundle


def run_icon_validate(bundle_path: Path) -> tuple[bool, str]:
    """Run icon-validate on the bundle. Returns (passed, output)."""
    import subprocess
    try:
        result = subprocess.run(
            ["icon-validate", bundle_path.name],
            cwd=str(bundle_path.parent),
            capture_output=True,
            text=True,
            timeout=30,
        )
        output = result.stdout + result.stderr
        passed = "successfully validated" in output
        return passed, output
    except FileNotFoundError:
        return False, "icon-validate not found on PATH"
    except subprocess.TimeoutExpired:
        return False, "icon-validate timed out"


def main() -> int:
    ap = argparse.ArgumentParser(description="Deterministic InsightConnect .icon generator")
    ap.add_argument("plan", nargs="?", help="Path to a workflow plan JSON file")
    ap.add_argument("-o", "--out", help="Output .icon path (default: <Name>.icon)")
    ap.add_argument("--bundle", action="store_true",
                    help="Generate a full 5-file bundle directory (icon + help.md + spec + "
                         "extension.png + screenshots/) and run icon-validate")
    ap.add_argument("--bundle-dir", help="Parent directory for the bundle (default: cwd)")
    ap.add_argument("--no-validate", action="store_true",
                    help="Skip icon-validate when using --bundle")
    ap.add_argument("--example", action="store_true", help="Print the example plan and exit")
    ap.add_argument("--check-only", action="store_true", help="Build+validate but do not write")
    args = ap.parse_args()

    if args.example:
        print(json.dumps(EXAMPLE_PLAN, indent=2))
        return 0

    if args.plan:
        plan = json.loads(Path(args.plan).read_text(encoding="utf-8"))
    else:
        print("No plan given; building the built-in example.", file=sys.stderr)
        plan = EXAMPLE_PLAN

    try:
        kom = build_workflow(plan)
    except PlanError as exc:
        print(f"PLAN ERROR: {exc}", file=sys.stderr)
        return 2

    if args.check_only:
        print("OK: plan builds and passes structural validation.")
        return 0

    if args.bundle:
        out_dir = Path(args.bundle_dir) if args.bundle_dir else None
        bundle = build_bundle(plan, kom, out_dir)
        print(f"Bundle created: {bundle}/")
        for f in sorted(bundle.rglob("*")):
            if f.is_file():
                print(f"  {f.relative_to(bundle)}")

        if not args.no_validate:
            print("\nRunning icon-validate...")
            passed, output = run_icon_validate(bundle)
            # Print last few meaningful lines
            lines = [l for l in output.splitlines() if l.strip()]
            for l in lines[-10:]:
                print(f"  {l}")
            if passed:
                print("\n✓ Bundle passed icon-validate.")
                return 0
            else:
                print("\n✗ Bundle failed icon-validate. Fix issues above and re-run.")
                return 1
        return 0

    out = args.out or (_dir_name(plan["name"]) + ".icon")
    Path(out).write_text(json.dumps(kom, indent=2), encoding="utf-8")
    print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
