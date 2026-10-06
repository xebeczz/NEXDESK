"""Seed 40 realistic resolved IT support tickets for Similar Tickets testing."""
from __future__ import annotations

import random
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.ticket import Ticket, compute_sla_status, sla_deadline_for
from app.models.enums import TicketPriority, TicketStatus

random.seed(42)


def create_ticket(
    db: Session,
    title: str,
    description: str,
    category: str,
    priority: TicketPriority,
    department: str | None,
    created_at: datetime,
    ai_summary: str | None,
    resolution_notes: str | None,
    status: TicketStatus = TicketStatus.RESOLVED,
) -> Ticket:
    existing = db.query(Ticket).filter(Ticket.title == title).first()
    if existing:
        print(f"SKIP (duplicate title): {title}")
        return existing

    day_label = created_at.strftime("%Y%m%d")
    from sqlalchemy import func
    from app.models.ticket import Ticket as T
    count = db.query(func.count(T.id)).filter(T.ticket_no.like(f"TCK-{day_label}-%")).scalar() or 0
    ticket_no = f"TCK-{day_label}-{count + 1:04d}"

    deadline = sla_deadline_for(priority, created_at)
    sla_status = compute_sla_status(created_at, deadline, created_at)

    ticket = Ticket(
        ticket_no=ticket_no,
        title=title,
        description=description,
        category=category,
        priority=priority,
        status=status.value,
        department=department,
        created_by_id="39bbe7dc-dc7f-46d7-b3c4-483bbbb36a5f",
        ai_summary=ai_summary,
        resolution_notes=resolution_notes,
        sla_status=sla_status.value,
        sla_deadline=deadline,
        created_at=created_at,
        updated_at=created_at,
        resolved_at=created_at + timedelta(hours=random.randint(1, 72)),
    )
    db.add(ticket)
    db.flush()
    print(f"ADDED: {ticket_no} - {title}")
    return ticket


