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
  - UI: listagens (turma e pública) com cartões responsivos, filtros por categoria/data e badges de estado.
  - Editor: TinyMCE configurado com upload.

- Diário MEM (`diary`)
  - Modelos: `DiarySession` (sessão ativa/arquivada), `DiaryEntry` (colunas: GOSTEI/NAO_GOSTEI/FIZEMOS/QUEREMOS).
  - Views: ver sessão ativa/por id, adicionar entrada, arquivar e iniciar nova sessão.

- Listas de Verificação (`checklists`)
  - Modelos: `ChecklistTemplate`, `ChecklistItem`, `ChecklistStatus` (por aluno/turma/template), `ChecklistMark` (estado do item: NOT_STARTED/IN_PROGRESS/COMPLETED/VALIDATED, com comentários e validação docente).
  - Views: "As minhas aprendizagens" (aluno), detalhe de checklist (aluno, marcação), visão de turma (professor, validação/retificação) e ajuda.
  - UI (turma): cabeçalhos dos itens com badges agregadas (validados/completos/em progresso/por iniciar) e progresso individual/coletivo visível.
  - Command `load_checklists` para seed de templates/itens.

- PIT (`pit`)
  - Modelos: `IndividualPlan` (rascunho/submetido/aprovado/concluído/avaliado) e `PlanTask`.
  - Views: criar/editar/submeter (aluno), listar e aprovar/devolver (professor), autoavaliação do aluno e avaliação do professor.
  - Notificações: emails em submissão e aprovação/devolução implementados.
  - UI/UX: lista do professor com filtros (estado/pesquisa), paginação e badges de estado; formulário do aluno com breadcrumbs/CTAs consistentes.

- Projetos (`projects`)
  - Modelos: `Project`, `ProjectTask`.
  - Views: listar/criar/detalhar por turma.
  - UI: listagem com cartões, badges por estado e contagem de membros; filtros (estado/pesquisa), paginação; breadcrumbs/CTAs consistentes.

- Conselho (`council`)
  - Modelos: `CouncilDecision` e `StudentProposal`.
  - Views: listar decisões e propostas, criar decisão (professor), criar proposta (aluno).
  - UI: listagem com cartões e badges por estado; filtros (estado/categoria), paginação; breadcrumbs/CTAs consistentes.

- Feedback interno (`infantinho_feedback`)
  - Modelo `FeedbackItem` e views para submeter, listar (por utilizador/admin) e atualizar estado/apagar (admin).

- Infraestrutura
  - Django 5.2, i18n ativada (PT-PT), estáticos/media prontos, `django-impersonate`, `widget_tweaks`, `tinymce`.
  - `djangorestframework` adicionado e configurado; `requirements.txt` atualizado.
  - `requirements.txt` atualizado; BD SQLite por defeito (PostgreSQL via env vars).

### Permissões (unificadas)
- Módulo `users/permissions.py` com helpers:
  - `is_admin`, `is_teacher_of_class`, `is_student_in_class`
  - `can_access_class` (acesso de leitura: admin/professor/aluno)
  - `can_moderate_class` (moderação: admin/professor)
- Decorators reutilizáveis (respondem 403 quando aplicável):
  - `class_member_required`, `class_teacher_required`, `class_student_required`
- Aplicação atual:
  - `diary`: usa helpers para acesso/moderação; rota extra `diary/archived/` para listar sessões.
  - `classes`: cálculo de `can_view_class`, `can_create_post`, `can_add_student` via helpers.
  - `projects`: `class_member_required` (listar/detalhe), `class_teacher_required` (criar).
  - `council`: `decision_list` (member), `decision_create` (teacher), `proposal_create` (member).
  - `infantinho_feedback`: `is_admin` para vista admin.
  - `blog`: mantém decorators próprios (`turma_member_required`, `turma_post_create_required`, etc.) por requisitos de testes (inclui regra especial: encarregados podem ler mas não criar/editar).

### Pontos em falta/ajustes prioritários
- Autenticação/SSO
  - Definir `ALLOWED_EMAIL_DOMAINS` no `.env` e documentar; pipeline `social-auth` está configurado nos settings mas biblioteca não está nas dependências (vestigial). Decidir: manter apenas MSAL (atual) ou integrar `social-auth-app-django` e alinhar.

