#!/usr/bin/env python3
"""
Deterministic analyzer for Rapid7 InsightConnect `.icon` workflow files.

Purpose
-------
Walk every `*.icon` bundle in the local `insightconnect-workflows` repo and derive an
evidence-based description of how known-good workflow files are actually built. The output
is consumed by the `workflow-builder` skill + steering so that workflow generation is a mix
of deterministic scaffolding (this catalog) and abstract reasoning (Kiro).

It answers, purely from real data:
  1. The canonical `.icon` structure: which keys appear at each level and how often.
  2. Built-in / native step types vs plugin-backed steps (actions & triggers).
  3. Per-plugin catalog of the actions and triggers actually used, with version spread.
  4. Schema-nullness rules (e.g. when `outputJSONSchema` is null vs an object) per step type.
  5. Input-configuration themes: when action/trigger `parameters.input` is present, empty,
     populated, and how required vs optional inputs tend to be expressed.
  6. Interpolation / data-mapping conventions ($workflow, $job, UUID refs).

Usage
-----
    python3 analyze_workflows.py [--repo /path/to/insightconnect-workflows] [--out ./output]

No third-party dependencies (stdlib only).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_REPO = str(Path(__file__).resolve().parent.parent.parent / "insightconnect-workflows")

# Step `type` values that are platform/native (no plugin object expected).
NATIVE_STEP_TYPES = {
    "artifact",
    "automated_decision",
    "human_decision",
    "pattern_match",
    "loop",
    "join",
    "filter",
    "trigger",  # native API/scheduled trigger (no plugin)
}

# ChatOps step types are handled specially (Slack/Teams conversational steps).
CHATOPS_STEP_TYPE_RE = re.compile(r"_chatops$")

# Interpolation patterns found in string values.
RE_WORKFLOW_PARAM = re.compile(r"\{\{\[\$workflow\]")
RE_JOB_REF = re.compile(r"\{\{\[\$job\]")
RE_UUID_REF = re.compile(
    r"\{\{\[[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\]"
)
RE_GLOBAL_REF = re.compile(r"\{\{\[\$global\]")


def is_empty_schema(schema: Any) -> bool:
    """An 'empty variables' schema: {properties:{}, ...} with no real props."""
    if not isinstance(schema, dict):
        return False
    props = schema.get("properties")
    return isinstance(props, dict) and len(props) == 0


def schema_state(schema: Any) -> str:
    """Classify a schema field's state."""
    if schema is None:
        return "null"
    if not isinstance(schema, dict):
        return "non_object"
    if is_empty_schema(schema):
        return "empty_object"
    return "populated_object"


