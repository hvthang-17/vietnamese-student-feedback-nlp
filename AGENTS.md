# Repository Instructions

## Scope and Sources

- Apply these instructions throughout this repository. Follow explicit user task constraints first; use any closer directory-level instructions for that directory.
- Keep technical names and code identifiers in English. Preserve Vietnamese UI text and communicate in Vietnamese unless the user requests another language.
- Use [README.md](README.md) for setup, [PRD](tasks/prd-vietnamese-student-feedback-nlp.md) for requirements, and [architecture](docs/architecture/README.md) for navigation. Use [knowledge docs](docs/knowledge/README.md) for background rather than duplicating them here.
- Distinguish implemented behavior, planned requirements, illustrative examples, and measured results. Verify documentation against executable code before making claims.

## Project Overview and Architecture

This academic project classifies Vietnamese student feedback using UIT-VSFC. Each text receives one sentiment label and one topic label from two independent classifiers, not a shared multitask model or aspect-based sentiment system.

- Sentiment: `0=negative`, `1=neutral`, `2=positive`.
- Topic: `0=lecturer`, `1=training_program`, `2=facility`, `3=others`.
- Treat [backend/app/labels.py](backend/app/labels.py) as the backend label mapping. Update frontend label definitions and tests together when an authorized change affects mappings.
- Stack: Python 3.11+, FastAPI/Pydantic, SQLite, scikit-learn/Joblib, ReportLab, and Hugging Face Datasets. Optional training uses Transformers, PyTorch and PyVi. Frontend uses JavaScript/JSX ES modules, React 18.3.1 and Vite 5.4.19; README requires Node.js 20+.
- Read actual dependency constraints in [backend requirements](backend/requirements.txt), [Transformer requirements](backend/requirements-transformers.txt), and [frontend manifest](frontend/package.json). Frontend has an npm lockfile; no Python dependency lockfile was found.

| Module | Actual responsibility |
| --- | --- |
| `backend/app/main.py` | App factory, lifespan composition, HTTP middleware/errors; ASGI entry point without import-time runtime I/O |
| `backend/app/api/` | HTTP routes for predictions, CSV imports, dashboard/listing and exports |
| `backend/app/services/` | Feedback/import/report use cases; dependencies injected through domain ports |
| `backend/app/repository.py` | SQLiteFeedbackRepository read/write SQL, pagination and aggregation |
| `backend/app/database.py`, `migrations.py` | Operation-scoped connections, explicit transactions, versioned migrations and FK enforcement |
| `backend/app/domain/`, `settings.py` | Domain values/ports and process-environment settings |
| `backend/app/inference.py` | Loads `artifacts/production.joblib`; calls sklearn `predict_proba`/`classes_`; uses keyword demo fallback only when the artifact is absent |
| `backend/app/preprocessing.py`, `schemas.py`, `labels.py`, `clock.py` | Text normalization, request/response models, labels and timezone |
| `frontend/src/main.jsx`, `App.jsx` | Mount React and switch views with state; no routing library |
| `frontend/src/pages/` | Analyze, Dashboard and Import; pages call `fetch` directly |
| `frontend/src/components/`, `config.js`, `styles.css` | Shared UI, API URL/labels and CSS |
| `ml/` | Stage CLI with `core/`, `data/`, `training/`, `evaluation/`, `deployment/`; verified snapshots and isolated runs |
| `tests/` | Preprocessing/config/metrics tests, direct endpoint tests and HTTP integration tests |
| `data/`, `artifacts/` | Runtime SQLite and generated model/experiment outputs |
| `docs/`, `tasks/` | Technical documentation, reports and product requirements |

Keep HTTP parsing in routers, use cases in services, and SQL in the repository adapter. Domain models/ports must not import FastAPI or SQLite. App factory injects dependencies and lifespan loads the model; importing main.py must not open a database or deserialize an artifact. Training remains offline; promoted model changes require API restart. See [system design](docs/architecture/system-design.md), [API design](docs/architecture/api-design.md) and [database design](docs/architecture/database-design.md).

## Source-Verified Commands

Commands below are supported by [README](README.md), [frontend scripts](frontend/package.json), [pytest config](pyproject.toml), and the named test/ML entry points. Source verification does not establish successful execution. See README for installation; do not install or upgrade packages as a side effect of validation.

Run Python commands from the repository root using the project environment. On Windows, use `.\.venv\Scripts\python.exe` instead of `python` when the virtual environment is not activated. The bare `uvicorn` command also requires that environment on PATH; otherwise use `.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload`.

