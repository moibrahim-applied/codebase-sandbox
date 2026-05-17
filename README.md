# MT codebase sandbox — multi-service demo target

This repository is the live target the **MT Security Patch Agent** patches when
CVEs are discovered against MT's containerized stack.

## Layout

Each tracked container has its own folder under `services/`:

```
services/
└── <container-name>/
    ├── Dockerfile        ← agent edits the FROM line here
    ├── (config files)
    └── (tests/, optional)
```

The patch agent finds the right Dockerfile via `grep -rn "FROM <container>:"`
and edits only the version pin.

## Services

| Service | Base image | Used by |
|---|---|---|
| `nginx` | `nginx:1.22.1` | FreeWeigh.Net web console |

New services are scaffolded automatically when an operator clicks **Add Container**
in the Lovable inventory page — the Coding Agent's `POST /add-container` endpoint
appends a row to the Supabase `containers` table AND creates a matching
`services/<name>/Dockerfile` here.

## CI

`.github/workflows/ci.yml` discovers every folder under `services/` and runs
`docker build` + optional smoke test for each in a matrix job.
