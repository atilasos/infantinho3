# TODO – Roadmap de Desenvolvimento Infantinho 3.0

Este ficheiro serve como guia prático para o desenvolvimento incremental do portal, alinhado ao contexto pedagógico e técnico do projeto. As tarefas estão organizadas por fases, com entregas claras e pontos de validação.

---

## Fase 0 – Planeamento e Configuração Inicial
- [x] 0.1 Rever requisitos com stakeholders (direção, professores MEM)
- [x] 0.2 Configurar repositório Git
- [x] 0.3 Preparar ambiente de desenvolvimento (Python 3.x, Django, DB local)
- [x] 0.4 Configurar integração contínua (pipeline de testes automáticos)
- [x] 0.5 Modelar esquema inicial da base de dados (entidades principais)
- [x] 0.6 Esboçar wireframes das principais telas (opcional, mas recomendado)
- [ ] 0.7 Planejar e implementar separação de versões: dev, mvp, full (branches Git e/ou ambientes de deploy)

## Fase 1 – Autenticação e Gestão Básica de Utilizadores/Turmas
- [x] 1.1 Implementar login/logout via SSO Microsoft (Azure AD)
- [x] 1.2 Criar modelos User e Turma (incluindo grupos/papéis)
- [x] 1.3 Views básicas: lista de turmas do professor, página de turma vazia
- [x] 1.4 Painel admin mínimo para validar utilizadores e atribuir papéis
- [x] 1.5 Testar fluxo: convidado → aluno/professor
    - [ ] Manual de teste:
        1. Criar/utilizar um utilizador convidado (status='convidado', role vazio).
           - No shell Django:
             ```python
             from users.models import User
             guest = User.objects.create_user(username='guest', email='guest@escola.pt', password='guest', status='convidado')
             admin = User.objects.create_user(username='admin', email='admin@escola.pt', password='admin', role='admin', status='ativo')
             prof = User.objects.create_user(username='prof', email='prof@escola.pt', password='prof', role='professor', status='ativo')
             prof2 = User.objects.create_user(username='prof2', email='prof2@escola.pt', password='prof2', role='professor', status='ativo')
             aluno = User.objects.create_user(username='aluno', email='aluno@escola.pt', password='aluno', role='aluno', status='ativo')
             ```
        2. Entrar como admin e promover o convidado a professor via admin ou método promote_to_role.
        3. Entrar como professor da turma e promover o convidado a aluno via página "Adicionar aluno/convidado".
        4. Confirmar que o utilizador promovido tem o papel correto e acesso esperado.
        5. Confirmar que professores de outras turmas não conseguem promover convidados nesta turma.
        6. Para correr os testes automáticos:
           ```bash
           python manage.py test users
           python manage.py test classes
           ```
- [x] 1.6 Entrega parcial: professor pode criar turma, aluno pode ser adicionado

## Fase 2 – Módulo de Blog/Diário de Turma (MVP Parte 1)
- [x] 2.1 Modelos de Dados
    - [x] 2.1.1 Criar modelo `Post`:
        - Campos: turma (FK), autor (FK), título (opcional), conteúdo (RichText), data/hora, categoria/tipo (choices), visibilidade (default: interna).
    - [x] 2.1.2 Criar modelo `Comment`:
        - Campos: post (FK), autor (FK), conteúdo, data/hora.
    - [x] 2.1.3 Adicionar métodos auxiliares nos modelos:
        - Ex: is_editable_by(user), get_category_display(), is_visible_to(user), remover(user, motivo=None), etc.
    - [x] 2.1.4 Migrar e testar modelos.
- [x] 2.2 Permissões e Visibilidade
    - [x] 2.2.1 Definir regras de acesso:
        - Apenas membros da turma (alunos, professores, encarregados) e admin podem ver posts.
        - Apenas professores e alunos da turma podem criar posts.
        - Professores podem editar/remover qualquer post da sua turma; alunos apenas os seus.
    - [x] 2.2.2 Decorators/mixins para views protegidas por turma e papel.