| Purpose | Working directory | Command |
| --- | --- | --- |
| Backend development | Root | `uvicorn backend.app.main:app --reload` |
| Configured server | Root | `python -m backend.app serve` |
| Explicit migrations | Root | `python -m backend.app migrate` (check database target and backup first) |
| Frontend development | `frontend/` | `npm run dev` |
| Frontend production build | `frontend/` | `npm run build` |
| Frontend preview | `frontend/` | `npm run preview` |
| Full Python suite | Root | `python -m pytest tests -q` |
| Pure unit/config/metrics tests | Root | `python -m pytest tests/test_preprocessing.py tests/test_data_integrity.py -q` |
| Direct endpoint/database tests | Root | `python -m pytest tests/test_api_direct.py -q` |
| HTTP integration tests | Root | `python -m pytest tests/test_api.py -q` |

Documented local addresses are frontend `http://localhost:5173`, backend `http://localhost:8000` and Swagger `/docs`. The Vite config does not explicitly pin a port; check the actual server output before browser validation.

Use these ML commands only when the task includes data analysis, training or benchmarking. They may download remote resources and overwrite generated outputs:

| Purpose | Root command |
| --- | --- |
| Prepare official snapshot | `python -m ml prepare --output data/processed/uit-vsfc-v1` |
| EDA | `python -m ml eda --data-dir data/processed/uit-vsfc-v1 --output artifacts/runs/eda-v1.json` |
| Train baseline | `python -m ml train-baseline --data-dir data/processed/uit-vsfc-v1 --run-dir artifacts/runs/baseline-v1` |
| Other stage arguments | `python -m ml train-phobert --help`, `python -m ml benchmark --help`, `python -m ml promote --help` |

Use [ml/README.md](ml/README.md) for the complete ordered workflow. `python -m ml` is the only training CLI; old flat script entry points were removed. Do not overwrite snapshot/run directories or replace production except through explicit promotion.

Use [current status](docs/status.md) for dated measurements, test evidence and open gates. Historical reports are phase snapshots, not current instructions. No training/tests/builds were rerun during the documentation synchronization.

No verified lint, formatting, typecheck, backend packaging or e2e workflow is established. Do not invent npm scripts or present inferred tool invocations as repository commands. See TODO-1 and TODO-2 below.

## Coding Standards and Existing-Code Changes

- Follow [.editorconfig](.editorconfig): UTF-8, LF, final newline; trim trailing whitespace except Markdown; four-space Python indentation and two-space JS/JSX/JSON/CSS indentation.
- Follow [pyproject.toml](pyproject.toml): Python 3.11 target, configured line length 100, Ruff groups `E`, `F`, `W`, `I`, with `E501` ignored. This is lint configuration, not evidence that Ruff is installed or enforced.
- Use Python `snake_case`, class `PascalCase`, and React function components with `PascalCase` names. Keep new Python interfaces typed consistently with neighboring schemas/services.
- Keep changed code readable and use the configured indentation. Existing compressed JSX/CSS and long Python lines are not a formatting standard; avoid whole-file reformatting unrelated to the task.
- Keep behavior-preserving refactors separate from algorithm, schema or UI behavior changes. Update affected imports and tests together. Former internal main.py helper exports were replaced by services/app factory; preserve the public ASGI entry point and HTTP contracts.
- Preserve endpoint paths, response fields, label IDs, database records and model interface unless the task requires changing them. Explain incompatible changes and their migration/validation needs.
- Avoid global path/environment changes in reusable modules. Before changing initialization, inspect import-time model/database dependencies and test fixtures.
- Update relevant documentation/tests when permitted by task scope. If scope excludes them, identify the remaining work instead of editing outside scope.

## API and Database Conventions

Sources: [schemas](backend/app/schemas.py), [routers](backend/app/api), [database](backend/app/database.py), [repository](backend/app/repository.py), [feedback service](backend/app/services/feedback.py).

