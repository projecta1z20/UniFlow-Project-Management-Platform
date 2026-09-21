# UniFlow model-layer contract

## Scope

This phase defines SQLAlchemy declarative models and model-level validation only. There are no queries, account-registration routines, workers, seed records, or UI changes. Importing the models registers metadata and audit safeguards; it does not connect to a database or create tables. Managed migrations own schema creation.

## Types and record conventions

- All tables share one declarative `Base` and use portable SQLAlchemy UUIDs, timezone-aware timestamps, fixed-precision numeric scores, and non-native enums with database CHECK constraints.
- Mutable records have creation/update timestamps and SQLAlchemy optimistic version counters. ORM flushes check the loaded version. Bulk SQL does not automatically honor version counters; future services must use ORM flushes or explicit compare-and-swap updates.
- Identity defaults are application-generated UUIDs. Other new columns have defaults or allow NULL. Nullable references support migration and incomplete records; they are not permission to publish incomplete records. Future workflow transactions must require complete references before activation, submission, assignment, or notification delivery. Uniqueness constraints apply to populated references; NULL-bearing draft rows are not deduplicated by SQL uniqueness.
- All event timestamps should be supplied as aware UTC datetimes. Recurring availability uses local wall-clock times in the user's scheduling timezone, with Monday represented by zero. Overnight windows are represented by two rows. Exceptions use absolute instants.
- Replace JSON values as a whole when editing them; nested mutations are not automatically tracked. JSON is reserved for configurable parameters, report definitions/snapshots, and audit value snapshots, not relational associations.

## Accounts and roles

Email is trimmed and lowercased on ORM assignment, validated for basic email syntax, and protected by a unique constraint and normalization CHECK. NULL email is permitted for incomplete records; registration must require an email. Passwords are never stored directly: only bcrypt encodings are accepted by the ORM validator. Account rows default inactive until registration completes, and active rows require a password hash. Password verification and hashing are intentionally not implemented here.

Role grants are normalized and unique per user/role. A newly constructed role grant defaults to student; inserting a user alone does not automatically insert a grant. Revocation is timestamped, rather than deleting the grant. Regranting updates the existing grant and should create an audit event.

The bootstrap claim has a singleton uniqueness constraint and a composite reference to a system-administrator grant. Later registration must atomically insert the account, grant, and fully populated claim in one transaction, handling concurrent uniqueness conflicts without leaving extra administrator grants. A uniqueness constraint alone does not select the earliest account or implement registration. Do not insert an empty claim. Revoking an administrator grant and preserving at least one active administrator are future authorization invariants.

## Projects and assignment history

Objectives, skill requirements, preferences, rule criteria, memberships, and template items are separate relational records. Preferences have one project and one rank per student per assignment round. Rule sets and templates distinguish logical family/revision identifiers from optimistic row versions.

Assignments retain their round and rule-set provenance. Manual overrides require an actor, timestamp, and nonblank reason. Membership departure is timestamped. Multiple historical assignments can reference a project; selecting one current assignment, preventing conflicting active memberships across rounds, and enforcing configured capacities require transactional workflow validation. Referenced/published rule and template revisions should be treated as frozen and copied to a new revision for changes.

Milestones copy template content so later template changes do not rewrite project expectations. A deliverable is the logical artifact; submission revisions are separate records uniquely numbered within that artifact. Composite foreign keys keep populated milestone, deliverable, submission, and team references within the same project. Allocate revisions transactionally and retry uniqueness conflicts. Final submissions and finalized evaluation/feedback revisions should be retained rather than overwritten.

Evaluation criterion scores are normalized, with explicit maxima and weights. Score aggregation, valid state transitions, role eligibility, sponsor ownership authorization, and deadline rules belong to later services.

## Deletion and audit

Historical/authorship links use RESTRICT. Cascades are limited to dependent profile scheduling/skill rows and project objective/skill rows. Users and projects with history should be deactivated or archived, not deleted. File records hold opaque storage keys and metadata, never file contents or temporary download credentials. Removing a record does not delete a stored object.

Audit events have creation/occurrence timestamps and no mutable-record fields. Mapper guards reject ORM updates/deletes, and a Session execution guard rejects ordinary bulk SQLAlchemy updates/deletes targeting the audit table. These are application-level append-only safeguards, not database-level tamper resistance: raw SQL, direct connections, and privileged database access can bypass them. Database-level enforcement requires a separately managed privilege or trigger policy, which is outside this schema-only phase. Audit snapshots must never include passwords, password hashes, credentials, or sensitive file contents. Entity identifiers intentionally are polymorphic references; actor/project references have explicit foreign keys.

## Notifications and reports

Notifications separate processing state from read state, and retain scheduling, retry, lease, delivery, and expiry metadata. Deduplication keys are optional and scoped per recipient. Worker claiming, retries, lease expiry, and actual notification generation are not implemented.

Saved reports hold editable definitions; exports hold independent filter/column/sort snapshots and artifact metadata. A ready export requires a file and completion timestamp. Report visibility and export authorization must be enforced by future services.
