
Act as a cybersecurity consultant and help me build a polished, functional, Docker-based website that monitors the ports and connections on my network and displays potential security vulnerabilities. This is a human-in-the-loop class project: ask me exactly two questions before implementation—one about my operating system, Docker setup, and the network I own or am authorized to monitor, and one about my security priorities and dashboard preferences. I will answer each question in a separate message, creating three human interactions including this initial prompt; those will be my only two responses, so do not ask additional questions. Use my answers to guide the implementation, make reasonable assumptions for remaining details, and document those assumptions. Include device and service discovery, port and connection monitoring, evidence-based vulnerability prioritization, remediation recommendations, and an appealing dashboard with clear navigation and useful filters. Provide Docker configuration, setup instructions, and functional verification steps. Distinguish observed findings from suspected vulnerabilities, label any demonstration data, and explain monitoring limitations and anything you could not test. Finish by explaining how each of my answers influenced the result and how human involvement improved its quality and trustworthiness.

…
Tuesday 8:44 PM
Question 1 of 2: What operating system will run this project, what is your Docker setup (for example, Docker Desktop with WSL2, native Docker Engine, or not yet installed), and which network do you own or have explicit permission to monitor—including its subnet if known and any devices or addresses that must be excluded?

Tuesday 8:44 PM
docker desktop w WSL2 on my windows machine. just use my computers terminal to check if its ports are secured and how they could be hardened

Tuesday 8:47 PM
Question 2 of 2: Which security concerns should the dashboard prioritize—for example, internet-exposed services, unnecessary listening ports, remote access, or suspicious outbound connections—and what dashboard style and features would you prefer, such as dark or light mode, a risk summary, live connection tables, filters, and step-by-step hardening guidance?

Tuesday 8:47 PM
internet exposed services, unnecessary listening ports, suspicious outbound connections. dark mode, risk summary, live connection tables, filters. i will use that information to do my own hardening

Tuesday 8:48 PM
Built Portlight, now running with a background collector at http://127.0.0.1:9090.

It includes a dark dashboard, risk summaries, refreshing connection tables, filters, process/service discovery, passive device discovery, and evidence-based hardening guidance. Demonstration data is explicitly labeled.

Download the project
Setup instructions and Docker configuration
Verification results and limitations
Observed: RPC/NetBIOS/SMB and database listeners deserve review. All three Windows firewall profiles report enabled. Internet reachability, vulnerable software versions, and malicious traffic remain unverified. No hardening changes were applied.

Verified: 14 tests passed locally and inside Docker. A temporary listener appeared and disappeared correctly through the complete Windows-to-dashboard flow. Filters, finding details, demo separation, stale warnings, and background start/stop were checked. External exposure and remediation effectiveness were not tested.

Stop monitoring from the project folder with .\scripts\Stop-Portlight.ps1.

Dashboard preview showing explicitly labeled demonstration data

Your Windows/WSL2 and computer-only answer selected native Windows collection, Docker hosting, and strictly local monitoring. Your security and dashboard preferences shaped the priorities, dark interface, summaries, filters, and manual remediation guidance. Human involvement made the scope precise, improved technical correctness, and preserved your judgment over uncertain findings and hardening decisions.