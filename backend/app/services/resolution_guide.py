"""Deterministic per-issue resolution guides for the AI Assistant.

This module is the backend knowledge base that drives the professional,
issue-specific troubleshooting response. Each guide maps an issue type to a
step-by-step resolution (basic checks, troubleshooting, configuration checks,
verification), plus escalation guidance and what information to collect.

It is intentionally deterministic: the AI Assistant always issues a complete,
structured, guaranteed-to-render response for real IT problems, regardless of
whether the NVIDIA provider is enabled.
"""
from __future__ import annotations

import re

from app.services import ai_rules


GUIDES: dict[str, dict] = {
    "vpn": {
        "title": "VPN Connection Failure",
        "root_cause": ("The most likely causes include a temporary VPN client failure, incorrect "
                       "authentication details, network instability, or a VPN gateway connectivity "
                       "problem."),
        "basic_checks": [
            "Confirm your device has a working internet connection (open a normal website).",
            "Check whether this affects only you or multiple users in your team.",
            "Note the exact error message shown when the VPN fails to connect.",
            "Make sure the corporate network/office connection is not also down.",
        ],
        "troubleshooting": [
            "Disconnect from the VPN client completely.",
            "Close the VPN client application and wait 10–15 seconds.",
            "Reopen the VPN client.",
            "Sign in again with your corporate credentials.",
            "Attempt to reconnect and test access to an internal resource (e.g. a shared drive or intranet page).",
            "If it still fails, restart your device and try once more.",
        ],
        "configuration_checks": [
            "Verify the correct VPN profile/server is selected.",
            "Confirm your credentials are correct and your account is active.",
            "Check whether the VPN client needs an update.",
            "For profile/server or admin-level steps, contact IT Support directly.",
        ],
        "verification": [
            "The client shows a 'Connected' status.",
            "You can open an internal application or shared drive.",
            "The connection stays stable for several minutes.",
        ],
        "if_persists": "This may involve the VPN gateway, the corporate authentication service, or your VPN client configuration. IT Operations should investigate.",
        "info_to_collect": [
            "The exact error message shown (copy verbatim).",
            "A screenshot of the error / connection log.",
            "VPN client name and version.",
            "Date and time the issue started.",
            "Network you are on (office / home / public WiFi).",
            "Steps already tried.",
        ],
    },
    "server": {
        "title": "Server / Service Outage",
        "root_cause": ("The most likely causes include a service crash, an overloaded or unattended "
                       "resource, an unapplied configuration change, or a dependency (database, network, "
                       "or another service) that is down."),
        "basic_checks": [
            "Confirm whether the outage affects one user, a department, or the whole company.",
            "Identify which service(s)/application(s) are affected.",
            "Check the server/service status page or monitoring dashboard if available.",
            "Record the exact error or behaviour when trying to access the service.",
        ],
        "troubleshooting": [
            "Restart the affected service or application.",
            "Check the service logs for the latest errors around the failure time.",
            "Verify the server has sufficient CPU, memory, and disk resources.",
            "Confirm that dependent services (database, network, other services) are healthy.",
            "If a recent change/update was applied, consider rolling it back.",
        ],
        "configuration_checks": [
            "Verify service configuration files are unchanged and valid.",
            "Check firewall/network rules that allow clients to reach the service.",
            "Confirm the service is set to start automatically on reboot.",
            "Escalate to the server/DevOps team for infrastructure-level checks.",
        ],
        "verification": [
            "The service responds successfully again.",
            "Multiple users can access the application without errors.",
            "Monitoring/alerts show the service is back to a healthy state.",
        ],
        "if_persists": "This may indicate a deeper infrastructure issue. IT Operations should investigate logs and monitor the service while a critical ticket is raised.",
        "info_to_collect": [
            "Which service/application is down.",
            "Number of users affected.",
            "Exact error message or behaviour.",
            "Time the outage started.",
            "Any recent deployments or configuration changes.",
            "Server logs relevant to the failure window.",
        ],
    },
    "database": {
        "title": "Database Connection Failure",
        "root_cause": ("The most likely causes include a database service that is down, incorrect "
                       "connection settings, network restrictions, authentication failures, or the "
                       "database being out of disk/connections."),
        "basic_checks": [
            "Confirm the database service/process is running.",
            "Check whether the issue affects a single application or multiple systems.",
            "Note the exact database error message (timeout, authentication, connection refused).",
            "Verify the database host and port are reachable from the affected client.",
        ],
        "troubleshooting": [
            "Restart the database service if it is stopped or unhealthy.",
            "Verify the connection string, host, port, and credentials are correct.",
            "Check the database connection pool / max connections limit.",
            "Confirm the database has sufficient disk space and memory.",
            "Test connectivity with a simple query from the server itself.",
        ],
        "configuration_checks": [
            "Validate the application's database configuration.",
            "Check network access controls / firewall between app and database.",
            "Confirm database authentication (password, account, permissions) is valid.",
            "Check for any recent configuration or schema changes.",
        ],
        "verification": [
            "The application connects to the database successfully.",
            "A test query returns results without error.",
            "Related applications/services are healthy again.",
        ],
        "if_persists": "This may indicate a database corruption, replication, or infrastructure issue. IT Operations/the DBA team should investigate.",
        "info_to_collect": [
            "The exact database error message (verbatim).",
            "Database name, host, and port affected.",
            "Which application(s) cannot connect.",
            "Time the failure started.",
            "Any recent schema or configuration changes.",
            "Database server logs.",
        ],
    },
    "network": {
        "title": "Network Connectivity Issue",
        "root_cause": ("The most likely causes include a dropped Wi-Fi signal, an incorrect network "
                       "selection, IP/address conflicts, network hardware (router/switch) problems, or "
                       "an outage affecting the office/location."),
        "basic_checks": [
            "Check whether the device has Wi-Fi enabled and the correct network selected.",
            "Test whether other devices on the same network work (isolate device vs. network issue).",
            "Note whether it affects a single device, a floor, or the whole office.",
            "Check if the 'no internet' state is accompanied by a specific diagnostic message.",
        ],
        "troubleshooting": [
            "Toggle Airplane mode off and on (or disconnect/reconnect Wi-Fi).",
            "Restart the router/modem or wait for the network team to do so.",
            "Run an IP refresh: on Windows use `ipconfig /release` then `ipconfig /renew`.",
            "Flush DNS: `ipconfig /flushdns`.",
            "Test with a wired (Ethernet) connection to rule out Wi-Fi issues.",
            "Restart the device if the network is still not recovered.",
        ],
        "configuration_checks": [
            "Verify the network SSID and security key are correct.",
            "Check proxy/VPN settings are not blocking traffic.",
            "Confirm the network adapter driver is up to date.",
            "Contact IT Network team for VLAN/AP-level issues.",
        ],
        "verification": [
            "The device has an IP address and connects to the internet.",
            "Internal resources and websites load normally.",
            "The connection remains stable.",
        ],
        "if_persists": "This may involve the office network infrastructure or an ISP outage. The IT Network team should investigate.",
        "info_to_collect": [
            "Device type and OS.",
            "Wi-Fi or Ethernet (wired) connection.",
            "Network name (SSID) / network segment.",
            "Exact error or diagnostic message.",
            "Time the issue started.",
            "Whether other devices/users are affected.",
        ],
    },
    "email": {
        "title": "Email Service Issue",
        "root_cause": ("The most likely causes include a mailbox that is full or near quota, mailbox "
                       "sync problems, add-in conflicts, or server-side email/outage problems."),
        "basic_checks": [
            "Check whether the email client shows 'Connected' in the status bar.",
            "Determine if it affects sending, receiving, or both.",
            "Note whether emails are queued in the Outbox.",
            "Check if other users are also having email issues.",
        ],
        "troubleshooting": [
            "Run Outlook in Safe mode (hold Ctrl while opening) to rule out add-in conflicts.",
            "Restart the email client.",
            "Check the mailbox/Inbox size and clear Deleted Items if near quota.",
            "Trigger a manual send/receive.",
            "Repair the email account profile if sync is failing.",
        ],
        "configuration_checks": [
            "Verify the account is configured with the correct server/port.",
            "Confirm you are running the latest version of the email client.",
            "Check for any email server maintenance or outage notices.",
            "Contact IT Support for server-side mailbox checks (permissions, quotas, rules).",
        ],
        "verification": [
            "You can send and receive test emails successfully.",
            "The client shows 'Connected'.",
            "The Outbox is empty and new mail arrives.",
        ],
        "if_persists": "This may involve the mail server, DNS (MX records), or mailbox configuration. IT Support should investigate.",
        "info_to_collect": [
            "Affected email address(es).",
            "Client (Outlook, mobile, webmail) and version.",
            "Exact error message (e.g. SMTP error code).",
            "Time the issue started.",
            "Whether sending, receiving, or both are affected.",
            "Recent changes to the mailbox/rules.",
        ],
    },
    "printer": {
        "title": "Printer Not Working",
        "root_cause": ("The most likely causes include the printer being offline or out of paper/ink, "
                       "a stuck print spooler, driver issues, or a network/connection problem with the "
                       "printer."),
        "basic_checks": [
            "Confirm the printer shows online (check the panel lights/screen).",
            "Check for paper jams, empty paper tray, and ink/toner levels.",
            "Determine whether printing fails from one device or all devices.",
            "Note the exact behaviour (no response, error, blank pages, stuck queue).",
        ],
        "troubleshooting": [
            "Restart the print spooler (Services > Print Spooler > Restart).",
            "Clear the stuck items from the print queue.",
            "Re-add the printer from Settings > Devices > Printers & Scanners.",
            "Reinstall the printer driver.",
            "Power-cycle the printer (off, wait, on) and reseat connections.",
        ],
        "configuration_checks": [
            "Verify the correct printer is set as the default printer.",
            "Confirm the printer is on the correct network (wireless/W-Fi direct/ethernet).",
            "Check driver version compatibility with the OS.",
            "Contact IT Support if shared/network printer permissions are the issue.",
        ],
        "verification": [
            "A test page prints successfully.",
            "The printer shows online.",
            "The print queue is empty.",
        ],
        "if_persists": "This may involve the print server, network printing, or a hardware fault. IT Support should investigate.",
        "info_to_collect": [
            "Printer model and location.",
            "How the printer is connected (USB, network, Wi-Fi).",
            "Exact error shown by printer/print queue.",
            "OS and driver version.",
            "Whether one user or all users are affected.",
            "Steps already tried.",
        ],
    },
    "software": {
        "title": "Software / Application Issue",
        "root_cause": ("The most likely causes include an outdated version, missing updates, corrupted "
                       "installation, licensing problems, or an application/combatibility conflict."),
        "basic_checks": [
            "Identify the exact application and version.",
            "Confirm you are running the latest available version/update.",
            "Check whether the issue is reproducible or happened once.",
            "Note the exact error message or failure behaviour.",
        ],
        "troubleshooting": [
            "Restart the application and try again.",
            "Restart the device to clear lingering processes/memory.",
            "Run the application as administrator if permission-related.",
            "Check for and install any pending updates for the application and OS.",
            "Repair or reinstall the application if it is corrupted.",
        ],
        "configuration_checks": [
            "Verify the application has the required license/activation.",
            "Check system requirements (OS version, RAM, disk space).",
            "Confirm any required dependencies or plugins are installed.",
            "Contact IT Support for enterprise deployment/licensing steps.",
        ],
        "verification": [
            "The application launches and the specific feature works.",
            "The action that previously failed now completes.",
            "No error messages remain.",
        ],
        "if_persists": "This may indicate a licensing, compatibility, or deployment issue. The Software team should investigate.",
        "info_to_collect": [
            "Application name and version.",
            "OS version.",
            "Exact error message (verbatim).",
            "Steps to reproduce the issue.",
            "Date/time it started.",
            "Whether it affects one user or many.",
        ],
    },
    "hardware": {
        "title": "Hardware Failure",
        "root_cause": ("The most likely causes include a power issue, failed component (battery, drive, "
                       "screen), overheating, or a loose/corrupted connection."),
        "basic_checks": [
            "Determine whether the device powers on at all (any lights/fans).",
            "Check for error indicators: beeps, blinking lights, or on-screen error codes.",
            "Note whether it is a laptop or desktop, and its model.",
            "Confirm power is connected and the battery (if laptop) is seated/charged.",
        ],
        "troubleshooting": [
            "For a laptop, remove the battery (if removable), hold the power button 15 seconds, reconnect and try.",
            "For a desktop, check the power cable, outlet, and power supply.",
            "Connect an external display to rule out a screen fault (if no display).",
            "Test with a known-good charger/kable if the battery is not charging.",
            "If overheating, ensure vents are clear and fans are running.",
        ],
        "configuration_checks": [
            "Verify BIOS/OS are not stuck in a boot loop (try safe mode).",
            "Confirm all internal cables/components are seated properly.",
            "Check for a hardware self-test (e.g. pre-boot diagnostics).",
            "Contact IT Support for warranty/repair handling.",
        ],
        "verification": [
            "The device powers on and boots normally.",
            "The screen displays correctly.",
            "The specific hardware component functions.",
        ],
        "if_persists": "This may require hardware repair or replacement under warranty. The Hardware/IT Support team should handle it.",
        "info_to_collect": [
            "Device make, model, and serial number.",
            "Whether it powers on (and any error lights/beeps).",
            "Screen/keyboard/battery/power behaviour.",
            "Time the failure started.",
            "Any recent drops, spills, or updates.",
            "Steps already tried.",
        ],
    },
    "password": {
        "title": "Password / Account Access Issue",
        "root_cause": ("The most likely causes include a wrong or forgotten password, a locked or "
                       "expired account, MFA/2FA problems, or a pending password reset."),
        "basic_checks": [
            "Confirm the account is not locked and the password is not expired.",
            "Check caps lock / number lock while typing.",
            "Note the exact error (invalid credentials, account locked, MFA failed).",
            "Determine if the issue is on one device or everywhere.",
        ],
        "troubleshooting": [
            "Use the 'Forgot password' / password reset link on the login page.",
            "Follow the reset email link and set a new password (min 8 characters).",
            "If you receive no reset email, check spam and confirm the email address used.",
            "If MFA/2FA is failing, verify the authenticator/code is correct and time-synced.",
            "For a locked account, wait for the lockout window or contact IT Support.",
        ],
        "configuration_checks": [
            "Verify the account is active and not disabled.",
            "Confirm password policy compliance and MFA settings.",
            "Check if SSO or group policy affects login.",
            "Contact IT Support to unlock/reset the account or review MFA.",
        ],
        "verification": [
            "You can log in successfully.",
            "MFA/2FA completes.",
            "Access to required systems/apps is restored.",
        ],
        "if_persists": "This may involve account lockout policy, SSO, or MFA configuration. IT Support should investigate.",
        "info_to_collect": [
            "Username/email affected.",
            "Exact error message (verbatim).",
            "Whether the account is locked, expired, or MFA is failing.",
            "Device(s) affected.",
            "Time the issue started.",
            "Steps already tried.",
        ],
    },
    "security": {
        "title": "Security Alert / Unauthorized Access",
        "root_cause": ("The most likely causes include phishing, malware, credential theft, or a "
                       "compromised account. Any suspected security incident must be treated urgently."),
        "basic_checks": [
            "Do NOT click any suspicious links, download attachments, or share credentials.",
            "Identify what the alert is about (email, popup, account activity, antivirus).",
            "Determine whether your account shows sign-ins you do not recognise.",
            "Report the incident immediately rather than troubleshooting yourself.",
        ],
        "troubleshooting": [
            "Change your password immediately if your account may be compromised.",
            "Revoke/end active sessions from unfamiliar locations.",
            "Run a full antivirus/malware scan on the affected device.",
            "Do not continue using the affected account until IT confirms it is safe.",
        ],
        "configuration_checks": [
            "Enable and verify MFA/2FA on your account.",
            "Confirm company security software is up to date and active.",
            "Review recent account activity for unauthorized changes.",
            "IT Security will inspect logs and quarantined items.",
        ],
        "verification": [
            "An IT security analyst has confirmed the account/device is safe.",
            "Suspicious access has been blocked and MFA is enforced.",
            "Any malware has been removed and the device is clean.",
        ],
        "if_persists": "Treat this as an active incident. IT Security should open an urgent security ticket and investigate immediately.",
        "info_to_collect": [
            "What the alert/incident is (exact wording).",
            "Whether it is email, popup, antivirus, or account activity.",
            "Date/time seen.",
            "Any suspicious emails/senders/links (do not click).",
            "Whether your account has unknown sign-ins.",
            "Device(s) involved.",
        ],
    },
    "bug": {
        "title": "Application Bug / Error",
        "root_cause": ("The most likely causes include a coding defect, a recent change/update, a "
                       "corrupted data or cache, or an interaction between applications/versions."),
        "basic_checks": [
            "Identify the exact application, screen, and action that triggers the bug.",
            "Note whether the error is reproducible consistently or intermittent.",
            "Record the exact error message / stack trace if visible.",
            "Check whether other users experience the same issue.",
        ],
        "troubleshooting": [
            "Restart the application and retry the action.",
            "Clear the application cache/temporary files.",
            "Update the application to the latest version (bug may already be fixed).",
            "Test in an incognito/private window or on another device to isolate browser vs. app.",
            "Retry after a device restart.",
        ],
        "configuration_checks": [
            "Confirm the OS and application are compatible/up to date.",
            "Check for any known issues from a recent deployment.",
            "Verify user permissions/role needed for the affected feature.",
            "Log a bug for the development team with reproduction steps.",
        ],
        "verification": [
            "The offending action now completes without error.",
            "The issue cannot be reproduced.",
            "No related errors appear in the application console/logs.",
        ],
        "if_persists": "This is likely a code defect. Log a bug ticket with full reproduction details for the development team.",
        "info_to_collect": [
            "Application name and version.",
            "Exact steps to reproduce (step by step).",
            "Expected vs. actual behaviour.",
            "Exact error message / stack trace (verbatim).",
            "OS and browser (if web).",
            "Whether it is repeatable and affects others.",
        ],
    },
    "general": {
        "title": "General IT Issue",
        "root_cause": "The cause depends on the specific symptoms. Let's gather a few quick details to narrow it down.",
        "basic_checks": [
            "Describe the exact problem and what you expected to happen.",
            "Note the device/application involved.",
            "Confirm whether it affects one device/user or several.",
            "Record the exact error or behaviour.",
        ],
        "troubleshooting": [
            "Restart the affected device or application.",
            "Check for updates to the OS and relevant software.",
            "Test the action again and note whether the error changes.",
        ],
        "configuration_checks": [
            "Review settings relevant to the feature/application.",
            "Confirm permissions/roles needed are present.",
            "Contact IT Support if access or policy is involved.",
        ],
        "verification": [
            "The expected action now works.",
            "No error message remains.",
        ],
        "if_persists": "Provide the collected information and IT Support will route the issue to the right team.",
        "info_to_collect": [
            "Description of the problem and expected result.",
            "Device, OS, and application involved.",
            "Exact error message.",
            "Steps attempted.",
            "Whether others are affected.",
        ],
    },
}


