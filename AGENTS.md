# Repository Guidelines

## Project Structure & Module Organization
This repository is a monorepo with a Go backend and shared TypeScript packages.
- `app/backend/`: Go API server (`cmd/go-boilerplate` entrypoint, `internal/` app code, `templates/`, `static/`).
- `packages/zod`: shared Zod schemas.
- `packages/openapi`: ts-rest contracts and OpenAPI generation.
- `packages/emails`: React Email templates exported to backend HTML templates.
- `README.md`: architecture, environment variables, and operational details.

## Build, Test, and Development Commands
Run from repository root unless noted.
- `bun run dev`: starts Turbo dev pipelines across workspaces.
- `bun run build`: builds all configured workspaces.
- `bun run lint`, `bun run typecheck`: workspace linting/type checks through Turbo.
- `cd app/backend && task run`: run the Go API locally.
- `cd app/backend && task tidy`: `go fmt`, `go mod tidy`, and dependency verification.
- `cd app/backend && task migrations:new name=add_users_table`: create a migration.
- `cd app/backend && BOILERPLATE_DB_DSN=... task migrations:up`: apply migrations.

## Coding Style & Naming Conventions
- Go code must pass `gofmt` and `golangci-lint` (`app/backend/.golangci.yml`).
- Keep packages focused by layer (`handler`, `service`, `repository`, `middleware`).
- Use `CamelCase` for exported Go symbols and `snake_case` file names for SQL migrations (e.g., `002_add_users.sql`).
- TypeScript packages use strict `tsconfig` settings; keep source in `src/` and exports explicit.

## Testing Guidelines
- Add Go tests as `*_test.go` files next to the package under test.
- Run backend tests with `cd app/backend && go test ./...`.
- For changed TS packages, at minimum run `bun run typecheck` and package build commands.
- Prefer table-driven tests for handlers/services and cover error paths (validation, DB, auth).

## Commit & Pull Request Guidelines
Recent history includes short messages and partial `feat:` prefixes; use clear, imperative commits consistently.
- Recommended format: `feat: add health check redis timeout handling`, `fix: map pg unique violation to 400`.
- Keep commits scoped to one concern.
- PRs should include: purpose, key changes, test commands run, config/migration impact, and sample API output when behavior changes (e.g., `/status` or `/docs`).

## Security & Configuration Tips
- Never commit secrets; use `BOILERPLATE_*` environment variables.
- For migration tasks, set `BOILERPLATE_DB_DSN` explicitly.
- Validate OpenAPI output stays in sync with backend static docs (`app/backend/static/openapi.json`).