- Blog/Notificações
  - Concluído: notificar encarregados apenas para categoria "AVISO"; links seguros incluídos.

- Permissões
  - Restantes apps já usam helpers; blog mantém decorators específicos. Próxima evolução: expandir helpers para contemplar encarregados (leitura) e cenários comuns (redirect vs 403) e substituir checks inline remanescentes.

- PIT
  - Concluído: autoavaliação do aluno, avaliação do professor e notificações de submissão/aprovação/devolução.
  - Em aberto: polir UI/UX (rótulos, ajuda contextual) e estados finais.

- Projetos/Conselho
  - UI base concluída (cartões/badges). Em aberto: filtros simples, paginação e mudanças de estado rápidas.

- I18N/UX
  - Em aberto: rever strings `gettext`, compilar mensagens, garantir PT-PT consistente; polir navegação.

- Segurança/Operação
  - CSRF no upload do TinyMCE está isento; avaliar alternativa com token. Configurar `SECURE_*` em produção. Adicionar grupos padrão na migração inicial.

### Próximos passos (ordem sugerida)
1) Fechar Autenticação MSAL
   - Documentar e carregar `ALLOWED_EMAIL_DOMAINS` no `.env`.
   - Remover/arquivar configuração `social-auth` não usada OU adicionar dependência e integrar de facto.

2) Permissões unificadas
   - Expandir `users/permissions.py` com:
     - `is_guardian_of_any_student_in_class`, `can_view_as_guardian`
     - `class_member_or_guardian_required` (leitura incluindo encarregados)
   - Aplicar gradualmente em apps que precisem de leitura por encarregados.

3) PIT — polir UI/UX e métricas
   - Afinar formulários, mensagens e estados; adicionar lembretes de prazo (opcional).

4) UX da Turma
   - `class_detail`: contadores reais concluídos; acrescentar CTAs diretas para cada módulo.

5) Diário — qualidade de vida
   - Sessões arquivadas concluídas; acrescentar edição/remoção por moderadores e controlos de visibilidade do botão "iniciar sessão".

6) Testes
   - Cobrir permissão/acesso e fluxos principais (blog, checklists, PIT) e fixtures mínimos.

7) I18N/Operação
   - Compilar traduções, preparar `collectstatic`, rever `SECURE_*` e `ALLOWED_HOSTS` para staging.

