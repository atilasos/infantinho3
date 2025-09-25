# Wave A — Backlog Operacional (MVP PIT Digital)

## Objetivo da Wave A

Entregar a fundação do PIT Digital: modelo/versionamento mínimo, criação e edição de planos semanais, exportação PDF simples e permissões/auditoria.

## Historias focadas

- H1 Criar PIT semanal a partir de modelo.
- H2 Editar áreas e tarefas do PIT.
- H7 Exportação PDF básica.
- H8 Permissões por papel & auditoria mínima.

## Tarefas detalhadas

### 1. Modelo de dados e versionamento (H1, H2)
- [x] Introduzir entidades `PitTemplate`, `TemplateSection`, `TemplateSuggestion` (versão datada, aplicado por turma/ciclo).
- [x] Migrar `IndividualPlan` para ligar a `PitTemplate` e armazenar `template_version`.
- [x] Campos novos: `suggestions_imported`, `pending_imported`, `origin_plan_id` para rastrear transporte.
- [x] Criar sementes/demo para templates por ciclo.
- [x] Documentar ER atualizado (`docs/diagrama_dados.md`).

### 2. Serviço de geração do PIT (H1)
- [x] Endpoint POST `/pit/plans/generate` que recebe turma+semana.
- [x] Carregar sugestões do conselho + pendentes (integração simplificada).
- [x] Criar default sections/áreas conforme template.
- [x] Notas de auditoria (log "generated_from_template").
- [x] Tests unitários para transporte e datas corretas.

### 3. UI/UX de criação e edição (H1, H2)
- [x] Página Next com wizard semanal (selecionar semana → revisão de sugestões → editar tarefas).
- [x] Editor drag-and-drop por área + filtros disciplina/tipo.
- [x] Validações front (campos obrigatórios, limites) e feedback inline.
- [x] Auto-save (debounce) + indicador de estado (rascunho/submetido).
- [x] Modo professor: leitura com campos para feedback geral.

### 4. Exportação PDF (H7)
- [x] Serviço backend (WeasyPrint/ReportLab) gerando A4 com capa, resumo, tarefas por área e sugestões importadas.
- [x] Endpoint `/pit/plans/{id}/export-pdf` + permissão por papel.
- [x] Component no frontend com botão "Exportar" e loading.
- [x] Teste gerando PDF dummy (snapshot via hash/byte length).

- [x] Reforçar policies nas views/API usando DRF permission classes declarativas.
- [x] Logger central (middleware) para mudanças de estado e tarefas (quem, quando, de → para).
- [x] Atualizar seeds: papéis aluno/professor/admin/coordenação.
- [x] Testes de autorização para endpoints críticos.
- [x] Doc curta de papéis + fluxo de aprovação.

## Dependências externas / riscos
- Integração com app `council` para sugestões pode exigir refactor do modelo (fazer stub se necessário).
- Exportação PDF depende da infra (ver storage/limits). Adotar abordagem síncrona primeiro; async se necessário.
- UI drag-and-drop exige escolha de lib (ex.: `@dnd-kit/core` ou nativo). Validar compatibilidade com Next.

## Métricas esperadas pós Wave A
- ≥ 90% dos alunos com PIT gerado a partir do template da turma.
- Tempo médio de geração ≤ 5s.
- Zero incidentes de permissão regressiva (testes tratados).
- PDF exportado em < 3s na demo.
