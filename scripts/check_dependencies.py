import json
import sys

try:
    with open("findings/sca_findings.json") as f:
        data = json.load(f)
except FileNotFoundError:
    print("[FAIL] Dependency findings file missing")
    sys.exit(1)

vulnerabilities = data.get("dependencies", [])
critical_count = 0

print(f"\n[SCA] Dependency scan results:\n")

for dep in vulnerabilities:
    vulns = dep.get("vulns", [])
    if vulns:
        for vuln in vulns:
            severity = vuln.get("fix_versions", [])
            print(f"  Package: {dep['name']}=={dep['version']}")
            print(f"  CVE:     {vuln['id']}")
            print(f"  Fix:     Upgrade to {vuln.get('fix_versions', ['unknown'])[0] if vuln.get('fix_versions') else 'no fix available'}")
            print()
            critical_count += 1

if critical_count > 0:
    print(f"[FAIL] {critical_count} vulnerable package(s) detected.")
    sys.exit(1)

print("[PASS] No vulnerable dependencies detected")