# Keyword cascade: ordered list of (issue_key, keyword list). First hit wins.
# More specific keywords come before the generic ones.
_ISSUE_KEYWORDS: list[tuple[str, list[str]]] = [
    ("database", ["database", "db connection", "cannot connect to database", "db error",
                  "database connection failed", "sql server"]),
    ("server", ["server down", "server is down", "server outage", "service down", "prod down",
                "production down", "server not responding", "server crash"]),
    ("security", ["security", "unauthorized", "breach", "malware", "virus", "hacked",
                  "ransomware", "phishing", "security alert"]),
    ("password", ["password", "forgot password", "reset password", "locked out", "login",
                  "log in", "cannot sign in", "account", "mfa", "authentication"]),
    ("vpn", ["vpn", "virtual private network", "remote access", "vpn client"]),
    ("email", ["email", "outlook", "mail", "mailbox", "inbox", "not receiving emails",
               "send email", "emails"]),
    ("printer", ["printer", "print", "printing", "paper jam", "toner", "not printing", "scan"]),
    ("network", ["internet", "internet not working", "wifi", "wi-fi", "wireless", "network",
                 "no internet", "ethernet", "no wifi", "connection"]),
    ("hardware", ["computer", "not turning on", "won't turn on", "wont turn on", "screen",
                  "monitor", "keyboard", "overheat", "frozen", "freeze", "blue screen",
                  "computer not", "laptop not", "hardware", "crash"]),
    ("software", ["software", "application", "install", "update", "browser", "app", "program"]),
    ("bug", ["bug", "glitch", "application crashing", "crashing", "error", "not working",
             "broken", "fails"]),
]


