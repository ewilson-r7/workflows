# Plugin Capability Catalog (usage-derived)

82 plugins actually used across the workflow library, ranked by usage. This is a **discovery aid, not a schema source**: it shows which plugin slug + action/trigger identifiers are real and commonly used. Always pull the exact current version and full input/output schema from `plugins/<slug>/plugin.spec.yaml` on `origin/master`.

> Vendor is `rapid7` for the entire first-party library (only exception observed: `automox`). Build the plugin object as `{name, slugVendor, slugName, slugVersion, imageData}`.

| slug | vendor | action uses | trigger uses | #versions | most-common version |
| --- | --- | --- | --- | --- | --- |
| microsoft_teams | rapid7 | 392 | 63 | 15 | 3.1.0 |
| rapid7_insightvm | rapid7 | 100 | 6 | 13 | 4.9.0 |
| rapid7_insightidr | rapid7 | 91 | 1 | 14 | 4.2.0 |
| type_converter | rapid7 | 78 | 0 | 11 | 1.8.2 |
| extractit | rapid7 | 36 | 0 | 6 | 3.0.6 |
| active_directory_ldap | rapid7 | 33 | 0 | 8 | 5.3.5 |
| virustotal | rapid7 | 29 | 0 | 4 | 10.0.0 |
| datetime | rapid7 | 22 | 0 | 6 | 3.0.0 |
| jira | rapid7 | 21 | 0 | 3 | 6.4.0 |
| palo_alto_pan_os | rapid7 | 21 | 0 | 3 | 6.1.1 |
| html | rapid7 | 19 | 0 | 4 | 1.2.2 |
| crowdstrike_falcon | rapid7 | 18 | 0 | 1 | 6.1.2 |
| hashit | rapid7 | 18 | 0 | 5 | 2.0.4 |
| python_3_script | rapid7 | 18 | 0 | 9 | 2.0.2 |
| recorded_future | rapid7 | 18 | 0 | 3 | 5.0.1 |
| math | rapid7 | 17 | 0 | 2 | 1.2.1 |
| rapid7_vulndb | rapid7 | 17 | 0 | 2 | 2.1.1 |
| timers | rapid7 | 6 | 11 | 4 | 2.0.5 |
| servicenow | rapid7 | 15 | 1 | 5 | 8.1.1 |
| microsoft_office365_email | rapid7 | 10 | 5 | 5 | 6.0.0 |
| storage | rapid7 | 15 | 0 | 2 | 1.0.1 |
| microsoft_office365_email_security | rapid7 | 14 | 0 | 4 | 4.0.0 |
| string | rapid7 | 13 | 0 | 2 | 1.4.0 |
| cisco_asa | rapid7 | 12 | 0 | 3 | 1.5.1 |
| fireeye_hx | rapid7 | 12 | 0 | 1 | 2.0.0 |
| sentinelone | rapid7 | 12 | 0 | 3 | 7.1.0 |
| whois | rapid7 | 11 | 0 | 6 | 3.0.3 |
| automox | automox | 10 | 0 | 2 | 1.1.1 |
| carbon_black_response | rapid7 | 10 | 0 | 2 | 3.1.10 |
| csv | rapid7 | 10 | 0 | 4 | 1.1.6 |
| fortinet_fortigate | rapid7 | 10 | 0 | 1 | 6.0.1 |
| microsoft_atp | rapid7 | 10 | 0 | 2 | 4.8.1 |
| sonicwall | rapid7 | 10 | 0 | 2 | 1.3.1 |
| any_run | rapid7 | 9 | 0 | 1 | 3.0.0 |
| zscaler | rapid7 | 9 | 0 | 1 | 1.4.0 |
| azure_ad_admin | rapid7 | 8 | 0 | 3 | 4.0.0 |
| checkpoint_ngfw | rapid7 | 8 | 0 | 1 | 2.0.1 |
| microsoft_sccm | rapid7 | 8 | 0 | 1 | 2.1.2 |
| rapid7_insight_agent | rapid7 | 8 | 0 | 2 | 2.0.1 |
| rest | rapid7 | 8 | 0 | 1 | 4.0.1 |
| threatcrowd | rapid7 | 8 | 0 | 2 | 3.0.0 |
| trendmicro_apex | rapid7 | 8 | 0 | 1 | 3.0.1 |
| broadcom_symantec_endpoint_protection | rapid7 | 6 | 0 | 1 | 1.0.2 |
| cylance_protect | rapid7 | 6 | 0 | 3 | 1.0.3 |
| cymru_malware_hash | rapid7 | 6 | 0 | 3 | 1.1.2 |
| meraki | rapid7 | 6 | 0 | 1 | 4.0.0 |
| palo_alto_cortex_xdr | rapid7 | 6 | 0 | 1 | 4.0.7 |
| base64 | rapid7 | 5 | 0 | 1 | 1.1.6 |
| dig | rapid7 | 5 | 0 | 2 | 2.0.0 |
| gmail | rapid7 | 3 | 2 | 1 | 6.1.0 |
| ipstack | rapid7 | 5 | 0 | 3 | 3.0.1 |
| markdown | rapid7 | 5 | 0 | 2 | 3.1.0 |
| bigfix | rapid7 | 4 | 0 | 1 | 7.0.0 |
| carbon_black_cloud | rapid7 | 4 | 0 | 1 | 1.0.1 |
| darktrace | rapid7 | 4 | 0 | 1 | 2.0.1 |
| jq | rapid7 | 4 | 0 | 1 | 3.0.0 |
| paloalto_wildfire | rapid7 | 4 | 0 | 1 | 2.0.0 |
| sleep | rapid7 | 4 | 0 | 1 | 1.0.2 |
| sophos_central | rapid7 | 4 | 0 | 1 | 4.4.0 |
| trendmicro_deepsecurity | rapid7 | 4 | 0 | 1 | 2.2.1 |
| urlscan | rapid7 | 4 | 0 | 1 | 4.1.1 |
| advanced_regex | rapid7 | 3 | 0 | 1 | 1.0.3 |
| microsoft_exchange | rapid7 | 1 | 2 | 2 | 5.2.0 |
| rapid7_attackerkb | rapid7 | 3 | 0 | 1 | 1.0.3 |
| rapid7_surface_command | rapid7 | 3 | 0 | 2 | 1.1.0 |
| zendesk | rapid7 | 3 | 0 | 1 | 4.0.0 |
| basename | rapid7 | 2 | 0 | 2 | 1.1.0 |
| cybereason | rapid7 | 2 | 0 | 1 | 2.0.1 |
| mimecast | rapid7 | 2 | 0 | 1 | 5.1.0 |
| rapid7_insightvm_cloud | rapid7 | 2 | 0 | 1 | 3.1.0 |
| unshorten | rapid7 | 2 | 0 | 1 | 1.0.5 |
| abuseipdb | rapid7 | 1 | 0 | 1 | 5.1.0 |
| bmc_remedy_itsm | rapid7 | 1 | 0 | 1 | 1.7.0 |
| connectwise | rapid7 | 1 | 0 | 1 | 1.0.0 |
| domaintools_phisheye | rapid7 | 1 | 0 | 1 | 1.0.0 |
| freshdesk | rapid7 | 1 | 0 | 1 | 1.0.0 |
| hybrid_analysis | rapid7 | 1 | 0 | 1 | 3.0.1 |
| ivanti_security_controls | rapid7 | 1 | 0 | 1 | 1.0.0 |
| manage_engine_service_desk | rapid7 | 1 | 0 | 1 | 2.0.0 |
| nasa | rapid7 | 1 | 0 | 1 | 1.0.2 |
| opsgenie | rapid7 | 1 | 0 | 1 | 1.1.1 |
| twilio | rapid7 | 1 | 0 | 1 | 1.0.2 |


