# Repository Guidelines

## Project Structure & Module Organization
- `manage.py` orquestra as tarefas Django; configurações principais ficam em `infantinho3/`.
- Apps centrais: `users/`, `classes/`, `blog/`, `checklists/`, `projects/`, `pit/`, `council/`, `ai/`, `diary/`, cada um com models, forms, views e `tests.py` dedicados.
- `templates/` agrupa layouts partilhados; `static/` contém ativos compilados; `locale/` guarda traduções; `deploy/` traz exemplos de serviço e variáveis; `demo/` disponibiliza seeds MEM.
- `media_dev/` é apenas para uploads locais; limpe ou ignore antes de commitar.

## Build, Test, and Development Commands
- `python -m venv venv && source venv/bin/activate`: cria/ativa o ambiente virtual.
- `pip install -r requirements.txt`: instala dependências bloqueadas para Django 5.2.
- `python manage.py migrate`: aplica migrações de base de dados.
- `python manage.py runserver`: sobe o servidor local em `http://localhost:8000`.
- `python manage.py demo_data --reset`: repõe um cenário MEM completo (ativo apenas com `DEBUG=True` ou `ALLOW_DEMO_SEED=1`).
- `python manage.py collectstatic` e `python manage.py compilemessages`: preparam assets estáticos e ficheiros de tradução.

## Coding Style & Naming Conventions
- Python com indentação de 4 espaços, `snake_case` para funções/campos e `CamelCase` para models/forms; agrupe imports por ordem standard/third-party/local.
- Prefira padrões Django (class-based views, `forms.ModelForm`) e reutilize helpers existentes antes de criar utilitários novos.
- Marque strings traduzíveis com `gettext_lazy`; mantenha blocos de templates alinhados com os nomes em `templates/`.
- Segredos, chaves e endpoints residem em `.env`; nunca os hardcode.

## Testing Guidelines
- Cada app possui `tests.py`; expanda-os com novos casos em vez de criar ficheiros paralelos.
- Execute `python manage.py test` antes de abrir PRs; cubra modelos, permissões e fluxos de formulário relevantes.
- Para comandos de seed ou migrações, adicione asserts que validem objetos criados e perfis de acesso.

## Commit & Pull Request Guidelines
- Utilize Conventional Commits (`feat:`, `fix:`, `docs:`, `chore:`), seguindo o histórico (`feat: refresh MEM workflows and IA helpers`).
- Uma feature ou correção por branch; inclua migrações e atualizações de `locale/` quando aplicável.
- PRs devem trazer contexto, comandos de teste executados, links para TODOs/issues e capturas de ecrã para alterações visuais.
- Garanta estado "verde": migrações aplicam, testes passam e não existem prints de debug.

## Environment & Security Notes
- Baseie-se em `deploy/.env.example` para configurar `.env`; mantenha o ficheiro real fora do repositório.
- Produção espera PostgreSQL; SQLite serve apenas para desenvolvimento local.
- Use `ALLOW_DEMO_SEED=1` com parcimónia fora de dev e limpe dados gerados após testes.
