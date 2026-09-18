# Build status

## Verified in this workspace

- FastAPI core and persistence tests: passing.
- Template variable and dynamic-table resolution: passing.
- PDF renderer: creates valid PDF bytes in tests.
- DOCX renderer: creates valid Office Open XML bytes in tests.
- SQLite template/document persistence and optimistic version conflicts: passing.
- TypeScript typecheck: `document-schema`, `template-engine`, `renderer`, `signature-engine`, `verification`, `sdk-js` pass.
- Product-neutrality scan: no LoanHub/gRisk/BuildTrack/Tjekatjeka/Guardrisk names in the standalone codebase.

## Not build-verified here

The `packages/editor` and `apps/web` dependency build could not be run in this execution environment because DNS access to `registry.npmjs.org` is blocked. The implementation follows the current Tiptap 3 package layout (including v3's consolidated table package), but CI must run `pnpm install`, `pnpm typecheck` and `pnpm build` once the repository is online.

## Pagination

The open core uses physical A4/Letter dimensions and explicit page-break nodes. Automatic overflow reflow into separate visual pages is the remaining pagination subsystem. It is deliberately not simulated with brittle fixed-height HTML. The document schema does not depend on a pagination provider, so the project can later use an Ithute-owned pagination plugin or Tiptap Pages if private-registry access is chosen.

## Explicitly deferred

External product/data connectors. The core accepts a neutral data dictionary and JSON records only.