- Preserve versioned `/api/v1/...` routes and the unversioned `/health`. Health reports `model_version` and `fallback_model`; it is not proof of model accuracy.
- Prediction requests require nonblank text, at most 5,000 characters; batch contains 1-100 items and preserves input order. CSV uses the same PredictionRequest schema. Optional created_at must include a timezone; unknown request fields and invalid enum/date filters return 422.
- Keep invalid-request errors understandable and return HTTP 422 for existing validation cases. Do not expose internal exception traces or sensitive content in responses.
- CSV accepts UTF-8/UTF-8 BOM, requires text and optionally aware ISO 8601 created_at. Validate header separately from data, report invalid records, enforce byte/row limits before persistence and retain valid-row atomicity. Record numbers start at 2 and count logical CSV records, not physical multiline lines.
- Use parameterized SQL values. Keep feedback and prediction insertion in the same transaction. Finish inference before opening the writer transaction. Batch writes are atomic. CSV may reject invalid records, but all accepted records persist atomically; do not turn model/database failures into input row errors.
- Schema: feedback_records stores id/raw_text/text/source/created_at/received_at; predictions stores one result per feedback_id with labels/confidence/model_version/predicted_at. Preserve one-to-one semantics until an explicit re-prediction/history migration changes them. schema_migrations records applied revisions.
- All connections enable PRAGMA foreign_keys=ON. Keep label/confidence/text constraints and parameterized SQL; add migration revisions instead of editing applied revisions.
- Migrations run in a transaction and preserve legacy IDs/sequences; invalid legacy data must abort without truncation or reset. Default production startup requires pre-applied schema. Test both upgrade and rollback-on-failure on disposable databases. Backup/retention policy remains TODO-3.
- Persist both raw_text and normalized text for new input. Migration backfills raw_text from legacy normalized text; never claim that original historical input was recovered.
- Persist new timestamps as aware UTC; use Asia/Ho_Chi_Minh only for local report filenames via clock.py. Source created_at, received_at before inference and predicted_at after inference are distinct. Date filters apply to predicted_at with inclusive lower/exclusive upper bounds.
- Keep the same FeedbackFilter contract across list/summary/export. Pagination and aggregation run in SQL. Dashboard.jsx includes pagination/date/matrix controls; browser fixture checks do not establish full real-model UI acceptance.
- Do not silently truncate exports: enforce MAX_EXPORT_ROWS with 413, wrap/paginate every accepted PDF record, and preserve spreadsheet formula protection in CSV. PDF requires an available Vietnamese-capable font; missing font returns 503 rather than Helvetica fallback.

## Environment and Security

Sources: [.env.example](.env.example), [.gitignore](.gitignore), [main.py](backend/app/main.py), [frontend config](frontend/src/config.js), [exports](backend/app/api/exports.py).

- Settings reads process environment at app creation; relative backend paths resolve from project root. Database/model I/O occurs in lifespan, not module import. Check resolved DATABASE_PATH before migrations. Frontend still reads VITE_API_URL separately.
- Settings consumes ENVIRONMENT, database/model paths, CORS, auth, limits and PDF font. HOST/PORT apply to python -m backend.app serve; Uvicorn CLI uses its own flags. See .env.example for exact names. Never print API_TOKEN or include it in dataclass repr.
- No automatic backend dotenv loading: export environment or explicitly pass --env-file to Uvicorn or python -m backend.app serve/migrate; existing process environment takes precedence. Local demo uses scripts/demo.ps1 and config/demo.env. Vite runs in frontend without an envDir override. Root .env does not implicitly configure both processes.
- Never include real credentials or identifiable feedback in commits, logs, fixtures or documentation. Do not print local secret values when inspecting configuration. Keep credentials out of frontend `VITE_*` values because those are client-facing.
- Keep environment files, SQLite databases, dependency caches and binary model checkpoints out of source changes according to `.gitignore`. It deliberately allows artifact JSON/Markdown; review those for sensitive metadata before sharing.
- Load Joblib artifacts only from trusted sources. Deserializing them can execute code; do not inspect an unknown artifact by loading it merely to enumerate metadata.
- Configured API_TOKEN protects /api/v1 with bearer comparison. Production requires a token, disables keyword demo and requires official-dataset provenance in the trusted model artifact. This is internal shared-token auth, not OIDC, RBAC or tenant isolation. Health/readiness/docs are public; never embed the shared token in the frontend.
- Bound request bodies before multipart parsing and enforce file/row limits. CSV inference runs in a sync worker, with no writer transaction during model work. Keep formula-injection escaping for dangerous CSV cell prefixes; quoting alone is insufficient. Log only request ID, method, route template, status, latency and redacted error type, never bodies/tokens/query values.
- Follow the PRD's data-privacy and dataset-use constraints. Verify dataset terms before non-academic use; predictions support aggregation, not disciplinary decisions about individuals.

