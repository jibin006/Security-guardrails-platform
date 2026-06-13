# Security Guardrails Platform

A policy-as-code security pipeline that enforces infrastructure, application, dependency, and secrets controls on every commit. Built to demonstrate that detection and decision are separate engineering concerns — scanners publish findings as artifacts, a suppression governance layer validates exceptions, and a dedicated security gate owns the block decision.

---

## What This Platform Enforces

### Infrastructure (OPA/Conftest — 6 Rego Policies)

| Finding ID | Policy | Resource | Standard |
|------------|--------|----------|----------|
| S3-001 | S3 bucket missing encryption | `aws_s3_bucket` | SOC2-CC6.1 |
| S3-002 | S3 bucket public read access | `aws_s3_bucket` | SOC2-CC6.6 |
| IAM-001 | IAM policy contains wildcard action | `aws_iam_policy` | SOC2-CC6.1 |
| IAM-002 | Root user access key detected | `aws_iam_access_key` | SOC2-CC6.2 |
| SG-001 | Security group exposes SSH to internet | `aws_security_group` | NIST-AC-4 |
| LOG-001 | CloudTrail not configured | absence of `aws_cloudtrail` | SOC2-CC7.2 |

### Application (Semgrep — 3 Custom Rules)

| Finding ID | Rule | Pattern | Severity |
|------------|------|---------|----------|
| SAST-001 | Command injection | `subprocess.run($X, shell=True)` | ERROR |
| SAST-002 | Code injection | `eval($X)` | ERROR |
| SAST-003 | Unsafe deserialization | `pickle.loads($X)` | WARNING |

### Dependencies (pip-audit)

| Finding ID | Control |
|------------|---------|
| SCA-001 through SCA-011 | 11 real CVEs in `urllib3==1.25.4` including CVE-2024-37891, CVE-2025-50181, CVE-2026-21441 |

### Secrets (detect-secrets)

| Finding ID | Control |
|------------|---------|
| SECRET-001 | Hardcoded AWS access key in `insecure.tf` |
| SECRET-002 | Hardcoded root access key pattern in `insecure.tf` |

---

## Pipeline Architecture

```
┌─────────────────────────────────────────┐
│           SOURCE CONTROL                │
│  insecure.tf        vulnerable_app.py   │
│  suppressions.yaml  policies/*.rego     │
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
│  if: always() on every upload step      │
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

Live run against the intentionally vulnerable targets in this repository:

```
Finding: IAM-001                              [OPEN]
Finding: IAM-002                              [OPEN]
Finding: LOG-001                              [OPEN]
Finding: S3-001                               [OPEN]
Finding: S3-002                               [OPEN]
Finding: SG-001                               [OPEN]
Finding: semgrep.SAST-001-command-injection   [OPEN]
Finding: semgrep.SAST-002-eval-injection      [OPEN]
Finding: semgrep.SAST-003-pickle-deserialization [SUPPRESSED]
Finding: SCA-001-PYSEC-2021-108               [OPEN]
Finding: SCA-002-PYSEC-2020-149               [OPEN]
Finding: SCA-003-PYSEC-2020-148               [OPEN]
Finding: SCA-004-PYSEC-2023-192               [OPEN]
Finding: SCA-005-PYSEC-2023-212               [OPEN]
Finding: SCA-006-PYSEC-2026-141               [OPEN]
Finding: SCA-007-CVE-2024-37891               [OPEN]
Finding: SCA-008-CVE-2025-50181               [OPEN]
Finding: SCA-009-CVE-2025-66418               [OPEN]
Finding: SCA-010-CVE-2025-66471               [OPEN]
Finding: SCA-011-CVE-2026-21441               [OPEN]
Finding: SECRET-001                           [OPEN]
Finding: SECRET-002                           [OPEN]

Total findings: 22
Suppressed: 1 (SAST-003 — ticket SEC-1847, approved by security-team, expires 2027-03-01)
Open: 21

