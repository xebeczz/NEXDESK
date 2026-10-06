"""Temporary test for resolution_guide.py — clean version."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/backend")

from app.services import ai_rules, resolution_guide as rg

CASES = [
    ("VPN Not Working", "VPN is not working for me"),
    ("Server Down", "The server is completely down"),
    ("Printer Not Working", "The printer is not working and not printing"),
    ("Email Not Working", "Email is not working, I cannot send emails"),
    ("Computer Not Turning On", "My computer is not turning on"),
    ("Application Crashing", "The application keeps crashing"),
    ("Database Connection Failed", "Database connection failed"),
    ("Password Reset Required", "I need a password reset"),
    ("Internet Not Working", "The internet is not working"),
    ("Security/Unauthorized Access Alert", "I got a security unauthorized access alert"),
]

print("=== Issue title mapping ===")
for label, text in CASES:
    analysis = ai_rules.build_analysis(text)
    title = rg.issue_title(analysis, text)
    print(f"  {label:<42} -> {title}")

print()
print("=== Response structure check ===")
required = ["AI ANALYSIS", "RECOMMENDED RESOLUTION", "Basic Checks", "Troubleshooting",
            "Configuration Checks", "Verification", "IF THE ISSUE PERSISTS",
            "INFORMATION TO COLLECT", "ESCALATION / NEXT ACTION", "SIMILAR TICKETS"]
all_ok = True
for label, text in CASES:
    analysis = ai_rules.build_analysis(text)
    resp = rg.build_professional_response(analysis, text)
    missing = [s for s in required if s not in resp]
    if missing:
        all_ok = False
    print(f"  {label:<42} {'OK' if not missing else 'MISSING: ' + str(missing)}")

print()
print("=== Content differs per issue ===")
vm = rg.build_professional_response(ai_rules.build_analysis("VPN not working all day"), "VPN not working all day")
pm = rg.build_professional_response(ai_rules.build_analysis("Printer not printing"), "Printer not printing")
ss = rg.build_professional_response(ai_rules.build_analysis("Server down production"), "Server down production")
print("  VPN mentions VPN:", "VPN" in vm)
print("  Printer mentions printer:", "Printer" in pm)
print("  Server mentions service:", "Service" in ss)

print()
print("=== All guides resolve (no crash) ===")
for label, text in CASES:
    analysis = ai_rules.build_analysis(text)
    g = rg.get_guide(analysis["intent"], text, analysis)
    assert g, f"No guide for {label}"
    assert set(["basic_checks", "troubleshooting", "configuration_checks",
                "verification", "if_persists", "info_to_collect"]).issubset(g), f"Missing keys {label}"
print("  All 10 issues resolved a complete guide.")
print()
print("ALL PASS" if all_ok else "SOME FAILED")