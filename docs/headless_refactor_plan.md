# Headless Refactor Plan

## Vision
Transform `Infantinho 3.0` into a headless platform: Django provides a secure REST API; Next.js delivers a MEM-aligned UX. The goal is to preserve existing business logic while exposing consistent contracts for a TypeScript frontend.

## Backend Roadmap (Django API)
1. **Project Structure**
   - Create `backend/` package (keep `manage.py` at root) and move current Django project inside for clarity (`backend/infantinho_core/`).
   - Add `core/` app for shared utilities (audit mixins, permissions, serialiser helpers).
   - Enable `django-environ`, `django-cors-headers`, `rest_framework`, `drf_spectacular`.
2. **Models & Migrations**
   - Consolidate user roles via `users.User` model with `role` choices and `is_guest` flag.
   - Introduce missing entities (`ChecklistStatus`, `AIInteractionSession`, etc.) and align relations (e.g. `ClassMembership` with role per class).
   - Add audit fields (`created_by`, `updated_at`) where workflows demand accountability.
3. **Serializers & ViewSets**
   - Organise per domain app (e.g. `checklists/api/serializers.py`, `checklists/api/views.py`).
   - Use `ModelViewSet` with nested routers for contextual endpoints (`/classes/{id}/posts/`).
   - Provide pagination defaults, filtering (django-filter), and field-level validation enforcing role logic.
4. **Auth & Permissions**
   - Integrate `social-auth-app-django` for Azure AD login; on callback create/update guest users.
   - Expose `/api/auth/microsoft/` (redirect) and `/api/auth/callback/` (create JWT).
   - Configure `SimpleJWT` with short-lived access + refresh tokens stored in HTTP-only cookies (frontend friendly).
   - Implement custom DRF permissions encapsulating MEM rules (per-class scoping, guest read-only, etc.).
5. **Business Endpoints**
   - CRUD for each module + action endpoints (e.g. `ChecklistsItemStatusViewSet` actions `mark`, `validate`).
   - PIT workflow endpoints (`submit`, `approve`, `evaluate`) updating state machine fields.
   - Project collaboration endpoints (`assign_member`, `remove_member`, `add_update`).
   - Council decision endpoints with versioning/history.
6. **AI Orchestration**
   - Service module `ai/services/orchestrator.py` invoked by `POST /api/ai/assistant/`.
   - Store sessions/conversations, allow streaming responses (server-sent events) for UI.
7. **Docs & Tooling**
   - Configure `drf-spectacular` schema at `/api/schema/`; serve Swagger UI at `/api/docs/`.
   - Write pytest-based tests per app (reuse `pytest-django`), covering permissions, workflows, AI orchestrator contract.
   - Add `Makefile` commands (`make migrate`, `make test`, `make lint`).

## Frontend Roadmap (Next.js + TypeScript)
1. **Project Setup**
   - Create `/frontend` workspace with Next.js App Router, TypeScript strict mode, Tailwind CSS + shadcn/ui.
   - Configure absolute imports, ESLint/Prettier matching backend naming conventions.
2. **Auth & Session Management**
   - Implement Microsoft login button hitting backend redirect; handle callback page to exchange auth code for backend JWT (set via secure cookies).
   - Create `AuthProvider` with React Query to refresh tokens and expose user context (role, memberships, guest state).
3. **Feature Surfaces**
   - **Dashboard** summarising to-dos (pending PIT approvals, new posts, checklist items) per role.
   - **Checklists**: components for student self-marking, teacher validation, progress bars per domain; optimistic updates via React Query mutations.
   - **PIT Flow**: wizard for drafting/submitting tasks; timeline showing statuses; comment thread per task.
   - **Diary/Blog**: WYSIWYG editor (shadcn + TipTap or React TinyMCE) with media upload support via backend signed URLs.
   - **Projects**: Kanban-style task board, team roster, AI-assisted idea prompts.
   - **Council Decisions**: chronological log with filters, printable summaries.
   - **AI Tutor**: contextual chat drawer component; posts payload {origin_app, context_id, message}.
