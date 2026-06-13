import json
import os

os.makedirs("findings", exist_ok=True)

with open("findings/sast_findings.json") as f:
    raw = json.load(f)

findings = [r.get("check_id", f"SAST-{i:03d}") for i, r in enumerate(raw.get("results", []), 1)]

summary = {
    "scanner": "sast",
    "count": len(findings),
    "findings": findings
}

with open("findings/sast_summary.json", "w") as f:
    json.dump(summary, f, indent=2)

print(f"SAST: {len(findings)} findings detected")
print(json.dumps(summary, indent=2))