# security-guardrails-platform

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