4. **State & Data Layer**
   - Use `@tanstack/react-query`; define `apiClient` using `fetch` wrappers that include CSRF/credentials.
   - Generate TypeScript types from OpenAPI schema (via `openapi-typescript`) to keep contracts in sync.
5. **Internationalisation**
   - Integrate `next-intl`; default `pt-PT`, prepare `en-GB`. Keep copy in `/frontend/messages/` with domain splits (common, dashboard, pit, etc.).
6. **Testing & QA**
   - Unit tests with Vitest; integration tests with Playwright for critical flows (login, PIT submission, checklist validation).
   - Storybook for core components (checklist card, PIT stepper, AI chat panel).

## Data Seeding & Dev Experience
- Move existing demo command to new `backend/demo/management/commands/populate_demo_data.py` generating consistent users/classes/projects with roles.
- Provide fixture JSON for frontend mocks (`frontend/mocks/*.json`) to allow UI work before backend readiness.
- Docker Compose stack for local dev: Django API, PostgreSQL, Next.js dev server.
- Document `.env` samples for backend (`backend/.env.example`) and frontend (`frontend/.env.example`).

## Milestones
1. **Foundations**: Restructure repo, enable DRF, basic auth flow (guest users), barebones Next.js app with login handshake.
2. **Core Modules**: Expose REST endpoints and frontend pages for Checklists, PIT, Blog, Projects, Council.
3. **AI Integration**: Implement orchestrator, chat UI, tune prompts.
4. **Polish & QA**: i18n coverage, accessibility review, e2e tests, documentation.


- [x] Repository reorganized with Django project under `backend/` and thin root `manage.py` wrapper.
- [x] Settings updated with DRF, SimpleJWT, CORS, Spectacular, and new `core` app scaffolding.
- [x] Initial API surface published at `/api/` with routers for `users` and `classes` plus schema endpoints.
- [x] Introduced explicit `ClassMembership` model with migrations, synced signals, and tests ensuring student/teacher membership creation.
- [x] Added headless blog API (`/api/blog/posts`) with role-aware filtering plus placeholder API packages for other domains.
- [x] Exposed checklist templates/statuses/marks via `/api/checklists/...` with DRF viewsets, serializer guards, and API smoke tests (`ChecklistAPITests`).
- [x] Delivered PIT, Projects, Council and AI endpoints (actions + permissions) com testes dedicados (`PitAPITests`, `ProjectAPITests`, `CouncilAPITests`, `AIAssistantAPITests`).
- [x] Implemented Microsoft SSO → SimpleJWT flow (`/api/auth/microsoft/*`, `/api/auth/token/refresh`, `/api/auth/logout`) com refresh cookie HTTP-only e emissão de access token.
- [x] Bootstrapped frontend Next.js (App Router, Tailwind, React Query) com providers de Auth/Query, páginas de dashboard/classes/projetos e login Microsoft integrado à API.

## Next Backend Tasks
1. Consolidar notificações (emails/webhooks) em serviços partilhados para PIT, projetos e checklists.
2. Documentar schemas via Spectacular com tags e exemplos; publicar `/api/docs` segmentado por domínio.
3. Expandir testes cobrindo fluxos negativos (permissões negadas, transições inválidas, quotas de IA).
4. Atualizar `demo_data` para gerar planos, projetos e decisões alinhadas com o headless API.

## Next Frontend Tasks
1. Gerar tipos e clients a partir do OpenAPI (`openapi-typescript`, `orval`) e centralizar consumo no frontend.
2. Construir páginas ricas para checklists, PIT e IA tutor com mutações otimistas e notificações de sucesso/erro.
3. Adicionar Storybook + Playwright para snapshots de UI e fluxos críticos (login, submissão PIT, validação checklist).
4. Internacionalizar com `next-intl` (pt-PT/en-GB) e rever acessibilidade/componentização (shadcn/ui).
