# Scraper failure diagnostics

Quarter failures include each exception type, source filename/function/line and
wrapped cause in both the job log and aggregate exception email. Exception
messages, source lines, locals, headers and response bodies are excluded.
The scraper continues processing later quarters and still exits nonzero if any
quarter failed. The final notification identifies every failed quarter.

Sanitized failure logs are also written immediately on each quarter failure and
on terminal exceptions to `SCRAPER_FAILURE_DIR` (locally `performance/failures`).
Kubernetes sets this to `/app/performance/failures`, on the existing shared PVC
under `cronjob_performance/failures`. They therefore survive deletion of a failed
pod. This is a diagnostic archive, not additional monitoring.

Retention is bounded to the newest 2048 `failure-*.log` files and 14 days, pruned
when a failure is recorded. Permissions are 0600. Unrelated performance files
are untouched. An archive write failure prints only its exception type and does
not stop remaining quarters or prevent the email from being attempted.

During maintenance, inspect the archive using an existing pod with this PVC
mounted, or a short-lived read-only mount when none exists. Save relevant files
in the maintenance run's durable evidence directory. Do not trigger a live
scrape merely to read the archive. Sudden SIGKILL/OOM before an exception handler
runs cannot produce a Python diagnostic; preserve Kubernetes events and live
pod logs promptly in that case. This change cannot reconstruct old lost logs.
