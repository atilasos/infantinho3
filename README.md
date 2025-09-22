# Infantinho 3.0

Portal educativo para o Colégio Infante Dom Henrique, alinhado com o Modelo Pedagógico do Movimento da Escola Moderna (MEM).

> **Desenvolvimento incremental:**
> Consulte o arquivo `TODO.md` para o roadmap detalhado, fases de implementação e tarefas técnicas. O desenvolvimento segue as etapas e prioridades ali descritas.

## Visão Geral
O Infantinho 3.0 é um portal educativo que facilita a gestão cooperada da aprendizagem, digitalizando instrumentos pedagógicos do MEM, como listas de verificação de aprendizagens, Planos Individuais de Trabalho (PIT), planos de projeto, diário de turma e registo de decisões do conselho de turma. Integra agentes de Inteligência Artificial (IA) para apoiar alunos e professores.

## Funcionalidades Principais
- **Gestão de Turmas e Utilizadores**: Criação e gestão de turmas, perfis de alunos, professores, encarregados de educação e administradores.
- **Ferramentas Cooperativas MEM**: Listas de verificação, PIT, planos de projeto, diário de turma, registo de decisões.
- **Blog/Diário de Turma**: Blog por turma para registo de atividades, reflexões e produções, agora com orientações pedagógicas MEM nos formulários e nas leituras detalhadas.
- **Planos Individuais de Trabalho**: Autoavaliação do aluno, feedback do professor e notificações automáticas em cada etapa.
- **Projetos Cooperativos**: Criação e edição de projetos partilhados por professores e alunos, com tarefas atribuídas apenas a membros da turma.
- **Participação Ativa dos Alunos**: Alunos criam posts, propõem e autoavaliam PITs, participam em projetos e interagem com IA.
- **Ferramentas do Professor**: Gestão de turmas, avaliação/validação de PITs e aprendizagens.
- **Agentes de IA Colaborativos**: Assistentes virtuais para apoio contextualizado, alinhados com documentos pedagógicos.
- **Autenticação Federada**: Login via contas Microsoft escolares (Office 365/Azure AD).
- **Internacionalização**: Interface em Português Europeu, preparada para outros idiomas.

## Arquitetura e Tecnologias
- **Backend**: Django 5 (REST Framework, SimpleJWT), apps modulares (`users`, `classes`, `checklists`, `pit`, `projects`, `council`, `ai`).
- **Frontend**: Next.js 15 (App Router, React Query, Tailwind) a consumir a API headless.
- **Autenticação**: Single Sign-On Microsoft (Azure AD) → JWT (access + refresh cookie HTTP-only).
- **Base de Dados**: PostgreSQL (produção) e SQLite (desenvolvimento local).
- **Integração IA**: Orquestrador configurável (OpenAI/Google), quotas e sessions persistentes.
- **Segurança & RGPD**: Controlo de acesso por papéis, tokens rotativos, cookies HttpOnly.
- **Internacionalização**: Interface padrão pt-PT, preparado para multi-idioma no frontend.

> ### Documentação
> Guias detalhados vivem em `docs/`:
> - `docs/AGENTS.md`: Guia para contribuidores/headless agents.
> - `docs/headless_refactor_plan.md`: Roadmap técnico da migração.
> - `docs/api-schema.yaml`: export do esquema OpenAPI gerado via `python manage.py spectacular --file docs/api-schema.yaml`.
> - `docs/notifications.md`: resumo da estratégia de notificações por email/webhook.
> - `docs/` _(+ restantes ficheiros de referência)_ mantém diagramas, listas e contextos.

## MVP (Produto Viável Mínimo)
O MVP inclui:
- Módulo de blog/diário de turma
- Listas de verificação de aprendizagens
- Gestão básica de utilizadores e turmas

## Instalação e Execução (Desenvolvimento)
1. Clone o repositório:
   ```bash
   git clone <repo-url>
   cd infantinho3
   ```
2. Crie e ative um ambiente virtual:
   ```bash
   python -m venv venv
   source venv/bin/activate  # ou venv\Scripts\activate no Windows
   ```
3. Instale as dependências do backend:
   ```bash
   pip install -r backend/requirements.txt
   ```
4. Configure o banco de dados (por padrão, SQLite para dev).
5. Execute as migrações:
   ```bash
   python manage.py migrate
   ```
6. Inicie o servidor de desenvolvimento:
   ```bash
   python manage.py runserver
   ```
7. (Opcional) Execute a API via [`manage.py`](manage.py) a partir da raiz ou dentro de `backend/`.

### Frontend Next.js (headless)
```bash
cd frontend
npm install
npm run dev  # http://localhost:3000
```

