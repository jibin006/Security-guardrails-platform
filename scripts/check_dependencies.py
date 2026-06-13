import json
import os

os.makedirs("findings", exist_ok=True)

with open("findings/sca_findings.json") as f:
    raw = json.load(f)

vulns = raw.get("dependencies", [])
findings = []
for i, dep in enumerate(vulns, 1):
    for vuln in dep.get("vulns", []):
        findings.append(f"SCA-{i:03d}-{vuln.get('id', 'UNKNOWN')}")

summary = {
    "scanner": "sca",
    "count": len(findings),
    "findings": findings
}

with open("findings/sca_summary.json", "w") as f:
    json.dump(summary, f, indent=2)

print(f"SCA: {len(findings)} findings detected")
print(json.dumps(summary, indent=2))