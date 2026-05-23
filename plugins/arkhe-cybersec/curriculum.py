#!/usr/bin/env python3
"""
ARKHE OS — Substrate 613 Cybersecurity Curriculum
Arquiteto: ORCID 0009-0005-2697-4668
"""

CURRICULUM = {
    "P1": {
        "name": "Linux Basics",
        "topics": [
            {"id": "613.P1.1", "name": "Linux Command Line Essentials", "tools": ["bash", "zsh"], "prerequisites": [],
             "content": "Master the Linux terminal: file navigation (cd, ls, pwd), file manipulation (cp, mv, rm, touch), text processing (grep, awk, sed), and I/O redirection (>, >>, |).\n\nKey commands:\n• ls -la — list all files with permissions\n• chmod 755 — change file permissions\n• ps aux — list running processes\n• find / -name '*.log' — search for files"},
            {"id": "613.P1.2", "name": "File System and Permissions", "tools": ["chmod", "chown"], "prerequisites": ["613.P1.1"],
             "content": "Understand the Linux filesystem hierarchy (FHS), user/group ownership, and the permission model (rwx for user, group, others).\n\nPermission notation:\n• r=4, w=2, x=1\n• 755 = rwxr-xr-x\n• 644 = rw-r--r--"},
            {"id": "613.P1.3", "name": "Process Management", "tools": ["ps", "top", "htop"], "prerequisites": ["613.P1.1"],
             "content": "Monitor and control running processes. Understand foreground vs background jobs, signals (SIGTERM, SIGKILL, SIGSTOP), and process priorities (nice/renice)."},
            {"id": "613.P1.4", "name": "Package Management", "tools": ["apt", "dpkg", "snap"], "prerequisites": ["613.P1.1"],
             "content": "Install, update, and remove software using APT (Advanced Package Tool). Understand repositories, dependencies, and package states."},
            {"id": "613.P1.5", "name": "Shell Scripting Basics", "tools": ["bash", "sh"], "prerequisites": ["613.P1.1"],
             "content": "Write simple shell scripts to automate tasks. Variables, conditionals (if/else), loops (for/while), functions, and error handling."},
        ]
    },
    "P2": {
        "name": "Lab Setup",
        "topics": [
            {"id": "613.P2.1", "name": "Virtualization", "tools": ["VirtualBox", "VMware"], "prerequisites": [],
             "content": "Set up isolated virtual machines for security testing. Understand hypervisor types, network modes (NAT, bridged, host-only), and resource allocation."},
            {"id": "613.P2.2", "name": "Kali Linux Installation", "tools": ["Kali Linux"], "prerequisites": ["613.P2.1"],
             "content": "Install and configure Kali Linux as a security testing platform. Update tools, configure repositories, and set up persistence on USB."},
            {"id": "613.P2.3", "name": "Isolated Network Setup", "tools": ["VirtualBox", "pfSense"], "prerequisites": ["613.P2.1"],
             "content": "Create isolated virtual networks for safe experimentation. Use internal network adapters, configure DHCP, and ensure no traffic leaks to the host network."},
            {"id": "613.P2.4", "name": "Snapshots and Restore", "tools": ["VirtualBox"], "prerequisites": ["613.P2.1"],
             "content": "Use VM snapshots to save and restore machine states. Essential for resetting lab environments after exploitation exercises."},
        ]
    },
    "P3": {
        "name": "Networking Fundamentals",
        "topics": [
            {"id": "613.P3.1", "name": "OSI Model and TCP/IP Stack", "tools": ["Wireshark"], "prerequisites": [],
             "content": "Understand the 7 layers of the OSI model and the 4 layers of the TCP/IP stack. Map protocols to layers (HTTP=7, TCP=4, IP=3, Ethernet=2)."},
            {"id": "613.P3.2", "name": "IP Addressing and Subnetting", "tools": ["ipcalc", "sipcalc"], "prerequisites": ["613.P3.1"],
             "content": "Master IPv4 addressing, subnet masks, CIDR notation, and subnet calculation. Understand public vs private IP ranges (RFC 1918)."},
            {"id": "613.P3.3", "name": "Common Protocols", "tools": ["tcpdump", "Wireshark"], "prerequisites": ["613.P3.1"],
             "content": "Analyze HTTP (port 80), HTTPS (443), DNS (53), DHCP (67/68), and ARP traffic. Understand request/response patterns and protocol headers."},
            {"id": "613.P3.4", "name": "Network Devices", "tools": ["GNS3", "Packet Tracer"], "prerequisites": ["613.P3.1"],
             "content": "Understand routers, switches, firewalls, and access points. Learn how they forward traffic, filter packets, and segment networks."},
        ]
    },
    "P4": {
        "name": "Wireless Security",
        "topics": [
            {"id": "613.P4.1", "name": "WiFi Encryption Standards", "tools": ["aircrack-ng"], "prerequisites": [],
             "content": "Compare WEP (broken), WPA (TKIP), WPA2 (AES-CCMP), and WPA3 (SAE). Understand the vulnerabilities of each standard and why WPA3 is preferred."},
            {"id": "613.P4.2", "name": "Wireless Reconnaissance", "tools": ["airodump-ng", "Kismet"], "prerequisites": ["613.P4.1"],
             "content": "Discover nearby WiFi networks, identify channels, signal strength, and client devices. Understand monitor mode and packet injection."},
            {"id": "613.P4.3", "name": "Common Wireless Attacks", "tools": ["aircrack-ng", "reaver", "hashcat"], "prerequisites": ["613.P4.2"],
             "content": "Study deauthentication attacks, WPA handshake capture, dictionary attacks, and WPS PIN brute-force. Focus on understanding the attack vectors, not execution on unauthorized networks."},
            {"id": "613.P4.4", "name": "Wireless Hardening", "tools": [], "prerequisites": ["613.P4.3"],
             "content": "Implement WPA3, strong pre-shared keys, MAC filtering, hidden SSIDs, and 802.1X authentication. Understand defense-in-depth for wireless networks."},
        ]
    },
    "P5": {
        "name": "Information Gathering",
        "topics": [
            {"id": "613.P5.1", "name": "OSINT Techniques", "tools": ["theHarvester", "Maltego", "Shodan"], "prerequisites": [],
             "content": "Gather information from public sources: search engines, social media, DNS records, WHOIS, and certificate transparency logs. Understand passive vs active reconnaissance."},
            {"id": "613.P5.2", "name": "DNS Enumeration", "tools": ["dig", "nslookup", "dnsenum", "dnsrecon"], "prerequisites": ["613.P5.1"],
             "content": "Enumerate DNS records (A, AAAA, MX, NS, TXT, CNAME). Perform zone transfers, subdomain discovery, and reverse DNS lookups."},
            {"id": "613.P5.3", "name": "Network Scanning (nmap)", "tools": ["nmap", "masscan"], "prerequisites": ["613.P3.2"],
             "content": "Master nmap for host discovery, port scanning, service version detection, and OS fingerprinting. Understand scan types (SYN, TCP connect, UDP) and timing options."},
            {"id": "613.P5.4", "name": "Service and Version Detection", "tools": ["nmap", "amap"], "prerequisites": ["613.P5.3"],
             "content": "Identify running services and their versions. Use banner grabbing and nmap scripts (NSE) to gather detailed service information."},
        ]
    },
    "P6": {
        "name": "Web Security Testing",
        "topics": [
            {"id": "613.P6.1", "name": "HTTP Request/Response Analysis", "tools": ["Burp Suite", "curl", "DevTools"], "prerequisites": [],
             "content": "Analyze HTTP methods (GET, POST, PUT, DELETE), headers, cookies, and response codes. Use intercepting proxies to view and modify traffic."},
            {"id": "613.P6.2", "name": "Web Application Architecture", "tools": [], "prerequisites": ["613.P6.1"],
             "content": "Understand client-server architecture, APIs (REST, GraphQL), authentication mechanisms (session-based, JWT, OAuth), and common frameworks."},
            {"id": "613.P6.3", "name": "Burp Suite / ZAP Basics", "tools": ["Burp Suite", "OWASP ZAP"], "prerequisites": ["613.P6.1"],
             "content": "Configure an intercepting proxy, set up browser proxying, install CA certificates for HTTPS inspection, and use the Repeater and Intruder tools."},
            {"id": "613.P6.4", "name": "Authentication Testing", "tools": ["Burp Suite", "Hydra"], "prerequisites": ["613.P6.3"],
             "content": "Test for weak passwords, brute-force protection, password reset flaws, and multi-factor authentication bypasses. Understand credential stuffing and password spraying."},
        ]
    },
    "P7": {
        "name": "SQL Injection",
        "topics": [
            {"id": "613.P7.1", "name": "SQL Fundamentals for Testers", "tools": ["sqlmap", "MySQL", "PostgreSQL"], "prerequisites": [],
             "content": "Learn basic SQL syntax: SELECT, WHERE, UNION, JOIN, and subqueries. Understand how databases process queries and how injection attacks manipulate them."},
            {"id": "613.P7.2", "name": "Error-Based and Union-Based Injection", "tools": ["sqlmap", "Burp Suite"], "prerequisites": ["613.P7.1"],
             "content": "Exploit error messages to extract database information. Use UNION SELECT to combine attacker-controlled data with legitimate query results."},
            {"id": "613.P7.3", "name": "Blind SQL Injection", "tools": ["sqlmap"], "prerequisites": ["613.P7.2"],
             "content": "Extract data when error messages are suppressed. Use boolean-based (true/false responses) and time-based (response delays) techniques."},
            {"id": "613.P7.4", "name": "Prevention and Parameterized Queries", "tools": [], "prerequisites": ["613.P7.3"],
             "content": "Implement prepared statements, input validation, stored procedures, and least-privilege database accounts. Use ORM frameworks that escape user input by default."},
        ]
    },
    "P8": {
        "name": "Cross-Site Scripting (XSS)",
        "topics": [
            {"id": "613.P8.1", "name": "Reflected, Stored, and DOM-Based XSS", "tools": ["Burp Suite", "XSStrike"], "prerequisites": [],
             "content": "Distinguish between reflected (immediate response), stored (persisted in database), and DOM-based (client-side JavaScript) XSS. Understand the attack flow for each type."},
            {"id": "613.P8.2", "name": "Payload Crafting", "tools": [], "prerequisites": ["613.P8.1"],
             "content": "Create XSS payloads that bypass filters: HTML entity encoding, JavaScript obfuscation, polyglot payloads, and filter evasion techniques."},
            {"id": "613.P8.3", "name": "Session Hijacking via XSS", "tools": [], "prerequisites": ["613.P8.2"],
             "content": "Use XSS to steal session cookies (document.cookie), perform actions on behalf of the victim, and chain with CSRF for advanced attacks."},
            {"id": "613.P8.4", "name": "Content Security Policy (CSP)", "tools": [], "prerequisites": ["613.P8.3"],
             "content": "Implement CSP headers to mitigate XSS: restrict script sources, disable inline scripts (nonce/hash-based), and report violations."},
        ]
    },
    "P9": {
        "name": "File Upload Vulnerabilities",
        "topics": [
            {"id": "613.P9.1", "name": "Unrestricted File Upload", "tools": ["Burp Suite"], "prerequisites": [],
             "content": "Exploit applications that allow arbitrary file uploads without validation. Upload web shells (PHP, ASPX, JSP) to gain remote code execution."},
            {"id": "613.P9.2", "name": "Bypassing Filters", "tools": [], "prerequisites": ["613.P9.1"],
             "content": "Bypass client-side (JavaScript) and server-side (extension, MIME type, content) filters. Use double extensions, null bytes, and magic number spoofing."},
            {"id": "613.P9.3", "name": "Web Shell Deployment", "tools": ["Weevely", "p0wny-shell"], "prerequisites": ["613.P9.2"],
             "content": "Deploy and use web shells for post-exploitation. Understand how to maintain access, escalate privileges, and pivot through the compromised host."},
            {"id": "613.P9.4", "name": "Secure File Handling", "tools": [], "prerequisites": ["613.P9.3"],
             "content": "Implement secure file upload: whitelist allowed extensions, validate MIME types, store files outside web root, rename files, and scan for malware."},
        ]
    },
    "P10": {
        "name": "Social Engineering Awareness",
        "topics": [
            {"id": "613.P10.1", "name": "Phishing and Spear-Phishing", "tools": ["GoPhish", "SET"], "prerequisites": [],
             "content": "Understand email-based social engineering: spoofed senders, malicious attachments, credential harvesting. Learn to identify red flags and conduct awareness training."},
            {"id": "613.P10.2", "name": "Pretexting and Baiting", "tools": [], "prerequisites": ["613.P10.1"],
             "content": "Study impersonation attacks (IT support, vendor, executive) and physical baiting (infected USB drives). Understand the psychology behind these attacks."},
            {"id": "613.P10.3", "name": "USB Drop Attacks", "tools": ["Rubber Ducky"], "prerequisites": ["613.P10.2"],
             "content": "Understand how malicious USB devices (keystroke injection, autorun payloads) can compromise systems. Learn to disable autorun and implement device control policies."},
            {"id": "613.P10.4", "name": "Security Awareness Training", "tools": [], "prerequisites": ["613.P10.3"],
             "content": "Design and deliver effective security awareness programs. Use simulated phishing campaigns, gamification, and regular reinforcement to build a security culture."},
        ]
    },
    "P11": {
        "name": "Security Monitoring",
        "topics": [
            {"id": "613.P11.1", "name": "Log Analysis", "tools": ["grep", "awk", "ELK Stack"], "prerequisites": [],
             "content": "Analyze system logs (syslog, auth.log, Apache/Nginx access logs) to detect security events. Understand log formats, rotation, and centralized collection."},
            {"id": "613.P11.2", "name": "Intrusion Detection Systems (IDS)", "tools": ["Snort", "Suricata"], "prerequisites": ["613.P11.1"],
             "content": "Deploy signature-based (Snort) and anomaly-based IDS. Understand rule creation, alert tuning, and false positive management."},
            {"id": "613.P11.3", "name": "SIEM Basics", "tools": ["Splunk", "ELK", "Wazuh"], "prerequisites": ["613.P11.2"],
             "content": "Understand Security Information and Event Management: log aggregation, correlation rules, dashboards, and incident response workflows."},
            {"id": "613.P11.4", "name": "Network Traffic Monitoring", "tools": ["Wireshark", "Zeek", "ntopng"], "prerequisites": ["613.P3.1"],
             "content": "Capture and analyze network traffic for anomalies. Detect port scans, C2 communication, data exfiltration, and protocol abuse."},
        ]
    },
    "P12": {
        "name": "Post-Exploitation Concepts",
        "topics": [
            {"id": "613.P12.1", "name": "Privilege Escalation", "tools": ["LinPEAS", "WinPEAS"], "prerequisites": [],
             "content": "Escalate from a low-privilege user to root/administrator. Exploit misconfigurations (SUID binaries, sudo rules, writable services) and kernel vulnerabilities."},
            {"id": "613.P12.2", "name": "Lateral Movement", "tools": ["PsExec", "WMI", "SSH"], "prerequisites": ["613.P12.1"],
             "content": "Move from one compromised host to another within a network. Use pass-the-hash, pass-the-ticket, and credential harvesting techniques."},
            {"id": "613.P12.3", "name": "Data Exfiltration", "tools": [], "prerequisites": ["613.P12.2"],
             "content": "Extract sensitive data from compromised systems: DNS tunneling, ICMP exfiltration, encrypted channels, and cloud storage exfiltration."},
            {"id": "613.P12.4", "name": "Persistence Mechanisms", "tools": [], "prerequisites": ["613.P12.3"],
             "content": "Maintain access to compromised systems: cron jobs, startup scripts, registry run keys, scheduled tasks, and backdoor user accounts."},
        ]
    },
}

def get_topic(topic_id):
    """Retrieve a topic by its ID (e.g., '613.P7.1')."""
    for p_id, p_data in CURRICULUM.items():
        for topic in p_data["topics"]:
            if topic["id"] == topic_id:
                return topic
    return None

def get_pillar_topics(pillar_id):
    """Retrieve all topics for a given pillar."""
    if pillar_id in CURRICULUM:
        return CURRICULUM[pillar_id]["topics"]
    return []