def main() -> None:
    db = SessionLocal()
    try:
        now = datetime.utcnow()
        count = 0

        # NETWORK — 8
        create_ticket(
            db,
            title="VPN Disconnects Frequently",
            description="User can connect to the company VPN, but the connection disconnects every few minutes during work.",
            category="Network & VPN",
            priority=TicketPriority.HIGH,
            department="Network Support",
            created_at=now - timedelta(days=random.randint(10, 60)),
            ai_summary="Unstable VPN connection caused by incorrect VPN client configuration.",
            resolution_notes="VPN client configuration was updated and the client was restarted. Connection stability was verified for 24 hours.",
        )
        create_ticket(
            db,
            title="Wi-Fi Authentication Failed",
            description="User can see the office Wi-Fi network but cannot connect to it. Authentication prompt keeps failing.",
            category="Network & VPN",
            priority=TicketPriority.HIGH,
            department="Network Support",
            created_at=now - timedelta(days=random.randint(10, 60)),
            ai_summary="Incorrect wireless authentication profile stored on the device.",
            resolution_notes="The old Wi-Fi profile was removed and the correct company profile was configured. User connected successfully after re-authentication.",
        )
        create_ticket(
            db,
            title="Slow Internet Connection",
            description="Internet is working but webpages and cloud applications load very slowly across all browsers.",
            category="Network & VPN",
            priority=TicketPriority.MEDIUM,
            department="Network Support",
            created_at=now - timedelta(days=random.randint(10, 60)),
            ai_summary="High network traffic on the local connection segment.",
            resolution_notes="Network traffic was analyzed and the affected connection was moved to the appropriate network segment. Speed tests confirmed normal throughput.",
        )
        create_ticket(
            db,
            title="DNS Resolution Failure",
            description="User can connect to the network but cannot access websites using their domain names. IP addresses work.",
            category="Network & VPN",
            priority=TicketPriority.HIGH,
            department="Network Support",
            created_at=now - timedelta(days=random.randint(10, 60)),
            ai_summary="Incorrect DNS server configuration on the workstation.",
            resolution_notes="DNS configuration was corrected to use the company primary and secondary DNS servers. Network settings were refreshed and domain resolution was verified.",
        )
        create_ticket(
            db,
            title="IP Address Conflict",
            description="User receives intermittent network connectivity and cannot access some internal systems after lunch.",
            category="Network & VPN",
            priority=TicketPriority.HIGH,
            department="Network Support",
            created_at=now - timedelta(days=random.randint(10, 60)),
            ai_summary="Duplicate IP address assigned to two devices on the same subnet.",
            resolution_notes="The conflicting IP configuration was identified and corrected. The affected device received a new valid address via DHCP reservation.",
        )
        create_ticket(
            db,
            title="Cannot Access Shared Network Drive",
            description="User cannot access the department's shared network folder. Error message says path not found.",
            category="Network & VPN",
            priority=TicketPriority.MEDIUM,
            department="Network Support",
            created_at=now - timedelta(days=random.randint(10, 60)),
            ai_summary="Network drive mapping was missing from the user's workstation.",
            resolution_notes="The correct shared drive was mapped to the user's workstation using the proper UNC path. Access was verified.",
        )
        create_ticket(
            db,
            title="Network Cable Not Detected",
            description="Desktop computer does not detect the wired LAN connection. Link light is off on the port.",
            category="Network & VPN",
            priority=TicketPriority.MEDIUM,
            department="Network Support",
            created_at=now - timedelta(days=random.randint(10, 60)),
            ai_summary="Faulty Ethernet cable causing physical layer failure.",
            resolution_notes="The network cable was replaced with a known good cable. Connectivity was restored and link light came on.",
        )
        create_ticket(
            db,
            title="Unable to Reach Internal Application",
            description="User can access the internet but cannot open the internal company HR application from the browser.",
            category="Network & VPN",
            priority=TicketPriority.HIGH,
            department="Network Support",
            created_at=now - timedelta(days=random.randint(10, 60)),
            ai_summary="Firewall rule was blocking the application's internal port.",
            resolution_notes="The firewall rule was reviewed and the required port was allowed. Application access was verified successfully.",
        )

        # SERVER / INFRASTRUCTURE — 6
        create_ticket(
            db,
            title="Application Server Unavailable",
            description="Employees cannot access the internal HR application. Error message says service unavailable.",
            category="Server",
            priority=TicketPriority.CRITICAL,
            department="Infrastructure",
            created_at=now - timedelta(days=random.randint(10, 60)),
            ai_summary="Application service stopped unexpectedly on the production server.",
            resolution_notes="The application service was restarted and server logs were checked for root cause. Service health was verified.",
        )
        create_ticket(
            db,
            title="Database Connection Failed",
            description="The application displays a database connection error when users try to log in.",
            category="Database",
            priority=TicketPriority.CRITICAL,
            department="Infrastructure",
            created_at=now - timedelta(days=random.randint(10, 60)),
            ai_summary="Database service was unavailable due to resource exhaustion.",
            resolution_notes="Database service was restarted and connectivity was verified. Connection pool settings were tuned to prevent recurrence.",
        )
        create_ticket(
            db,
            title="File Server Storage Full",
            description="Users cannot save new files to the department file server. Error says disk full.",
            category="Server",
            priority=TicketPriority.HIGH,
            department="Infrastructure",
            created_at=now - timedelta(days=random.randint(10, 60)),
            ai_summary="File server storage reached its maximum capacity.",
            resolution_notes="Old temporary files were removed and storage capacity was restored. Quota monitoring was configured.",
        )
        create_ticket(
            db,
            title="Scheduled Backup Failed",
            description="The nightly backup job did not complete successfully. Monitoring shows failed status.",
            category="Server",
            priority=TicketPriority.HIGH,
            department="Infrastructure",
            created_at=now - timedelta(days=random.randint(10, 60)),
            ai_summary="Backup destination storage was unavailable due to network path issue.",
            resolution_notes="Backup storage connectivity was restored and the backup was run again successfully. Success was confirmed.",
        )
        create_ticket(
            db,
            title="Server CPU Usage Very High",
            description="Internal applications are responding slowly for multiple users. CPU at 98% on app server.",
            category="Server",
            priority=TicketPriority.HIGH,
            department="Infrastructure",
            created_at=now - timedelta(days=random.randint(10, 60)),
            ai_summary="A background process was consuming excessive CPU resources.",
            resolution_notes="The process was identified using performance monitoring and stopped. Normal CPU levels were restored.",
        )
        create_ticket(
            db,
            title="Internal Web Portal Not Loading",
            description="Employees receive a timeout when opening the internal company portal.",
            category="Server",
            priority=TicketPriority.HIGH,
            department="Infrastructure",
            created_at=now - timedelta(days=random.randint(10, 60)),
            ai_summary="Web service was not responding correctly due to hung worker processes.",
            resolution_notes="The web service was restarted and application health was verified. Portal loaded successfully.",
        )

        # ACCOUNT / AUTHENTICATION — 6
        create_ticket(
            db,
            title="User Account Locked",
            description="User cannot log in after several unsuccessful login attempts. Account is locked.",
            category="Identity & Access",
            priority=TicketPriority.MEDIUM,
            department="IT Support",
            created_at=now - timedelta(days=random.randint(10, 60)),
            ai_summary="Account was automatically locked after repeated failed login attempts.",
            resolution_notes="Account was unlocked after verifying the user's identity. User was advised to use the correct password.",
        )
        create_ticket(
            db,
            title="Password Expired",
            description="User receives a password expiration message during login and cannot access email.",
            category="Identity & Access",
            priority=TicketPriority.MEDIUM,
            department="IT Support",
            created_at=now - timedelta(days=random.randint(10, 60)),
            ai_summary="Company password validity period had expired for the user account.",
            resolution_notes="User password was reset according to security policy and the user was guided through the change process.",
        )
        create_ticket(
            db,
            title="New Employee Account Not Created",
            description="New employee cannot access company applications on their first day. Login fails.",
            category="Identity & Access",
            priority=TicketPriority.HIGH,
            department="IT Support",
            created_at=now - timedelta(days=random.randint(10, 60)),
            ai_summary="Employee account provisioning was incomplete due to missing HR ticket.",
            resolution_notes="The required account and application permissions were created. All systems were verified and the user logged in successfully.",
        )
        create_ticket(
            db,
            title="Access Denied to Shared Folder",
            description="User receives an access denied message when opening a department folder on the file server.",
            category="Identity & Access",
            priority=TicketPriority.MEDIUM,
            department="IT Support",
            created_at=now - timedelta(days=random.randint(10, 60)),
            ai_summary="User was missing the required security group membership for folder access.",
            resolution_notes="User was added to the appropriate security group. Access was verified after group policy refresh.",
        )
        create_ticket(
            db,
            title="Multi-Factor Authentication Failed",
            description="User cannot complete login because the MFA verification code is not being accepted.",
            category="Identity & Access",
            priority=TicketPriority.HIGH,
            department="Security Team",
            created_at=now - timedelta(days=random.randint(10, 60)),
            ai_summary="MFA device registration was out of sync with the authentication server.",
            resolution_notes="MFA registration was reset and the user's device was registered again. Login succeeded after verification.",
        )
        create_ticket(
            db,
            title="User Cannot Change Password",
            description="User receives an error when attempting to change their account password in the portal.",
            category="Identity & Access",
            priority=TicketPriority.MEDIUM,
            department="IT Support",
            created_at=now - timedelta(days=random.randint(10, 60)),
            ai_summary="New password did not satisfy the configured password policy requirements.",
            resolution_notes="Password requirements were explained to the user and a compliant password was created successfully.",
        )

        # EMAIL — 5
        create_ticket(
            db,
            title="Email Messages Delayed",
            description="Incoming emails are arriving several minutes after they are sent by external contacts.",
            category="Email",
            priority=TicketPriority.MEDIUM,
            department="Email Support",
            created_at=now - timedelta(days=random.randint(10, 60)),
            ai_summary="Mail server queue was temporarily overloaded due to spam spike.",
            resolution_notes="Mail queue was cleared and normal delivery was restored. Spam filters were tuned.",
        )
        create_ticket(
            db,
            title="Cannot Send Email Attachment",
            description="User can send normal emails but messages with attachments larger than 10MB fail.",
            category="Email",
            priority=TicketPriority.MEDIUM,
            department="Email Support",
            created_at=now - timedelta(days=random.randint(10, 60)),
            ai_summary="Attachment size exceeded the configured mail transport limit.",
            resolution_notes="The attachment was compressed using zip and sent successfully. User was informed about size limits.",
        )
        create_ticket(
            db,
            title="Mailbox Storage Full",
            description="User cannot receive new emails because the mailbox is full. Senders get bounce messages.",
            category="Email",
            priority=TicketPriority.MEDIUM,
            department="Email Support",
            created_at=now - timedelta(days=random.randint(10, 60)),
            ai_summary="Mailbox exceeded its storage quota due to large attachments.",
            resolution_notes="Old unnecessary emails were archived to PST and storage was reduced below quota. Normal operation restored.",
        )
        create_ticket(
            db,
            title="Email Application Keeps Crashing",
            description="The desktop email application closes unexpectedly while being used. No error message.",
            category="Software",
            priority=TicketPriority.MEDIUM,
            department="IT Support",
            created_at=now - timedelta(days=random.randint(10, 60)),
            ai_summary="Corrupted local application cache causing instability.",
            resolution_notes="The cache was cleared and the email application was restarted. Application ran smoothly after cache rebuild.",
        )
        create_ticket(
            db,
            title="Email Signature Missing",
            description="User's company email signature no longer appears on outgoing messages after an update.",
            category="Email",
            priority=TicketPriority.LOW,
            department="Email Support",
            created_at=now - timedelta(days=random.randint(10, 60)),
            ai_summary="Email signature configuration was removed during mailbox migration.",
            resolution_notes="The standard company email signature was configured again via transport rules. Signature appeared on new messages.",
        )

        # HARDWARE — 5
        create_ticket(
            db,
            title="Laptop Battery Draining Quickly",
            description="Laptop battery drops from full charge to low battery within one hour of unplugged use.",
            category="Hardware",
            priority=TicketPriority.MEDIUM,
            department="Hardware Support",
            created_at=now - timedelta(days=random.randint(10, 60)),
            ai_summary="Battery health had significantly degraded below usable capacity.",
            resolution_notes="Battery health was checked using diagnostics and the battery was replaced. Battery life returned to normal.",
        )
        create_ticket(
            db,
            title="Laptop Overheating",
            description="Laptop becomes very hot and slows down during normal usage. Fan runs constantly.",
            category="Hardware",
            priority=TicketPriority.MEDIUM,
            department="Hardware Support",
            created_at=now - timedelta(days=random.randint(10, 60)),
            ai_summary="Dust buildup was restricting cooling airflow inside the chassis.",
            resolution_notes="The cooling system was cleaned, thermal paste was reapplied, and thermal performance was restored.",
        )
        create_ticket(
            db,
            title="Keyboard Keys Not Working",
            description="Several keyboard keys do not respond when pressed. Some keys stick.",
            category="Hardware",
            priority=TicketPriority.LOW,
            department="Hardware Support",
            created_at=now - timedelta(days=random.randint(10, 60)),
            ai_summary="Physical keyboard failure due to wear and spill damage.",
            resolution_notes="The keyboard was replaced with a new unit. All keys responded correctly after replacement.",
        )
        create_ticket(
            db,
            title="External Monitor Not Detected",
            description="Laptop does not detect the external monitor connected through HDMI. Screen stays black.",
            category="Hardware",
            priority=TicketPriority.MEDIUM,
            department="Hardware Support",
            created_at=now - timedelta(days=random.randint(10, 60)),
            ai_summary="Faulty HDMI cable causing no display signal.",
            resolution_notes="The HDMI cable was replaced with a known good cable. The monitor was detected and displayed correctly.",
        )
        create_ticket(
            db,
            title="Computer Does Not Power On",
            description="Desktop computer does not start when the power button is pressed. No lights, no fans.",
            category="Hardware",
            priority=TicketPriority.HIGH,
            department="Hardware Support",
            created_at=now - timedelta(days=random.randint(10, 60)),
            ai_summary="Faulty power supply unit failed to deliver standby power.",
            resolution_notes="The power supply was tested and replaced. The system powered on normally after replacement.",
        )

        # SOFTWARE — 5
        create_ticket(
            db,
            title="Application Installation Failed",
            description="User receives an error while installing an approved company application. Error code 1603.",
            category="Software",
            priority=TicketPriority.MEDIUM,
            department="IT Support",
            created_at=now - timedelta(days=random.randint(10, 60)),
            ai_summary="Required software dependency was missing from the system.",
            resolution_notes="The missing dependency was installed and the application installation completed successfully.",
        )
        create_ticket(
            db,
            title="Software License Expired",
            description="User's productivity application displays a license expiration message and features are disabled.",
            category="Software",
            priority=TicketPriority.MEDIUM,
            department="IT Support",
            created_at=now - timedelta(days=random.randint(10, 60)),
            ai_summary="Software license had expired and was not automatically renewed.",
            resolution_notes="The appropriate company license was assigned to the user. Application features were reactivated.",
        )
        create_ticket(
            db,
            title="Application Freezes Frequently",
            description="A desktop application becomes unresponsive when processing large files over 100MB.",
            category="Software",
            priority=TicketPriority.MEDIUM,
            department="IT Support",
            created_at=now - timedelta(days=random.randint(10, 60)),
            ai_summary="Application version was outdated and had known stability issues.",
            resolution_notes="The application was updated to the latest approved version. Large file processing was tested and stable.",
        )
        create_ticket(
            db,
            title="Browser Pages Not Loading",
            description="The browser opens but several websites fail to load correctly. Shows generic error page.",
            category="Software",
            priority=TicketPriority.LOW,
            department="IT Support",
            created_at=now - timedelta(days=random.randint(10, 60)),
            ai_summary="Corrupted browser cache and problematic extensions causing page load failures.",
            resolution_notes="Browser cache was cleared, history was removed, and problematic extensions were disabled. Pages loaded correctly.",
        )
        create_ticket(
            db,
            title="PDF Files Not Opening",
            description="User cannot open PDF documents on the workstation. Error says file is damaged.",
            category="Software",
            priority=TicketPriority.LOW,
            department="IT Support",
            created_at=now - timedelta(days=random.randint(10, 60)),
            ai_summary="PDF reader installation was corrupted during a Windows update.",
            resolution_notes="The PDF reader was repaired using the application installer. PDF files opened normally after repair.",
        )

        # PRINTER / PERIPHERALS — 2
        create_ticket(
            db,
            title="Printer Shows Offline",
            description="The office printer appears offline in the system even though it is powered on and connected.",
            category="Hardware",
            priority=TicketPriority.MEDIUM,
            department="Hardware Support",
            created_at=now - timedelta(days=random.randint(10, 60)),
            ai_summary="Printer lost its network connection due to DHCP lease renewal.",
            resolution_notes="The printer network connection was restored and the device was reconnected to the print server. Status changed to online.",
        )
        create_ticket(
            db,
            title="Printer Printing Blank Pages",
            description="Printer processes the job but produces blank pages. No error message displayed.",
            category="Hardware",
            priority=TicketPriority.MEDIUM,
            department="Hardware Support",
            created_at=now - timedelta(days=random.randint(10, 60)),
            ai_summary="Printer cartridge was empty and print head was clogged.",
            resolution_notes="The cartridge was replaced, print head was cleaned, and a test page printed successfully with proper content.",
        )

        # SECURITY — 3
        create_ticket(
            db,
            title="Suspicious Login Alert",
            description="User received a security alert for a login they do not recognize from an unknown location.",
            category="Security",
            priority=TicketPriority.CRITICAL,
            department="Security Team",
            created_at=now - timedelta(days=random.randint(10, 60)),
            ai_summary="Unauthorized login attempt detected from a foreign IP address.",
            resolution_notes="The account password was reset, active sessions were reviewed, and MFA was reconfigured. No further suspicious activity.",
        )
        create_ticket(
            db,
            title="Blocked USB Device",
            description="User cannot access a USB storage device on their company computer. Device is not recognized.",
            category="Security",
            priority=TicketPriority.MEDIUM,
            department="Security Team",
            created_at=now - timedelta(days=random.randint(10, 60)),
            ai_summary="USB storage devices are restricted by company security policy by default.",
            resolution_notes="The device was verified for ownership and temporary approved access was provided according to company policy.",
        )
        create_ticket(
            db,
            title="Antivirus Alert",
            description="The workstation displays an antivirus warning for a suspicious file in the downloads folder.",
            category="Security",
            priority=TicketPriority.HIGH,
            department="Security Team",
            created_at=now - timedelta(days=random.randint(10, 60)),
            ai_summary="Potentially malicious file detected by endpoint protection heuristics.",
            resolution_notes="The file was quarantined immediately and the workstation was scanned successfully. No malware was found active.",
        )

        # Additional 5 tickets to reach 40 — mixed categories
        create_ticket(
            db,
            title="Email Delivery Failure to External Domain",
            description="Emails sent to external domain partners are bouncing back with relay access denied.",
            category="Email",
            priority=TicketPriority.HIGH,
            department="Email Support",
            created_at=now - timedelta(days=random.randint(10, 60)),
            ai_summary="SMTP relay permission was missing for the external domain.",
            resolution_notes="The external domain was added to the allowed relay list. Emails were delivered successfully after re-sending.",
        )
        create_ticket(
            db,
            title="Laptop Screen Flickering",
            description="Laptop screen flickers intermittently especially when opening large spreadsheets.",
            category="Hardware",
            priority=TicketPriority.MEDIUM,
            department="Hardware Support",
            created_at=now - timedelta(days=random.randint(10, 60)),
            ai_summary="Loose display cable connection between motherboard and screen.",
            resolution_notes="Display cable was reseated and the screen assembly was tested. Flickering stopped after cable reconnection.",
        )
        create_ticket(
            db,
            title="Software Update Stuck",
            description="Windows update is stuck at 45% and prevents the computer from restarting.",
            category="Software",
            priority=TicketPriority.MEDIUM,
            department="IT Support",
            created_at=now - timedelta(days=random.randint(10, 60)),
            ai_summary="Windows update cache was corrupted and blocking progress.",
            resolution_notes="Update cache was cleared, Windows Update service was reset, and updates were re-applied successfully.",
        )
        create_ticket(
            db,
            title="Shared Calendar Not Syncing",
            description="Team shared calendar is not syncing with Outlook. Events are missing for the whole week.",
            category="Software",
            priority=TicketPriority.MEDIUM,
            department="IT Support",
            created_at=now - timedelta(days=random.randint(10, 60)),
            ai_summary="Outlook cache mode was causing sync conflicts with the shared calendar.",
            resolution_notes="Outlook cache was rebuilt, shared calendar was re-added, and sync status returned to normal.",
        )
        create_ticket(
            db,
            title="VoIP Phone Not Registering",
            description="Office VoIP phone shows no registration and cannot make or receive calls.",
            category="Network & VPN",
            priority=TicketPriority.HIGH,
            department="Network Support",
            created_at=now - timedelta(days=random.randint(10, 60)),
            ai_summary="VoIP phone lost its DHCP lease and could not reach the SIP server.",
            resolution_notes="Phone was rebooted and network settings were restored. Phone registered successfully and calls were tested.",
        )

        db.commit()
        total = db.query(Ticket).count()
        print(f"\nTotal tickets in database: {total}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
