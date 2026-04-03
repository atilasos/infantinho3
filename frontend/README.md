# Infantinho 3.0 • Frontend Headless

Interface Next.js 15 em TypeScript que consome a API Django. O foco é apresentar os instrumentos MEM de forma moderna e responsiva para alunos, professores, encarregados e administração.

## Scripts disponíveis

```bash
npm run dev            # Inicia o app em modo desenvolvimento (Turbopack)
npm run build          # Compila a aplicação para produção
npm run start          # Serve a build de produção
npm run lint           # Lint do código
npm run generate:api   # Gera tipos TypeScript a partir do esquema OpenAPI
npm run storybook      # Abre a biblioteca de componentes em http://localhost:6006
npm run build-storybook# Compila o Storybook exportável
npm run test:e2e       # Executa os testes Playwright (precisa do backend desligado ou acessível)
```

> 💡 Antes de correr os testes E2E execute `npx playwright install chromium` uma vez para descarregar o browser.

## Estrutura relevante

```
src/
  app/                # Rotas App Router: painel, checklists, PIT, diário, assistente IA
  components/
    layout/           # AppShell partilhado para páginas autenticadas
    ui/               # Componentes reutilizáveis (ex.: ActionCard + story)
  lib/                # Utilitários (classes CSS, helpers de dados)
  providers/          # Contextos globais (autenticação Microsoft → JWT)
  types/              # Tipos derivados de OpenAPI (src/types/openapi.ts)
```

## Integração OpenAPI

1. Gere o esquema com o backend (se necessário):
   ```bash
   python manage.py spectacular --file docs/api-schema.yaml
   ```
2. Produza os tipos para o frontend:
   ```bash
   cd frontend
   API_SCHEMA_URL=../docs/api-schema.yaml npm run generate:api
   ```

`AppUser`, `ChecklistStatus`, `IndividualPlan`, `Project` e restantes modelos passam a vir diretamente de `src/types/api.ts`, que reexporta os tipos gerados.

## Estrutura das rotas

- `/` — blog público alimentado por `GET /api/blog/public`, ideal para apresentar a direção sem iniciar sessão.
- `/dashboard` — painel autenticado com atalhos para checklists, PIT, diário, projetos e tutor IA.
- restantes rotas (`/checklists`, `/pit`, `/diario`, `/projects`, `/assistente`) partilham o `AppShell` e protecção por sessão Microsoft.

## Storybook

```bash
npm run storybook
```

- A biblioteca abre em `http://localhost:6006` com o `ActionCard` e futuros componentes de interface MEM.
- Utilize esta galeria para apresentar rapidamente estados visuais à direção da escola.

## Testes End-to-End

```bash
npx playwright install chromium   # apenas na primeira vez
npm run test:e2e
```

Os testes verificam o hero público e o comportamento responsivo do fluxo de login. Personalize `PLAYWRIGHT_BASE_URL` se executar atrás de proxy.

## Variáveis de ambiente

Crie `frontend/.env.local` com:

```
NEXT_PUBLIC_API_URL=http://localhost:8000/api
NEXT_PUBLIC_SITE_URL=http://localhost:3000
```

`NEXT_PUBLIC_API_BASE_URL` continua a ser aceite por compatibilidade, mas a variável canónica é `NEXT_PUBLIC_API_URL`.

Opcionalmente adicione `API_SCHEMA_URL` ao correr o script de geração de tipos.

---

Com o frontend a correr e a API disponível, o portal pode ser apresentado à direção da escola demonstrando o painel, listas de verificação, PIT, diário e assistente IA em navegação responsiva.