- [x] 2.3 Views e URLs
    - [x] 2.3.1 Listar posts da turma:
        - URL: `/turmas/<id>/blog/`
        - Filtros: categoria, data.
        - Paginação.
    - [x] 2.3.2 Ver post individual:
        - URL: `/turmas/<id>/blog/post/<id>/`
        - Exibir comentários.
    - [x] 2.3.3 Criar post:
        - URL: `/turmas/<id>/blog/novo/`
        - Formulário com CKEditor.
    - [x] 2.3.4 Editar/remover post:
        - URLs: `/turmas/<id>/blog/post/<id>/editar/`, `/remover/`
        - Permissões conforme regras.
    - [x] 2.3.5 Adicionar/remover comentário (AJAX ou formulário simples):
        - URL: `/turmas/<id>/blog/post/<id>/comentar/`
        - Professores podem remover comentários.
- [x] 2.4 Templates
    - [x] 2.4.1 Criar templates para:
        - Listagem de posts (com filtros, agrupamento por mês/semana).
        - Visualização de post (com comentários).
        - Formulário de criação/edição (com CKEditor).
        - Confirmação de remoção.
    - [x] 2.4.2 Herdar de `base.html` global e de turma.
- [ ] 2.5 Editor de Texto Rico
    - [x] 2.5.1 Integrar CKEditor (ou similar) no campo de conteúdo do post.
    - [x] 2.5.2 Configurar upload de imagens (media storage seguro) [TinyMCE ativo]
    - [ ] 2.5.3 Testar formatação básica, listas, links, imagens.
    - [ ] 2.6 Notificações
    - [x] 2.6.1 Enviar email para membros da turma ao criar post (usar SMTP O365).
    - [x] 2.6.2 Notificar encarregados apenas para categorias "Aviso" (corrigido).
    - [x] 2.6.3 Notificar autor do post sobre novos comentários.
- [x] 2.7 Testes e Validação
    - [x] 2.7.1 Testes unitários dos modelos (criação, permissões).
    - [x] 2.7.2 Testes de views (acesso, criação, edição, remoção).
    - [x] 2.7.3 Testes de permissões (aluno só na sua turma, professor modera).
    - [x] 2.7.4 Testes de notificações (mock de envio de email).
    - [x] 2.7.5 Testes manuais com utilizadores reais.
- [x] 2.8 Moderação e Logs
    - [x] 2.8.1 Professores podem editar/remover posts e comentários.
    - [x] 2.8.2 Guardar logs de moderação (quem removeu o quê).
- [x] 2.9 Documentação e UX
    - [x] 2.9.1 Documentar uso do blog para professores/alunos.
    - [x] 2.9.2 Garantir acessibilidade e usabilidade dos templates.

## Fase 3 – Módulo de Listas de Verificação (MVP Parte 2)
- [x] 3.1 Modelos e Estrutura de Dados
    - Implementar modelos: ChecklistTemplate, ChecklistItem, ChecklistStatus (e opcionalmente ChecklistMark para histórico)
    - ChecklistItem deve incluir: texto do objetivo, campo opcional de critérios/descritores, campo booleano "contratualizado_em_conselho"
    - ChecklistStatus/ChecklistMark deve permitir comentários do aluno e do professor, armazenar data e autor de cada marcação
    - Criar migrações e scripts de seed para os modelos
- [x] 3.2 Pré-carregamento de Templates
    - Pré-carregar templates de 1-2 disciplinas/anos (ex: Português 5.º ano, Matemática 7.º ano) com dados reais das Aprendizagens Essenciais
    - Garantir que scripts de seed só afetam dev/test
- [x] 3.3 UI Aluno: Página de Marcação de Objetivos
    - Página "As minhas aprendizagens" listando disciplinas e itens
    - Permitir marcação/desmarcação de itens (autoavaliação), com destaque visual de que é autoavaliação
    - Permitir adicionar comentário em cada item
    - (Opcional) Adicionar nota/evidência ao marcar concluído
