import json
import os

os.makedirs("findings", exist_ok=True)

with open("findings/sca_findings.json") as f:
    raw = json.load(f)

findings = []
counter = 1

for dep in raw.get("dependencies", []):
    for vuln in dep.get("vulns", []):
        findings.append(f"SCA-{counter:03d}-{vuln.get('id', 'UNKNOWN')}")
        counter += 1

# Deduplicate while preserving order
seen = set()
unique_findings = []
for f in findings:
    if f not in seen:
        seen.add(f)
        unique_findings.append(f)

summary = {
    "scanner": "sca",
    "count": len(unique_findings),
    "findings": unique_findings
}

with open("findings/sca_summary.json", "w") as f:
    json.dump(summary, f, indent=2)

print(f"SCA: {len(unique_findings)} findings detected")
print(json.dumps(summary, indent=2))