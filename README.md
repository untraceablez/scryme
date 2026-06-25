# scryme

A localized, self-hostable implementation of [Scryfall](https://scryfall.com), designed for
indexing and searching **your own** Magic: The Gathering collection.

Upload an export from **ManaBox**, **Dragon Shield**, or **Delver Lens** and search it with a
Scryfall-style interface that understands [Scryfall search syntax](https://scryfall.com/docs/syntax)
and [regular expressions](https://scryfall.com/docs/regular-expressions).

> Status: early development. Phase 0 (project scaffold + CI) is the first feature branch.

## Features (planned)

- 📥 Import collections from ManaBox, Dragon Shield, and Delver Lens
- 🔁 Merge strategies on re-import: **replace**, **increment**, or decide **per card**
- 🔎 Scryfall-compatible search syntax and regex, scoped to your collection (or all cards)
- 🖼️ Local card database and image cache — works offline, respects Scryfall's API policy
- 🐳 Self-hostable via Docker, with a small public demo (read-only)

## Quick start (self-host)

```bash
docker compose up -d
# open http://localhost:8080
```

On first run the collection is empty, so the home page shows an upload prompt. After importing a
collection it becomes a Scryfall-style search bar.

### Configuration

| Variable | Default | Purpose |
| --- | --- | --- |
| `POSTGRES_PASSWORD` | `scryme` | Database password |
| `SCRYME_PORT` | `8080` | Host port for the web UI |
| `SCRYME_READ_ONLY` | `false` | Demo mode — disables uploads/mutations |

## Development

```bash
docker compose -f docker-compose.dev.yml up   # hot reload, app on http://localhost:8000
cd backend && pytest tests/                   # tests (needs Postgres via SCRYME_DATABASE_URL)
```

See [CLAUDE.md](CLAUDE.md) for architecture and conventions.

## Tech stack

FastAPI · SQLAlchemy (async) · PostgreSQL · Alembic · Jinja2 + HTMX + Tailwind · Docker ·
Jenkins + SonarQube.

## Acknowledgements

Card data and images come from [Scryfall](https://scryfall.com). scryme is unofficial Fan
Content permitted under the Wizards of the Coast Fan Content Policy and is not affiliated with
or endorsed by Wizards of the Coast or Scryfall.

## License

See [LICENSE](LICENSE).
