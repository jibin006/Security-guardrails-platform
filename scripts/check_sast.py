import json
import sys

with open("findings/sast_findings.json") as f:
    data = json.load(f)

findings = data.get("results", [])
errors = [f for f in findings if f.get("extra", {}).get("severity") == "ERROR"]

print(f"\n[SAST] {len(findings)} finding(s) detected ({len(errors)} ERROR severity)\n")

for finding in findings:
    print(f"  Rule:     {finding['check_id']}")
    print(f"  File:     {finding['path']}")
    print(f"  Line:     {finding['start']['line']}")
    print(f"  Severity: {finding['extra']['severity']}")
    print(f"  Message:  {finding['extra']['message'][:80]}")
    print()

if errors:
    print("[FAIL] ERROR severity findings detected. Fix before merge.")
    sys.exit(1)

print("[PASS] No ERROR severity SAST findings")