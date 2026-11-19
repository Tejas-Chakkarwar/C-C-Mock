# Cypher Circle

Cypher Circle is a Python 3.13 console application backed by Neo4j. The
repository is currently at Milestone 0, the vertical slice defined in
`docs/DESIGN.md`: SNAP ego-Twitter data is downloaded and deterministically
preprocessed, loaded into Neo4j, and exercised through registration, login,
follow, and network recommendation checks.

## Local setup

Use the project-local environment only:

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
make data
make load
make slice-check
```

`make data` keeps the original archive at `data/raw/twitter.tar.gz`, safely
extracts it under `data/raw/twitter/`, and writes deterministic CSV output to
`data/processed/`. Raw and processed data, credentials, and the local virtual
environment are gitignored.

The accepted SNAP archive SHA-256 is
`5ed7b52a8013a1a1d43301a5414dfcb844e50cb4e2fb8dc801a7bef399552bb0`.

The design document is currently stored at `docs/DESIGN.md`; the design calls
for a root-level `DESIGN.md`, so that path discrepancy remains an identified
repository conflict until the document is relocated intentionally.

