# security-guardrails-platform
# Security Guardrails Platform

A build-focused security pipeline that enforces infrastructure, application, dependency, and secrets controls on every commit. Detection is separated from decision. Scanners publish findings as artifacts. A dedicated security gate owns the block decision.

Built as a hands-on demonstration of shift-left security engineering — not scanner integration, but a platform that manages detection, governance, enrichment, and enforcement as independent concerns.

---

## What This Platform Enforces

| Scanner | Control | Finding IDs |
|---------|---------|-------------|
| OPA/Conftest | S3 bucket encryption required | S3-001 |
| Semgrep | Command injection via `shell=True` | SAST-001 |
| Semgrep | Code injection via `eval()` | SAST-002 |
| Semgrep | Unsafe pickle deserialization | SAST-003 |
| pip-audit | Known CVEs in Python dependencies | SCA-001 through SCA-011 |
| detect-secrets | Hardcoded AWS credentials | SECRET-001 |

**Standards coverage:** OWASP A03, SOC2-CC6.1, SOC2-CC6.3, NIST-SI-2

---

## Pipeline Architecture

```
┌─────────────────────────────────────────┐
│           SOURCE CONTROL                │
│  insecure.tf        vulnerable_app.py   │
│  suppressions.yaml  policies/s3.rego    │
│  semgrep/custom-rules.yml               │
│  requirements.txt                       │
└────────────────┬────────────────────────┘
                 │ git push
                 ▼
┌─────────────────────────────────────────┐
│           SCANNER LAYER                 │
│  OPA/Conftest  → opa_findings.json      │
│  Semgrep       → sast_findings.json     │
│  detect-secrets→ secrets_raw.json       │
│  pip-audit     → sca_findings.json      │
│                                         │
│  All jobs use if: always() on upload    │
│  Scanners never own the exit decision   │
└────────────────┬────────────────────────┘
                 │ actions/upload-artifact
                 ▼
┌─────────────────────────────────────────┐
│         ARTIFACT STORAGE                │
│  GitHub Actions Artifacts               │
│  Findings persist across isolated jobs  │
└────────────────┬────────────────────────┘
                 │ actions/download-artifact
                 ▼
┌─────────────────────────────────────────┐
│       SUPPRESSION GOVERNANCE            │
│  validate_suppressions.py               │
│  Enforces: owner, approver, ticket,     │
│  expiry, reason on every suppression    │
│  Rejects expired or incomplete entries  │
│  Outputs: valid_suppressions.json       │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│       REMEDIATION ENRICHMENT            │
│  enrich.py                              │
│  Loads all scanner artifacts            │
│  Applies suppression decisions          │
│  Marks each finding OPEN / SUPPRESSED   │
│  Writes findings.json                   │
│  Exits 0 always — owns no gate logic    │
└────────────────┬────────────────────────┘
                 │ upload enriched-findings
                 ▼
┌─────────────────────────────────────────┐
│           SECURITY GATE                 │
│  security_gate.py                       │
│  Reads findings.json                    │
│  Blocks on HIGH/CRITICAL unsuppressed   │
│  Owns sys.exit(1) — single exit point   │
└────────────────┬────────────────────────┘
                 │
        ┌────────┴────────┐
        ▼                 ▼
      PASS              FAIL
```

---

## Real Pipeline Output

From a live run against the intentionally vulnerable targets in this repository:

```
Finding: S3-001                          [OPEN]
Finding: semgrep.SAST-001-command-injection  [OPEN]
Finding: semgrep.SAST-002-eval-injection     [OPEN]
Finding: semgrep.SAST-003-pickle-deserialization [SUPPRESSED]
Finding: SCA-001-PYSEC-2021-108          [OPEN]
Finding: SCA-002-PYSEC-2020-149          [OPEN]
Finding: SCA-003-PYSEC-2020-148          [OPEN]
Finding: SCA-004-PYSEC-2023-192          [OPEN]
Finding: SCA-005-PYSEC-2023-212          [OPEN]
Finding: SCA-006-PYSEC-2026-141          [OPEN]
Finding: SCA-007-CVE-2024-37891          [OPEN]
Finding: SCA-008-CVE-2025-50181          [OPEN]
Finding: SCA-009-CVE-2025-66418          [OPEN]
Finding: SCA-010-CVE-2025-66471          [OPEN]
Finding: SCA-011-CVE-2026-21441          [OPEN]
Finding: SECRET-001                      [OPEN]

Total findings: 16
Suppressed: 1 (SAST-003 — SEC-1847, approved by security-team, expires 2027-03-01)
Open: 15

[FAIL] Build blocked by: S3-001, semgrep.SAST-001-command-injection,
semgrep.SAST-002-eval-injection, SCA-001 through SCA-011, SECRET-001
```