- [x] 3.4 UI Professor: Visão Geral e Validação
    - Página de visão geral da turma: alunos vs. % de conclusão por disciplina
    - Permitir validação/retificação de marcações dos alunos, com possibilidade de comentário
    - Visualização coletiva (alunos x itens), com destaque para itens "contratualizados em conselho"
- [x] 3.5 Lógica de Marcação, Validação e Notificações
    - Permissões: aluno só altera o próprio status, professor valida/retifica, admin tudo
    - Notificações para professor e aluno sobre marcações e validações
    - Histórico de alterações de estado, incluindo data, autor e comentário
- [x] 3.6 Testes Automatizados
    - Testar criação/edição de templates, itens e status
    - Testar fluxo de marcação e validação, incluindo comentários e campos pedagógicos
    - Testar permissões e notificações
    - Garantir que seeds/scripts não afetam produção
- [ ] 3.7 Entrega e Monitorização
    - Listas ativas por aluno
    - Monitorização pelo professor (progresso coletivo e individual)
    - Documentação dos modelos, endpoints, scripts e instruções de uso

## Fase 4 – Feedback MVP e Ajustes
- [ ] 4.0 Planejar e implementar separação de versões: dev, mvp, full (branches Git e/ou ambientes de deploy)
- [ ] 4.1 Apresentar MVP a professores MEM (validação de usabilidade)
- [ ] 4.2 Recolher feedback e iterar design se necessário
- [ ] 4.3 Corrigir bugs e ajustar funcionalidades essenciais

### Permissões Unificadas
- [ ] Criar e aplicar decorators de permissão comuns por app (evitar checks inline)

### Autenticação MSAL
- [x] Documentar `ALLOWED_EMAIL_DOMAINS` e ler via env
- [x] Remover pipeline social-auth não utilizado dos settings

## Fase 5 – Módulo PIT (Planos Individuais de Trabalho)
 - [x] 5.1 Criar modelos PIT (IndividualPlan) e PlanTask
 - [x] 5.2 Views Aluno: criar/editar PIT, submeter
 - [x] 5.3 Views Professor: aprovar PIT, visualizar
- [ ] 5.4 Formulários de autoavaliação (aluno) e avaliação (professor)
 - [x] 5.5 Notificações básicas (submissão, aprovação, avaliação) - IMPLEMENTADO
 - [x] 5.6 Garantir restrição: só um PIT por período
 - [x] 5.7 Testes de fluxo principal e casos de concorrência
- [ ] 5.8 Integração leve com checklists (botão para abrir checklist)

## Fase 6 – Módulo Projetos Cooperativos
 - [x] 6.1 Criar modelos Project e ProjectTask
 - [x] 6.2 Views: criar projeto (prof/aluno), adicionar membros, listar/detalhar projetos
- [x] 6.3 Permissões: só membros editam - IMPLEMENTADO (2026-02-02)
- [x] 6.4 Testes: criar projeto, adicionar update - IMPLEMENTADO (5 testes)

## Fase 7 – Módulo Conselho de Turma
- [x] 7.1 Criar modelos CouncilDecision e StudentProposal
- [x] 7.2 Views: propor pauta (aluno), listar propostas, aprovar/discutir (professor), registar decisão
- [ ] 7.3 Ligação opcional com Diário (parsear posts marcados como decisões) - OPCIONAL
- [x] 7.4 Testes: propor, aprovar, listar decisão - IMPLEMENTADO (2 testes)

## Fase 8 – Integração de IA (Protótipo)
- [ ] 8.1 Implementar `ai_service` para chamada à API (OpenAI GPT-3.5 ou similar)
- [ ] 8.2 Interface de chat (botão/modal para aluno e professor)
- [ ] 8.3 Prompts básicos: nome, papel, texto fixo do sistema
- [ ] 8.4 Testes manuais de perguntas simples

