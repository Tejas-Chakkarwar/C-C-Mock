# Cypher Circle

SJSU CS157C NoSQL Database Systems

Team project report

Semester: [TO BE SUPPLIED]

Team members:

- [TEAM MEMBER NAME - TO BE SUPPLIED] - [EMAIL - TO BE SUPPLIED]
- [TEAM MEMBER NAME - TO BE SUPPLIED] - [EMAIL - TO BE SUPPLIED]
- [TEAM MEMBER NAME - TO BE SUPPLIED] - [EMAIL - TO BE SUPPLIED]

This report is generated from the checked-in implementation and the deterministic
preprocessing log. Names, emails, and screenshots are not invented when the
team has not supplied them.

<!-- PAGEBREAK -->

## 1. Project Overview

Cypher Circle is a Python 3.13 console application backed by Neo4j Community
5.26.0. It models users, directed follows, and circle membership in a property
graph. The console provides registration, authentication, profile and circle
editing, social connections, recommendations, search, popular-user discovery,
and an offline browser-based network visualization.

The project uses a deterministic subset of SNAP ego-Twitter for seeded graph
relationships. Synthetic profile fields make the graph readable without
claiming that generated names, emails, biographies, or locations are real
Twitter attributes. The application separates the Rich CLI, service-layer
validation and business logic, and the Neo4j driver boundary.

## 2. Technology Stack

| Component | Version or role |
|---|---|
| Python | 3.13.x in the project-local .venv |
| Neo4j | Community 5.26.0 |
| Driver | neo4j==5.26.0 |
| Passwords | bcrypt==5.0.0 |
| Synthetic profiles | Faker==40.54.0, locale en_US, seed 157 |
| Console | rich==15.0.0 |
| Visualization | pyvis==0.3.2, self-contained HTML |
| Configuration | python-dotenv==1.2.4 |
| Tests | pytest==9.2.0 |
| Report build | reportlab==4.4.5 and Pillow==11.3.0 |

All application Cypher is centralized in cyphercircle/queries.py and uses
parameters. db.py is the only production module importing the Neo4j driver.

## 3. Property Graph Schema

![Property graph schema: User, Circle, FOLLOWS, and IN_CIRCLE](diagrams/schema.png)

Figure 1. Property graph schema.

| Node | Important properties |
|---|---|
| User | username, email, name, name_lc, password_hash, bio, location, joined_at, updated_at, source_id, source |
| Circle | circle_id, name, source_label, owner_source_id, source |

| Relationship | Direction | Meaning |
|---|---|---|
| FOLLOWS | User -> User | Directed follow with since DateTime |
| IN_CIRCLE | User -> Circle | Dataset or app circle membership |

Unique constraints cover usernames, emails, source IDs, and circle IDs.
Text indexes cover name_lc and username. Required fields are validated by the
application because Neo4j Community does not provide existence constraints.

{{SCHEMA_QUERY_DETAILS}}

## 4. Dataset and Deterministic Preprocessing

### 4.1 Source and provenance

The source is SNAP ego-Twitter:

- Archive: https://snap.stanford.edu/data/twitter.tar.gz
- Dataset page: https://snap.stanford.edu/data/ego-Twitter.html
- Citation: J. McAuley and J. Leskovec, Learning to Discover Social Circles
  in Ego Networks, NIPS 2012.

The full dataset is documented as 81,306 nodes, 1,768,149 edges, and 973 ego
networks. Per-ego .edges files describe directed follows among followees;
.circles files describe user-created lists. The project does not use
twitter_combined.txt.gz.

This dataset was chosen because its directed follow edges make Following and
Followers distinct for UC-7, and its circle lists provide a second node type
with real provenance. An ego-Facebook graph is undirected, so converting it to
follows would make those two lists identical; email-Eu-core records email
communication rather than a follow relationship. The selected subset keeps
loading and screenshots practical while exceeding the project thresholds.

The archive SHA-256 recorded by this run is {{ARCHIVE_SHA256}}. Public
availability through SNAP is not an unrestricted open-source license claim.