## Actions & triggers per plugin

### `microsoft_teams` (Microsoft Teams)
- Actions: send_html_message, send_message
- Triggers: new_message_received

### `rapid7_insightvm` (Rapid7 InsightVM, Rapid7 InsightVM Console)
- Actions: asset_search, get_asset, generate_adhoc_sql_report, get_vulnerability, top_remediations, review_exception, delete_asset, get_vulnerability_affected_assets, tag_asset, get_tags, get_asset_groups, scan, create_tag, get_asset_group_assets, get_sites, list_inactive_assets, get_expiring_vulnerability_exceptions, get_asset_group, get_user, get_asset_tags, get_site, get_scan, update_scan_status, update_asset_group_search_criteria, create_asset_group, delete_exception, get_tag_assets, tag_assets, update_site_included_targets, create_exception, get_scan_assets
- Triggers: new_exception_request, new_scans, scan_completion

### `rapid7_insightidr` (Rapid7 InsightIDR)
- Actions: create_comment, get_investigation, set_status_of_investigation_action, list_alerts_for_investigation, get_alert_evidence, upload_attachment, create_investigation, get_alert_information, get_alert_actors, advanced_query_on_log_set, update_investigation
- Triggers: get_new_investigations

### `type_converter` (Type Converter)
- Actions: combine_arrays, string_to_integer, string_to_object, string_to_float, string_to_list, array_diff, array_match, array_to_string
- Triggers: -

