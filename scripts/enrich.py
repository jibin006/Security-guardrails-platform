import yaml
import json
import sys
from datetime import date

def load_catalog():
    with open("remediation/remediation_catalog.yaml") as f:
        return yaml.safe_load(f)

def load_suppressions():
    try:
        with open("findings/valid_suppressions.json") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def enrich_finding(finding_id, catalog, suppressions):
    info = catalog.get(finding_id, {})
    suppressed = finding_id in suppressions
    
    return {
        "id": finding_id,
        "title": info.get("title", "Unknown Finding"),
        "severity": info.get("severity", "UNKNOWN"),
        "risk": info.get("risk", "").strip(),
        "fix": info.get("fix", "").strip(),
        "reference": info.get("reference", ""),
        "standard": info.get("standard", ""),
        "suppressed": suppressed,
        "status": "SUPPRESSED" if suppressed else "OPEN",
        "generated_date": str(date.today())
    }

def print_enriched(finding):
    status_label = "[SUPPRESSED]" if finding["suppressed"] else "[OPEN]"
    print(f"\n{'='*60}")
    print(f"Finding: {finding['id']} {status_label}")
    print(f"{'='*60}")
    print(f"Title:     {finding['title']}")
    print(f"Severity:  {finding['severity']}")
    print(f"Status:    {finding['status']}")
    print(f"Standard:  {finding['standard']}")
    print(f"\nRisk:")
    print(f"  {finding['risk'][:120]}")
    print(f"\nFix:")
    print(f"  {finding['fix'][:120]}")
    print(f"\nReference: {finding['reference']}")
    print()

# Simulate findings from all scanners
raw_findings = ["S3-001", "SAST-001", "SAST-002", "SAST-003"]

catalog = load_catalog()
suppressions = load_suppressions()

enriched = []
blocked = []

for fid in raw_findings:
    finding = enrich_finding(fid, catalog, suppressions)
    enriched.append(finding)
    print_enriched(finding)
    
    if not finding["suppressed"] and finding["severity"] in ["HIGH", "CRITICAL"]:
        blocked.append(fid)

# Write findings inventory
with open("findings/findings.json", "w") as f:
    json.dump(enriched, f, indent=2)

print(f"\n[SUMMARY]")
print(f"  Total findings:   {len(enriched)}")
print(f"  Suppressed:       {len([f for f in enriched if f['suppressed']])}")
print(f"  Open:             {len([f for f in enriched if not f['suppressed']])}")
print(f"  Blocking build:   {len(blocked)}")

if blocked:
    print(f"\n[FAIL] Build blocked by: {', '.join(blocked)}")
    sys.exit(1)

print("\n[PASS] No blocking findings")