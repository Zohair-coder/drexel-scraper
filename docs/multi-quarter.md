# Multi-quarter implementation and review plan

## Request / acceptance criteria

Discover all quarters advertised in TMS. Students choose a quarter in Grafana;
courses, assigned professors, statistics and update time follow that selection.
Store all colleges with full credits/prerequisites and cached RMP enrichment.
Repeated CRNs must remain isolated by term. A failed scrape must preserve the
previous successful data. Deploy to **dev only**, verify, and open a PR to main;
production promotion requires user code review and approval.

## Schema

`src/create_tables.sql` contains four normalized tables: `terms`, `courses`,
`instructors`, `course_instructors`. Courses have composite `(term_code, crn)`
keys; assignments carry the same composite foreign key. No JSON snapshots.
The joined view keeps legacy Grafana column names while adding `term_code`.
The Grafana service account receives SELECT only.

TMS exposes instructor names but not authoritative staff identifiers. Names are
not unique database keys. The importer reuses only an unambiguous exact name +
RMP-ID match from the existing ratings matcher/cache. This remains a heuristic,
not a verified university identity. Without that match, assignments retain
separate instructor records rather than falsely merging two people by name.
Consequently unresolved records can overcount distinct people in summaries.
Historical quarters show current cached RMP scores, not historical ratings.

## Non-destructive migration

`python src/main.py --migrate-only` runs a transaction under an advisory lock.
On the legacy schema it moves the original tables/view into
`legacy_single_quarter`, creates the new schema, and copies all rows using the
term code from the legacy metadata. It preserves IDs and fixes the identity
sequence. Missing/invalid metadata aborts and rolls the whole migration back.
No legacy table or row is deleted. Subsequent invocations are idempotent.
The legacy timestamp is left unknown until the next verified refresh.

Take a database backup before promotion. Keep `legacy_single_quarter` until
the rollout is accepted; deleting it is a separate reviewed operation. An old
scraper must **not** be run against the new public schema: its table-reset SQL
is destructive. A rollback requires pausing the scraper, restoring the old
dashboard/image and restoring the preserved schema or database backup as a
coordinated operation, not merely reverting the image.

## Collection and publication

- `--all-quarters`: discover from the authenticated TMS catalogue, including
  last year's quarters; ignore semester links. One authenticated session is
  reused serially because TMS subject/detail routes depend on session state.
- `--term 202625`: explicitly refresh one available quarter.
- Without either flag, the existing configured/auto-selected quarter is used.
- Each complete nonempty term is published in one transaction. Stale sections
  and assignments for that term disappear; other terms remain intact.
- Empty results, expired sessions, parse failures and invalid DB rows fail
  closed. In an all-quarter run, failures in collection, file output or database
  publication are recorded per quarter and later quarters are still attempted.
  An aggregate error at the end keeps the Job/exception notification marked as
  failed. Successful quarters remain committed and failed quarters retain their
  previous database data. Single-quarter runs still propagate errors immediately.
- Availability is independently updated from a successfully parsed catalogue;
  disappeared terms remain stored but are excluded from the dropdown.
- Cache keys are `term_code:crn`; ambiguous old CRN-only entries are ignored.
- The first full backfill is slower. The scheduled job allows six hours and
  forbids overlapping scheduled executions. Subsequent runs reuse the cache.

Grafana performs read-only SQL queries; selecting a term does not start a
scrape. Each panel and instructor join is scoped to the quarter. Reset clears
other filters but preserves the quarter. A not-yet-loaded term explicitly says
`Not loaded yet`. Summary panels retain their previous semantics: they describe
the selected quarter, independently of course-table rating/time filters.

The scraper stores `terms.is_default` from its configured quarter (the existing
`get_current_quarter_and_year()` logic, including environment overrides). Grafana
orders this quarter first and has no saved hardcoded selection. Fresh visits use
that default; `var-quarter` links retain the explicitly chosen quarter. If TMS
does not yet advertise the configured quarter, the newest available quarter is
the fallback. The default is refreshed with each successful catalogue discovery;
Grafana does not duplicate the Python date-boundary rules in SQL.

## Deployment / tests

The existing dev-branch GitHub workflow builds the ARM64 image, waits for active
scraper jobs, migrates using the existing CronJob's environment, then provisions
the Helm release and dashboard. Main is not updated or merged during dev review.
The migration Job has a 900-second deadline to allow for scheduling and image
pulls; the client waits up to 960 seconds, longer than the Job deadline.

`tests/test_multi_quarter.py` uses an explicitly configured disposable `_test`
database to test migration preservation/idempotence, CRN and instructor identity
isolation, rollback, refresh replacement and every dashboard SQL query.
`tests/test_term_cache.py` verifies reused CRNs cannot contaminate credits or
prerequisites and expired sessions are rejected. CI runs both plus existing
unit tests, strict mypy, Ruff, Helm/dashboard checks and a real single-term scrape.

Deployment revision, successful run evidence, UI checks and PR URL will be
recorded in the dev verification report after deployment.
