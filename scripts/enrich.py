import json
import os
import sys

os.makedirs("findings", exist_ok=True)

# Load suppressions
suppressed_ids = []
try:
    with open("findings/valid_suppressions.json") as f:
        suppressed_ids = json.load(f)
except Exception as e:
    print(f"Warning: could not load suppressions: {e}")


def load_findings():
    findings = []

    try:
        with open("findings/opa_findings.json") as f:
            data = json.load(f)
            findings.extend(data.get("findings", []))
            print(f"OPA findings loaded: {data.get('findings', [])}")
    except Exception as e:
        print(f"Warning: opa_findings.json not found: {e}")

    try:
        with open("findings/sast_findings.json") as f:
            raw = json.load(f)
            ids = [r.get("check_id", f"SAST-{i:03d}") for i, r in enumerate(raw.get("results", []), 1)]
            findings.extend(ids)
            print(f"SAST findings loaded: {ids}")
    except Exception as e:
        print(f"Warning: sast_findings.json not found: {e}")

    try:
        with open("findings/sca_findings.json") as f:
            raw = json.load(f)
            ids = []
            for i, dep in enumerate(raw.get("dependencies", []), 1):
                for vuln in dep.get("vulns", []):
                    ids.append(f"SCA-{i:03d}-{vuln.get('id', 'UNKNOWN')}")
            findings.extend(ids)
            print(f"SCA findings loaded: {ids}")
    except Exception as e:
        print(f"Warning: sca_findings.json not found: {e}")

    try:
        with open("findings/secrets_raw.json") as f:
            raw = json.load(f)
            results = raw.get("results", {})
            ids = [f"SECRET-{i:03d}" for i in range(1, len(results) + 1)]
            findings.extend(ids)
            print(f"Secrets findings loaded: {ids}")
    except Exception as e:
        print(f"Warning: secrets_raw.json not found: {e}")

    return findings


raw_findings = load_findings()

enriched = []
blocked = []

for fid in raw_findings:
    suppressed = fid in suppressed_ids
    severity = "HIGH"  # Default; extend with real severity mapping per scanner

    entry = {
        "id": fid,
        "suppressed": suppressed,
        "severity": severity
    }

    enriched.append(entry)

    status = "SUPPRESSED" if suppressed else "OPEN"
    print(f"Finding: {fid} [{status}]")

    if not suppressed:
        blocked.append(fid)

# Write enriched findings for security gate
with open("findings/findings.json", "w") as f:
    json.dump(enriched, f, indent=2)

print("\nEnrichment complete")
print(f"Total findings: {len(enriched)}")
print(f"Suppressed: {len(enriched) - len(blocked)}")
print(f"Open: {len(blocked)}")