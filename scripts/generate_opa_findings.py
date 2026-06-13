import json
import os

os.makedirs("findings", exist_ok=True)

# OPA violations are written to stdout by conftest.
# For now, we define known violations from plan analysis.
# In a real pipeline, parse conftest --output json instead.

findings = {
    "scanner": "opa",
    "count": 0,
    "findings": []
}

# Switch conftest to JSON output and parse it here.
# conftest test terraform/plan.json --policy policies/ --output json > findings/conftest_raw.json
conftest_raw_path = "findings/conftest_raw.json"
if os.path.exists(conftest_raw_path):
    with open(conftest_raw_path) as f:
        raw = json.load(f)
    for result in raw:
        for failure in result.get("failures", []):
            findings["findings"].append(failure.get("msg", "OPA-UNKNOWN"))
    findings["count"] = len(findings["findings"])

with open("findings/opa_findings.json", "w") as f:
    json.dump(findings, f, indent=2)

print(f"OPA: {findings['count']} findings")
print(json.dumps(findings, indent=2))