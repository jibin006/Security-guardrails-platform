# DECISIONS.md

# Security Guardrails Platform – Engineering Decisions

This document records major architectural decisions, tradeoffs, and rationale behind the Security Guardrails Platform.

---

# Decision 1 — Use Policy-as-Code for Infrastructure Validation

## Context

Terraform configurations required automated security validation before deployment.

## Options Considered

### Option A

Manual code reviews.

### Option B

Policy-as-Code using OPA + Conftest.

## Decision

Selected OPA + Conftest.

## Rationale

Policy-as-Code provides:

* Repeatable enforcement
* Version-controlled security requirements
* Automated validation in CI/CD
* Reduced reviewer burden

## Tradeoffs

### Accepted

* Additional policy maintenance

### Rejected

* Reliance on human review alone

---

# Decision 2 — Enforce Security in CI/CD Instead of Developer Workstations

## Context

Local validation can be bypassed.

## Decision

GitHub Actions is the enforcement boundary.

## Rationale

Developers may:

* Skip local checks
* Use different tool versions
* Ignore findings

CI/CD provides centralized enforcement.

## Tradeoffs

### Accepted

Longer feedback cycle compared to local execution.

### Benefit

Consistent policy enforcement across all contributors.

---

# Decision 3 — Introduce Multiple Security Controls

## Context

No single scanner identifies all security issues.

## Decision

Implemented:

* OPA (Infrastructure Security)
* detect-secrets (Credential Exposure)
* Semgrep (Application Security)
* pip-audit (Dependency Security)

## Rationale

Each scanner covers a different attack surface.

## Tradeoffs

### Accepted

Higher pipeline complexity.

### Benefit

Broader security coverage.

---

# Decision 4 — Separate Governance from Detection

## Context

Detection alone cannot determine business risk acceptance.

## Decision

Created Suppression Governance.

## Rationale

Organizations require documented exceptions.

Examples:

* False positives
* Compensating controls
* Temporary risk acceptance

## Tradeoffs

### Accepted

Additional operational process.

### Benefit

Controlled and auditable exceptions.

---

# Decision 5 — Require Expiring Suppressions

## Context

Permanent suppressions accumulate unmanaged risk.

## Decision

Every suppression requires:

* Owner
* Approver
* Reason
* Expiry Date

## Rationale

Exceptions should be reviewed periodically.

## Tradeoffs

### Accepted

Operational overhead.

### Benefit

Reduces forgotten security exceptions.

---

# Decision 6 — Artifact-Based State Transfer

## Context

GitHub Actions jobs are isolated.

Generated files do not automatically persist across jobs.

## Decision

Use upload-artifact and download-artifact.

## Rationale

Suppression approvals must be available to downstream enrichment jobs.

## Tradeoffs

### Accepted

Additional workflow complexity.

### Benefit

Explicit and auditable state transfer.

---

# Decision 7 — Enrich Findings with Security Context

## Context

Raw scanner output is difficult for developers to act on.

## Decision

Create remediation enrichment layer.

## Enrichment Includes

* Severity
* Risk Description
* Remediation Guidance
* Security Standards Mapping
* References

## Rationale

Developers require actionable information, not scanner output.

## Tradeoffs

### Accepted

Maintenance of remediation catalog.

### Benefit

Improved developer experience.

---

# Decision 8 — Security Findings Mapped to Standards

## Context

Organizations often require compliance evidence.

## Decision

Map findings to:

* SOC2
* OWASP
* NIST

## Rationale

Provides traceability between controls and findings.

## Tradeoffs

### Accepted

Additional metadata management.

### Benefit

Improved audit readiness.

---

# Decision 9 — Removed Simulated Findings

## Context
Initial implementation used hardcoded finding identifiers
(S3-001, SAST-001, SAST-002, SAST-003) to validate governance
and enrichment logic before scanner normalization was complete.

## Current State — RESOLVED
All hardcoded findings removed as of [date].
enrich.py now reads from:
- findings/opa_findings.json     (OPA/Conftest output)
- findings/sast_findings.json    (Semgrep output)
- findings/sca_findings.json     (pip-audit output)
- findings/secrets_raw.json      (detect-secrets output)

## Outcome
Gate output now reflects real scanner findings:
S3-001 from OPA, 3 SAST findings from Semgrep,
11 CVEs from pip-audit, SECRET-001 from detect-secrets.
---

# Decision 10 — Security Gate as Final Decision Point

## Context

Detection should not directly determine merge decisions.

