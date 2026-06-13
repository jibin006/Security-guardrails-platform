import json
import os

os.makedirs("findings", exist_ok=True)

findings = {
    "scanner": "opa",
    "count": 0,
    "findings": []
}

conftest_raw_path = "findings/conftest_raw.json"
if os.path.exists(conftest_raw_path):
    with open(conftest_raw_path) as f:
        raw = json.load(f)
    for result in raw:
        for failure in result.get("failures", []):
            msg = failure.get("msg", "OPA-UNKNOWN")
            # Extract ID from message prefix e.g. "S3-001: ..."
            finding_id = msg.split(":")[0].strip()
            findings["findings"].append(finding_id)
    findings["count"] = len(findings["findings"])

with open("findings/opa_findings.json", "w") as f:
    json.dump(findings, f, indent=2)

print(f"OPA: {findings['count']} findings")
print(json.dumps(findings, indent=2))