### 4.2 Subset selection and cleaning

Ego IDs are processed in numeric order until both production thresholds are
met. The selected egos are {{EGOS_SELECTED}} of {{EGOS_TOTAL}} total ego
networks. The final deterministic subset has:

{{PROCESSED_COUNTS}}

The preprocessing log records {{EDGES_FROM_FILES}} edges from ego files and
{{EGO_EDGES_ADDED}} reconstructed ego-to-user edges. SNAP documents that the
ego follows every node in its file; these edges are reconstructed from that
meaning and are not additional lines in the .edges files.

Cleaning removed {{SELF_LOOPS_DROPPED}} self-loops, {{DUPLICATES_DROPPED}}
duplicate edges, and {{DANGLING_DROPPED}} dangling edges. It parsed
{{CIRCLES_RAW}} raw circles, dropped {{CIRCLES_DROPPED}} circles smaller than
three members, and retained {{USERS_WITHOUT_CIRCLE}} users without a circle.
Circle membership comes from the original Twitter lists, filtered to users
included in our deterministic subset. Circle names are synthetic; the original
circle label is retained only as source_label for provenance.

### 4.3 Synthetic enrichment and reproducibility

Every displayed profile field is synthetic. Faker is pinned at {{FAKER_VERSION}},
uses locale en_US, and is seeded with {{SEED}}. Usernames are generated in
sorted source-ID order and are unique and normalized. Emails use example.com.
Bio, location, names, joined timestamps, follow timestamps, and circle names
are generated deterministically.

CSV rows and JSON keys are sorted and the preprocessing log contains no run
timestamp. Running make data twice on the same archive must produce
byte-identical processed files.

| Processed file | SHA-256 |
|---|---|
{{PROCESSED_HASHES}}

### 4.4 Demo values

These values are read from data/processed/preprocess_log.json, not hardcoded:

{{DEMO_VALUES}}

The seeded password is a public demo-only credential and is not production
security.

### 4.5 Loading and database verification

![Data processing and loading pipeline](diagrams/pipeline.png)

Figure 2. Download, preprocess, load, and verify pipeline.

The loader validates archive binding, processed-file hashes, CSV headers, row
counts, required fields, endpoints, circle ownership, and minimums before a
reset can delete database data. It loads parameterized UNWIND batches of 1,000,
creates constraints and indexes, and compares live VERIFY_COUNTS with the log.

Processed dataset counts are the values above. The live database result at
report-build time is:

{{LIVE_COUNTS}}

If Neo4j is unavailable, no live count is invented. Run make up, make data,
make load, and rebuild the report before submission.

## 5. Architecture

![Cypher Circle system architecture](diagrams/architecture.png)

Figure 3. Console, services, data boundary, and QueryLog.

The CLI communicates only with AuthService, ProfileService, GraphService,
SearchService, and VisualizationService. Services validate inputs, enforce
actor scoping through authenticated Session, call named queries, and return
application dataclasses. Database translates Neo4j failures into application
errors. QueryLog records ordered, recursively redacted queries for Show Cypher.

![Cypher Circle use-case relationships](diagrams/use_cases.png)

Figure 4. Use-case and evidence relationships.

The visualizer reads a capped ego network, writes
output/network_username.html, removes external resources, and opens the
offline page in a browser.

## 6. Use Cases

| Use case | Behavior | Verification |
|---|---|---|
| UC-1 | Register with validation, hidden password confirmation, optional bio, and up to three circles | Unit tests and strict integration when Neo4j is available |
| UC-2 | Login with generic authentication errors and three attempts | CLI unit and integration tests |
| UC-3 | View profile with counts and up to five circles | Profile service and CLI tests |
| UC-4 | Edit details, join circles, leave circles, and clear optional fields with a dash | Profile service and CLI tests |
| UC-5 | Follow a target with self, missing, and duplicate checks | Graph service and integration tests |
| UC-6 | Unfollow a target with missing relationship handling | Graph service and integration tests |
| UC-7 | Paginated Following and Followers tables with follow-back indicators | CLI pagination and integration tests |
| UC-8 | True mutual total, paginated users, and relationship status | Graph service and integration tests |
| UC-9 | Network, circle, and popular recommendation tiers with reasons and scores | Recommendation tests and QueryLog assertions |
| UC-10 | Normalized case-insensitive search excluding the current user | Search service and CLI tests |
| UC-11 | Ranked popular users and follow selection | Search service and CLI tests |
| UC-12 | Capped directed ego graph rendered as offline HTML | Visualization service, CLI, and strict integration tests |