## Decision

Introduce Security Gate layer.

Architecture:

```text
Detection
    ↓
Governance
    ↓
Enrichment
    ↓
Security Gate
```

## Rationale

Separates:

* Evidence collection
* Risk evaluation
* Enforcement

## Tradeoffs

### Accepted

Additional workflow stage.

### Benefit

Clearer ownership and decision logic.

---

# Decision 11 — Fail Closed for Security Controls

## Context

Missing findings or scanner failures may hide security issues.

## Decision

Treat missing or invalid security data as failure conditions.

## Rationale

Security controls should fail closed.

## Example

If a scanner crashes:

```text
Scanner Failure
      ↓
Pipeline Failure
```

instead of:

```text
Scanner Failure
      ↓
Pipeline Success
```

## Benefit

Reduces silent security control failures.

---

# Decision 12 — Security Platform Over Tool Integration

## Context

The objective was not to integrate scanners.

## Decision

Design a platform that includes:

* Detection
* Governance
* Enrichment
* Enforcement

## Rationale

Security tools generate findings.

Security platforms manage decisions.

## Outcome

Final architecture:

```text
OPA
Secrets
SAST
SCA
   │
   ▼
Artifacts
   │
   ▼
Suppression Governance
   │
   ▼
Remediation Enrichment
   │
   ▼
Enriched Findings
   │
   ▼
Security Gate
   │
   ▼
PASS / FAIL
```

---

# Future Architectural Improvements

1. Normalize real scanner outputs into a common schema.
2. Remove hardcoded findings.
3. Generate pull request security reports.
4. Store findings history for trend analysis.
5. Add risk scoring and prioritization.
6. Add security metrics dashboard.
7. Support additional scanners.
8. Introduce approval workflows for high-risk suppressions.

These improvements would move the platform closer to production-grade security governance.




## Decision: Step ordering in policy-as-code job

Date: [today]
Problem: Debug and generate steps ran before conftest executed.
conftest_raw.json did not exist when generate_opa_findings.py ran.
Result: opa_findings.json was always empty.
Fix: Reordered steps — Generate Terraform JSON → Run OPA → Debug → Generate OPA Findings → Upload.
Learning: GitHub Actions steps execute sequentially within a job.
A file produced by step N is not available to step N-1.

## Decision: Enrichment owns transformation, gate owns exit code

Date: [today]
Decision: enrich.py exits 0 always. security_gate.py owns sys.exit(1).
Reason: If enrichment fails the build, findings.json is never written,
the gate never runs, and no findings are published. Detection and
decision are separate concerns.
Trade-off: A silent bug in enrich.py passes the gate. Mitigated by
the debug step that prints all loaded findings before enrichment runs.

## Decision: if: always() on all scanner upload steps

Date: [today]
Decision: Every artifact upload step has if: always().
Reason: Scanners that find violations cause downstream steps to be
skipped by default. Without if: always(), the upload is skipped when
a scanner finds something — artifacts only exist when there are no
findings, which inverts the pipeline's purpose.
Trade-off: A crashed scanner attempts to upload a missing file and
fails at the upload step with a clear artifact-not-found error.
This is the correct failure mode — visible and diagnosable.

## Decision: OPA finding ID extracted from message prefix

Date: [today]
Decision: generate_opa_findings.py splits on ":" to extract ID only.
Reason: Full message string used as ID breaks suppression matching —
suppression registry stores short IDs like "S3-001", not full sentences.
Trade-off: If message format changes, the split produces wrong IDs.
Mitigated by debug step that prints opa_findings.json after generation.

## Stage 5 Metrics — Break Test Results

Date: [today]

### Suppression Governance
- Invalid suppression rejection rate: 2/2 (100%)
- Valid suppression pass-through rate: 1/1 (100%)
- Schema enforcement: owner, approver, ticket, expiry all enforced

### OPA Policy Coverage
- Policies tested for precision (no FP on compliant resource): 6/6
- Policies tested for recall (fires on violation): 6/6
- False positive rate: 0%

### Artifact Flow
- if: always() required for artifact upload when scanner finds violations: confirmed
- Recovery from missing if: always(): 1 line, 1 push

### Gate Behavior
- Suppression takes precedence over severity threshold: confirmed
- CRITICAL-only threshold: 4 blocking findings
- HIGH+ threshold: 21 blocking findings

### Finding ID Uniqueness
- SCA deduplication holds under duplicate CVE input: confirmed
- No two findings share the same ID across 22 total findings