8) IA (protótipo, pós-MVP consolidado)
   - Orientação pedagógica: IA como mediadora de comunicação e síntese (não corretora). Foco em co-construção, evidências, rotinas cooperativas e explicabilidade para docentes e alunos.
   - Funcionalidades (faseadas e MEM-compatíveis):
     - Tutor dialógico (planeamentos, conselhos, assembleias, diários): gera perguntas abertas, não respostas finais.
     - Sínteses (aluno/turma) a partir de evidências: distingue factos vs hipóteses e mostra sempre fontes; rascunho com validação docente obrigatória.
     - Ajuda à cooperação: distribuição justa de tarefas, rotação de papéis, check-ins de participação.
     - Feedback formativo por rubricas MEM (autonomia, cooperação, comunicação, responsabilidade, criatividade, autoavaliação) com próximas ações (sem notas).
     - Curadoria de portefólios (seleção de artefactos por critérios co-definidos).
     - Observatório de comunicação (mapa simples de interações/tempo de fala para promover equidade, começando por métricas básicas a partir de eventos/diário).
     - Preparação do Conselho: agenda, recolha de propostas, síntese de decisões e compromissos.
   - Princípios de segurança/ética:
     - Consentimento granular por finalidade; minimização de dados; pseudonimização; direitos de acesso/retificação.
     - Human-in-the-loop: professor valida cada síntese antes de circular.
     - Rastreabilidade: cada frase da síntese liga a evidências via `Summary`/`EventLink`.
     - Explicabilidade curta: “o que foi usado”, “como foi resumido”, “com que confiança”.
   - Arquitetura de dados (alinhada a Django):
     - Reutilizar modelos existentes: `users.User`, `classes.Class`, `blog.Post`, `diary.*`, `checklists.*`, `pit.*`, `projects.*`, `council.*`.
     - Novos modelos (app `evidence` ou `ai_core`):
       - `Rubric(name)`, `Descriptor(rubric, text, scale_json)` — vocabulário MEM.
       - `Event(student, turma, teacher, type, occurred_at, payload_json, source_uri)` — observação/participação/artefacto/reflexão/etc.
       - `Artefact(student, turma, title, kind, storage_uri, metadata_json, created_at)` — ficheiros em `MEDIA_ROOT` (dev) e S3/MinIO (prod).
       - `Summary(scope, scope_id, period, version, content_json, rationale_json, created_by, created_at, approved_by, approved_at)` — sínteses rascunho/validadas.
       - `EventLink(event, artefact, summary)` — ligações para rastreabilidade.
     - Objetivos/planos: reutilizar `pit.IndividualPlan`/`PlanTask` e `checklists.ChecklistItem`/`ChecklistMark`. Ligar por ID dentro de `content_json`/`metadata_json` quando necessário (evitar duplicar `Goal/Plan`).
   - Índice vetorial e RAG:
     - v0 (protótipo): sem vetor — busca estruturada por turma/aluno/data + RAG leve com conteúdos do Blog/Diário/Events.
     - v0.2: Postgres com `pgvector` (coleções `events`, `artefacts`, `reflexoes`), embeddings de texto limpo + tags MEM + data + turma/aluno.
   - Algoritmo de “condensação” controlada (heurísticas):
     - Facto exige ≥2 evidências de momentos e fontes distintas; decaimento temporal favorece recente; nunca incluir dados sensíveis não pedagógicos.
     - Hipótese aceita 1 evidência; confiança calculada por diversidade temporal + fonte (<0.7 indica baixa evidência).
     - Saídas alvo: “Cartão de Aprendizagem do Aluno” e “Síntese de Turma” em JSON estruturado (com listas de `facts`, `hypotheses`, `next_actions`, `sources`).
   - Fluxos de uso:
     - Professor regista `Event`/`Artefact`; IA sugere descritores MEM e níveis; professor valida/edita.
     - Geração de `Summary` rascunho; professor aprova; só então fica visível à turma/encarregados.
     - Conselho: pauta/síntese a partir de eventos e metas; exportável para ata (integra com Blog/Diário).
     - Portefólio: seleção semiautomática com critérios negociados.
   - API mínima (Django views/DRF):
     - `POST /api/events` — criar observação/participação/reflexão.
     - `POST /api/artefacts` — upload + metadados.
     - `POST /api/summaries/draft` — gerar rascunho de Cartão/Síntese de Turma.
     - `POST /api/summaries/approve` — aprovar síntese.
     - `GET /api/students/{id}/card?period=AAAA-SX` — obter Cartão.
     - `GET /api/turmas/{id}/summary?period=AAAA-SX` — obter Síntese de Turma.
     - `GET /api/trace/{summary_id}` — fontes e explicações.
   - UI essencial:
     - Editor de observações com sugestões de descritores MEM e exemplos.
     - Painel de turma com rede de interação e “calor” por rubrica.
     - Cartões de aprendizagem editáveis por professor/aluno; botão “Porquê?” em cada frase mostra eventos/artefactos ligados.
   - Stack/execução:
     - Backend: Django; `ai_service` com provider configurável (OpenAI/Google). Jobs de síntese com Celery (opcional) e fila.
     - Vetorial: introduzir `pgvector` assim que migrarmos para Postgres.
     - Autenticação: manter MSAL/OIDC; respeitar consentimento granular por finalidade.
     - Operação/privacidade: auditoria append-only e política de retenção por período letivo.
   - Fases:
     - 9.1 (v0.1) — ENTREGUE (backend mínimo): criada app `ai_core` com modelos `Rubric`, `Descriptor`, `Event`, `Artefact`, `Summary`, `EventLink`; endpoints `POST /api/events` e `POST /api/summaries/draft`; sinais em `blog` e `diary` a criar `Event`; serviço de síntese heurístico (sem vetores).
     - 9.2 (v0.2): `pgvector` + condensação explicável (factos/hipóteses/next_actions) + painéis básicos e painel lateral “IA da Turma”.
     - 9.3 (v0.3): observatório de comunicação e curadoria de portefólio; integração mais profunda com PIT/Checklists e Conselho.

   - Estado atual (implementado — IA):
     - App `ai_core` ativa em `INSTALLED_APPS`.
     - DRF instalado e namespace `/api/` registado.
     - Sinais: `blog.Post` e `diary.DiaryEntry` geram `Event` automaticamente.
     - Geração de rascunho de síntese (aluno/turma) com rastreio de fontes via `EventLink`.

   - Em falta para v0.2:
     - Endpoints: `POST /api/artefacts` (upload e metadados), `POST /api/summaries/approve`, `GET /api/students/{id}/card`, `GET /api/turmas/{id}/summary`, `GET /api/trace/{summary_id}`.
     - Suportar JSON body nos endpoints e validação de consentimentos/finalidades.
     - Painel lateral reutilizável (UI) e botões contextuais por app.
     - Integração `pgvector` (PostgreSQL) e pipeline de embeddings para `Event/Artefact`.
     - Regras de permissão finas para encarregados (leitura) aplicadas a endpoints IA.
     - Upload de `Artefact` (armazenamento S3/MinIO em produção) e form de observações com sugestões de descritores MEM.

   - Integração transversal por app (papel da IA e ligações):
     - `classes` (página da turma): painel lateral “IA da Turma” com comandos rápidos (preparar conselho, síntese semanal, rotação de papéis). Sugere dinâmicas cooperativas, aponta temas recorrentes e liga a evidências.
     - `blog` (diário de turma): no editor, sugestões de perguntas abertas e estrutura de reflexão; gerar resumo para encarregados (apenas rascunho); apoio à moderação (detetar conteúdo sensível) mantendo decisão humana.
     - `diary` (sessão MEM): sugestões de prompts por coluna (GOSTEI/NAO_GOSTEI/FIZEMOS/QUEREMOS); após sessão, síntese rascunho com ligações a entradas; identificação leve de participação para equidade.
     - `checklists`: ajuda a mapear evidências a itens; guia de autoavaliação com perguntas; sugestões de próximos passos; criação automática de `Event` ao marcar/validar itens para rastreabilidade.
     - `pit`: tutor dialógico para planear tarefas ligadas a objetivos e checklists; apoio à autoavaliação (perguntas, não notas); resumo para aprovação do professor com referências a evidências.
     - `projects`: decomposição de tarefas, distribuição justa, rotação de papéis; lembretes de check-ins; curadoria de artefactos ligados ao portefólio da turma.
     - `council`: preparação de agenda a partir de propostas/eventos; minuta/ata em rascunho; síntese de decisões/compromissos com rastreio.
     - `infantinho_feedback`: triagem assistida (agregação de temas), preservando anonimato quando aplicável; sugestões de UX para admin.
     - `users`/autenticação: gestão de consentimentos por finalidade; preferências de IA (ativar/desativar por utilizador/turma).

   - Pontos de integração técnica:
     - UI: botões “Perguntar à IA”/“Gerar síntese” contextuais em cada app; painel lateral reutilizável com contexto (utilizador, turma, objeto atual).
     - Backend: sinais (post_save) criam `Event` para ações-chave (post criado, entrada de diário, marcação checklist, mudança de estado PIT/projeto, decisão de conselho).
     - DRF: endpoints já listados sob `/api/...`; todos respeitam `class_member_or_guardian_required` e consentimentos.
     - Permissões: IA só lê dados autorizados ao utilizador atual; guardas adicionais para conteúdos de alunos quando o solicitante é encarregado (leitura, sem edição).
     - Auditoria: registar chamadas de síntese (quem, quando, finalidade) em log append‑only.

   - Faseamento por app (incremental):
     - 9.1: `checklists` + `pit` (tutor dialógico básico, geração de rascunhos de cartão do aluno), `diary` (prompts), `classes` (painel mínimo).
     - 9.2: `blog` (resumos rascunho), `council` (agenda/minuta), `projects` (distribuição de tarefas), índice vetorial para RAG.
     - 9.3: observatório de comunicação (rede/tempo de fala leve), curadoria de portefólio e integrações cruzadas (PIT ↔ Checklists ↔ Blog/Projetos ↔ Conselho).

### Notas rápidas
- Editor Rich Text ativo (TinyMCE) com upload para `MEDIA_ROOT`.
- Seeds: comandos para checklists e demo users/turmas presentes.
- BD: pronto para PostgreSQL via env vars.


