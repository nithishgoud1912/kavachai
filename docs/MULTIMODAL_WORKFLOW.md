# Combined inspection analysis

Restart the backend after installing this change. Existing tasks retain the plan
and results recorded when they ran; create a new task to test the new routing.
After restarting, `http://localhost:8000/api/v1/health` must include
`"workbench_workflow": "multimodal-v2"`. If that field is absent, the old backend
process is still serving requests.

1. Choose **Auto** or **Document**, with **Word Doc** output.
2. Attach the inspection PDF and its CSV measurements. The supplied synthetic
   report also contains a numeric PDF table, which can be analysed without a CSV.
3. Ask: "Inspect the visual evidence, calculate the numeric trends, reconcile
   conflicting records, and draft a manager review report. Keep different assets
   and observation periods separate and cite every source."

For a report with both visual and numeric evidence, the plan has five stages:

| Stage | Default component | Actual operation |
| --- | --- | --- |
| Evidence search | nomic-embed-text | Search authorized local document text |
| Visual inspection | qwen2.5vl:3b | Inspect image attachments and scanned/illustrated PDF pages |
| Numeric analysis | qwen2.5-coder:3b | Produce a validated calculation plan for detected numeric tables |
| Synthesis and verification | qwen2.5:3b | Combine source text, visual observations and calculated results |
| Office export | Local Office exporter | Create the requested file without another model call |

Routing follows the configured model map, so model names can differ from these
defaults. A plain text task does not call a vision or coding model unnecessarily.
Explicit Vision mode inspects every PDF page; automatic routing inspects pages
with substantial embedded images, sparse text or diagram content. Image/scan
inspection is bounded to 20 pages; numeric analysis to 12 tables with 10,000 rows
and 64 columns each. Oversized requests fail with a split-request message.

## Running without Docker

Document numeric analysis runs without Docker. The coder returns a declarative
JSON plan selecting mean, minimum, maximum and/or date-ordered percentage change.
A closed local calculator validates columns and numbers and evaluates these
operations over the stored source table. Generated Python is never executed on
the host. This is distinct from the **Code** task, which still requires the
isolated Docker worker to execute arbitrary generated Python and its assertions.

The calculator keeps recognized equipment/asset, metric and unit groups separate.
Missing values are counted explicitly; invalid numbers, ambiguous date ordering,
missing endpoints and zero baselines are rejected for percentage changes. It does
not infer engineering thresholds, threshold-crossing dates, causes or remaining
life. Units follow the source headers and require review if unspecified.

## Checking the result

The plan shows a separate vision and coding stage when relevant content is
detected. The tool timeline records `document_search`, `vision_inspect` and
`bounded_table_calculation`, including real success/failure states and source IDs.
`models_used` records model selections as the stages run, not all installed models.
The export retains the visual observations and calculated results, even if the
reasoning summary omits them. Human review remains required. A specialist model
failure fails the task visibly; the system does not substitute invented evidence.

Vision requests preserve aspect ratio and limit images to 1024 pixels on the
longest edge by default to reduce CPU inference cost. Set `VISION_MAX_IMAGE_EDGE`
(512-4096) for different image detail needs; larger images cost more time and RAM.
`VISION_TIMEOUT_SECONDS` controls the per-request timeout. Text inference uses
`LLM_CONTEXT_TOKENS` (default 8192) and bounded evidence excerpts.

## Validation

Run from `backend`:

```powershell
python -m pytest tests/unit/test_multimodal_workbench.py tests/unit/test_review_fixes.py tests/unit/test_synthesis_verification.py tests/unit/test_document_export.py tests/unit/test_code_sandbox.py -q -p no:cacheprovider
```

These regression tests use isolated temporary stores and controlled model replies.
They verify the combined PDF-plus-CSV route, actual specialist function calls,
numeric outputs, failure propagation, audit events and Word export. They do not
certify local model quality or deployment-wide network isolation.