def get_guide(intent: str, user_text: str, analysis: dict | None = None) -> dict:
    """Return the resolution guide for the given user message.

    A keyword cascade runs first so that issue-specific guides are chosen even
    when the detected intent is generic (e.g. "Database Connection Failed" with
    a ``question`` intent still maps to the database guide). Falls back to the
    intent name, then to ``general``.
    """
    t = (user_text or "").lower()

    # 1. Keyword cascade (most specific first).
    for issue_key, keywords in _ISSUE_KEYWORDS:
        if any(kw in t for kw in keywords):
            guide = GUIDES.get(issue_key)
            if guide:
                return guide

    # 2. Fall back by intent name where a direct mapping exists.
    if analysis:
        intent = analysis.get("intent") or intent
    intent_guide = _guide_for_intent(intent)
    if intent_guide:
        return intent_guide

    # 3. Always have a usable guide.
    return GUIDES["general"]


def _guide_for_intent(intent: str) -> dict | None:
    mapping = {
        ai_rules.VPN: "vpn",
        ai_rules.NETWORK: "network",
        ai_rules.EMAIL: "email",
        ai_rules.PRINTER: "printer",
        ai_rules.SOFTWARE: "software",
        ai_rules.HARDWARE: "hardware",
        ai_rules.PASSWORD_RESET: "password",
        ai_rules.SECURITY: "security",
        ai_rules.BUG: "bug",
    }
    key = mapping.get(intent)
    return GUIDES.get(key) if key else None