---

## Suppression Governance

Suppressions are not scanner tuning. They are documented risk acceptance decisions.

Every suppression requires:

```yaml
- id: SAST-003
  owner: platform-team
  reason: >
    pickle.loads() used only with internally serialized data from
    trusted pipeline artifacts. External input never reaches this function.
    Tracked in risk register RR-2025-019.
  expiry: "2027-03-01"
  approver: security-team
  approved_date: "2025-07-01"
  ticket: "SEC-1847"
```

Missing any field → suppression rejected at governance stage.
Expired suppression → finding returns to OPEN, gate blocks.

---

## Remediation Catalog

Each finding ID maps to structured remediation guidance:

**S3-001 — S3 Bucket Encryption Missing** `SOC2-CC6.1`
```hcl
resource "aws_s3_bucket_server_side_encryption_configuration" "example" {
  bucket = aws_s3_bucket.demo.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}
```

**SAST-001 — Command Injection** `OWASP-A03`
Remove `shell=True`. Pass arguments as a list. Validate all input before system calls.

**SAST-002 — eval() Code Injection** `OWASP-A03`
Remove `eval()`. Use `ast.literal_eval()` for safe literal parsing.

**SECRET-001 — Hardcoded AWS Credentials** `SOC2-CC6.3`
Remove immediately. Rotate in AWS IAM. Use environment variables or AWS Secrets Manager.

**SCA-001 — Vulnerable Dependency** `NIST-SI-2`
Upgrade to fixed version per CVE advisory. Pin version in `requirements.txt`.

---

## OPA Policy — Infrastructure as Code Enforcement

```rego
package main

deny contains msg if {
    resource := input.resource.aws_s3_bucket[_]
    not resource.server_side_encryption_configuration
    msg := sprintf(
        "S3-001: S3 bucket '%v' missing encryption configuration",
        [resource.bucket]
    )
}
```

Policy is evaluated against `terraform/plan.json` using Conftest v0.68.2.
Failures are parsed into structured finding IDs and published as artifacts.

---

## Semgrep Custom Rules

Three rules targeting high-severity Python vulnerabilities:

```yaml
SAST-001-command-injection    subprocess.run($X, shell=True)   ERROR
SAST-002-eval-injection       eval($X)                         ERROR
SAST-003-pickle-deserialization pickle.loads($X)               WARNING
```

Rules are version-controlled alongside the codebase. Violations produce
finding IDs that flow through governance before reaching the gate.

---

## Key Architectural Decisions

**Scanners never own the exit decision.**
If a scanner calls `sys.exit(1)` on findings, its artifact upload is skipped.
The artifact only exists when there are no findings — inverting the pipeline's purpose.
Solution: `if: always()` on every upload step. Gate owns the only `sys.exit(1)`.

**Enrichment exits 0 always.**
Enrichment is a data transformation step. If enrichment fails the build,
`findings.json` is never written, the gate never runs, and no findings are published.
Detection and decision are separate concerns.

**Artifacts are the contract between jobs.**
GitHub Actions jobs run on isolated ephemeral runners. Files do not persist.
`upload-artifact` and `download-artifact` are the only mechanism for passing
state between jobs. Every scanner publishes its output regardless of exit code.

**Suppression is governance, not configuration.**
Suppressions require owner, approver, ticket reference, expiry date, and documented reason.
A suppression without a ticket is rejected. An expired suppression returns the finding
to OPEN. Permanent exceptions are not permitted.

---

## Repository Structure

```
├── .github/workflows/security.yml   # Pipeline definition
├── policies/s3.rego                 # OPA infrastructure policy
├── semgrep/custom-rules.yml         # SAST custom rules
├── suppressions/suppressions.yaml   # Suppression registry
├── remediation/remediation_catalog.yaml  # Remediation guidance per finding
├── scripts/
│   ├── tf_to_json.py                # Terraform plan serializer
│   ├── generate_opa_findings.py     # Conftest output parser
│   ├── check_sast.py                # SAST findings normalizer
│   ├── check_secrets.py             # Secrets findings normalizer
│   ├── check_dependencies.py        # SCA findings normalizer
│   ├── validate_suppressions.py     # Suppression governance enforcer
│   ├── enrich.py                    # Findings enrichment engine
│   └── security_gate.py             # Gate — owns exit decision
├── terraform/insecure.tf            # Intentionally vulnerable IaC
├── scripts/vulnerable_app.py        # Intentionally vulnerable Python
├── FAILURES.md                      # Build failures and root causes
└── DECISIONS.md                     # Architectural decisions and tradeoffs
```

