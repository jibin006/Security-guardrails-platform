import json
import sys

with open("findings/findings.json") as f:
    findings = json.load(f)

blocking = []

for finding in findings:
    if (
        not finding["suppressed"]
        and finding["severity"] in ["CRITICAL"]
    ):
        blocking.append(finding["id"])

print(f"\nBlocking Findings: {blocking}")

if blocking:
    print(f"\n[FAIL] Build blocked by: {', '.join(blocking)}")
    sys.exit(1)

print("\n[PASS] No blocking findings")