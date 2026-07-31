# Description

This workflow creates a Jira ticket and can be executed directly from the Remediation Hub.

A Jira ticket is created and will contain all remediations. The attached CSV file(s) provide a complete list of all impacted assets and remediated vulnerabilities for greater detail.

# Key Features

*  Create a Jira ticket from the Remediation Hub.

# Requirements

* InsightConnect
* [Jira](https://www.atlassian.com/software/jira)

# Documentation

## Setup

Import the workflow from the Rapid7 Extension Library and proceed through the Import Workflow wizard in InsightConnect. Import plugins, create or select connections, and rename the workflow as a part of the Import Workflow wizard as necessary. Don't forget to include a time savings estimate!

## Usage

To use this workflow:

1. Navigate to **Platform Home**.
2. Select **Risk** > **Remediation Hub**.
3. Click on the remediation for which the Jira ticket should be created.
4. Select **Send to Workflow**.
5. Choose **Create Jira Ticket**.
6. Select **Run**.

## Technical Details

Plugins utilized by workflow:

| Plugin | Version | Count |
|----|---------|-------|
|Jira|6.5.2|2|
|CSV|2.0.4|2|


## Troubleshooting

# Version History

* 1.1.0 - Updated Variables in Workflow Due to trigger changes | Updated Plugin versions
* 1.0.0 - Initial workflow

# Links

## References

* [Jira](https://www.atlassian.com/software/jira)