---

## What Is Intentionally Vulnerable

This repository contains deliberately insecure code for pipeline validation:

`terraform/insecure.tf` — S3 bucket without encryption (triggers S3-001)
`scripts/vulnerable_app.py` — `subprocess.run(shell=True)`, `eval()`, `pickle.loads()` (triggers SAST-001, SAST-002, SAST-003)
`requirements.txt` — Pinned to `urllib3==1.25.4` with 11 known CVEs (triggers SCA-001 through SCA-011)

These are not accidents. They are the test corpus that proves the pipeline catches real vulnerabilities.

---

## Known Gaps and Planned Improvements

| Gap | Impact | Priority |
|-----|--------|----------|
| Only 1 Rego policy (S3 encryption) | OPA coverage limited to one control | High |
| Severity hardcoded to HIGH in enrich.py | Gate cannot distinguish CRITICAL vs MEDIUM | High |
| No suppression expiry enforcement at gate runtime | Expired suppressions not rechecked until validate_suppressions runs | Medium |
| Secret finding lacks file path and line number | SECRET-001 has no location context | Medium |
| No findings history or trend tracking | Cannot measure FP rate or MTTD over time | Low |

---

## Build Failures Encountered

Twelve real failures documented during this build. Selected highlights:

**Step ordering (opa_findings.json always empty):** Debug and generate steps placed before conftest executed. Files produced by step N are not available to step N-1. Fixed by reordering steps.

**Artifact not found (sast-findings):** Missing `if: always()` on upload step. When semgrep found violations, the upload was skipped. Artifact only existed when there were no findings.

**SCA duplicate finding IDs:** Used dependency loop index as finding number prefix. Multiple CVEs in the same dependency received identical IDs. Fixed with global counter and `seen` set deduplication.

Full failure log: [FAILURES.md](./FAILURES.md)
Full decision log: [DECISIONS.md](./DECISIONS.md)






```
┌─────────────────────────────────────────┐
│           SOURCE CONTROL                │
│  insecure.tf  vulnerable_app.py         │
│  suppressions.yaml  policies/*.rego     │
│  semgrep/custom-rules.yml               │
│  requirements.txt                       │
└────────────────┬────────────────────────┘
                 │ git push
                 ▼
┌─────────────────────────────────────────┐
│           SCANNER LAYER                 │
│  OPA/Conftest  → opa_findings.json      │  ⚠️ 1 policy, needs 6
│  Semgrep       → sast_findings.json     │  ✅
│  detect-secrets→ secrets_raw.json       │  ✅
│  pip-audit     → sca_findings.json      │  ✅
└────────────────┬────────────────────────┘
                 │ actions/upload-artifact
                 │ if: always()
                 ▼
┌─────────────────────────────────────────┐
│         ARTIFACT STORAGE                │
│  GitHub Actions Artifacts               │  ✅
└────────────────┬────────────────────────┘
                 │ actions/download-artifact
                 ▼
┌─────────────────────────────────────────┐
│       SUPPRESSION GOVERNANCE            │
│  validate_suppressions.py               │
│  suppressions.yaml → valid_suppres.json │  ⚠️ no expiry enforcement
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│       REMEDIATION ENRICHMENT            │
│  enrich.py                              │
│  loads all findings + suppressions      │
│  marks OPEN / SUPPRESSED                │  ⚠️ severity hardcoded HIGH
│  writes findings.json                   │
│  exits 0 always                         │  ✅
└────────────────┬────────────────────────┘
                 │ upload enriched-findings
                 ▼
┌─────────────────────────────────────────┐
│           SECURITY GATE                 │
│  security_gate.py                       │
│  blocks on HIGH/CRITICAL unsuppressed   │  ✅
│  owns sys.exit(1)                       │  ✅
└────────────────┬────────────────────────┘
                 │
        ┌────────┴────────┐
        ▼                 ▼
      PASS              FAIL
```
