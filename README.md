# Cypher Circle

Cypher Circle is a Python 3.13 console application backed by Neo4j. Milestones
0, 1, and 2 are complete: the vertical slice, environment workflow, and
deterministic SNAP ego-Twitter data pipeline defined in `DESIGN.md` are
implemented and acceptance-checked. The loaded graph is exercised through
registration, login, follow, and network recommendation checks.

## Local setup

Use Python 3.13 in the project-local environment only:

```sh
python3.13 -m venv .venv
source .venv/bin/activate
python --version
pip install -r requirements.txt
cp .env.example .env
```

Start Neo4j 5.26.0 Community and run the vertical slice. `make up` creates a
local, gitignored `.env` from `.env.example` if needed; the Compose ports are
bound to localhost only:

```sh
make up
make verify-env
make smoke-check
make test
make data
make load
make test-integration
make slice-check
```

`make load` intentionally refuses a non-empty database. To deliberately clear
the configured database and reload the processed dataset, use `make reset`.
This passes `--reset` to the loader; run it only against a database that is
safe to erase.

All Makefile targets use `.venv/bin/python` by default. Override `PYTHON` only
when intentionally running a compatible toolchain, for example
`make PYTHON=python3.13 test`.

`make data` keeps the original archive at `data/raw/twitter.tar.gz`, safely
extracts it under `data/raw/twitter/`, and writes deterministic CSV output to
`data/processed/`. Raw and processed data, credentials, and the local virtual
environment are gitignored.

`make smoke-check` loads the local Neo4j settings, executes `RETURN 1` through
`Database.read()`, and confirms that the query was recorded in `QueryLog`.
Missing or invalid `NEO4J_*` settings fail with an actionable configuration
message.

The accepted SNAP archive SHA-256 is
`5ed7b52a8013a1a1d43301a5414dfcb844e50cb4e2fb8dc801a7bef399552bb0`.

`reference/orbit/` is read-only comparison material and is intentionally local-
only. It is ignored by Git and is not required for tests, preprocessing, or
runtime. A fresh clone contains only `reference/README.md`; do not copy or
modify Orbit code.

