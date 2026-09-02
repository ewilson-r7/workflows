---
name: workflow-submission
description: Submit InsightConnect workflows to the rapid7/insightconnect-workflows repository. Covers new submissions and updates to existing ones, including normalizing the .icon file, writing help.md and workflow.spec.yaml, choosing approved keywords and use cases, running icon-validate, and preparing the branch and commit. Use when asked to submit, contribute, publish, or update a workflow in the workflows repo, and when icon-validate errors need diagnosing.
---

# Workflow Submission

Submit workflows to `insightconnect-workflows`, the repository of pre-built automation
workflows for the InsightConnect SOAR platform.

This skill covers publishing an existing `.icon` bundle. To build a bundle from a plain-language
description first, use the `workflow-builder` skill, then return here to submit it.

## Repository location

All git commands below target the upstream workflows repo as a sibling checkout:

```
Documents/GitHub/
├── workflows/                  ← this repo
└── insightconnect-workflows/   ← https://github.com/rapid7/insightconnect-workflows
```

Prefix git commands with `-C ../insightconnect-workflows` so the working directory of this repo
is never disturbed. If the checkout lives elsewhere, substitute its path.

## New workflow submissions

1. **Analyze the `.icon` file.** Extract the workflow name and description, the plugins in use
   (`slugName` and `slugVersion`), the step names, the trigger type, and any parameters under
   `parameters.definitionSchema.properties`.

2. **Branch from master**, publishing the branch before committing so the remote exists:

   ```bash
   git -C ../insightconnect-workflows checkout master
   git -C ../insightconnect-workflows checkout -b <descriptive-branch-name>
   git -C ../insightconnect-workflows push -u origin <descriptive-branch-name>
   ```

3. **Create the directory structure:**

   ```
   workflows/<Workflow_Name>/
   ├── <Workflow_Name>.icon
   ├── help.md
   ├── workflow.spec.yaml
   ├── extension.png          # placeholder until a real image is supplied
   └── screenshots/
       └── workflow.png       # placeholder until a real screenshot is supplied
   ```

4. **Normalize the `.icon` file before copying it in.** These fields fail validation when left
   as exported:

   - set `kom.komandVersion` to `"2.0.0"` when empty
   - set the workflow `description` when empty
   - set the workflow `name` to match the new directory name
   - replace null `inputJsonSchema` and `outputJsonSchema` in `kom.triggers[]` with
     `{"properties": {}, "title": "Variables", "type": "object"}`
   - replace null schemas in trigger steps (`defaultInputJSONSchema`,
     `defaultOutputJSONSchema`, and siblings)
   - correct title casing in step names

5. **Write `help.md`** with these sections, in order: `# Description` (five sentences at most),
   `# Key Features`, `# Requirements`, `# Documentation` (containing `## Setup`, `### Usage`,
   `## Technical Details`, `## Troubleshooting`), `# Version History` starting at
   `* 1.0.0 - Initial workflow`, and `# Links` with a `## References` subsection. A full
   template appears at the end of this file.

6. **Write `workflow.spec.yaml`:**

   ```yaml
   extension: workflow
   products: ["insightconnect"]
   name: <Directory_Name>
   title: "<Human Readable Title>"
   description: "<two-sentence description>"
   version: 1.0.0
   vendor: rapid7
   support: rapid7
   status: []
   hub_tags:
     use_cases: [<approved_use_case>]
     keywords: [<approved_keywords>]
     features: []
     vendors: [<vendor_names>]
     products: [<product_names>]
   resources:
     source_url: https://github.com/rapid7/insightconnect-workflows/tree/master/workflows/<Directory_Name>
     license_url: https://github.com/rapid7/insightconnect-workflows/blob/master/LICENSE
     screenshots:
     - name: workflow.png
       title: Workflow Builder View
   ```

7. **Validate:**

   ```bash
   icon-validate workflows/<Workflow_Name>
   ```

   If `icon-validate` is missing, install it with
   `pip install insightconnect-integrations-validators`. On a `pkg_resources` error, pin
   `pip install "setuptools<81"`.

8. **Commit and push:**

   ```bash
   git -C ../insightconnect-workflows add workflows/<Workflow_Name>/
   git -C ../insightconnect-workflows commit -m "Add <Workflow Title> workflow"
   git -C ../insightconnect-workflows push
   ```

## Workflow updates

1. Branch from master, as above.

2. **Identify what changed.** Diff the new `.icon` against the existing one and note plugin
   version changes and new or modified steps.

3. **Replace the `.icon` file** with the new export, then apply every normalization from step 4
   above. A fresh export reintroduces the same defects each time.

4. **Update `help.md`:** plugin versions in the Technical Details table, Setup and Usage when
   behavior changed, and Key Features when capabilities were added.

5. **Bump `version` in `workflow.spec.yaml`** following semver:

   | Increment | When |
   |---|---|
   | Major (`x.0.0`) | Breaking changes or replaced workflow logic |
   | Minor (`1.x.0`) | New capabilities, added steps, new parameters |
   | Patch (`1.0.x`) | Bug fixes, plugin version bumps, minor tweaks |

