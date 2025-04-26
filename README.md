# Infantinho 3.0

Portal educativo para o Colégio Infante Dom Henrique, alinhado com o Modelo Pedagógico do Movimento da Escola Moderna (MEM).

> **Desenvolvimento incremental:**
> Consulte o arquivo `TODO.md` para o roadmap detalhado, fases de implementação e tarefas técnicas. O desenvolvimento segue as etapas e prioridades ali descritas.

## Visão Geral
O Infantinho 3.0 é um portal educativo que facilita a gestão cooperada da aprendizagem, digitalizando instrumentos pedagógicos do MEM, como listas de verificação de aprendizagens, Planos Individuais de Trabalho (PIT), planos de projeto, diário de turma e registo de decisões do conselho de turma. Integra agentes de Inteligência Artificial (IA) para apoiar alunos e professores.

## Funcionalidades Principais
- **Gestão de Turmas e Utilizadores**: Criação e gestão de turmas, perfis de alunos, professores, encarregados de educação e administradores.
- **Ferramentas Cooperativas MEM**: Listas de verificação, PIT, planos de projeto, diário de turma, registo de decisões.
- **Blog/Diário de Turma**: Blog por turma para registo de atividades, reflexões e produções.
- **Participação Ativa dos Alunos**: Alunos criam posts, propõem e autoavaliam PITs, participam em projetos e interagem com IA.
- **Ferramentas do Professor**: Gestão de turmas, avaliação/validação de PITs e aprendizagens.
- **Agentes de IA Colaborativos**: Assistentes virtuais para apoio contextualizado, alinhados com documentos pedagógicos.
- **Autenticação Federada**: Login via contas Microsoft escolares (Office 365/Azure AD).
- **Internacionalização**: Interface em Português Europeu, preparada para outros idiomas.

## Arquitetura e Tecnologias
- **Backend**: Python (Django), ORM integrado, autenticação, i18n.
- **Frontend**: Django Templates (MVP), possível evolução para SPA (React/Vue) no futuro.
- **Base de Dados**: PostgreSQL (produção), SQLite (desenvolvimento).
- **Integração Microsoft**: OAuth2/OpenID Connect via bibliotecas como social-auth-app-django.
- **IA**: Integração com OpenAI GPT ou Google PaLM, configurável pelo administrador.
- **Administração**: Painel para configuração de domínios, IA, língua padrão, gestão global.
- **Segurança**: Controlo de acesso por papéis, validação de dados, conformidade RGPD.
- **Internacionalização**: Suporte nativo a múltiplos idiomas via Django.

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
3. Instale as dependências:
   ```bash
   pip install -r requirements.txt
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

## Estrutura do Projeto
- `users/` — Gestão de utilizadores, papéis e autenticação
- `classes/` — Gestão de turmas
- `blog/` — Módulo de blog/diário de turma
- `checklists/` — Listas de verificação de aprendizagens

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
Veja o arquivo `deploy/.env.example` para todas as variáveis necessárias.

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