## ML Data, Evaluation and Artifact Rules

- Keep train/validation/test roles distinct. Expected UIT-VSFC counts are 11,426/1,583/3,166; inspect actual loaded data rather than accepting configuration constants as validation.
- Fit vocabulary, IDF and model parameters on train. Select configuration using validation; evaluate test after selection. Report exact/near duplicates and handling rather than silently redefining the benchmark.
- Preserve Vietnamese diacritics, NFC normalization and negation. Evaluate changes to text processing instead of applying generic stopword deletion.
- Keep training and inference preprocessing consistent. Record the segmenter, tokenizer/checkpoint, truncation length, seed and actual hyperparameters; some current settings remain hardcoded despite experiment config fields.
- Keep the vectorizer with the baseline estimator. Evaluate the final calibrated pipeline after changing TF-IDF, SVM or calibration.
- PhoBERT uses normalized snapshot text, PyVi, a pinned model revision, separate task runs and early stopping. Per-task metrics use the same schema as baseline. Use `python -m ml import-phobert --help`, `python -m ml verify-phobert --help` and `python -m ml benchmark-phobert --help` for the imported-run CPU workflow; see ml/README.md for full commands. Verify hashes and use local safetensors only; never deserialize training_args.bin. Keep the CPU environment separate in ignored .venv-phobert. API promotion still supports baseline only.
- Serving PhoBERT uses backend/app/phobert.py and the shared lazy CPU runtime in backend/app/phobert_runtime.py. Select MODEL_BACKEND and both PHOBERT task run paths explicitly; validate receipts/hashes before loading. Serialize model work with the adapter lock and keep inference outside DB writer transactions. Do not change a Joblib path to select PhoBERT.
- Production training loads only verified official snapshots. There is no synthetic fallback. Test fixtures may be tiny synthetic data but must never be promoted or reported as UIT-VSFC evidence. Train writes a new run directory; only the explicit `promote` stage may replace production.
- Legacy baseline metrics identify `canonical_local_seed`; legacy EDA includes estimated statistics. They remain historical files and are not read by the new workflow. New EDA measures a checksum-verified snapshot.
- Missing measurements remain missing. New metrics fail latency acceptance until a measurement exists. Benchmark records the exact artifact hash and dataset; promote checks run/metrics/artifact integrity and explicit acceptance thresholds.
- Report accuracy, macro/weighted F1, per-class precision/recall/F1/support and confusion matrix for both tasks. PRD targets are macro F1 >=0.80 sentiment, >=0.75 topic and p95 <2 seconds; do not state these as achieved without valid experiments.
- Separate model loading, warmed-up inference and complete request latency. State hardware, sample count, batch size and mean/p95; benchmark the same scope when comparing models.
- Record data source/revision, actual split sizes, seed, library versions and environment for changed experiments. [ml/core/config.py](ml/core/config.py) controls active settings, including warmup ratio, macro F1 selection and early-stopping patience.
- Preserve unrelated checkpoints and metrics. The duplicated training notebook was removed. notebooks/phobert_colab.ipynb is a thin CLI wrapper with checksum-verified code/data handoff, not a second training implementation; see [Colab guide](docs/workflows/colab_training_guide.md).
- Test dataset validation/checksums, non-overwriting runs, missing metrics, benchmark/artifact matching and rejection of synthetic promotion with `python -B -m pytest tests/test_ml_workflow.py tests/test_data_integrity.py tests/test_preprocessing.py -q -p no:cacheprovider`.

## Testing Requirements

