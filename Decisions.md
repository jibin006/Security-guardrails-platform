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