### 6.1 Query appendix

{{UC_QUERY_DETAILS}}

### 6.2 Evidence checklist

No report screenshots were found in report/screenshots/ at build time. These
placeholders are not claims that screenshots exist.

| File | Required evidence |
|---|---|
| uc01.png | UC-1 registration prompts and account-created message |
| uc02.png | UC-2 login and welcome message |
| uc03.png | UC-3 profile card and circles |
| uc04.png | UC-4 edited profile and circle membership |
| uc05.png | UC-5 follow success |
| uc06.png | UC-6 unfollow success |
| uc07.png | UC-7 separate Following and Followers tables |
| uc08.png | UC-8 mutual total and relationship status |
| uc09.png | UC-9 reasons, scores, and Show Cypher |
| uc10.png | UC-10 normalized search and following status |
| uc11.png | UC-11 popular-user leaderboard |
| uc12.png | UC-12 console confirmation and browser graph |

Run make demo-info for current usernames and the search term. Run make run,
enable Show Cypher with C, and capture the labeled screens from DESIGN.md
Section 15. UC-12 also requires a browser capture. Verify that no password,
password hash, local credential, or unrelated user data appears.

## 7. Security and Correctness

- Passwords are validated and hashed with bcrypt. Seeded credentials are demo-only.
- All Cypher is named and parameterized in cyphercircle/queries.py.
- Actor-scoped operations derive the acting username from Session.
- QueryLog recursively redacts keys containing password and truncates large lists.
- Neo4j failures become application errors; the CLI logs unexpected failures
  without showing a traceback.
- Rich output and visualization labels remove terminal controls and escape HTML.
- Visualization HTML rejects external src and href resources.
- The generated network is directed and capped at 50 following users, 50
  followers, and 500 edges.
- SNAP relationships and synthetic profile fields are documented separately.

## 8. Reproducibility and Setup

Use Python 3.13 in the project-local environment:

```sh
python3.13 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
make verify-env
make up
make data
make load
make test
make test-integration
make run
```

make report requires the local environment, ReportLab, Pillow, and Poppler
(pdfinfo, pdftotext, and pdftoppm). It generates diagrams, renders the
Markdown report to report/report.pdf, extracts text, and renders every page.
No network asset is used by the report builder.

## 9. Testing and Acceptance

The report builder ran the clean-clone-compatible unit suite:

{{UNIT_RESULT}}

make verify-env, compile checks, and git diff --check are required acceptance
checks. Strict integration tests require local Neo4j and must fail clearly when
Neo4j is unavailable. The live status at build time is stated in Section 4.5.

## 10. Team Responsibilities

Team assignments are placeholders because no names or emails were supplied.
Fill the title page and this table before submission.

| Area | Owner |
|---|---|
| Data pipeline, schema, loader | [TO BE SUPPLIED] |
| AuthService and ProfileService | [TO BE SUPPLIED] |
| GraphService | [TO BE SUPPLIED] |
| SearchService, VisualizationService, CLI, report | [TO BE SUPPLIED] |

## 11. Limitations and Future Work

- The graph is a deterministic union of selected ego networks, not a complete
  Twitter graph. Missing edges are not confirmed non-connections.
- SNAP provenance and license claims remain conservative.
- The console and generated static visualization are not a web API or GUI.
- The seeded password is suitable only for the public demo path.
- Screenshots, team identities, semester, and live Neo4j counts remain
  submission evidence to supply when unavailable during this build.