## Fase 9 – Aprimoramento dos Agentes de IA
- [ ] 9.1 Incorporar dados reais nos prompts (ex: resumo do PIT, status das listas)
- [ ] 9.2 Pipeline de meta-agente (se viável) ou guidelines no prompt
- [ ] 9.3 Gravar logs de Q&A, permitir admin ver logs
- [ ] 9.4 Testar Google API como alternativa (opcional)
- [ ] 9.5 Recolher feedback de utilizadores sobre IA
- [ ] 9.6 Documentar funcionamento e limites da IA

## Fase 10 – Internacionalização Completa
- [ ] 10.1 Extrair strings para ficheiro .po
- [ ] 10.2 Completar tradução PT-PT
- [ ] 10.3 Adicionar EN (ou outro) como teste (20% das strings)
- [ ] 10.4 Interface para troca de idioma (menu drop-down)
- [ ] 10.5 Testar páginas-chave em EN

## Fase 11 – Refinação, Testes Finais e Deploy Piloto
- [ ] 11.1 Teste de carga leve (simular 300 alunos)
- [ ] 11.2 Revisão de segurança (HTTPS, cookies, endpoints)
- [ ] 11.3 Depuração de bugs finais
- [ ] 11.4 Preparar scripts de deployment (Dockerfile/docker-compose ou guia)
- [ ] 11.5 Configurar servidor de produção (Ubuntu, Gunicorn, Nginx, PostgreSQL)
- [ ] 11.6 Preparar documentação e tutoriais para utilizadores
- [ ] 11.7 Realizar formação para professores
- [ ] 11.8 Deploy piloto para 1-2 turmas

## Fase 12 – Revisão Pós-Piloto e Expansão
- [ ] 12.1 Recolher feedback real de uso
- [ ] 12.2 Ajustar funcionalidades conforme feedback
- [ ] 12.3 Entrar em ciclo ágil de melhorias
- [ ] 12.4 Planejar funcionalidades extra (ex: integração com sistema de notas, gamificação)
- [ ] 12.5 Escalar para todas as turmas do colégio
- [ ] 12.6 Monitorizar desempenho e uso

---

## Mapa atual de views, urls e templates

```
users/
├── views.py
│   ├── login_choice          <-- /auth/login/ (login_choice.html)
│   ├── login_local           <-- /auth/login/local/ (login.html)
│   ├── login_microsoft       <-- /auth/login/microsoft/
│   ├── callback_microsoft    <-- /auth/callback/microsoft/
│   ├── logout_microsoft      <-- /auth/logout/microsoft/
│   ├── password_reset        <-- /auth/password-reset/ (password_reset.html, password_reset_done.html)
├── templates/users/
│   ├── login_choice.html
│   ├── login.html
│   ├── password_reset.html
│   ├── password_reset_done.html

classes/
├── views.py
│   ├── class_list            <-- /turmas/ (class_list.html)
│   ├── class_detail          <-- /turmas/<id>/ (class_detail.html)
│   ├── add_student           <-- /turmas/<id>/adicionar-aluno/ (add_student.html)
│   ├── manage_classes        <-- /admin/turmas/ (manage_classes.html)
│   ├── landing_page          <-- / (landing.html)
├── templates/classes/
│   ├── class_list.html
│   ├── class_detail.html
│   ├── add_student.html
│   ├── manage_classes.html
│   ├── landing.html
│   └── base.html

blog/
├── templates/blog/
│   └── base.html

checklists/
├── templates/checklists/
│   └── base.html

templates/
└── base.html (template global)
```

- As setas `<--` indicam o path/url que ativa cada view e o template associado (quando aplicável).
- Apps `blog` e `checklists` têm apenas templates base, sem views/urls implementadas.
- O template global `base.html` é herdado por todos os templates principais. 