### `extractit` (ExtractIt)
- Actions: url_extractor, domain_extractor, sha256_extractor, md5_extractor, sha1_extractor, ip_extractor
- Triggers: -

### `active_directory_ldap` (Active Directory LDAP)
- Actions: query, disable_user, enable_user, force_password_reset, unlock_user, query_group_membership
- Triggers: -

### `virustotal` (VirusTotal)
- Actions: scan_url_report, lookup_hash, domain_report, ip_address_report, scan_url, rescan_file, lookup_hashes, scan_file, scan_file_report
- Triggers: -

### `datetime` (Datetime)
- Actions: get_datetime, date_from_epoch, time_elapsed, add_to_datetime, subtract_from_datetime
- Triggers: -

### `jira` (Jira)
- Actions: create_issue, comment_issue, find_issues, transition_issue, assign_issue, find_users, attach_issue
- Triggers: -

### `palo_alto_pan_os` (Palo Alto Firewall, Palo Alto PAN-OS)
- Actions: add_address_object_to_group, check_if_address_object_in_group, set_address_object, remove_address_object_from_group, commit, add_to_policy, get_addresses_from_group
- Triggers: -

### `html` (HTML)
- Actions: text
- Triggers: -

### `crowdstrike_falcon` (CrowdStrike Falcon)
- Actions: blacklist_ioc, quarantine, get_agent_details
- Triggers: -

### `hashit` (HashIt)
- Actions: string, bytes
- Triggers: -

### `python_3_script` (Python 3 Script)
- Actions: run
- Triggers: -

### `recorded_future` (Recorded Future)
- Actions: lookup_IP_address, lookup_domain, lookup_url, lookup_hash, lookup_vulnerability
- Triggers: -

### `math` (Math)
- Actions: calculate
- Triggers: -

### `rapid7_vulndb` (Rapid7 Vulnerability & Exploit Database)
- Actions: get_content, search_db
- Triggers: -

### `timers` (Timers)
- Actions: delay
- Triggers: daily, weekly, periodic, hourly

### `servicenow` (ServiceNow)
- Actions: create_incident, update_incident, read_incident, search_incident, put_incident_attachment, create_security_incident, get_incident_comments_worknotes
- Triggers: incident_changed

### `microsoft_office365_email` (Microsoft Office 365 Email)
- Actions: send_email, get_email_from_user, delete_email
- Triggers: email_received

