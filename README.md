# Soukly

AI-powered marketplace & concierge for Morocco. First vertical: **Real Estate**.

## Staging (Render)

See `render.yaml` and `docs/STAGING.md`.

```bash
python3 server/migrate.py && python3 server/app.py
```

Serves UI at `/` and API at `/api/*` on the same host.
