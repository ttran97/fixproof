# FixProof Primary Benchmark Suite v1

This directory contains the frozen target-only applications for the FixProof
primary study. They are deliberately vulnerable and must be run only on the
local loopback interface for controlled testing.

The pilot applications under `sample_apps/` and their evidence are historical
and remain unchanged. These primary applications use the same three CWE classes
but remove unrelated intentionally seeded vulnerabilities.

| Directory | Target | Route | Intended insecure flow |
|---|---|---|---|
| `xss/` | CWE-79 reflected XSS | `GET /hello?name=...` | `req.query.name` to an HTML `res.send` response |
| `sqli/` | CWE-89 SQL injection | `GET /user?username=...` | `req.query.username` to SQLite query text |
| `path-traversal/` | CWE-22 path traversal | `GET /file?name=...` | `req.query.name` to `fs.readFile` without containment |

Each directory contains an exact dependency lockfile. Test definitions,
scanner expectations, baseline hashes, and evidence requirements are held in
`data/evaluation/primary-benchmark-manifest.json`; they are evaluator inputs
and must never be included in an AI remediation prompt.

Install dependencies from the repository root:

```powershell
Push-Location benchmarks\primary\v1\xss
npm ci
Pop-Location

Push-Location benchmarks\primary\v1\sqli
npm ci
Pop-Location

Push-Location benchmarks\primary\v1\path-traversal
npm ci
Pop-Location
```

Verify all three baselines from the repository root:

```powershell
.\.venv\Scripts\python.exe -m fixproof.evaluation.benchmark_verifier
```

The frozen trial plan schedules five initial attempts per case. Do not edit a
benchmark after primary model generation begins; create a new suite version
instead.