def matches_issue_keywords(text: str) -> bool:
    """Return True if the text looks like a real IT issue (gets a guide)."""
    t = (text or "").lower()
    for keywords in _ISSUE_KEYWORDS:
        if any(kw in t for kw in keywords[1]):
            return True
    return False


def issue_title(analysis: dict | None, user_text: str = "") -> str:
    """Return the guide's title for the AI ANALYSIS 'Issue:' field and session title."""
    guide = get_guide("", user_text, analysis)
    return guide.get("title", "General IT Issue")


def escalation_for(priority: str, department: str | None) -> str:
    """Return escalation guidance based on the detected priority."""
    p = (priority or "").lower()
    dept = department or "IT Support"
    if p == "critical":
        return (f"This is a critical issue. Escalate immediately to {dept} / Security and "
                "ensure a high-priority ticket is created. Work is blocked or production is "
                "affected, so this requires urgent attention.")
    if p == "high":
        return (f"Escalate to {dept} as a high-priority ticket — the issue is blocking work "
                "or affecting multiple users. Include the collected information and any "
                "affected user list.")
    if p == "medium":
        return (f"If troubleshooting does not resolve it, raise a support ticket for {dept} "
                "with the collected information. This is not blocking all users but should "
                "be tracked.")
    return (f"If troubleshooting does not resolve it, continue with the steps above, or "
            f"raise a normal ticket for {dept} so it can be tracked.")


