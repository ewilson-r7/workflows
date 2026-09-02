# InsightConnect Workflow Builder

Deterministic workflow generation for Rapid7 InsightConnect. Describe an automation in plain language, get a validated, import-ready `.icon` bundle.

## Setup

1. Clone this repo alongside the plugin and workflow repos:
   ```
   Documents/GitHub/
   ├── workflows/                  ← this repo
   ├── insightconnect-plugins/     ← https://github.com/rapid7/insightconnect-plugins
   ├── komand-plugins/             ← https://github.com/rapid7/komand-plugins
   └── insightconnect-workflows/   ← https://github.com/rapid7/insightconnect-workflows
   ```

2. Open this repo in Kiro. The `.kiro/skills/workflow-builder/SKILL.md` skill activates automatically when you describe a workflow to build.

3. Ensure `icon-validate` is installed:
   ```bash
   pip install insightconnect-integrations-validators
   # If you get pkg_resources errors: pip install "setuptools<81"
   ```

## Usage

In Kiro, describe what you want:

> Build a workflow that triggers on new IDR investigations, checks if the title matches "Alert XYZ", and posts to Teams if it does.

The skill reasons out a plan, looks up real plugin schemas from `origin/master`, and runs the deterministic generator to produce a validated bundle in `output/`.

### Direct script usage

```bash
# Generate from a plan file
python3 scripts/build_workflow.py plans/my_plan.json --bundle --bundle-dir output/

# Validate a plan without generating
python3 scripts/build_workflow.py plans/my_plan.json --check-only

# Print the example plan format
python3 scripts/build_workflow.py --example
```

## Regenerating catalogs

When the `insightconnect-workflows` repo updates with new workflows:

```bash
python3 analysis/analyze_workflows.py --repo ../insightconnect-workflows
python3 analysis/build_catalogs.py
python3 analysis/extract_templates.py
```

## Structure

```
.kiro/skills/workflow-builder/SKILL.md     Build a validated .icon bundle (auto-activates)
.kiro/skills/workflow-submission/SKILL.md  Submit a bundle to insightconnect-workflows
.kiro/steering/     Scoped steering (activates when .icon files are in context)
scripts/            Deterministic .icon generator
analysis/           Corpus analysis and catalog generation scripts
references/         Hand-crafted rules + knowledge base
references/generated/  Evidence-based catalogs derived from 234 real workflows
plans/              Example workflow plans (IR format)
output/             Generated bundles land here
```