Configure `NEXT_PUBLIC_API_BASE_URL` (ver `frontend/.env.example`) para apontar para o domínio do backend (`http://localhost:8000/api` em desenvolvimento).
- A página `/` apresenta o blog público do colégio consumindo o endpoint aberto `/api/blog/public`.
- O painel autenticado fica exposto em `/dashboard`, mantendo as restantes páginas (`/checklists`, `/pit`, `/diario`, `/assistente`).

#### Ferramentas de apoio Frontend

- `npm run generate:api` — gera `src/types/openapi.ts` a partir do esquema exposto em `/api/schema` (usa `API_SCHEMA_URL` quando necessário). O arquivo `docs/api-schema.yaml` facilita a execução offline.
- `npm run storybook` — abre a biblioteca de componentes headless (ex.: cartões de módulo) na porta `6006`; útil para demonstrar o UI kit à direção.
- `npm run test:e2e` — corre testes Playwright sobre o fluxo visitante → login. Execute `npx playwright install chromium` uma vez antes da primeira corrida.
- `npm run lint` — lint React/TypeScript com as novas páginas (`/checklists`, `/pit`, `/diario`, `/assistente`).

## Estrutura do Projeto
- `backend/` — Projeto Django (apps, config, static, migrations, testes)
- `frontend/` — Aplicação Next.js 15 (App Router, Tailwind, React Query)
- `docs/` — Documentação funcional/técnica consolidada
- `deploy/` — Exemplos de configuração (systemd, nginx, env)
- `TODO.md` — Roadmap incremental

## Deploy em Produção

### Checklist de Preparação
- [ ] Configure o arquivo `.env` a partir de `.env.example` com todas as variáveis reais (nunca suba o real para o repositório)
- [ ] Atualize `requirements.txt` e instale dependências em ambiente virtual
- [ ] Rode `python manage.py migrate` para aplicar as migrations
- [ ] Rode `python manage.py collectstatic` para coletar arquivos estáticos
- [ ] Rode `python manage.py compilemessages` para internacionalização
- [ ] Configure o banco de dados PostgreSQL e usuário dedicado
- [ ] Configure Gunicorn como serviço (exemplo em `deploy/gunicorn.service.example`)
- [ ] Configure Nginx como proxy reverso (exemplo em `deploy/nginx.conf.example`)
- [ ] Ative HTTPS (Let's Encrypt recomendado)
- [ ] Configure backup regular do banco e da pasta `/media/`

### Variáveis de Ambiente
- Backend: `deploy/.env.example`
- Frontend: `frontend/.env.example`
- Opcional (backend): `NOTIFICATION_WEBHOOK_URL` para replicar avisos por HTTP além de email.

### Comandos Essenciais
```sh
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp deploy/.env.example .env  # edite com seus dados reais
python manage.py migrate
python manage.py collectstatic
python manage.py compilemessages
```

### Exemplos de Configuração
- Gunicorn: `deploy/gunicorn.service.example`
- Nginx: `deploy/nginx.conf.example`
- .env: `deploy/.env.example`

## Fluxo rápido de desenvolvimento

```sh
# 1) Ativar virtualenv
source venv/bin/activate

# 2) Instalar/atualizar dependências
pip install -r requirements.txt

# 3) Migrar base de dados e (opcional) criar superuser
python manage.py migrate
# python manage.py createsuperuser

# 4) (Opcional) compilar traduções se editar ficheiros .po/.mo
python manage.py compilemessages

# 5) Iniciar servidor
python manage.py runserver
```

## Dados de demonstração

O repositório inclui um comando que gera um cenário MEM completo (utilizadores, turmas, blog, checklists, PIT, projetos, conselho e traços de IA) para testes e demonstrações.

```sh
# criar dados
python manage.py demo_data

# recriar dados do zero
python manage.py demo_data --reset

# remover dados demo
python manage.py demo_data --clean

# opções adicionais
python manage.py demo_data --classes=3 --alunos=12 --seed=123
```

Para segurança, o comando só corre se `DEBUG=True` ou se definir `ALLOW_DEMO_SEED=1` no ambiente. Todos os registos criados são catalogados e removidos automaticamente com `--clean`.

No final da execução é apresentada uma tabela com os logins demo (email e palavra-passe `demo1234`) para validação manual.

## Dicas rápidas de Git

```sh
# Ver estado e branch atual
git status -sb

# Trazer alterações remotas
git pull --rebase

# Adicionar e commitar
git add -A
git commit -m "Mensagem descritiva"

# Enviar para a branch remota atual
git push
```
