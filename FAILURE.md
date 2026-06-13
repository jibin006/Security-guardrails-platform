# FAILURES.md

# Security Guardrails Platform – Build Log & Failure Analysis

This document captures the major failures encountered while building the Security Guardrails Platform and the lessons learned while resolving them.

---

# Failure 1 — Conftest Installation via pip

## Problem

Attempted installation:

```bash
pip install conftest
```

Result:

```text
ERROR: Could not find a version that satisfies the requirement conftest
```

## Root Cause

Conftest is not distributed through PyPI.

It is released as a standalone binary through GitHub Releases.

## Resolution

Downloaded Conftest directly:

```powershell
Invoke-WebRequest `
  -Uri https://github.com/open-policy-agent/conftest/releases/download/v0.68.2/conftest_0.68.2_Windows_x86_64.zip `
  -OutFile conftest.zip
```

Extracted binary and executed directly.

## Lesson

Always verify tool distribution methods before assuming PyPI availability.

---

# Failure 2 — Windows Path Execution

## Problem

Attempted:

```powershell
C:\Users\jilub\iam drift\conftest.exe --version
```

Result:

```text
CommandNotFoundException
```

## Root Cause

PowerShell treats spaces as argument separators.

## Resolution

Executed using:

```powershell
& "C:\Users\jilub\iam drift\conftest.exe" --version
```

## Lesson

Executable paths containing spaces must be quoted and invoked using PowerShell's call operator.

---

# Failure 3 — Rego Syntax Incompatibility

## Problem

GitHub Actions failed with:

```text
rego_parse_error
if keyword is required
contains keyword is required
```

## Root Cause

Local machine used:

```text
Conftest 0.68.2
OPA 1.15.2
```

GitHub Actions used:

```text
Conftest 0.50.0
```

Different parser capabilities caused policy parsing failures.

## Resolution

Upgraded CI installation:

```yaml
conftest_0.68.2_Linux_x86_64.tar.gz
```

## Lesson

Policy engines must be version-aligned across developer and CI environments.

---

# Failure 4 — GitHub Actions as Enforcement Point

## Problem

Initially validated policies only locally.

## Risk

Developers could bypass local execution entirely.

## Resolution

Moved enforcement into GitHub Actions.

```text
Developer
   ↓
Git Push
   ↓
GitHub Actions
   ↓
OPA Policy Check
```

## Lesson

Local tooling provides feedback.

CI/CD provides enforcement.

---
# Failure 5 — detect-secrets False Positive Investigation

## Problem
detect-secrets flagged an AWS Access Key inside insecure.tf.

## Root Cause
The Terraform file contained a hardcoded fake AWS key string
intentionally placed as a vulnerable pattern. detect-secrets
pattern-matched on the key format, not on whether it was real.

## Resolution
Confirmed this was a true positive for the build — the file
intentionally contains a vulnerable pattern. Finding correctly
appears as SECRET-001 in the pipeline output.

The suppression flow was validated by adding SECRET-001 to
suppressions.yaml with a ticket reference and confirming
the gate moved it from OPEN to SUPPRESSED.

## Lesson
detect-secrets cannot distinguish between real credentials
and test credentials with valid key format. Suppression
governance is the correct mechanism for managing intentional
test patterns, not scanner tuning.

# Failure 6 — Dependency Resolver Conflict

## Problem

requirements.txt:

```text
urllib3==1.25.4
requests==2.20.0
```

pip-audit failed.

```text
ResolutionImpossible
```

## Root Cause

Package dependency constraints conflicted.

Scanner never executed.

## Resolution

Reduced requirements file:

```text
urllib3==1.25.4
```

## Lesson

Dependency scanners rely on successful dependency resolution before vulnerability analysis.

---

# Failure 7 — Fail-Open Scanner Logic

## Problem

Workflow contained:

```bash
pip-audit ... || true
```

If scanning failed, pipeline continued.

## Risk

Scanner crashes could be interpreted as successful security checks.

## Resolution

Modified validation logic to fail when findings output is missing.

## Lesson

Security controls should fail closed, not fail open.

---

# Failure 8 — Suppression Expiry Governance

## Problem

Suppression entry:

```yaml
expiry: "2026-03-01"
```

Validation failed.

```text
Suppression expired
```

## Root Cause

Suppression exceeded approved validity period.

## Resolution

Updated suppression:

```yaml
expiry: "2027-03-01"
```

## Lesson

Security exceptions require lifecycle management.

Permanent suppressions create unmanaged risk.

---

# Failure 9 — GitHub Actions Job Isolation

## Problem

Suppression validation generated:

```text
findings/valid_suppressions.json
```

Remediation enrichment could not read the file.

## Root Cause

GitHub Actions jobs run on separate runners.

Files are not automatically shared.

## Resolution

Implemented artifact persistence.

Upload:

```yaml
actions/upload-artifact@v4
```

Download:

```yaml
actions/download-artifact@v4
```

## Lesson

State must be explicitly transferred between CI jobs.

---

# Failure 10 — Empty Artifact Consumption

## Problem

Enrichment crashed with:

```text
JSONDecodeError
```

## Root Cause

Artifact file existed but was empty.

```text
valid_suppressions.json
```

## Resolution

Added validation and debugging steps.

```yaml
cat findings/valid_suppressions.json
```

Verified artifact contents before enrichment.

## Lesson

Presence of a file does not guarantee valid content.

---

# Failure 11 — Workflow Dependency Design

## Problem

Remediation enrichment depended on all scanner jobs.

```yaml
needs:
  - policy-as-code
  - secrets-detection
  - sast
  - dependency-scan
```

Because scanners intentionally failed, enrichment never executed.

## Resolution

Temporarily reduced dependency chain:

```yaml
needs:
  - suppression-validation
```

to validate enrichment logic.

## Lesson

Testing complex pipelines often requires isolating components before integrating the full workflow.

---

# Failure 12 — Suppression Registry Successfully Enforced

## Expected Outcome

```text
SAST-003 → SUPPRESSED
SAST-001 → OPEN
SAST-002 → OPEN
S3-001   → OPEN
```

## Result

```text
[FAIL] Build blocked by:
S3-001
SAST-001
SAST-002
```

while:

```text
SAST-003 [SUPPRESSED]
```

passed through governance.

## Lesson

Exceptions should be narrowly scoped, documented, approved, and time-bound.

---

# Key Engineering Lessons

1. Security controls must fail closed.
2. CI/CD is the enforcement boundary.
3. Version drift causes policy failures.
4. Security exceptions require governance.
5. Artifact management is critical in GitHub Actions.
6. Scanner output must be validated before use.
7. Detection alone is insufficient; remediation and suppression workflows are required.
8. Platform engineering challenges often occur outside the scanners themselves.

These failures were intentionally preserved because they demonstrate real-world engineering challenges encountered while building a security guardrails platform.
