import json
import os

os.makedirs("findings", exist_ok=True)

with open("findings/secrets_raw.json") as f:
    raw = json.load(f)

results = raw.get("results", {})
findings = list(results.keys())

summary = {
    "scanner": "secrets",
    "count": len(findings),
    "findings": [f"SECRET-{i:03d}" for i in range(1, len(findings) + 1)]
}

with open("findings/secrets_summary.json", "w") as f:
    json.dump(summary, f, indent=2)

print(f"Secrets: {len(findings)} findings detected")
print(json.dumps(summary, indent=2))