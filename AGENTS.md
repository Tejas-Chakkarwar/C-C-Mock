# Cypher Circle Project Instructions

## Source of truth

- Read `DESIGN.md` before making implementation decisions.
- Implement milestones in the order specified in Section 13.
- Treat the design document as authoritative when code and documentation conflict.
- Keep `AGENTS.md` concise; do not duplicate the full design document here.

## Reference project

- `reference/orbit/` is read-only reference material.
- Use it only to understand possible UI flows, report organization, and presentation quality.
- Do not copy its code, dataset, credentials, plaintext-password approach, or architecture.
- Do not modify anything under `reference/orbit/`.

## Technology constraints

- Python 3.13.x in this project's local `.venv`.
- Neo4j Community 5.26.0.
- Python console interface with generated browser-based visualization.
- SNAP `ego-Twitter` deterministic subset.
- Neo4j Python driver pinned to 5.26.0.
- All Cypher queries belong in `cyphercircle/queries.py`.
- Use parameterized Cypher only.
- Do not add another database or unapproved dependency.

## Data and reproducibility

- Preserve the fixed Faker version, locale, seed, and random seed from `DESIGN.md`.
- Preserve deterministic CSV ordering and timestamp generation.
- Follow the exact bounded timestamp rules in Section 4.4.
- Preserve the archive SHA-256 and extraction-manifest validation.
- Keep original circle labels as `source_label`.
- Do not claim the selected graph is a complete Twitter graph.
- Clearly distinguish public dataset relationships from synthetic profile fields.

## Architecture

- The CLI communicates only with services.
- Services contain validation and business logic.
- `db.py` is the only production module that imports the Neo4j driver.
- Services return application dataclasses, not Neo4j records.
- All query names and Cypher constants remain centralized.
- Never expose or print `password_hash`.

## Workflow

Before changing code:

1. Inspect the repository and run `git status`.
2. Read the relevant sections of `DESIGN.md`.
3. Inspect existing code and tests.
4. Identify conflicts before implementing.

Implement one milestone at a time.

After each milestone:

- Run the relevant unit tests.
- Run the required acceptance checks.
- Run `make verify-env` when dependencies or Python behavior are involved.
- Run `make test-integration` for database behavior.
- Update documentation when behavior changes.
- Report changed files and verification results.

## Testing

- `make test` runs unit tests only.
- `make test-integration` must fail if Neo4j is unavailable.
- Integration tests must use isolated `zztest_<uuid-hex>_` users and clean them up.
- Do not treat skipped integration tests as successful database verification.
- Test deterministic preprocessing twice and compare generated file hashes.

## Safety

- Never modify `reference/orbit/`.
- Never commit `.env`, passwords, API keys, or local credentials.
- The seeded password is demo-only and must not be treated as production security.
- Do not reset or delete database data unless explicitly requested through the project reset command.
- Do not overwrite unrelated user changes.
- Ensure `make zip` excludes raw data, processed data, credentials, temporary directories, and virtual environments.

## Completion criteria

A milestone is complete only when:

1. Its design requirements are implemented.
2. Its tests pass.
3. Its acceptance checks pass.
4. Documentation is updated.
5. The implementation remains consistent with `DESIGN.md`.