[FAIL] Build blocked by: IAM-001, IAM-002, LOG-001, S3-001, S3-002, SG-001,
semgrep.SAST-001-command-injection, semgrep.SAST-002-eval-injection,
SCA-001 through SCA-011, SECRET-001, SECRET-002
```

---

## Suppression Governance

Suppressions are documented risk acceptance decisions, not scanner configuration.

Every entry requires all six fields or it is rejected at governance time:

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

**Enforcement rules:**
- Missing any field → suppression rejected, finding remains OPEN
- Expired suppression → finding returns to OPEN automatically
- Permanent suppressions not permitted — every entry requires an expiry date

---

## Remediation Catalog

Every finding ID maps to structured remediation guidance covering severity, risk, fix, Terraform/code example, and compliance standard mapping.

| Finding | Title | Severity | Standard |
|---------|-------|----------|----------|
| S3-001 | S3 Bucket Encryption Missing | HIGH | SOC2-CC6.1 |
| S3-002 | S3 Bucket Public Access Enabled | CRITICAL | SOC2-CC6.6 |
| IAM-001 | IAM Policy Contains Wildcard Permissions | HIGH | SOC2-CC6.1 |
| IAM-002 | Root Access Key Usage Detected | CRITICAL | SOC2-CC6.2 |
| SG-001 | Security Group Allows Public SSH Access | HIGH | NIST-AC-4 |
| LOG-001 | CloudTrail Not Configured | HIGH | SOC2-CC7.2 |
| SAST-001 | Command Injection via subprocess | HIGH | OWASP-A03 |
| SAST-002 | Code Injection via eval() | HIGH | OWASP-A03 |
| SAST-003 | Unsafe Deserialization via pickle.loads() | MEDIUM | OWASP-A08 |
| SECRET-001/002 | Hardcoded AWS Credentials | CRITICAL | SOC2-CC6.3 |
| SCA-001–011 | Vulnerable Dependency Detected | HIGH | NIST-SI-2 |

Full catalog: [remediation/remediation_catalog.yaml](./remediation/remediation_catalog.yaml)

---

## Key Architectural Decisions

**Scanners never own the exit decision.**
If a scanner calls `sys.exit(1)` on findings, GitHub Actions skips all subsequent steps including artifact upload. The artifact only exists when there are no findings — inverting the pipeline's purpose. Solution: `if: always()` on every upload step. The security gate is the only job that calls `sys.exit(1)`.

**Enrichment exits 0 always.**
Enrichment is a data transformation step. If enrichment fails the build, `findings.json` is never written, the gate never runs, and no findings are published. Detection and decision are separate concerns with separate ownership.

**Artifacts are the contract between jobs.**
GitHub Actions jobs run on isolated ephemeral runners. Files written in one job do not exist in another. `upload-artifact` and `download-artifact` are the only mechanism for passing state between jobs. Every scanner publishes its output regardless of exit code.

**Step ordering is execution ordering.**
Debug and generate steps placed before the step that produces their input file will always see an empty or missing file. A file produced by step N is not available to step N-1. Discovered during build — documented in FAILURES.md entry 13.

**Suppression is governance, not configuration.**
Suppressions require owner, approver, ticket reference, expiry date, and documented reason. A suppression without a ticket is rejected at governance time. An expired suppression returns the finding to OPEN at the next run.

Full decision log: [DECISIONS.md](./DECISIONS.md)

---

## Repository Structure

```
├── .github/workflows/security.yml        # Pipeline — 7 jobs
├── policies/
│   ├── s3.rego                           # S3-001: encryption required
│   ├── s3_public_access.rego             # S3-002: no public ACL
│   ├── iam_wildcard.rego                 # IAM-001: no wildcard actions
│   ├── root_access_key.rego              # IAM-002: no root access keys
│   ├── security_group_ssh.rego           # SG-001: no SSH to 0.0.0.0/0
│   └── cloudtrail_enabled.rego           # LOG-001: CloudTrail required
├── semgrep/custom-rules.yml              # SAST-001/002/003 custom rules
├── suppressions/suppressions.yaml        # Suppression registry
├── remediation/remediation_catalog.yaml  # Remediation guidance per finding
├── scripts/
│   ├── tf_to_json.py                     # Terraform plan serializer
│   ├── generate_opa_findings.py          # Conftest output parser
│   ├── check_sast.py                     # SAST findings normalizer
│   ├── check_secrets.py                  # Secrets findings normalizer
│   ├── check_dependencies.py             # SCA findings normalizer
│   ├── validate_suppressions.py          # Suppression governance enforcer
│   ├── enrich.py                         # Findings enrichment engine
│   └── security_gate.py                  # Gate — single exit point
├── terraform/insecure.tf                 # Intentionally vulnerable IaC
├── scripts/vulnerable_app.py             # Intentionally vulnerable Python
├── FAILURES.md                           # 15 real build failures + root causes
└── DECISIONS.md                          # 12 architectural decisions + tradeoffs
```

---

## Intentionally Vulnerable Targets

This repository contains deliberately insecure resources to validate pipeline detection:

**`terraform/insecure.tf`**
- S3 bucket without encryption → S3-001
- S3 bucket with `acl = "public-read"` → S3-002
- IAM policy with `Action = "*"` → IAM-001
- `aws_iam_access_key` with `user = "root"` → IAM-002
- Security group with port 22 open to `0.0.0.0/0` → SG-001
- No `aws_cloudtrail` resource → LOG-001
- Hardcoded AWS key patterns → SECRET-001, SECRET-002

**`scripts/vulnerable_app.py`**
- `subprocess.run(user_input, shell=True)` → SAST-001
- `eval(user_input)` → SAST-002
- `pickle.loads(data)` → SAST-003

**`requirements.txt`**
- `urllib3==1.25.4` — 11 known CVEs → SCA-001 through SCA-011

These are the test corpus that proves the pipeline catches real vulnerabilities across all four scanner categories.

---

## Known Gaps

| Gap | Impact | Priority |
|-----|--------|----------|
| Severity hardcoded to HIGH in enrich.py | Gate cannot distinguish CRITICAL vs MEDIUM per finding | High |
| No suppression expiry recheck at gate runtime | Expired suppressions not caught until next suppression-validation run | Medium |
| Secret findings lack file path and line number | SECRET-001/002 have no location context in enriched output | Medium |
| No findings history or trend tracking | Cannot measure FP rate or MTTD over time | Low |
| tf_to_json.py is a simulator not a real parser | Does not parse actual HCL — plan.json is hand-authored | Low |

---

## Build Failures Encountered

15 real failures documented during this build. Three most instructive:

**Step ordering — opa_findings.json always empty**
Debug and generate steps placed before conftest executed. Files produced by step N are not available to step N-1. Fixed by reordering steps within the job.

**Artifact not found — sast-findings**
Missing `if: always()` on upload step. When semgrep found violations, the upload was skipped. Artifact only existed when there were no findings — inverting the pipeline's purpose.

**SCA duplicate finding IDs**
Dependency loop index used as finding number prefix. Multiple CVEs in the same dependency received identical IDs. Fixed with global counter and `seen` set deduplication.

Full failure log with root causes: [FAILURES.md](./FAILURES.md)
