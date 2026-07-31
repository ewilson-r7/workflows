#!/usr/bin/env python3
"""
Extract real, representative step + trigger skeletons from known-good workflows.

For each distinct step `type` and each distinct trigger-array `type`, pull one real example
straight out of the corpus (UUIDs and mapped values left intact so the shape is exact) and save
them as machine-readable templates. These give the workflow-builder deterministic, copy-exact
skeletons to assemble from, rather than hand-written guesses.

Selection heuristic: for each type, choose the SMALLEST real example (fewest characters) so the
template is the cleanest minimal shape. For plugin `action`/`trigger` steps we additionally keep
one example per plugin::identifier so the builder can copy the exact input shape for a given action.

Output (../references/generated/):
  step_templates.json      one minimal example per step type
  trigger_templates.json   one minimal example per trigger-array type
  action_templates.json    one example per plugin::identifier (action & plugin-trigger steps)
"""

from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent / "insightconnect-workflows" / "workflows"
OUT = Path(__file__).parent.parent / "references" / "generated"


def iter_icons():
    for p in sorted(REPO.rglob("*.icon")):
        try:
            yield p, json.loads(p.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            continue


def size(obj) -> int:
    return len(json.dumps(obj))


def main() -> int:
    step_by_type: dict[str, dict] = {}
    step_src: dict[str, str] = {}
    trig_by_type: dict[str, dict] = {}
    trig_src: dict[str, str] = {}
    action_by_key: dict[str, dict] = {}
    action_src: dict[str, str] = {}

    for path, data in iter_icons():
        kom = data.get("kom", {})
        for wfv in kom.get("workflowVersions", []) or []:
            for step in (wfv.get("steps", {}) or {}).values():
                if not isinstance(step, dict):
                    continue
                stype = str(step.get("type"))
                # smallest example per type
                if stype not in step_by_type or size(step) < size(step_by_type[stype]):
                    step_by_type[stype] = step
                    step_src[stype] = path.name
                # per plugin::identifier for plugin steps
                plugin = step.get("plugin")
                ident = step.get("action") or step.get("identifier")
                if isinstance(plugin, dict) and ident:
                    key = f"{plugin.get('slugName')}::{ident}"
                    if key not in action_by_key or size(step) < size(action_by_key[key]):
                        action_by_key[key] = step
                        action_src[key] = path.name

        for trig in kom.get("triggers", []) or []:
            if not isinstance(trig, dict):
                continue
            ttype = str(trig.get("type"))
            if ttype not in trig_by_type or size(trig) < size(trig_by_type[ttype]):
                trig_by_type[ttype] = trig
                trig_src[ttype] = path.name

    OUT.mkdir(parents=True, exist_ok=True)

    step_out = {
        t: {"_source_workflow": step_src[t], "template": s}
        for t, s in sorted(step_by_type.items())
    }
    trig_out = {
        t: {"_source_workflow": trig_src[t], "template": s}
        for t, s in sorted(trig_by_type.items())
    }
    action_out = {
        k: {"_source_workflow": action_src[k], "template": s}
        for k, s in sorted(action_by_key.items())
    }

    (OUT / "step_templates.json").write_text(json.dumps(step_out, indent=2), encoding="utf-8")
    (OUT / "trigger_templates.json").write_text(json.dumps(trig_out, indent=2), encoding="utf-8")
    (OUT / "action_templates.json").write_text(json.dumps(action_out, indent=2), encoding="utf-8")

    print(f"step types: {len(step_out)} -> step_templates.json")
    print(f"trigger types: {len(trig_out)} -> trigger_templates.json")
    print(f"plugin action/trigger shapes: {len(action_out)} -> action_templates.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