6. **Prepend a version history entry** to `help.md`, newest first:

   ```markdown
   * 2.0.0 - Added support for Linux and Android analysis
   * 1.1.0 - Updated plugin versions, added PCAP attachment option
   * 1.0.0 - Initial workflow
   ```

7. Validate and commit, as above.

## Naming conventions

- Directory name uses `Snake_Case_With_Capitals`, for example
  `Enrich_InsightIDR_Investigation_with_ANYRUN`
- The `.icon` filename matches the directory name exactly, plus the `.icon` extension
- `name` in `workflow.spec.yaml` matches the directory name exactly
- `title` is human readable with normal capitalization

### Title casing in step names

Validation rejects lowercase words that should be capitalized. Capitalize nouns and verbs
generally, and these in particular: Analysis, Attachment, Comment, Investigation, Report,
PCAP, IOCs.

## Approved vocabulary

Keywords and use cases are validated against the Extension Library, so values outside these
lists fail. Confirm against the upstream repo when a needed term is absent rather than
inventing one.

**Keywords:** `chat`, `chatops`, `parameters`, `work_from_home`, `enrichment`, `containment`,
`quarantine`, `blacklist`, `firewall`, `edr`, `mdr`, `cloud_enabled`, `hash`, `url`,
`ip_address`, `ioc`, `email`, `slack`, `teams`, `microsoft_teams`, `active_directory`, `ldap`,
`azure`

**Use cases:** `threat_intel`, `threat_detection_and_response`, `vulnerability_management`,
`asset_management`, `endpoint_detection_response`, `network_firewall`,
`alerting_and_notifications`, `ticketing`, `phishing`, `iam`, `utility`

### The parameters keyword rule

When the `.icon` file contains a `parameters` field, include the `parameters` keyword in
`workflow.spec.yaml`. This holds even when `definitionSchema` is null or empty, because the
validator checks for the field's presence rather than its contents.

## Extracting plugin data from a .icon file

Plugin versions:

```python
import re
for m in re.finditer(r'"slugName":\s*"([^"]+)",\s*"slugVersion":\s*"([^"]+)"', content):
    print(f'{m.group(1)}: {m.group(2)}')
```

Plugin display names and usage counts. `WorkflowHelpPluginUtilizationValidator` matches on
`plugin.name`, not `slugName`, so the Technical Details table must use the display name:

```python
plugins = {}
for step_id, step in steps.items():
    name = step.get('plugin', {}).get('name', '')
    if name:
        plugins[name] = plugins.get(name, 0) + 1
```

## Setup section wording

- Do not mention an "Import Workflow wizard". No such wizard exists, and referencing it
  misleads the reader.
- With parameters: "After importing the workflow, configure the following parameters: [list].
  Then create or select connections..."
- Without parameters: "After importing the workflow, create or select connections for the
  following plugins..."
- Close with: "Once [parameters and] connections are configured, activate the workflow..."

## Validation checklist

Confirm before declaring the submission complete:

- [ ] `icon-validate` passes with no errors
- [ ] Directory name matches the `.icon` filename without its extension
- [ ] Directory name matches `name` in `workflow.spec.yaml`
- [ ] Step names use correct title casing
- [ ] Plugin versions in `help.md` match the `.icon` file
- [ ] `parameters` keyword present when the workflow uses parameters
- [ ] Every keyword and use case comes from the approved lists
- [ ] `source_url` points at the correct directory
- [ ] Version history is present and accurate

## Validation errors and their fixes

| Error | Fix |
|-------|-----|
| `komandVersion key is not defined` | Set `data['kom']['komandVersion'] = '2.0.0'` |
| `Title contains a lowercase 'X'` | Correct title casing in step names |
| `Workflow description cannot be blank` | Set `wf['description']` in the `.icon` file |
| `inputJsonSchema should be TriggersInputJsonSchema` | Replace null schemas in `kom.triggers[]` |
| `parameters keyword not present` | Add `parameters` to keywords in the spec |
| `Unsupported keywords found` | Replace with values from the approved list |
| `Plugin found in .icon but not in help` | Update the Technical Details table |

## Git conventions

- One workflow per branch and per PR
- Branch from `master`, and publish the branch before committing
- Descriptive branch names, for example `anyrun-siem-url-analysis-workflow`
- Commit messages read `Add <Workflow Title> workflow` or `Update <Workflow Title> workflow`

## help.md template

```markdown
# Description

<Brief description of what the workflow does, five sentences at most>

# Key Features

* <Feature 1>
* <Feature 2>
* <Feature 3>

# Requirements

* [Product Name](https://link.to/product)
* [Another Product](https://link.to/product) API credentials

# Documentation

## Setup

Import the workflow from the Rapid7 Extension Library and proceed through the import process in InsightConnect.

After importing the workflow, create or select connections for the following plugins:

* **Plugin Name** - Configure with your API credentials
* **Another Plugin** - Configure with your API key

Once connections are configured, activate the workflow.

### Usage

<How the workflow is triggered and what it does>

## Technical Details

Plugins utilized by workflow:

|Plugin|Version|Count|
|----|----|--------|
|Plugin Name|1.0.0|2|

## Troubleshooting

_There is no troubleshooting information at this time_

# Version History

* 1.0.0 - Initial workflow

# Links

## References

* [Product](https://link.to/product)
```
