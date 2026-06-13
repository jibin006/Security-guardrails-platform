import json
import os

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

    # OPA Findings
    try:
        with open("findings/opa_findings.json") as f:
            data = json.load(f)

            ids = data.get("findings", [])

            findings.extend(ids)

            print(f"OPA findings loaded: {ids}")

    except Exception as e:
        print(f"Warning: opa_findings.json not found: {e}")

    # SAST Findings (Normalized)
    try:
        with open("findings/sast_findings.json") as f:
            raw = json.load(f)

        mapping = {
            "semgrep.SAST-001-command-injection": "SAST-001",
            "semgrep.SAST-002-eval-injection": "SAST-002",
            "semgrep.SAST-003-pickle-deserialization": "SAST-003"
        }

        ids = []

        for result in raw.get("results", []):
            check_id = result.get("check_id")

            canonical_id = mapping.get(check_id)

            if canonical_id:
                ids.append(canonical_id)

        findings.extend(ids)

        print(f"SAST findings loaded: {ids}")

    except Exception as e:
        print(f"Warning: sast_findings.json not found: {e}")

    # SCA Findings
    try:
        with open("findings/sca_findings.json") as f:
            raw = json.load(f)

        ids = []
        seen = set()
        counter = 1

        for dep in raw.get("dependencies", []):
            for vuln in dep.get("vulns", []):

                vuln_id = vuln.get("id", "UNKNOWN")

                if vuln_id not in seen:
                    seen.add(vuln_id)

                    finding_id = f"SCA-{counter:03d}-{vuln_id}"

                    ids.append(finding_id)

                    counter += 1

        findings.extend(ids)

        print(f"SCA findings loaded: {ids}")

    except Exception as e:
        print(f"Warning: sca_findings.json not found: {e}")

    # Secrets Findings
    try:
        with open("findings/secrets_raw.json") as f:
            raw = json.load(f)

        results = raw.get("results", {})

        ids = [
            f"SECRET-{i:03d}"
            for i in range(1, len(results) + 1)
        ]

        findings.extend(ids)

        print(f"Secrets findings loaded: {ids}")

    except Exception as e:
        print(f"Warning: secrets_raw.json not found: {e}")

    # Global Deduplication
    findings = list(dict.fromkeys(findings))

    return findings


raw_findings = load_findings()

enriched = []
blocked = []

for fid in raw_findings:

    suppressed = fid in suppressed_ids

    severity = "HIGH"

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

with open("findings/findings.json", "w") as f:
    json.dump(enriched, f, indent=2)

print("\nEnrichment complete")
print(f"Total findings: {len(enriched)}")
print(f"Suppressed: {len(enriched) - len(blocked)}")
print(f"Open: {len(blocked)}")