def walk_strings(obj: Any):
    """Yield every string value found anywhere in a nested structure."""
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from walk_strings(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from walk_strings(v)


def classify_step_type(step_type: str) -> str:
    """Bucket a step type into native / plugin / chatops."""
    if CHATOPS_STEP_TYPE_RE.search(step_type or ""):
        return "chatops"
    if step_type == "action":
        return "plugin_action"
    if step_type in NATIVE_STEP_TYPES:
        return "native"
    return "other"


class Analysis:
    def __init__(self) -> None:
        # File-level
        self.total_files = 0
        self.parse_errors: list[str] = []

        # Top-level key frequency
        self.kom_keys = Counter()
        self.komfileversion_values = Counter()
        self.komandversion_values = Counter()

        # workflowVersions item keys
        self.wfv_keys = Counter()
        self.wfv_type_values = Counter()
        self.human_cost_units = Counter()
        self.tags_state = Counter()  # null / empty_list / populated
        self.parameters_state = Counter()  # absent / null_defschema / populated_defschema
        self.definition_schema_keys = Counter()

        # Steps
        self.step_type_counts = Counter()          # raw type -> count
        self.step_type_bucket = Counter()          # native/plugin_action/chatops/other
        self.step_keys_by_type = defaultdict(Counter)
        self.connection_type_values = Counter()

        # Schema nullness per step type (the import-breaking rules)
        # {step_type: {field: Counter(state)}}
        self.schema_states = defaultdict(lambda: defaultdict(Counter))

        # Plugin catalog: slug -> info
        # slug -> {"vendor": set, "name": set, "versions": Counter,
        #          "actions": Counter(identifier), "triggers": Counter(identifier)}
        self.plugins: dict[str, dict[str, Any]] = defaultdict(
            lambda: {
                "vendor": set(),
                "display_names": set(),
                "versions": Counter(),
                "actions": Counter(),
                "triggers": Counter(),
            }
        )

        # Action/trigger input configuration
        # key: (slug, identifier, kind) -> stats
        self.io_configs: dict[tuple, dict[str, Any]] = defaultdict(
            lambda: {
                "occurrences": 0,
                "input_present": 0,
                "input_absent": 0,
                "input_empty": 0,
                "input_populated": 0,
                "input_key_freq": Counter(),
                "empty_string_values": 0,
                "interpolated_values": 0,
            }
        )

        # Trigger array (top-level kom.triggers[])
        self.trigger_entry_keys = Counter()
        self.trigger_types = Counter()
        self.trigger_input_state = Counter()  # null / empty_object / populated
        self.trigger_options_present = Counter()
        self.trigger_options_keys = Counter()
        self.trigger_has_plugin = Counter()

        # ChatOps
        self.chatops_app_names = Counter()
        self.chatops_keys = Counter()

        # Interpolation usage (per file, does it use each style)
        self.interp_workflow_param = 0
        self.interp_job = 0
        self.interp_uuid = 0
        self.interp_global = 0

        # Graph shape
        self.node_counts: list[int] = []
        self.step_counts: list[int] = []
        self.edge_counts: list[int] = []
        self.trigger_count_per_wf: list[int] = []

    # ------------------------------------------------------------------
    def analyze_file(self, path: Path) -> None:
        self.total_files += 1
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            self.parse_errors.append(f"{path.name}: {exc}")
            return

        kom = data.get("kom")
        if not isinstance(kom, dict):
            self.parse_errors.append(f"{path.name}: no 'kom' object")
            return

        for k in kom:
            self.kom_keys[k] += 1
        self.komfileversion_values[str(kom.get("komFileVersion"))] += 1
        self.komandversion_values[str(kom.get("komandVersion"))] += 1

        # File-level interpolation scan
        blob_strings = list(walk_strings(kom))
        joined = "\n".join(blob_strings)
        if RE_WORKFLOW_PARAM.search(joined):
            self.interp_workflow_param += 1
        if RE_JOB_REF.search(joined):
            self.interp_job += 1
        if RE_UUID_REF.search(joined):
            self.interp_uuid += 1
        if RE_GLOBAL_REF.search(joined):
            self.interp_global += 1

        for wfv in kom.get("workflowVersions", []) or []:
            self._analyze_wfv(wfv)

        triggers = kom.get("triggers", []) or []
        self.trigger_count_per_wf.append(len(triggers))
        for trig in triggers:
            self._analyze_trigger_entry(trig)

    # ------------------------------------------------------------------
    def _analyze_wfv(self, wfv: dict) -> None:
        if not isinstance(wfv, dict):
            return
        for k in wfv:
            self.wfv_keys[k] += 1
        self.wfv_type_values[str(wfv.get("type"))] += 1
        self.human_cost_units[str(wfv.get("humanCostDisplayUnit"))] += 1

        tags = wfv.get("tags", "__absent__")
        if tags == "__absent__":
            self.tags_state["absent"] += 1
        elif tags is None:
            self.tags_state["null"] += 1
        elif isinstance(tags, list) and not tags:
            self.tags_state["empty_list"] += 1
        else:
            self.tags_state["populated"] += 1

        params = wfv.get("parameters", "__absent__")
        if params == "__absent__":
            self.parameters_state["absent"] += 1
        elif isinstance(params, dict):
            ds = params.get("definitionSchema")
            if ds is None:
                self.parameters_state["null_definitionSchema"] += 1
            elif isinstance(ds, dict):
                if ds.get("properties"):
                    self.parameters_state["populated_definitionSchema"] += 1
                else:
                    self.parameters_state["empty_definitionSchema"] += 1
                for k in ds:
                    self.definition_schema_keys[k] += 1
            else:
                self.parameters_state["other"] += 1
        else:
            self.parameters_state["other"] += 1

        graph = wfv.get("graph") or {}
        self.node_counts.append(len(graph.get("nodes", {}) or {}))
        self.edge_counts.append(len(graph.get("edges", {}) or {}))

        steps = wfv.get("steps", {}) or {}
        self.step_counts.append(len(steps))
        for step in steps.values():
            self._analyze_step(step)

    # ------------------------------------------------------------------
    def _analyze_step(self, step: dict) -> None:
        if not isinstance(step, dict):
            return
        stype = str(step.get("type"))
        self.step_type_counts[stype] += 1
        self.step_type_bucket[classify_step_type(stype)] += 1

        for k in step:
            self.step_keys_by_type[stype][k] += 1

        if "connectionType" in step:
            self.connection_type_values[str(step.get("connectionType"))] += 1

        # Schema nullness rules
        for field in (
            "defaultInputJSONSchema",
            "defaultOutputJSONSchema",
            "outputJSONSchema",
        ):
            if field in step:
                self.schema_states[stype][field][schema_state(step[field])] += 1

        # ChatOps details
        if classify_step_type(stype) == "chatops":
            if "chatOpsAppName" in step:
                self.chatops_app_names[str(step.get("chatOpsAppName"))] += 1
            for k in step:
                if k.startswith("chatOps"):
                    self.chatops_keys[k] += 1

        # Plugin catalog + IO config
        plugin = step.get("plugin")
        if isinstance(plugin, dict):
            slug = str(plugin.get("slugName"))
            info = self.plugins[slug]
            info["vendor"].add(str(plugin.get("slugVendor")))
            info["display_names"].add(str(plugin.get("name")))
            info["versions"][str(plugin.get("slugVersion"))] += 1

            identifier = step.get("action") or step.get("identifier")
            if "trigger" in stype:
                kind = "trigger"
                if identifier:
                    info["triggers"][str(identifier)] += 1
            else:
                kind = "action"
                if identifier:
                    info["actions"][str(identifier)] += 1

            if identifier:
                self._record_io_config(slug, str(identifier), kind, step)

    # ------------------------------------------------------------------
    def _record_io_config(self, slug: str, identifier: str, kind: str, step: dict) -> None:
        key = (slug, identifier, kind)
        cfg = self.io_configs[key]
        cfg["occurrences"] += 1

        params = step.get("parameters")
        inp = None
        if isinstance(params, dict):
            inp = params.get("input")

        if inp is None:
            if isinstance(params, dict) and "input" in params:
                cfg["input_present"] += 1
                cfg["input_empty"] += 1
            else:
                cfg["input_absent"] += 1
            return

        cfg["input_present"] += 1
        if isinstance(inp, dict):
            if not inp:
                cfg["input_empty"] += 1
            else:
                cfg["input_populated"] += 1
                for k, v in inp.items():
                    cfg["input_key_freq"][k] += 1
                    if isinstance(v, str):
                        if v == "":
                            cfg["empty_string_values"] += 1
                        elif "{{" in v:
                            cfg["interpolated_values"] += 1

    # ------------------------------------------------------------------
    def _analyze_trigger_entry(self, trig: dict) -> None:
        if not isinstance(trig, dict):
            return
        for k in trig:
            self.trigger_entry_keys[k] += 1
        self.trigger_types[str(trig.get("type"))] += 1

        inp = trig.get("input", "__absent__")
        if inp == "__absent__":
            self.trigger_input_state["absent"] += 1
        elif inp is None:
            self.trigger_input_state["null"] += 1
        elif isinstance(inp, dict) and not inp:
            self.trigger_input_state["empty_object"] += 1
        else:
            self.trigger_input_state["populated"] += 1

        opts = trig.get("options")
        if opts is None:
            self.trigger_options_present["absent_or_null"] += 1
        else:
            self.trigger_options_present["present"] += 1
            if isinstance(opts, dict):
                for k in opts:
                    self.trigger_options_keys[k] += 1

        self.trigger_has_plugin["yes" if isinstance(trig.get("plugin"), dict) else "no"] += 1

    # ------------------------------------------------------------------
    def summarize_numeric(self, values: list[int]) -> dict:
        if not values:
            return {"count": 0}
        s = sorted(values)
        n = len(s)
        return {
            "count": n,
            "min": s[0],
            "max": s[-1],
            "mean": round(sum(s) / n, 2),
            "median": s[n // 2],
        }

    def to_report(self) -> dict:
        def top(counter: Counter, n: int | None = None) -> dict:
            items = counter.most_common(n)
            return {k: v for k, v in items}

        plugin_catalog = {}
        for slug, info in sorted(self.plugins.items()):
            plugin_catalog[slug] = {
                "vendor": sorted(info["vendor"]),
                "display_names": sorted(info["display_names"]),
                "versions": dict(info["versions"].most_common()),
                "actions": dict(info["actions"].most_common()),
                "triggers": dict(info["triggers"].most_common()),
                "total_action_uses": sum(info["actions"].values()),
                "total_trigger_uses": sum(info["triggers"].values()),
            }

        io_catalog = {}
        for (slug, identifier, kind), cfg in sorted(self.io_configs.items()):
            io_catalog[f"{slug}::{identifier}::{kind}"] = {
                "slug": slug,
                "identifier": identifier,
                "kind": kind,
                "occurrences": cfg["occurrences"],
                "input_present": cfg["input_present"],
                "input_absent": cfg["input_absent"],
                "input_empty": cfg["input_empty"],
                "input_populated": cfg["input_populated"],
                "top_input_keys": dict(cfg["input_key_freq"].most_common(15)),
                "empty_string_values": cfg["empty_string_values"],
                "interpolated_values": cfg["interpolated_values"],
            }

        schema_states = {}
        for stype, fields in sorted(self.schema_states.items()):
            schema_states[stype] = {
                f: dict(states) for f, states in sorted(fields.items())
            }

        step_keys = {}
        for stype, keys in sorted(self.step_keys_by_type.items()):
            step_keys[stype] = dict(keys.most_common())

        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "corpus": {
                "total_icon_files": self.total_files,
                "parse_errors": self.parse_errors,
            },
            "top_level": {
                "kom_keys": dict(self.kom_keys.most_common()),
                "komFileVersion_values": dict(self.komfileversion_values.most_common()),
                "komandVersion_values": dict(self.komandversion_values.most_common()),
            },
            "workflow_version_item": {
                "keys": dict(self.wfv_keys.most_common()),
                "type_values": dict(self.wfv_type_values.most_common()),
                "humanCostDisplayUnit_values": dict(self.human_cost_units.most_common()),
                "tags_state": dict(self.tags_state.most_common()),
                "parameters_state": dict(self.parameters_state.most_common()),
                "definitionSchema_keys": dict(self.definition_schema_keys.most_common()),
            },
            "graph_shape": {
                "nodes_per_workflow": self.summarize_numeric(self.node_counts),
                "edges_per_workflow": self.summarize_numeric(self.edge_counts),
                "steps_per_workflow": self.summarize_numeric(self.step_counts),
                "triggers_per_workflow": self.summarize_numeric(self.trigger_count_per_wf),
            },
            "step_types": {
                "raw_counts": dict(self.step_type_counts.most_common()),
                "bucket_counts": dict(self.step_type_bucket.most_common()),
                "keys_by_type": step_keys,
                "connectionType_values": dict(self.connection_type_values.most_common()),
            },
            "schema_nullness_by_step_type": schema_states,
            "trigger_array_entry": {
                "keys": dict(self.trigger_entry_keys.most_common()),
                "type_values": dict(self.trigger_types.most_common()),
                "input_state": dict(self.trigger_input_state.most_common()),
                "options_present": dict(self.trigger_options_present.most_common()),
                "options_keys": dict(self.trigger_options_keys.most_common()),
                "has_plugin": dict(self.trigger_has_plugin.most_common()),
            },
            "chatops": {
                "app_names": dict(self.chatops_app_names.most_common()),
                "keys": dict(self.chatops_keys.most_common()),
            },
            "interpolation_usage_files": {
                "workflow_param_{{[$workflow]}}": self.interp_workflow_param,
                "job_ref_{{[$job]}}": self.interp_job,
                "uuid_ref": self.interp_uuid,
                "global_ref_{{[$global]}}": self.interp_global,
            },
            "plugin_catalog": plugin_catalog,
            "io_config_catalog": io_catalog,
        }


def main() -> int:
    ap = argparse.ArgumentParser(description="Analyze InsightConnect .icon workflows")
    ap.add_argument("--repo", default=DEFAULT_REPO, help="Path to insightconnect-workflows repo")
    ap.add_argument(
        "--out",
        default=str(Path(__file__).parent / "output"),
        help="Output directory for reports",
    )
    args = ap.parse_args()

    workflows_dir = Path(args.repo) / "workflows"
    if not workflows_dir.is_dir():
        print(f"ERROR: {workflows_dir} not found", file=sys.stderr)
        return 1

    icon_files = sorted(workflows_dir.rglob("*.icon"))
    if not icon_files:
        print(f"ERROR: no .icon files under {workflows_dir}", file=sys.stderr)
        return 1

    analysis = Analysis()
    for path in icon_files:
        analysis.analyze_file(path)

    report = analysis.to_report()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    report_path = out_dir / "structure_report.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    # Console summary
    print(f"Analyzed {report['corpus']['total_icon_files']} .icon files")
    if report["corpus"]["parse_errors"]:
        print(f"  parse errors: {len(report['corpus']['parse_errors'])}")
    print(f"  distinct plugins: {len(report['plugin_catalog'])}")
    print(f"  distinct action/trigger configs: {len(report['io_config_catalog'])}")
    print(f"  step types: {report['step_types']['raw_counts']}")
    print(f"Wrote {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