def _format_similar(similar_tickets: list | None) -> str:
    if not similar_tickets:
        return "No closely matching previous ticket found."
    lines = [f"## SIMILAR TICKETS", ""]
    for i, tkt in enumerate(similar_tickets[:5], start=1):
        title = tkt.get("title") or "Untitled"
        tno = tkt.get("ticket_no") or "?"
        sim = tkt.get("similarity") or 0.0
        notes = tkt.get("resolution_notes") or tkt.get("ai_summary") or \
            "No resolution notes recorded."
        lines.append(f"{i}. **{title}** (#{tno}, {round(float(sim))}% similar)")
        lines.append(f"   - Previous Resolution: {notes}")
    return "\n".join(lines)


def build_professional_response(
    analysis: dict,
    user_text: str,
    similar_tickets: list | None = None,
) -> str:
    """Assemble the full professional markdown troubleshooting response."""
    guide = get_guide(analysis.get("intent", ""), user_text, analysis)
    priority = (analysis.get("priority") or "medium").title()
    confidence = round(float(analysis.get("confidence") or 0.0) * 100)

    lines: list[str] = []
    lines.append("## AI ANALYSIS")
    lines.append("")
    lines.append(f"**Issue:** {guide['title']}")
    lines.append(f"**Category:** {analysis.get('category') or 'General'}")
    lines.append(f"**Department:** {analysis.get('department') or 'IT Support'}")
    lines.append(f"**Priority:** {priority}")
    lines.append(f"**Sentiment:** {(analysis.get('sentiment') or 'neutral').title()}")
    lines.append(f"**Root Cause:** {guide['root_cause']}")
    lines.append(f"**AI Confidence:** {confidence}%")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## RECOMMENDED RESOLUTION")
    lines.append("")
    lines.append("### 1. Basic Checks")
    for item in guide["basic_checks"]:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("### 2. Troubleshooting")
    for i, step in enumerate(guide["troubleshooting"], start=1):
        lines.append(f"{i}. {step}")
    lines.append("")
    lines.append("### 3. Configuration Checks")
    for item in guide["configuration_checks"]:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("### 4. Verification")
    for item in guide["verification"]:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append(f"## IF THE ISSUE PERSISTS")
    lines.append("")
    lines.append(guide["if_persists"])
    lines.append("")
    lines.append("## INFORMATION TO COLLECT")
    for item in guide["info_to_collect"]:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("## ESCALATION / NEXT ACTION")
    lines.append("")
    lines.append(escalation_for(analysis.get("priority"), analysis.get("department")))
    lines.append("")
    lines.append(_format_similar(similar_tickets))

    return "\n".join(lines)