### `storage` (Storage)
- Actions: store, retrieve, check_for_variable
- Triggers: -

### `microsoft_office365_email_security` (Microsoft Office365 Email Security)
- Actions: block_sender_transport_rule, mass_search_and_purge, mass_purge, email_compliance_search
- Triggers: -

### `string` (String Operations)
- Actions: split_to_list, lower, upper
- Triggers: -

### `cisco_asa` (Cisco Adaptive Security Appliance)
- Actions: check_if_address_object_in_group, add_address_to_group, remove_address_from_group, create_address_object
- Triggers: -

### `fireeye_hx` (FireEye HX)
- Actions: get_host_id_from_hostname, check_host_quarantine_status, quarantine_host, unquarantine_host
- Triggers: -

### `sentinelone` (SentinelOne)
- Actions: blacklist, quarantine, update_analyst_verdict, update_incident_status, get_agent_details
- Triggers: -

### `whois` (WHOIS)
- Actions: address, domain
- Triggers: -

### `automox` (Automox)
- Actions: get_device_by_ip, get_device_by_hostname, get_vulnerability_sync_batch, action_on_vulnerability_sync_task, action_on_vulnerability_sync_batch, list_vulnerability_sync_tasks, upload_vulnerability_sync_file
- Triggers: -

### `carbon_black_response` (Cb Response, VMware Carbon Black EDR)
- Actions: blacklist_hash, isolate_sensor, unisolate_sensor
- Triggers: -

### `csv` (CSV)
- Actions: to_json, json_to_csv_bytes
- Triggers: -

### `fortinet_fortigate` (Fortinet FortiGate)
- Actions: remove_address_object_from_group, add_address_object_to_address_group, get_address_objects, create_address_object, check_if_address_in_group
- Triggers: -

### `microsoft_atp` (Microsoft Windows Defender ATP)
- Actions: blacklist, get_machine_information, isolate_machine, unisolate_machine
- Triggers: -

### `sonicwall` (SonicWall Firewall)
- Actions: check_if_address_in_address_group, add_address_object_to_group, create_address_object, remove_address_from_group
- Triggers: -

### `any_run` (ANY.RUN)
- Actions: get_analysis_verdict, linux_url_analysis, download_pcap, get_ioc, windows_url_analysis, android_url_analysis, get_analysis_report, get_intelligence, get_reputation
- Triggers: -

### `zscaler` (Zscaler)
- Actions: blacklist_url, get_blacklist_url
- Triggers: -

### `azure_ad_admin` (Azure AD Admin)
- Actions: force_user_to_change_password, revoke_sign_in_sessions, enable_user_account, disable_user_account
- Triggers: -

### `checkpoint_ngfw` (Check Point NGFW)
- Actions: remove_address_object_from_group, add_address_object_to_group, create_address_object, check_if_address_in_group
- Triggers: -

### `microsoft_sccm` (Microsoft SCCM)
- Actions: get_software_update_group, get_devices, new_software_update_group, new_collection, add_software_updates_to_group, get_software_updates, get_collection, add_devices_to_collection
- Triggers: -

### `rapid7_insight_agent` (Rapid7 Insight Agent)
- Actions: quarantine, get_agent_details
- Triggers: -

### `rest` (HTTP Requests)
- Actions: post
- Triggers: -

### `threatcrowd` (Threat Crowd)
- Actions: hash, domain, address
- Triggers: -

### `trendmicro_apex` (Trend Micro Apex)
- Actions: blacklist, quarantine
- Triggers: -

### `broadcom_symantec_endpoint_protection` (Broadcom Symantec Endpoint Protection)
- Actions: quarantine, blacklist
- Triggers: -

### `cylance_protect` (BlackBerry CylancePROTECT)
- Actions: blacklist, quarantine
- Triggers: -

