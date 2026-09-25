# Local deployment and acceptance

The application now fails when inference or sandbox execution is unavailable. A successful build or passing mocked test is not evidence of a working GPU deployment or a sealed network.

## Prepare on an approved staging machine

1. Build the backend and frontend images from this reviewed source. Record the source commit, image IDs/digests, package lockfiles, licenses and model licenses. The Dockerfiles need package repositories during staging; do not build them inside the disconnected venue.
2. Provision the configured reasoning, coding, vision and embedding models in Ollama. Keep the complete model store, including blobs and manifests, and record the digests returned by `/api/tags`. Use distinct reasoning/coding models for the two-task demonstration. Confirm each model's license allows the intended use.
3. Preload the configured Python sandbox image into a **dedicated isolated worker daemon**, and record its image digest. The app uses `--pull=never`; missing images fail. Give the backend access only to that daemon, through a protected local endpoint. Do not expose an unauthenticated Docker TCP port or mount a general-purpose host Docker socket into the app. The repository does not provision this daemon for you.
4. Include Tesseract language data. If using EasyOCR, stage its weights in the runtime user's cache; runtime downloading is disabled. Include the vision model for OCR fallback. Exercise all required languages and representative scans before transfer.
5. Export built images with `docker save`, and stage the Ollama store, OCR assets, source snapshot, deployment configuration template and operating instructions in a dedicated release directory. Exclude `.env`, passwords, runtime databases, organizational documents and private keys. Do not distribute a populated development database.
6. Run `python backend/scripts/offline_manifest.py create <release-directory>`. Sign or separately retain `manifest.sha256.json` using the organization's approved process. After transfer, run the same script with `verify`. A hash stored alongside mutable files proves transfer integrity only, not release authenticity.

## Start disconnected

Load the previously exported images with `docker load`. Restore model/OCR assets to the correct volumes without downloading anything. Supply exact reviewed image digests/tags to Compose; the Ollama service and sandbox refuse implicit pulls. Use `docker compose up --no-build --pull never` after assigning the built application image names in your deployment override. The repository's Compose file is a staging/development build definition, not a complete offline bundle.

Use `ENVIRONMENT=production` and `ALLOW_DEMO_SESSIONS=false`. Existing `.env` values override code defaults; check them explicitly. Set a long random `BOOTSTRAP_TOKEN` only for the initial administrator setup, enroll MFA through `/api/v1/auth/bootstrap`, then remove that token and restart. Assign workbench/reviewer roles explicitly: administrator does not automatically receive document access. Demo credentials and demo sessions are for public samples only.

Compose publishes ports to loopback and uses an internal network. Keep a single backend worker: restart recovery marks interrupted work failed for explicit resubmission, and the legacy approval service is not a distributed queue. Configure a local TLS reverse proxy and firewall for any authorized LAN access. Restrict network paths between the app, model server, worker daemon and clients; an application socket hook cannot replace firewall policy. GPU device access must be enabled for your actual host.

From the backend environment, run `python scripts/preflight.py`. It checks production authentication, locally installed model digests, a real embedding operation/dimension check, Docker availability, the preloaded worker image and Tesseract. It never installs anything. It always reports whole-deployment air-gap verification as pending because that requires independent observation. Also exercise `/api/v1/readiness` as an authenticated user.

## Migrate existing data deliberately

Stop the application and back up SQLite, Chroma and object storage together. Configuration now resolves relative `data/...` paths under `backend/data`; verify the actual configured paths before restart. Existing database columns are added at startup. This is an additive compatibility migration, not a fully versioned migration system.

The former mixed synthetic/real embedding collection is deliberately quarantined. Run `python scripts/reindex_corpus.py` for an inventory of registered ready documents, then `python scripts/reindex_corpus.py --apply` to rebuild them with the real local embedding model. Restart after resolving every failed source. Unknown/orphaned files are not implicitly made public. Changing embedding model or dimension selects a new collection and requires another reindex. Retain the backup and old collection until acceptance is complete.

Old generated reports/exports, demo graph entries and historical audit records are not retroactively validated. Regenerate required deliverables from their original sources. Tracked runtime files may remain in Git history; repository history cleanup and credential rotation require a separate, coordinated migration. Local hash-chained audit records are not WORM storage; retain signed checkpoints in an independent protected destination if that assurance is required.

## Demonstrate PS 26117

- Upload a public scanned inspection PDF. Confirm every page is processed, source links resolve, and a document task creates a real Word archive with supported findings and a pending human review state.
- Submit a code task. Confirm the selected coding model differs from the document model, the isolated worker records actual output and exit codes, and deliberately failing code is repaired or fails visibly. Generated assertions are not independent engineering validation.
- Submit an image/PDF with **vision** mode. Confirm the vision model is logged and compare its observations against the original image; model-to-model agreement is not visual ground truth.
- Generate Word, PowerPoint and Excel outputs; open them with local Office-compatible software. Spreadsheet exports currently contain report findings, supplied telemetry and explicit calculation inputs; they are not a general workbook-editing agent.
- Capture traffic across the browser/client, host, app containers, Ollama and worker during startup, OCR, document, code and export workflows. Include attempts by native subprocesses and direct-IP connections, and a deliberate denied-egress probe. Retain timestamps, interface scope, firewall rules and capture evidence. The built-in monitor covers Python backend socket events only and does not certify zero external traffic.

Retain the test prompts, input hashes, output hashes, selected model digests, hardware information, observed timings, worker results and packet capture with the acceptance report. Do not label the deployment sovereign-certified until this independent evidence exists.
