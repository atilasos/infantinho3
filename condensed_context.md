## Infantinho 3.0 — Estado Atual e Próximos Passos

### Estado atual (implementado)
- Utilizadores e Autenticação
  - Modelo `users.User` (custom) com `email` único, `role` (aluno/professor/admin/encarregado) e `status` (convidado/ativo).
  - Backend de autenticação por email ou username.
  - Login Microsoft (MSAL) com callback e validação de domínio (via `ALLOWED_EMAIL_DOMAINS`).
  - Modelo `GuardianRelation` (encarregado-aluno) e `PreApprovedStudent` (pré-aprovação por email para associação automática a turma).

- Turmas (`classes`)
  - Modelo `Class` com M2M `students` e `teachers` (filtrados por papel).
  - Views: listar turmas, detalhe de turma (estatísticas básicas), adicionar aluno (promove convidado a aluno), pré-aprovar alunos, gerir turmas (criar turma), associar checklist à turma, detalhe de aluno (inclui checklists e posts do diário, se ativos).

- Blog/Diário de Turma (`blog`)
  - Modelos: `Post`, `Comment`, `ModerationLog` com workflow PENDING/PUBLISHED, soft-delete, anexos (imagem/ficheiro) e aprovação por professor/admin.
  - Views: lista por turma, criação por turma, detalhe global por `post_id`, editar/remover/restaurar, lista de pendentes, aprovar post, listagem pública paginada (landing), upload de imagens (TinyMCE).
  - Editor: TinyMCE configurado com upload.

- Diário MEM (`diary`)
  - Modelos: `DiarySession` (sessão ativa/arquivada), `DiaryEntry` (colunas: GOSTEI/NAO_GOSTEI/FIZEMOS/QUEREMOS).
  - Views: ver sessão ativa/por id, adicionar entrada, arquivar e iniciar nova sessão.

- Listas de Verificação (`checklists`)
  - Modelos: `ChecklistTemplate`, `ChecklistItem`, `ChecklistStatus` (por aluno/turma/template), `ChecklistMark` (estado do item: NOT_STARTED/IN_PROGRESS/COMPLETED/VALIDATED, com comentários e validação docente).
  - Views: "As minhas aprendizagens" (aluno), detalhe de checklist (aluno, marcação), visão de turma (professor, validação/retificação) e ajuda.
  - Command `load_checklists` para seed de templates/itens.

- PIT (`pit`)
  - Modelos: `IndividualPlan` (rascunho/submetido/aprovado/concluído/avaliado) e `PlanTask`.
  - Views: criar/editar/submeter (aluno), listar e aprovar/devolver (professor).

- Projetos (`projects`)
  - Modelos: `Project`, `ProjectTask`.
  - Views: listar/criar/detalhar por turma.

- Conselho (`council`)
  - Modelos: `CouncilDecision` e `StudentProposal`.
  - Views: listar decisões e propostas, criar decisão (professor), criar proposta (aluno).

- Feedback interno (`infantinho_feedback`)
  - Modelo `FeedbackItem` e views para submeter, listar (por utilizador/admin) e atualizar estado/apagar (admin).

- Infraestrutura
  - Django 5.2, i18n ativada (PT-PT), estáticos/media prontos, `django-impersonate`, `widget_tweaks`, `tinymce`.
  - `requirements.txt` atualizado; BD SQLite por defeito (PostgreSQL via env vars).

### Pontos em falta/ajustes prioritários
- Autenticação/SSO
  - Definir `ALLOWED_EMAIL_DOMAINS` no `.env` e documentar; pipeline `social-auth` está configurado nos settings mas biblioteca não está nas dependências (vestigial). Decidir: manter apenas MSAL (atual) ou integrar `social-auth-app-django` e alinhar.

- Blog/Notificações
  - Função de notificação usa categoria "DIARIO", mas essa opção já não existe nas `CATEGORIA_CHOICES`. Ajustar para notificar encarregados apenas em "AVISO" (ou reintroduzir categoria de Diário, se desejado).

- Permissões
  - Consolidar decorators de permissão (algumas views usam checks inline); garantir consistência para aluno/professor/admin/encarregado em todas as apps.

- PIT
  - Falta UI de autoavaliação/avaliação final e notificações (submissão/aprovação/avaliação).

- Projetos/Conselho
  - Rever permissões e adicionar testes/UX mínimos (p. ex., atualizações de projeto, mudança de estado de decisão, listagens paginadas).

- I18N/UX
  - Rever strings para `gettext`, compilar mensagens, garantir PT-PT consistente; polir templates base e navegação entre módulos (links na página da turma).

- Segurança/Operação
  - CSRF no upload do TinyMCE está isento; avaliar alternativa com token. Configurar `SECURE_*` em produção. Adicionar grupos padrão na migração inicial.

### Próximos passos (ordem sugerida)
1) Corrigir fluxo de notificações do Blog
   - Remover referência a "DIARIO" e notificar encarregados apenas para `AVISO`.
   - Rever emails e textos; adicionar link seguro para o post.

2) Fechar Autenticação MSAL
   - Documentar e carregar `ALLOWED_EMAIL_DOMAINS` no `.env`.
   - Remover/arquivar configuração `social-auth` não usada OU adicionar dependência e integrar de facto.

3) Permissões unificadas
   - Criar `permissions.py` por app (ou comum) com decorators reutilizáveis; aplicar nas views que hoje fazem checks inline.

4) PIT — avaliação e notificações
   - Formulários de autoavaliação/avaliação; emails (aluno/professor) ao submeter/aprovar/avaliar.

5) UX da Turma
   - Na `class_detail`, ligar Blog, Diário, Checklists, PIT, Projetos e Conselho com contadores e CTAs.

6) Diário — qualidade de vida
   - Listar sessões arquivadas; editar/apagar entradas por moderadores; botão iniciar sessão visível só a prof/admin.

7) Testes
   - Cobrir permissão/acesso e fluxos principais (blog, checklists, PIT) e fixtures mínimos.

8) I18N/Operação
   - Compilar traduções, preparar `collectstatic`, rever `SECURE_*` e `ALLOWED_HOSTS` para staging.

9) IA (protótipo, pós-MVP consolidado)
   - Criar `ai_service` stub e UI de chat simples para professor/aluno.

### Notas rápidas
- Editor Rich Text ativo (TinyMCE) com upload para `MEDIA_ROOT`.
- Seeds: comandos para checklists e demo users/turmas presentes.
- BD: pronto para PostgreSQL via env vars.