### `cymru_malware_hash` (Team Cymru MHR)
- Actions: lookup_hash
- Triggers: -

### `meraki` (Cisco Meraki)
- Actions: get_network_ssids, get_networks, update_l3_firewall_rule
- Triggers: -

### `palo_alto_cortex_xdr` (Palo Alto Cortex XDR)
- Actions: isolate_endpoint, get_endpoint_details
- Triggers: -

### `base64` (Base64)
- Actions: decode, encode
- Triggers: -

### `dig` (DNS, Dig)
- Actions: reverse, forward
- Triggers: -

### `gmail` (Gmail)
- Actions: delete_message_by_id, find_messages
- Triggers: email_received

### `ipstack` (IPStack)
- Actions: lookup
- Triggers: -

### `markdown` (Markdown)
- Actions: markdown_to_html
- Triggers: -

### `bigfix` (BigFix)
- Actions: create_multiaction_group, fetch_relevant_fixlets
- Triggers: -

### `carbon_black_cloud` (Carbon Black Cloud)
- Actions: quarantine
- Triggers: -

### `darktrace` (Darktrace)
- Actions: update_watched_domains
- Triggers: -

### `jq` (jq)
- Actions: run_jq
- Triggers: -

### `paloalto_wildfire` (Palo Alto Wildfire)
- Actions: get_verdict, submit_file, submit_url
- Triggers: -

### `sleep` (Sleep)
- Actions: sleep
- Triggers: -

### `sophos_central` (Sophos Central)
- Actions: blacklist
- Triggers: -

### `trendmicro_deepsecurity` (Trend Micro Deep Security)
- Actions: search_computers, deploy_rules, search_rules
- Triggers: -

### `urlscan` (urlscan.io)
- Actions: get_scan_results, submit_url_for_scan
- Triggers: -

### `advanced_regex` (Advanced Regex)
- Actions: replace, split
- Triggers: -

### `microsoft_exchange` (Microsoft Exchange)
- Actions: send_email
- Triggers: email_received

### `rapid7_attackerkb` (Rapid7 AttackerKB)
- Actions: topics
- Triggers: -

### `rapid7_surface_command` (Rapid7 Surface Command)
- Actions: run_adhoc_query, run_query
- Triggers: -

### `zendesk` (Zendesk)
- Actions: update_ticket, search, create_ticket
- Triggers: -

### `basename` (Basename)
- Actions: basename
- Triggers: -

### `cybereason` (Cybereason)
- Actions: isolate_machine
- Triggers: -

### `mimecast` (Mimecast)
- Actions: create_blocked_sender_policy, create_managed_url
- Triggers: -

### `rapid7_insightvm_cloud` (Rapid7 InsightVM Cloud)
- Actions: asset_search
- Triggers: -

### `unshorten` (Unshorten.me)
- Actions: unshorten
- Triggers: -

### `abuseipdb` (AbuseIPDB)
- Actions: check_ip
- Triggers: -

### `bmc_remedy_itsm` (BMC Remedy ITSM)
- Actions: create_incident
- Triggers: -

### `connectwise` (ConnectWise)
- Actions: create_ticket
- Triggers: -

### `domaintools_phisheye` (DomainTools PhishEye)
- Actions: domain_list
- Triggers: -

### `freshdesk` (FreshDesk)
- Actions: createTicket
- Triggers: -

### `hybrid_analysis` (Hybrid Analysis)
- Actions: lookup_hash
- Triggers: -

### `ivanti_security_controls` (Ivanti Security Controls)
- Actions: get_agents
- Triggers: -

### `manage_engine_service_desk` (Manage Engine Service Desk)
- Actions: add_request
- Triggers: -

### `nasa` (NASA)
- Actions: get_image
- Triggers: -

### `opsgenie` (Opsgenie)
- Actions: get_on_calls
- Triggers: -

### `twilio` (Twilio)
- Actions: send_sms
- Triggers: -