- Select checks by the changed behavior and use existing test patterns. Add regression coverage for meaningful fixes; avoid tests that only mirror implementation or assert a rearranged module layout.
- `test_preprocessing.py` and `test_data_integrity.py` cover text, mappings, config and metrics. The split-integrity test checks constants, not real corpus isolation.
- `test_api_direct.py` calls endpoint functions and writes SQLite; it is not a fully isolated unit suite. `test_api.py` exercises HTTP behavior through FastAPI `TestClient`.
- Protect data/feedback.db. Tests use shared fixtures in tests/conftest.py with explicit Settings, temporary SQLite and fake predictors; do not restore global environment-path overrides or delete database files in fixture setup. Test migration constraints and rollback using test_architecture.py. In AGENTS.md-only tasks do not run tests/builds that write generated outputs.
- For request/schema changes, cover valid and invalid input plus relevant batch order/limits. For import/export changes, cover invalid rows, Unicode, filters and completeness. For database changes, verify persisted relationships and failure behavior using an isolated database.
- For frontend changes, run the existing production build and exercise the affected flow when a browser is available. Check loading/error/empty states; capture screenshots for layout-sensitive changes. No configured frontend unit/e2e suite exists. Local Edge/CDP fixture checks are recorded in docs/reports/2026-11-07/ui-redesign.md; do not equate them with real-model E2E coverage.
- For documentation-only changes, validate local links, paths, command evidence and Markdown structure. Application tests, training and builds are not required. If checking safe Python unit tests without generated files, use `python -B -m pytest tests/test_preprocessing.py -q -p no:cacheprovider`; `-B` disables bytecode and the pytest option disables its cache. The metrics module uses the standard library, so data-integrity tests do not import SciPy; the baseline smoke/reference tests in test_ml_workflow.py do require scikit-learn.
- Report exact commands actually run and their outcomes. If a test hangs or a runtime is unavailable, state the gap; a passing direct suite does not verify HTTP or browser behavior. Never equate file existence with a successful build.

## Git and Pull Requests

The inspected directory has no recognized Git worktree: `git rev-parse`, branch and log inspection failed. No CI or contribution policy was found. Do not assume a default branch, Conventional Commits, branch prefixes, merge strategy, required checks or reviewer policy. Resolve TODO-5 before documenting these as established rules; do not initialize Git solely to satisfy documentation.

If Git becomes available, inspect the diff before committing; keep generated artifacts and runtime data out of unrelated commits. Artifact JSON/Markdown are intentionally allowed by `.gitignore`, so do not categorically exclude requested experiment reports. Do not create commits, push, publish or open a PR unless the task authorizes that action.

## Unresolved Repository Policies

These TODOs require repository evidence or an explicit maintainer decision. They are not instructions to implement unrelated work during the current task.

- **TODO-1 — Quality tooling:** define and verify lint, formatter, typecheck and backend build/package commands; Ruff settings exist but its installation/workflow is unspecified.
- **TODO-2 — Automated validation:** define frontend unit/e2e tooling, browser commands, coverage expectations and CI checks; no Playwright or CI configuration was found.
- **TODO-3 — Database operations:** formalize backup/restore, retention/deletion and release rollback procedures. Versioned migrations and legacy upgrade/failure tests now exist.
- **TODO-4 — Secrets lifecycle:** choose production secret provisioning/rotation and a public-web identity flow. Explicit process-environment loading and host/port/log/CORS handling now exist.
- **TODO-5 — Git workflow:** verify repository/remote, default branch, branch naming, commit format, PR template/review/check requirements and merge policy.
- **TODO-6 — Deployment scale:** define reverse proxy/TLS, process supervision, load testing and PostgreSQL/queue adapters when needed. Internal bearer auth, request limits and CSV protection exist; OIDC/RBAC/multi-tenancy do not. Provision a Unicode font in the target image.
- **TODO-7 — Reproducible model release:** add a Python dependency lock strategy, release rollback and concurrency/load validation. Imported-run hashes, reload verification, CPU benchmarking and an offline baseline/PhoBERT comparison now exist; sequential HTTP/DB latency has evidence; concurrent load and full release acceptance remain unverified. Resolve near-duplicate analysis and dataset-use terms for intended distribution.

## Definition of Done

Before marking a task complete, check each item or explicitly report why it is not applicable or remains blocked. Do not claim completion while requested work remains unfinished.

- [ ] Changes stay within the user's authorized file and feature scope; existing work and unrelated artifacts are preserved.
- [ ] Modified code respects module boundaries, EditorConfig, label mappings and relevant API/database/model contracts.
- [ ] Behavior changes have appropriate regression coverage; documentation-only changes have link/path/command checks.
- [ ] Relevant verified tests/builds or manual flows were run, or the precise validation limitation is reported. No invented lint/e2e command or assumed pass is listed.
- [ ] Test database targets and generated-output paths were checked; runtime feedback and unrelated model artifacts were not overwritten.
- [ ] No secret/identifiable feedback, cache, accidental dependency change or unrequested generated file is included.
- [ ] Any ML result states its actual data source and evaluation scope; missing measurements and synthetic evidence are identified.
- [ ] Affected documentation is consistent with implementation where editing it is authorized; otherwise remaining updates are disclosed.
- [ ] The final response names the changes, their purpose, actual validation and unresolved risks/TODOs without claiming checks that were not performed.
