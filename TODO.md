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
        - Formulário com TinyMCE.
    - [x] 2.3.4 Editar/remover post:
        - URLs: `/turmas/<id>/blog/post/<id>/editar/`, `/remover/`
        - Permissões conforme regras.
    - [x] 2.3.5 Adicionar/remover comentário (AJAX ou formulário simples):
        - URL: `/turmas/<id>/blog/post/<id>/comentar/`
        - Professores podem remover comentários.
    - [x] 2.3.6 Adicionar orientações pedagógicas MEM nos formulários e detalhe do blog para orientar alunos e professores.
- [x] 2.4 Templates
    - [x] 2.4.1 Criar templates para:
        - Listagem de posts (com filtros, agrupamento por mês/semana).
        - Visualização de post (com comentários).
        - Formulário de criação/edição (com TinyMCE).
        - Confirmação de remoção.
    - [x] 2.4.2 Herdar de `base.html` global e de turma.
- [ ] 2.5 Editor de Texto Rico
    - [x] 2.5.1 Integrar TinyMCE com toolbar MEM-friendly e autosave.
    - [x] 2.5.2 Configurar upload autenticado de imagens (media storage seguro).
    - [x] 2.5.3 Cobrir o fluxo com testes (upload válido e rejeição de tipos inválidos).
- [ ] 2.6 Notificações
    - [x] 2.6.1 Enviar email para membros da turma ao criar post (usar SMTP O365).
    - [x] 2.6.2 Notificar encarregados apenas para categorias "Diário de Turma" ou "Aviso".
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
- [ ] 3.1 Modelos e Estrutura de Dados
    - [x] Implementar modelos: ChecklistTemplate, ChecklistItem, ChecklistStatus e ChecklistMark
    - [x] Adicionar campo booleano `contratualizado_em_conselho` (pendente planeamento com equipa pedagógica)
    - [x] ChecklistStatus/ChecklistMark permitem comentários, data e autor de cada marcação
    - [x] Criar migrações e scripts de seed para os modelos
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
    - Visualização coletiva (alunos x itens) com destaque visual para itens "contratualizados em conselho"
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
    - [x] Listas ativas por aluno ("As minhas aprendizagens")
    - [x] Monitorização pelo professor (grade coletiva com validação)
    - [ ] Documentação dos modelos, endpoints, scripts e instruções de uso

## Fase 4 – Feedback MVP e Ajustes
- [ ] 4.0 Planejar e implementar separação de versões: dev, mvp, full (branches Git e/ou ambientes de deploy)
- [ ] 4.1 Apresentar MVP a professores MEM (validação de usabilidade)
- [ ] 4.2 Recolher feedback e iterar design se necessário
- [ ] 4.3 Corrigir bugs e ajustar funcionalidades essenciais

## Fase 5 – Módulo PIT (Planos Individuais de Trabalho)
 - [x] 5.1 Criar modelos PIT (IndividualPlan) e PlanTask
 - [x] 5.2 Views Aluno: criar/editar PIT, submeter
 - [x] 5.3 Views Professor: aprovar PIT, visualizar
 - [x] 5.4 Formulários de autoavaliação (aluno) e avaliação (professor)
 - [x] 5.5 Notificações básicas (submissão, aprovação, avaliação)
 - [x] 5.6 Garantir restrição: só um PIT por período
 - [x] 5.7 Testes de fluxo principal e casos de concorrência
- [ ] 5.8 Integração leve com checklists (botão para abrir checklist)

## Fase 6 – Módulo Projetos Cooperativos
 - [x] 6.1 Criar modelos Project e ProjectTask
 - [x] 6.2 Views: criar projeto (prof/aluno), adicionar membros, listar/detalhar projetos
 - [x] 6.3 Permissões: só membros editam
 - [x] 6.4 Testes: criar projeto, adicionar update

## Fase 7 – Módulo Conselho de Turma
- [x] 7.1 Criar modelos CouncilDecision e StudentProposal (categorias, estados, responsável opcional)
- [x] 7.2 Views: propor pauta (aluno), listar propostas/decisões, registar decisão (professor)
- [ ] 7.3 Ligação opcional com Diário (parsear posts marcados como decisões)
- [x] 7.4 Testes: propor, aprovar, listar decisão

## Fase 8 – Fundação da Orquestração IA MEM
- [x] 8.1 Criar app `ai` com modelos `AIRequest`, `AIInteractionSession`, `AIResponseLog` e serviço `AIRequestOrchestrator`
- [x] 8.2 Implementar `PromptOptimizer` (GPT-5 nano) com fallback local para dev/teste
- [x] 8.3 Implementar `ModelRouter` para distribuir pedidos entre GPT-5 nano/mini/normal com configuração no admin
- [x] 8.4 Construir `ContextBroker` + `LearnerContextSnapshot` mínimo alimentado por PIT e checklists
- [x] 8.5 Expor endpoint/serviço `ai_assistant` (REST) com testes unitários e de contrato
- [x] 8.6 Registar custos estimados por chamada e criar alertas básicos via logging

