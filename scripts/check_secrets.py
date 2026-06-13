import json
import sys

with open("findings/secrets_raw.json") as f:
    data = json.load(f)

results = data.get("results", {})
total_secrets = sum(len(v) for v in results.values())

if total_secrets > 0:
    print(f"\n[FAIL] {total_secrets} secret(s) detected:\n")
    for filepath, secrets in results.items():
        for secret in secrets:
            print(f"  File: {filepath}")
            print(f"  Type: {secret['type']}")
            print(f"  Line: {secret['line_number']}")
            print()
    sys.exit(1)
else:
    print("[PASS] No secrets detected")
    