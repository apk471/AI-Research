# Repository Guidelines

## Project Structure & Module Organization
This repository is a monorepo with a Go backend and shared TypeScript packages.
- `app/backend/`: Go API server (`cmd/go-boilerplate` entrypoint, application code in `internal/`, static docs in `static/`, HTML/email templates in `templates/`).
- `packages/zod`: shared Zod schemas.
- `packages/openapi`: `ts-rest` contracts and OpenAPI generation.
- `packages/emails`: React Email templates consumed by backend template workflows.
- Tests live next to source as `*_test.go` (Go) and under each TS package’s `src/`-adjacent test setup.

## Build, Test, and Development Commands
Run from repo root unless noted.
- `bun run dev`: starts Turbo dev pipelines across workspaces.
- `bun run build`: builds all configured workspaces.
- `bun run lint`: runs workspace linting through Turbo.
- `bun run typecheck`: runs TypeScript type checks.
- `cd app/backend && task run`: starts the Go API locally.
- `cd app/backend && task tidy`: runs `go fmt`, `go mod tidy`, and dependency verification.
- `cd app/backend && go test ./...`: runs backend tests.
- `cd app/backend && task migrations:new name=add_users_table`: creates a migration file.
- `cd app/backend && BOILERPLATE_DB_DSN=... task migrations:up`: applies DB migrations.

## Coding Style & Naming Conventions
- Go code must pass `gofmt` and `golangci-lint` (`app/backend/.golangci.yml`).
- Keep Go packages aligned by layer: `handler`, `service`, `repository`, `middleware`.
- Use `CamelCase` for exported Go symbols.
- Use `snake_case` for migration files (example: `002_add_users.sql`).
- TypeScript packages use strict `tsconfig`; keep source in `src/` with explicit exports.

## Testing Guidelines
- Add table-driven Go tests for handlers/services where practical.
- Cover success and error paths (validation failures, DB errors, auth checks).
- Run `cd app/backend && go test ./...` for backend changes.
- For TS package changes, at minimum run `bun run typecheck` and relevant package builds.

## Commit & Pull Request Guidelines
- Prefer clear, imperative commit messages with scoped prefixes:
  - `feat: add health check redis timeout handling`
  - `fix: map pg unique violation to 400`
- Keep commits focused on one concern.
- PRs should include purpose, key changes, test commands run, config/migration impact, and sample API output when behavior changes (for example `/status` or `/docs`).

## Security & Configuration Tips
- Never commit secrets; use `BOILERPLATE_*` environment variables.
- Set `BOILERPLATE_DB_DSN` explicitly for migration commands.
- Keep generated OpenAPI output synchronized with `app/backend/static/openapi.json`.