## Fase 9 – IA Contextualizada e Integrada nas Apps
- [x] 9.1 Ligar botões/contextos IA no blog, PIT, checklists, projetos e conselho mantendo UX natural
- [x] 9.2 Enriquecer `ContextBroker` com decisões de conselho, diário e notas do professor (resumos automáticos via GPT-5 nano)
- [x] 9.3 Implementar `ResponseGuard` (nano) e painéis de auditoria/admin (limites, quotas, logs, custo)
- [x] 9.4 Configurar caching e rate limiting específicos por turma/utente
- [x] 9.5 Criar guias pedagógicos MEM (templates de prompt) e recolher feedback estruturado de alunos/professores
- [x] 9.6 Documentar arquitetura IA, políticas de dados e procedimentos de revisão humana
- [x] 9.7 Avaliar modelos alternativos (ex: GPT-5 mini, modelos open) com base em custo/benefício

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

## Mapa atual de apps, views e templates principais

```
users/
├── urls.py → /auth/login/, /auth/login/local/, /auth/login/microsoft/, /auth/logout/, /auth/password-reset/
├── views.py → login_choice, login_local, login_microsoft, callback_microsoft, logout_microsoft, password_reset
└── templates/users/ → login_choice.html, login.html, password_reset.html, password_reset_done.html

classes/
├── urls.py → /turmas/, /turmas/<id>/, /turmas/<id>/adicionar-aluno/
├── views.py → class_list, class_detail, add_student, manage_classes, landing_page
└── templates/classes/ → class_list.html, class_detail.html, add_student.html, manage_classes.html, landing.html, base.html

blog/
├── urls.py (`blog:`) → /blog/, /blog/post/<id>/, /blog/post/<id>/comentar/, /blog/pendentes/
├── class_urls.py (`class_blog:`) → /turmas/<class_id>/blog/…, criação dentro da turma
├── views.py → post_list, post_list_public, post_detail, post_create/post_edit, post_remove/post_restore, post_pending_list, moderation_logs, tinymce_image_upload
└── templates/blog/ → post_list.html, post_list_public.html, post_detail.html, post_form.html, post_form_global.html, post_pending_list.html, moderation_logs.html, blog_help.html, *confirm_remove*.html, base.html

checklists/
├── urls.py → /checklists/minhas/, /checklists/<template_id>/, /checklists/turma/<class_id>/<template_id>/
├── views.py → MyChecklistsView, ChecklistDetailView, ChecklistTurmaView, HelpView
└── templates/checklists/ → my_checklists.html, checklist_detail.html, checklist_turma.html, help.html, base.html

pit/
├── urls.py → /pit/<class_id>/novo/, /pit/<class_id>/<plan_id>/, /pit/<class_id>/<plan_id>/autoavaliacao/, /pit/<class_id>/professor/, /pit/<class_id>/<plan_id>/avaliar/
├── views.py → my_current_plan_redirect, plan_create, plan_edit, plan_self_evaluate, TeacherPlanListView, TeacherPlanApproveView, plan_teacher_evaluate
└── templates/pit/ → plan_form.html, plan_list_teacher.html, plan_self_evaluation.html, plan_teacher_evaluation.html

projects/
├── urls.py → /projetos/<class_id>/, /projetos/<class_id>/novo/, /projetos/<class_id>/<project_id>/, /projetos/<class_id>/<project_id>/editar/
├── views.py → project_list, project_create, project_detail, project_update
└── templates/projects/ → project_list.html, project_form.html, project_detail.html

council/
├── urls.py → /conselho/<class_id>/, /conselho/<class_id>/decisao/novo/, /conselho/<class_id>/proposta/novo/
├── views.py → decision_list, decision_create (professor), proposal_create (aluno)
└── templates/council/ → decision_list.html, decision_form.html, proposal_form.html

diary/
├── urls.py (`diary:`) → /turmas/<class_id>/diario/…
├── views.py → view_diary, add_diary_entry, archive_and_start_new_session
└── templates/diary/ → view_diary.html, no_active_diary.html

infantinho_feedback/
├── urls.py → /feedback/, /feedback/obrigado/, /feedback/<pk>/estado/, /feedback/<pk>/apagar/
├── views.py → feedback_submit_view, feedback_thank_you_view, feedback_update_status_view, feedback_delete_view
└── templates/infantinho_feedback/ → feedback_form.html, feedback_thank_you.html, includes/partials

templates/
└── base.html → layout global partilhado (nav, mensagens, carregamento de TinyMCE)
```

- As setas indicam URLs principais e o respetivo namespace.
- A maioria das apps já dispõe de views, templates e testes de fluxo básicos; documentação complementar está a ser atualizada fase a fase.
